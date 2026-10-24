#!/usr/bin/env python3
"""Instaluje albo aktualizuje trybik-engine w katalogu projektu (tylko stdlib). Sam zostaje w repo trybik-engine.

  python3 install.py <katalog-projektu>             pierwsza instalacja (nowy albo istniejący projekt)
  python3 install.py --upgrade <katalog-projektu>   aktualizacja projektu, w którym trybik-engine już jest

Kopiowana jest zawartość `template/`. Pliki dzielą się na dwie grupy:
- kit (KIT_OWNED: hooki, skille, agenci, docs_check, szablony, runbooki, PROCESS.md) — aktualizuje je `--upgrade`;
- projekt (reszta: CLAUDE.md, STATE, QUESTIONS, BACKLOG, journal, ci.sh, settings.json, workflowy…) —
  kopiowane tylko, gdy ich brak; potem należą do projektu i `--upgrade` ich nie rusza.

Pierwsza instalacja, plik projektu różni się od pliku trybik-engine:
- `.gitignore`, `.gitattributes` — dopisuje brakujące linie trybik-engine;
- `.env.example` i workflowy w `.github/workflows/` — zostaje wersja projektu (workflow scala T-001);
- pozostałe — wersja projektu → `<plik>.pre-kit`, na jej miejsce wersja trybik-engine (scalenie: docs/runbooks/adoption.md).

`--upgrade`, plik kitu różni się od nowej wersji:
- projekt go nie zmieniał (skrót zgodny z manifestem `.claude/trybik-engine.json`) → nadpisuje;
- projekt go zmienił albo brak manifestu → wersja projektu → `<plik>.pre-kit`, na jej miejsce nowa wersja.
Pliki projektu zostają; dla `.claude/settings.json` instalator wypisuje hooki i uprawnienia, które doszły w kicie.

Odmawia, gdy: cel to katalog trybik-engine, repo ma niezacommitowane zmiany, repo z historią stoi na main/master,
zostały pliki `*.pre-kit` z poprzedniej instalacji; `--upgrade` także, gdy w celu nie ma trybik-engine.
"""
import filecmp
import fnmatch
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
PAYLOAD = ENGINE / "template"  # wszystko, co trafia do projektu
SKIP = {"__pycache__", "settings.local.json", ".DS_Store"}
KEEP_PROJECT = (".env.example",)
WORKFLOWS = ".github/workflows/"
MANIFEST = ".claude/trybik-engine.json"
KIT_OWNED = (".claude/hooks/*", ".claude/skills/*", ".claude/agents/*", "tools/docs_check.py",
             "docs/templates/*", "docs/runbooks/*", "docs/PROCESS.md")
ENC = {"encoding": "utf-8", "errors": "surrogateescape"}  # obce kodowanie przechodzi bajt w bajt


def kit_owned(rel):
    return any(fnmatch.fnmatch(rel, p) for p in KIT_OWNED)  # `*` w fnmatch obejmuje też `/`


def engine_paths():
    for f in sorted(PAYLOAD.rglob("*")):
        if not SKIP & set(f.relative_to(PAYLOAD).parts) and f.suffix != ".pyc":
            yield f


