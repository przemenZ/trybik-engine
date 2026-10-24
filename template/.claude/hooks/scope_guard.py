#!/usr/bin/env python3
"""Hook PreToolUse agenta `implementer` (frontmatter w .claude/agents/implementer.md): scope guard.

- Edit/Write/NotebookEdit: plik musi pasować do `allow` aktywnego ticketu (ID z nazwy brancha `…/T-NNN-…`).
- `docs/tickets/**`: zawsze zakaz (także Read) — tam jest status ticketu i warstwa C, ukryta przed implementatorem.
- Pliki poza repo, brak gita, branch bez ID, brak ticketu lub pusty `allow` → przepuszcza.

Globy `allow`: `*` w obrębie katalogu, `**` przez katalogi, ścieżka bez gwiazdek = plik albo cały katalog.
Blokada = exit 2 + komunikat na stderr (trafia do agenta). Własna awaria hooka nie blokuje, ale jest widoczna (exit 1, .git/trybik-hooks.log).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hooklib import crashed  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BRANCH_ID = re.compile(r"(?:^|/)(T-\d+)(?:-|$)")
WRITE_TOOLS = ("Edit", "Write", "NotebookEdit")


def glob_re(glob):
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile(out + r"\Z")


def allowed(rel, globs):
    for g in globs:
        g = g.strip("`'\" ")
        g = g[2:] if g.startswith("./") else g  # python 3.8: bez removeprefix
        if not g:
            continue
        if not any(c in g for c in "*?"):
            d = g.rstrip("/")
            if rel == d or rel.startswith(d + "/"):
                return True
        elif glob_re(g).match(rel):
            return True
    return False


def active_ticket():
    p = subprocess.run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=ROOT,
                       capture_output=True, text=True, timeout=5)
    m = BRANCH_ID.search(p.stdout.strip())
    if not m:
        return None
    files = sorted((ROOT / "docs" / "tickets").glob(f"{m.group(1)}-*.md"))
    if not files:
        return None
    sys.dont_write_bytecode = True  # bez tools/__pycache__ w repo
    sys.path.insert(0, str(ROOT / "tools"))
    import docs_check

    fields, _ = docs_check.parse_front(files[0].read_text(encoding="utf-8"))
    return m.group(1), docs_check.split_list((fields or {}).get("allow", ""))


def check(tool, path):
    try:
        rel = Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None  # poza repo
    if rel.startswith("docs/tickets/"):
        return ("Implementator nie czyta ani nie zmienia ticketów (`docs/tickets/`): wszystko, czego potrzebujesz, "
                "masz w prompcie (A+B). Status i AC zmienia sesja główna.")
    if tool not in WRITE_TOOLS:
        return None
    t = active_ticket()
    if not t or not t[1]:
        return None
    tid, globs = t
    if allowed(rel, globs):
        return None
    return (f"`{rel}` jest poza zakresem {tid} (allow: {', '.join(globs)}). Nie obchodź tego (Bash, inne pliki): "
            "zatrzymaj się i zgłoś w raporcie, który plik i po co jest potrzebny.")


def main():
    try:
        data = json.load(sys.stdin)
        inp = data.get("tool_input") or {}
        path = inp.get("file_path") or inp.get("notebook_path")
        msg = check(data.get("tool_name"), path) if path else None
    except Exception:
        return crashed("scope_guard")
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
