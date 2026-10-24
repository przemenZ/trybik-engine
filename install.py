#!/usr/bin/env python3
"""Instaluje kit w katalogu projektu — nowym albo istniejącym (tylko stdlib). Sam zostaje w kicie.

  python3 install.py <katalog-projektu>

Brakujące pliki kopiuje, identyczne pomija. Gdy plik projektu różni się od pliku kitu:
- `.gitignore` — dopisuje brakujące linie kitu;
- `.env.example` i workflowy w `.github/workflows/` — zostaje wersja projektu (workflow scala T-001);
- pozostałe — wersja projektu → `<plik>.pre-kit`, na jej miejsce wersja kitu (scalenie: docs/runbooks/adoption.md).
Odmawia, gdy: cel to katalog kitu, repo ma niezacommitowane zmiany, repo z historią stoi na main/master,
zostały pliki `*.pre-kit` z poprzedniej instalacji.
"""
import filecmp
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
ITEMS = ("CLAUDE.md", "docs", "tools", ".claude", ".github", ".gitignore", ".env.example")
SKIP = {"__pycache__", "settings.local.json", ".DS_Store"}
KEEP_PROJECT = (".env.example",)
WORKFLOWS = ".github/workflows/"
ENC = {"encoding": "utf-8", "errors": "surrogateescape"}  # obce kodowanie przechodzi bajt w bajt


def kit_paths():
    for item in ITEMS:
        p = KIT / item
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if not SKIP & set(f.relative_to(KIT).parts) and f.suffix != ".pyc":
                    yield f


def git(target, *args):
    try:
        r = subprocess.run(["git", "-C", str(target), *args], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def refusals(target, paths):
    out = []
    if target == KIT or KIT in target.parents:
        out.append("cel to katalog kitu")
    if git(target, "rev-parse", "--is-inside-work-tree") == "true":
        if git(target, "status", "--porcelain"):
            out.append("repo ma niezacommitowane zmiany — zacommituj je albo odłóż (git stash)")
        if git(target, "rev-parse", "-q", "--verify", "HEAD") and git(target, "rev-parse", "--abbrev-ref", "HEAD") in ("main", "master"):
            out.append("repo stoi na głównej gałęzi — najpierw: git switch -c docs/adoption")
    for src in paths:
        dst = target / src.relative_to(KIT)
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
        dst.write_text(text + sep + "\n# process-kit\n" + "\n".join(missing) + "\n", **ENC)
    return len(missing)


def main(argv):
    if len(argv) != 1:
        print("użycie: python3 install.py <katalog-projektu>")
        return 2
    target = Path(argv[0]).expanduser().resolve()
    paths = list(kit_paths())
    errors = refusals(target, paths)
    for e in errors:
        print(f"ODMOWA: {e}")
    if errors:
        return 1

    new = same = appended = 0
    kept, moved = [], []
    for src in paths:
        rel = src.relative_to(KIT)
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        elif not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            new += 1
        elif filecmp.cmp(src, dst, shallow=False):
            same += 1
        elif rel.as_posix() == ".gitignore":
            appended = append_missing(src, dst)
        elif rel.as_posix() in KEEP_PROJECT or rel.as_posix().startswith(WORKFLOWS):
            kept.append(rel.as_posix())
        else:
            dst.rename(Path(str(dst) + ".pre-kit"))
            shutil.copy2(src, dst)
            moved.append(rel.as_posix())

    print(f"Kit zainstalowany w {target}: nowe pliki {new}, identyczne {same}.")
    if appended:
        print(f"- .gitignore: dopisano {appended} linii kitu")
    for r in kept:
        note = " (workflow kitu pominięty — scalenie w T-001)" if r.startswith(WORKFLOWS) else ""
        print(f"- zostaje wersja projektu: {r}{note}")
    for r in moved:
        print(f"- do scalenia: {r}.pre-kit (wersja projektu; na jej miejscu wersja kitu)")
    if git(target, "rev-parse", "--is-inside-work-tree") == "true":
        probe = (".claude/settings.json", "tools/docs_check.py", "docs/PROCESS.md", "CLAUDE.md")
        ignored = [p for p in probe if git(target, "check-ignore", "-q", p) is not None]
        if ignored:
            print(f"UWAGA: .gitignore projektu ignoruje pliki kitu ({', '.join(ignored)}) — popraw go, inaczej kit nie trafi do repo.")
    print("Dalej: README.md kitu, sekcja „Użycie”.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
