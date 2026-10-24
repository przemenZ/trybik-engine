"""W5, D1, D2: walidacja ticketów w tools/docs_check.py."""
import unittest

from kit import ProjectCase

FILLED = """---
id: {id}
title: {title}
status: {status}
rank: 10
depends: {depends}
spec:
kind: logic
allow: src/**
---

# A. Produkt

## Cel
Użytkownik loguje się hasłem.

## Zakres
- **In:** logowanie
- **Out:** rejestracja

## Akceptacja
- [ ] AC1: poprawne hasło loguje
- [ ] AC2: złe hasło pokazuje błąd

---

# B. Implementacja

## Cel techniczny
Endpoint logowania.

---

# C. Weryfikacja

## Scenariusze
1. [AC1] poprawne hasło
2. [AC2] złe hasło
"""


class Tickets(ProjectCase):
    def ticket(self, id="T-001", title="Logowanie", status="ready", depends=""):
        return self.write(f"docs/tickets/{id}-x.md", FILLED.format(id=id, title=title, status=status, depends=depends))

    def check(self, *args):
        r = self.py("tools/docs_check.py", *args)
        return r.returncode, r.stdout + r.stderr

    def test_fresh_draft_is_green(self):
        self.assertEqual(self.py("tools/docs_check.py", "--new", "Szkic").returncode, 0)
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_template_content_is_not_ready(self):
        self.py("tools/docs_check.py", "--new", "Szkic")
        code, out = self.check("--check", "T-001")
        self.assertNotEqual(code, 0)
        self.assertIn("niewypełnione miejsca z szablonu", out)

    def test_filled_ticket_is_ready(self):
        self.ticket(status="draft")
        code, out = self.check("--check", "T-001")
        self.assertEqual(code, 0, out)

    def test_done_ticket_with_placeholder_stays_green(self):
        p = self.ticket(status="done")
        p.write_text(p.read_text(encoding="utf-8").replace("- [ ] AC1", "- [x] AC1").replace("- [ ] AC2", "- [x] AC2")
                     + "\n## Uwagi\n- ...\n", encoding="utf-8")
        self.py("tools/docs_check.py", "--write")
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_dependency_on_dropped(self):
        self.ticket("T-001", status="dropped")
        self.ticket("T-002", depends="T-001")
        self.py("tools/docs_check.py", "--write")
        code, out = self.check()
        self.assertNotEqual(code, 0)
        self.assertIn("T-001 jest dropped", out)

    def test_title_quotes_and_pipe(self):
        self.ticket(title='"API: a | b"')
        self.py("tools/docs_check.py", "--write")
        backlog = self.path("docs/BACKLOG.md").read_text(encoding="utf-8")
        self.assertIn("API: a \\| b", backlog)
        self.assertNotIn('"API', backlog)


if __name__ == "__main__":
    unittest.main()
