#!/usr/bin/env python3
"""Hook PreToolUse (Bash): zakazy gitowe i bramka CI przed scaleniem do main/master.

To barierka dla agenta, który współpracuje, a nie zabezpieczenie: aliasy gita, skrypty, `bash -c "…"`
i ręczna praca właściciela przechodzą. Ochronę po stronie serwera (reguły gałęzi na GitHubie) ustawia projekt.

Polecenie jest dzielone na kroki (`;`, `&&`, `||`, `|`, nowa linia). Hook śledzi w nim `cd`, `git -C`
i zmiany gałęzi (`git switch`/`checkout`), więc ocenia gałąź, na której krok faktycznie się wykona.

- `git push`: liczy gałęzie docelowe. Zakaz, gdy któraś to main/master (jawnie, przez `HEAD` albo push bez
  refspecu z main), przy force pushu (`--force`, `-f`, `+refspec`; dozwolone `--force-with-lease`)
  oraz przy `--mirror`, `--all`, `--prune`. Usunięcie własnej gałęzi (`--delete feat/x`) i tagi są dozwolone.
- `git commit` na main/master. Wyjątki: pierwszy commit w repo, dokończenie merge po `git pull`.
- `git merge` do main/master: wolno tylko aktualizację z `origin/main`.
- `git cherry-pick|rebase|reset|revert|am` na main/master: zakaz; wolno `reset --hard origin/main`,
  `reset [-- plik]` (unstage) oraz `--abort/--continue/--skip/--quit`.
- `gh pr merge` do main/master tylko, gdy CI na GitHubie jest zielone dla ostatniego commita PR.
  Gdy GitHub nie uruchomił testów (PR tylko z dokumentacją, brak minut) — wystarczy, że ten sam stan
  przeszedł lokalnie `bash tools/ci.sh` (zapis w .git/ci-passed; to deklaracja agenta, nie dowód).
  Błąd testów na GitHubie blokuje zawsze; błąd `gh` (brak logowania, sieć) też blokuje, z komunikatem.

Blokada = exit 2 + komunikat na stderr (trafia do agenta). Własna awaria hooka nie blokuje, ale jest widoczna:
exit 1 + komunikat + wpis w .git/trybik-hooks.log.
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hooklib import crashed  # noqa: E402

MAIN = ("main", "master")
PR_ONLY = "Do {b} scalamy tylko przez PR: `gh pr merge --squash` (automat sprawdza wtedy CI)."
SEPARATORS = {";", "&&", "||", "|", "&", "\n", "(", ")", "|&", ";;"}
REDIRECT = re.compile(r"^[<>&]+$")
# opcje globalne gita przed podkomendą; True = bierze wartość w osobnym tokenie
GIT_GLOBAL = {"-C": True, "-c": True, "--git-dir": True, "--work-tree": True, "--namespace": True,
              "--exec-path": False, "-P": False, "--no-pager": False, "-p": False, "--paginate": False,
              "--bare": False, "--no-replace-objects": False, "--literal-pathspecs": False,
              "--no-optional-locks": False}
PUSH_VALUE_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
PUSH_BANNED = {"--mirror", "--all", "--prune"}
MERGE_VALUE_FLAGS = {"-m", "-F", "--file", "-s", "--strategy", "-X", "--strategy-option"}
REWRITE = ("cherry-pick", "rebase", "reset", "revert", "am")
SEQUENCE_CONTROL = {"--abort", "--quit", "--continue", "--skip"}
GH_VALUE_FLAGS = {"-t", "--subject", "-b", "--body", "-F", "--body-file", "-A", "--author-email",
                  "--match-head-commit", "-R", "--repo"}
JOB_URL = re.compile(r"github\.com/([^/]+/[^/]+)/actions/runs/\d+/job/(\d+)")


def run(cmd, cwd, timeout=30):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return p.stdout


def git(cwd, *args):
    try:
        return run(["git", *args], cwd, timeout=5).strip()
    except (RuntimeError, OSError):
        return None


def split(args):
    try:
        return shlex.split(args)
    except ValueError:
        return args.split()


def positional(tokens, value_flags):
    out, skip = [], False
    for t in tokens:
        if skip:
            skip = False
        elif t in value_flags:
            skip = True
        elif not t.startswith("-"):
            out.append(t)
    return out


def steps(command):
    """Polecenie → lista kroków (listy tokenów), z pominięciem przekierowań (`> plik`, `2>&1`)."""
    lex = shlex.shlex(command, posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError:  # niedomknięty cudzysłów: zgrubny podział
        tokens = re.sub(r"(;|&&|\|\||\||\n)", r" \1 ", command).split(" ")
    out, cur, skip = [], [], False
    for t in tokens:
        if skip:
            skip = False
        elif t in SEPARATORS:
            if cur:
                out.append(cur)
            cur = []
        elif REDIRECT.match(t):
            if cur and cur[-1].isdigit():
                cur.pop()  # deskryptor przed przekierowaniem (`2>`)
            skip = True  # następny token to plik albo deskryptor (`>&1`)
        elif t:
            cur.append(t)
    if cur:
        out.append(cur)
    return out


class State:
    """Katalog i gałąź, w których wykona się kolejny krok polecenia."""

    def __init__(self, cwd):
        self.cwd = cwd
        self.branch = None  # None = odczytaj z repo

    def at(self, cwd):
        return self.branch if self.branch is not None else current_branch(cwd)


def current_branch(cwd):
    return git(cwd, "symbolic-ref", "--short", "-q", "HEAD")


def resolve(cwd, path):
    p = Path(path).expanduser()
    return str(p if p.is_absolute() else Path(cwd) / p)


def parse_git(tokens, cwd):
    """`git [opcje globalne] sub args…` → (katalog, sub, args)."""
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        t = tokens[i]
        name = t.split("=", 1)[0]
        takes = GIT_GLOBAL.get(name, False) and "=" not in t
        if name == "-C" and i + 1 < len(tokens):
            cwd = resolve(cwd, tokens[i + 1])
        i += 2 if takes else 1
    if i >= len(tokens):
        return cwd, None, []
    return cwd, tokens[i], tokens[i + 1:]


def switched_to(sub, args, cwd):
    """Gałąź po `git switch`/`checkout` albo None, gdy krok nie zmienia gałęzi."""
    if sub not in ("switch", "checkout"):
        return None
    if "--" in args:
        return None  # `git checkout main -- plik` przywraca plik, nie zmienia gałęzi
    create = {"-c", "-C", "--create", "--force-create", "-b", "-B"}
    for i, t in enumerate(args):
        if t in create and i + 1 < len(args):
            return args[i + 1]
    pos = positional(args, {"--orphan"})
    if args[:1] == ["-"] or pos[:1] == ["-"]:
        return git(cwd, "rev-parse", "--abbrev-ref", "@{-1}") or ""
    if "--detach" in args or not pos:
        return None if not pos else ""
    if sub == "checkout" and git(cwd, "rev-parse", "--verify", "-q", f"refs/heads/{pos[0]}") is None:
        if git(cwd, "rev-parse", "--verify", "-q", f"refs/remotes/origin/{pos[0]}") is None:
            return None  # `git checkout plik` (bez `--`) albo commit — nie zmienia gałęzi na nazwaną
    return pos[0]


def check_push(args, branch):
    if any(t in ("--force", "-f") for t in args) or any(re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", t) for t in args):
        return "Force push jest zabroniony (dozwolone `--force-with-lease`). Jeśli naprawdę potrzebny, właściciel robi go ręcznie."
    banned = PUSH_BANNED & set(args)
    if banned:
        return f"`git push {' '.join(sorted(banned))}` jest zabroniony dla agenta (może nadpisać albo usunąć {'/'.join(MAIN)})."
    pos = positional(args, PUSH_VALUE_FLAGS)
    refspecs = pos[1:]  # pierwszy pozycyjny = remote
    if any(r.startswith("+") for r in refspecs):
        return "Force push (`+refspec`) jest zabroniony. Jeśli naprawdę potrzebny, właściciel robi go ręcznie."
    if "--tags" in args and not refspecs:
        return None
    if not refspecs:
        return PR_ONLY.format(b=branch) if branch in MAIN else None
    for r in refspecs:
        dst = r.split(":", 1)[-1]
        if dst.startswith("refs/tags/"):
            continue
        dst = dst[len("refs/heads/"):] if dst.startswith("refs/heads/") else dst
        if dst in ("HEAD", "@") and ":" not in r:
            dst = branch
        if dst in MAIN:
            return PR_ONLY.format(b=dst)
    return None


def check_commit(branch, switched, cwd):
    if branch not in MAIN:
        return None
    if not switched:
        if git(cwd, "rev-parse", "--verify", "-q", "HEAD") is None:
            return None  # pierwszy commit w repo
        gitdir = git(cwd, "rev-parse", "--git-dir")
        if gitdir and (Path(cwd) / gitdir / "MERGE_HEAD").exists():
            return None  # dokończenie merge po `git pull`
    return (
        f"Commit na gałęzi {branch} jest zabroniony. Utwórz branch: wg ticketu "
        "`git switch -c feat/T-NNN-slug` (albo fix|chore|docs/…), a bez ticketu "
        "(kickoff, szkice ticketów) `git switch -c docs/<temat>`."
    )


def check_merge(args, branch):
    if SEQUENCE_CONTROL & set(args) or branch not in MAIN:
        return None
    allowed = (f"origin/{branch}", "FETCH_HEAD", "@{u}", "@{upstream}")
    if all(t in allowed for t in positional(args, MERGE_VALUE_FLAGS)):
        return None  # aktualizacja main z GitHuba
    return PR_ONLY.format(b=branch)


def check_rewrite(sub, args, branch):
    if SEQUENCE_CONTROL & set(args) or branch not in MAIN:
        return None
    if sub == "reset":
        if not {"--hard", "--soft", "--mixed", "--keep", "--merge"} & set(args):
            return None  # `git reset` / `git reset -- plik` = tylko unstage
        targets = positional(args, set())
        if targets[:1] in ([f"origin/{branch}"], ["@{u}"], ["@{upstream}"]):
            return None  # synchronizacja z GitHubem
    return f"`git {sub}` na {branch} jest zabroniony: zmiany na {branch} tylko przez PR."


def outcome(c):
    if c.get("__typename") == "StatusContext":
        return {"SUCCESS": "ok", "PENDING": "pending", "EXPECTED": "pending"}.get(c.get("state"), "fail")
    if c.get("status") != "COMPLETED":
        return "pending"
    return {"SUCCESS": "ok", "SKIPPED": "skip", "NEUTRAL": "skip"}.get(c.get("conclusion"), "fail")


def not_started(c, cwd):
    """Zadanie GitHub Actions zakończone bez uruchomienia (brak minut / limit wydatków): bez runnera i kroków."""
    m = JOB_URL.search(c.get("detailsUrl") or "")
    if not m:
        return False
    try:
        job = json.loads(run(["gh", "api", f"repos/{m.group(1)}/actions/jobs/{m.group(2)}"], cwd))
    except Exception:
        return False
    return not job.get("runner_name") and not job.get("steps")


def passed_locally(cwd, sha):
    tree = git(cwd, "rev-parse", "-q", "--verify", f"{sha}^{{tree}}") if sha else None
    common = git(cwd, "rev-parse", "--git-common-dir")
    if not tree or not common:
        return False
    f = Path(cwd) / common / "ci-passed"
    return f.exists() and tree in f.read_text(encoding="utf-8").split()


def check_pr_merge(args, cwd):
    pos = positional(args, GH_VALUE_FLAGS)
    repo = next((args[i + 1] for i, t in enumerate(args[:-1]) if t in ("-R", "--repo")), None)
    cmd = ["gh", "pr", "view", *pos[:1], *(["-R", repo] if repo else []),
           "--json", "baseRefName,headRefOid,statusCheckRollup"]
    try:
        info = json.loads(run(cmd, cwd))
    except (RuntimeError, OSError, ValueError) as e:
        return (f"Nie udało się sprawdzić CI przez `gh pr view` ({str(e)[:200] or type(e).__name__}). "
                "Sprawdź `gh auth status` i połączenie, potem spróbuj ponownie.")
    if info.get("baseRefName") not in MAIN:
        return None
    checks = info.get("statusCheckRollup") or []

    def names(cs):
        return ", ".join(c.get("name") or c.get("context") or "?" for c in cs)

    pending = [c for c in checks if outcome(c) == "pending"]
    if pending:
        return f"CI na GitHubie jeszcze trwa ({names(pending)}). Poczekaj: `gh pr checks --watch`, potem scal."
    failed = [c for c in checks if outcome(c) == "fail"]
    ran = [c for c in failed if not not_started(c, cwd)]
    if ran:
        return (f"CI na GitHubie nie przeszło ({names(ran)}). Szczegóły: `gh pr checks`; "
                "popraw, wypchnij i poczekaj na zielone.")
    if not failed and any(outcome(c) == "ok" for c in checks):
        return None
    if passed_locally(cwd, info.get("headRefOid")):
        return None
    return ("GitHub nie uruchomił testów dla tego PR (PR tylko z dokumentacją albo brak minut na GitHubie). "
            "Uruchom `bash tools/ci.sh` na tym branchu (wszystko zacommitowane, ten sam commit co w PR) "
            "i scal ponownie.")


def check(command, cwd):
    state = State(cwd)
    for tokens in steps(command):
        while tokens and re.match(r"^[A-Za-z_]\w*=", tokens[0]):
            tokens = tokens[1:]  # `VAR=x git …`
        if not tokens:
            continue
        prog = tokens[0]
        if prog == "cd":
            state.cwd = resolve(state.cwd, tokens[1]) if len(tokens) > 1 else str(Path.home())
            state.branch = None
            continue
        if prog == "gh" and tokens[1:3] == ["pr", "merge"]:
            msg = check_pr_merge(tokens[3:], state.cwd)
        elif prog == "git":
            step_cwd, sub, args = parse_git(tokens, state.cwd)
            other_repo = step_cwd != state.cwd
            branch = current_branch(step_cwd) if other_repo else state.at(step_cwd)
            switched = state.branch is not None and not other_repo
            msg = None
            if sub == "push":
                msg = check_push(args, branch)
            elif sub == "commit":
                msg = check_commit(branch, switched, step_cwd)
            elif sub == "merge":
                msg = check_merge(args, branch)
            elif sub in REWRITE:
                msg = check_rewrite(sub, args, branch)
            else:
                new = switched_to(sub, args, step_cwd)
                if new is not None and not other_repo:
                    state.branch = new
        else:
            continue
        if msg:
            return msg
    return None



def main():
    try:
        data = json.load(sys.stdin)
        command = (data.get("tool_input") or {}).get("command") or ""
        if data.get("tool_name") != "Bash" or ("git" not in command and "gh" not in command):
            return 0
        msg = check(command, data.get("cwd") or ".")
    except Exception:
        return crashed("guard_git")
    if msg:
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):  # UTF-8 niezależnie od kodowania systemu (Windows: cp1250)
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
