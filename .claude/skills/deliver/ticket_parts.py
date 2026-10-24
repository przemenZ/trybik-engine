#!/usr/bin/env python3
"""Wycina z ticketu część dla roli (docs/runbooks/delivery.md, „Kto co dostaje”), żeby izolacja ról
nie zależała od ręcznego kopiowania sekcji. Wynik = prompt agenta.

  python3 .claude/skills/deliver/ticket_parts.py implementer [T-NNN]  # nagłówek + A + B
  python3 .claude/skills/deliver/ticket_parts.py tester [T-NNN]       # A (Cel, Zakres, Akceptacja) + C + zmienione pliki
  python3 .claude/skills/deliver/ticket_parts.py reviewer [T-NNN]     # A (Cel, Zakres, Akceptacja) + „Docs do aktualizacji”

Bez T-NNN: ticket z nazwy bieżącego brancha (`feat/T-NNN-slug`).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True  # bez tools/__pycache__ w repo
sys.path.insert(0, str(ROOT / "tools"))
import docs_check  # noqa: E402

ROLES = ("implementer", "tester", "reviewer")
A_FOR_OTHERS = ("Cel", "Zakres", "Akceptacja")
HIDDEN_FROM_TESTER = ("docs/tickets/", "docs/BACKLOG.md")


def git(*args):
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
    return p.stdout.strip() if p.returncode == 0 else None


def clean(text):
    text = re.sub(r"<!--.*?-->", "", text or "", flags=re.S)
    return re.sub(r"\n\s*---\s*$", "", text.strip()).strip()


def section(layer, name):
    m = re.search(rf"^## {name}\b[^\n]*\n.*?(?=^## |\Z)", layer or "", re.S | re.M)
    return clean(m.group(0)) if m else None


def find_ticket(tid):
    if not tid:
        m = re.search(r"(?:^|/)(T-\d+)(?:-|$)", git("symbolic-ref", "--short", "-q", "HEAD") or "")
        if not m:
            sys.exit("Podaj T-NNN albo przełącz się na branch ticketu (feat/T-NNN-slug).")
        tid = m.group(1)
    for t in docs_check.load_tickets([]):
        if t.id == tid:
            return t
    sys.exit(f"Nie znaleziono ticketu {tid} w docs/tickets/.")


def changed_files():
    base = next((b for b in ("main", "master") if git("rev-parse", "-q", "--verify", b)), None)
    out = git("diff", "--name-only", f"{base}...HEAD") if base else None
    if out is None:
        return ["(nie udało się ustalić — sesja główna podaje listę ręcznie)"]
    files = [f for f in out.splitlines() if not f.startswith(HIDDEN_FROM_TESTER)]
    return files or ["(brak zmian względem głównej gałęzi)"]


def render(role, t):
    a = t.layer("A")
    head = f"Ticket {t.id}: {t.title}"
    if role == "implementer":
        return "\n\n".join([
            f"{head}\nkind: {t.kind}\nallow: {t.fields.get('allow', '')}",
            "# A. Produkt (CO / DLACZEGO) — nadrzędna\n\n" + clean(a),
            "# B. Implementacja (JAK)\n\n" + clean(t.layer("B")),
        ])
    if t.kind != "logic":
        sys.exit(f"{t.id} ma kind: {t.kind} — bez testera i review (delivery.md).")
    parts = [head, "# A. Produkt (wyciąg)\n\n" + "\n\n".join(s for s in (section(a, n) for n in A_FOR_OTHERS) if s)]
    if role == "tester":
        parts.append("# C. Weryfikacja\n\n" + clean(t.layer("C")))
        parts.append("## Zmienione pliki\n" + "\n".join(f"- {f}" for f in changed_files()))
    else:
        parts.append(section(t.layer("B"), "Docs do aktualizacji") or "## Docs do aktualizacji\n- (brak)")
    return "\n\n".join(parts)


def main(argv):
    if not argv or argv[0] not in ROLES:
        sys.exit(f"Użycie: ticket_parts.py {{{'|'.join(ROLES)}}} [T-NNN]")
    t = find_ticket(argv[1] if len(argv) > 1 else None)
    if t.layer("A") is None:
        sys.exit(f"{t.id}: brak warstwy `# A. …`.")
    print(render(argv[0], t))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