def sha(path):
    """Skrót niezależny od końców linii (Windows: core.autocrlf zamienia LF na CRLF przy checkoutcie)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def git(target, *args):
    try:
        r = subprocess.run(["git", "-C", str(target), *args], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def version():
    return git(ENGINE, "describe", "--tags", "--always", "--dirty") or "nieznana"


def refusals(target, paths, upgrade):
    out = []
    if target == ENGINE or ENGINE in target.parents:
        out.append("cel to katalog trybik-engine")
    if upgrade and not (target / "tools" / "docs_check.py").exists():
        out.append("w celu nie ma trybik-engine — pierwsza instalacja bez --upgrade")
    if git(target, "rev-parse", "--is-inside-work-tree") == "true":
        if git(target, "status", "--porcelain"):
            out.append("repo ma niezacommitowane zmiany — zacommituj je albo odłóż (git stash)")
        if git(target, "rev-parse", "-q", "--verify", "HEAD") and git(target, "rev-parse", "--abbrev-ref", "HEAD") in ("main", "master"):
            out.append(f"repo stoi na głównej gałęzi — najpierw: git switch -c {'chore/trybik-upgrade' if upgrade else 'docs/adoption'}")
    for src in paths:
        dst = target / src.relative_to(PAYLOAD)
        if Path(str(dst) + ".pre-kit").exists():
            out.append(f"został {dst.relative_to(target)}.pre-kit z poprzedniej instalacji — najpierw go scal")
        if dst.exists() and dst.is_dir() != src.is_dir():
            out.append(f"{dst.relative_to(target)}: w projekcie jest {'katalog' if dst.is_dir() else 'plik'} o tej nazwie")
    return out


def append_missing(src, dst):
    text = dst.read_text(**ENC)
    have = {line.strip() for line in text.splitlines()}
    missing = [l for l in src.read_text(**ENC).splitlines() if l.strip() and not l.startswith("#") and l.strip() not in have]
    if missing:
        sep = "\n" if text and not text.endswith("\n") else ""
        dst.write_text(text + sep + "\n# trybik-engine\n" + "\n".join(missing) + "\n", **ENC)
    return len(missing)


def load_manifest(target):
    try:
        return json.loads((target / MANIFEST).read_text(encoding="utf-8")).get("files", {})
    except (OSError, ValueError):
        return {}


def settings_news(src, dst):
    """Uprawnienia i komendy hooków z settings.json kitu, których brak w settings.json projektu."""
    try:
        kit, proj = (json.loads(p.read_text(encoding="utf-8")) for p in (src, dst))
    except (OSError, ValueError):
        return ["nie da się porównać .claude/settings.json (błędny JSON) — porównaj ręcznie z wersją kitu"]
    out = []
    for kind in ("allow", "ask", "deny"):
        have = set((proj.get("permissions") or {}).get(kind) or [])
        out += [f"permissions.{kind}: {p}" for p in (kit.get("permissions") or {}).get(kind) or [] if p not in have]

    def commands(s):
        return {(event, h.get("command")) for event, groups in (s.get("hooks") or {}).items()
                for g in groups for h in g.get("hooks") or []}

    out += [f"hooks.{e}: {c}" for e, c in sorted(commands(kit) - commands(proj))]
    for k, v in (kit.get("env") or {}).items():
        if k not in (proj.get("env") or {}):
            out.append(f"env.{k}: {v}")
    return out


def main(argv):
    upgrade = "--upgrade" in argv
    args = [a for a in argv if a != "--upgrade"]
    if len(args) != 1:
        print("użycie: python3 install.py [--upgrade] <katalog-projektu>")
        return 2
    target = Path(args[0]).expanduser().resolve()
    paths = list(engine_paths())
    errors = refusals(target, paths, upgrade)
    for e in errors:
        print(f"ODMOWA: {e}")
    if errors:
        return 1

    manifest = load_manifest(target)
    new = same = updated = appended = 0
    kept, moved, settings = [], [], []
    hashes = {}
    for src in paths:
        rel = src.relative_to(PAYLOAD).as_posix()
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        if kit_owned(rel):
            hashes[rel] = sha(src)
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            new += 1
        elif filecmp.cmp(src, dst, shallow=False):
            same += 1
        elif rel in (".gitignore", ".gitattributes"):
            appended += append_missing(src, dst)
        elif upgrade and not kit_owned(rel):
            if rel == ".claude/settings.json":
                settings = settings_news(src, dst)
        elif not upgrade and (rel in KEEP_PROJECT or rel.startswith(WORKFLOWS)):
            kept.append(rel)
        elif upgrade and manifest.get(rel) == sha(dst):
            shutil.copy2(src, dst)
            updated += 1
        else:
            dst.rename(Path(str(dst) + ".pre-kit"))
            shutil.copy2(src, dst)
            moved.append(rel)

    m = target / MANIFEST
    m.parent.mkdir(parents=True, exist_ok=True)
    m.write_text(json.dumps({"version": version(), "files": hashes}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    action = "zaktualizowany" if upgrade else "zainstalowany"
    print(f"trybik-engine {version()} {action} w {target}: nowe pliki {new}, identyczne {same}"
          + (f", zaktualizowane {updated}." if upgrade else "."))
    if appended:
        print(f"- .gitignore/.gitattributes: dopisano {appended} linii trybik-engine")
    for r in kept:
        note = " (workflow trybik-engine pominięty — scalenie w T-001)" if r.startswith(WORKFLOWS) else ""
        print(f"- zostaje wersja projektu: {r}{note}")
    for r in moved:
        why = "zmieniony w projekcie" if upgrade else "wersja projektu"
        print(f"- do scalenia: {r}.pre-kit ({why}; na jej miejscu wersja trybik-engine)")
    if settings:
        print("- .claude/settings.json należy do projektu; w nowej wersji kitu doszło (dopisz ręcznie, jeśli chcesz):")
        for s in settings:
            print(f"    {s}")
    if git(target, "rev-parse", "--is-inside-work-tree") == "true":
        probe = (".claude/settings.json", "tools/docs_check.py", "docs/PROCESS.md", "CLAUDE.md", MANIFEST)
        ignored = [p for p in probe if git(target, "check-ignore", "-q", p) is not None]
        if ignored:
            print(f"UWAGA: .gitignore projektu ignoruje pliki trybik-engine ({', '.join(ignored)}) — popraw go, inaczej nie trafią do repo.")
    print("Dalej: " + ("przejrzyj `git diff`, scal `*.pre-kit` i zacommituj." if upgrade
                       else "otwórz projekt w Claude Code i napisz „zacznij projekt” (od zera) albo „przejmij projekt” (jest już kod lub dokumenty)."))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):  # UTF-8 niezależnie od kodowania systemu (Windows: cp1250)
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main(sys.argv[1:]))
