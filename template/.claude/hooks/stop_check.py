#!/usr/bin/env python3
"""Hook Stop: zanim agent zakończy odpowiedź, sprawdza dokumentację procesu (tools/docs_check.py).

- Blokuje zakończenie (exit 2; komunikat ze stderr trafia do agenta) najwyżej raz na turę użytkownika.
- Pomija błędy szkiców (`draft`), bo to praca właściciela w toku.
- Własna awaria hooka nigdy nie blokuje (exit 0).
"""
import json
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if data.get("stop_hook_active"):
        return 0  # agent już raz dostał uwagi w tej turze
    try:
        sys.dont_write_bytecode = True  # bez tools/__pycache__ w repo
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
        import docs_check

        r = docs_check.collect()
        problems = r.choice + r.other
    except Exception:
        return 0
    if not problems:
        return 0
    lines = ["Dokumentacja procesu ma błędy (python3 tools/docs_check.py):"]
    lines += [f"- {p}" for p in problems]
    lines.append(
        "Popraw te, które wynikają z Twojej pracy w tej sesji (np. `--write` po zmianie ticketu). "
        "Pozostałe wymień właścicielowi w odpowiedzi i zakończ."
    )
    print("\n".join(lines), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
