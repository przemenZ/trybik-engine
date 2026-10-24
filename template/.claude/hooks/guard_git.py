#!/usr/bin/env python3
"""Hook PreToolUse (Bash): zakazy gitowe i bramka CI przed scaleniem do main/master.

- `git push` z `--force` / `-f` (dozwolone `--force-with-lease`) albo wprost do main (`…:main`).
- `git commit` na main/master. Wyjątki: pierwszy commit w repo, dokończenie merge po `git pull`,
  polecenie, które najpierw tworzy branch (`git switch -c …` / `git checkout -b …`).
- `git merge` do main/master: do main tylko przez PR (wolno tylko aktualizację z `origin/main`).
- `gh pr merge` do main/master tylko, gdy CI na GitHubie jest zielone dla ostatniego commita PR.
  Gdy GitHub nie uruchomił testów (PR tylko z dokumentacją, brak minut) — wystarczy, że ten sam stan
  przeszedł lokalnie `bash tools/ci.sh` (zapis w .git/ci-passed). Błąd testów na GitHubie blokuje zawsze.

Blokada = exit 2 + komunikat na stderr (trafia do agenta). Własna awaria hooka nigdy nie blokuje (exit 0).
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

GIT_CMD = re.compile(r"\bgit\s+(?:-[Cc]\s+\S+\s+)*(commit|push|merge)(?![\w-])([^;&|]*)")
# zmiana gałęzi w tym samym poleceniu: grupa 1 = nowa gałąź (-c/-b), grupa 2 = istniejąca
SWITCH = re.compile(
    r"\bgit\s+(?:(?:switch\s+(?:-c|-C|--create)|checkout\s+-[bB])\s+([^\s;&|]+)"
    r"|(?:switch|checkout)\s+(?!-)([^\s;&|]+))"
)
FORCE = re.compile(r"(?<!\S)(?:--force|-f)(?!\S)")
PUSH_TO_MAIN = re.compile(r":(?:refs/heads/)?(?:main|master)(?![\w/.-])")
GH_MERGE = re.compile(r"\bgh\s+pr\s+merge(?![\w-])([^;&|]*)")
GH_VALUE_FLAGS = {"-t", "--subject", "-b", "--body", "-F", "--body-file", "-A", "--author-email",
                  "--match-head-commit", "-R", "--repo"}
MERGE_VALUE_FLAGS = {"-m", "-F", "--file", "-s", "--strategy", "-X", "--strategy-option"}
JOB_URL = re.compile(r"github\.com/([^/]+/[^/]+)/actions/runs/\d+/job/(\d+)")
MAIN = ("main", "master")
PR_ONLY = "Do {b} scalamy tylko przez PR: `gh pr merge --squash` (automat sprawdza wtedy CI)."


def run(cmd, cwd, timeout=30):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip())
    return p.stdout


def git(cwd, *args):
    try:
        return run(["git", *args], cwd, timeout=5).strip()
    except RuntimeError:
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
        elif not t.startswith("-") and not re.search(r"[<>]", t):
            out.append(t)
    return out


def branch_at(command, pos, cwd):
    """Gałąź, na której wykona się polecenie z pozycji `pos`, i czy zmieniono ją wcześniej w tym samym poleceniu."""
    found = list(SWITCH.finditer(command[:pos]))
    if found:
        m = found[-1]
        return m.group(1) or m.group(2), True
    return git(cwd, "symbolic-ref", "--short", "-q", "HEAD"), False


def check_push(args):
    if FORCE.search(args):
        return "Force push jest zabroniony. Jeśli naprawdę potrzebny, właściciel robi go ręcznie."
    if PUSH_TO_MAIN.search(args):
        return PR_ONLY.format(b="main")
    return None


def check_commit(command, pos, cwd):
    branch, switched = branch_at(command, pos, cwd)
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


def check_merge(command, pos, args, cwd):
    tokens = split(args)
    if {"--abort", "--quit", "--continue"} & set(tokens):
        return None
    branch, _ = branch_at(command, pos, cwd)
    if branch not in MAIN:
        return None
    allowed = (f"origin/{branch}", "FETCH_HEAD", "@{u}", "@{upstream}")
    if all(t in allowed for t in positional(tokens, MERGE_VALUE_FLAGS)):
        return None  # aktualizacja main z GitHuba
    return PR_ONLY.format(b=branch)


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
    return f.exists() and tree in f.read_text().split()


def check_pr_merge(args, cwd):
    tokens = split(args)
    pos = positional(tokens, GH_VALUE_FLAGS)
    repo = next((tokens[i + 1] for i, t in enumerate(tokens[:-1]) if t in ("-R", "--repo")), None)
    cmd = ["gh", "pr", "view", *pos[:1], *(["-R", repo] if repo else []),
           "--json", "baseRefName,headRefOid,statusCheckRollup"]
    info = json.loads(run(cmd, cwd))  # błąd gh → wyjątek → przepuszczamy (gh pr merge i tak się nie uda)
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
    for m in GIT_CMD.finditer(command):
        sub, args = m.group(1), m.group(2)
        if sub == "push":
            msg = check_push(args)
        elif sub == "commit":
            msg = check_commit(command, m.start(), cwd)
        else:
            msg = check_merge(command, m.start(), args, cwd)
        if msg:
            return msg
    for m in GH_MERGE.finditer(command):
        msg = check_pr_merge(m.group(1), cwd)
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
        return 0
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
