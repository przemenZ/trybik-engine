#!/usr/bin/env python3
"""Blokada lokalnego tools/ci.sh na czas pracy subagentów (mało RAM-u: jeden ciężki proces naraz).

  subagent_lock.py start    hook SubagentStart: dopisuje wpis `<epoch> <agent_id> <agent_type>`
  subagent_lock.py stop     hook SubagentStop: usuwa wpis o tym id
  subagent_lock.py --check  wołane z tools/ci.sh: exit 1, gdy jest wpis młodszy niż 30 min

Wpisy leżą w `<git-common-dir>/subagents-active`. Starsze niż 30 min są ignorowane
(zabezpieczenie przed przerwanym subagentem). Wymuszenie: usunąć ten plik.
`start` i `stop` nigdy nie blokują subagenta (zawsze exit 0). Własna awaria `--check` nie blokuje CI.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hooklib import ROOT, crashed  # noqa: E402

MAX_AGE = 30 * 60


def lock_file():
    """Ścieżka pliku wpisów albo None poza repo git (git-common-dir: wspólny dla worktree)."""
    p = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True,
                       text=True, timeout=5)
    if p.returncode != 0:
        return None
    return ROOT / p.stdout.strip() / "subagents-active"  # ścieżka bezwzględna zastępuje ROOT


def read_entries(f):
    out = []
    try:
        lines = f.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return out
    for line in lines:
        parts = line.split(None, 2)
        if len(parts) >= 2 and parts[0].isdigit():
            out.append((int(parts[0]), parts[1], parts[2] if len(parts) > 2 else "?"))
    return out


def write_entries(f, entries):
    tmp = f.with_name(f.name + f".{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:  # open(): write_text(newline=) dopiero od 3.10
        fh.write("".join(f"{t} {i} {a}\n" for t, i, a in entries))
    os.replace(tmp, f)  # atomowo: równoległe SubagentStart


def hook(action):
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    ident = "".join(str(data.get("agent_id") or data.get("session_id") or "?").split()) or "?"
    kind = "_".join(str(data.get("agent_type") or "?").split()) or "?"
    f = lock_file()
    if f is None:
        return 0
    entries = [e for e in read_entries(f) if e[1] != ident]
    if action == "start":
        entries.append((int(time.time()), ident, kind))
    write_entries(f, entries)
    return 0


def check():
    f = lock_file()
    if f is None:
        return 0
    now = time.time()
    active = [e for e in read_entries(f) if now - e[0] < MAX_AGE]
    if not active:
        return 0
    print("CI wstrzymane: działa subagent (jeden ciężki proces naraz). Poczekaj, aż skończy:", file=sys.stderr)
    for t, i, a in active:
        print(f"- {a} ({i}), od {int((now - t) // 60)} min", file=sys.stderr)
    print(f"Wymuszenie (np. po przerwanym subagencie): usuń plik {f}", file=sys.stderr)
    return 1


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "--check":
        try:
            return check()
        except Exception:
            crashed("subagent_lock")
            return 0  # awaria blokady nie może zatrzymać CI (set -e w ci.sh)
    if arg in ("start", "stop"):
        try:
            return hook(arg)
        except Exception:
            crashed("subagent_lock")
            return 0  # nigdy nie blokuj subagenta
    print("użycie: subagent_lock.py start|stop|--check", file=sys.stderr)
    return 1


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):  # UTF-8 niezależnie od kodowania systemu (Windows: cp1250)
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
