---
name: deliver
description: Dostarcza ticket od startu do merge (implementer → tester → reviewer → PR). Użyj, gdy właściciel mówi „dostarcz kolejny feature”, „dostarcz T-NNN” albo każe dokończyć ticket in-progress.
---

# Dostarczanie ticketu

Kontrakt (role, STOP, oszczędność kontekstu, brak CI na GitHubie): `docs/runbooks/delivery.md` — przeczytaj, jeśli nie masz go w kontekście. Tu jest tylko kolejność kroków i komendy. `PARTS` = `python3 .claude/skills/deliver/ticket_parts.py`.

## 1. Start
- Ticket: wskazany przez właściciela albo `python3 tools/docs_check.py --next`. Brak `ready`/`in-progress` → postępuj wg `CLAUDE.md` (skill `/ticket`) i zakończ.
- `ready`: `git switch -c feat/T-NNN-slug` (`fix|chore|docs` wg charakteru), `status: in-progress`, `python3 tools/docs_check.py --write`, commit `docs(<scope>): start (T-NNN)`.
- `in-progress`: przełącz się na branch ticketu; `git log main..HEAD --oneline` pokazuje, które kroki są zrobione (`feat`/`fix` = implementacja, `test` = testy). Kontynuuj od pierwszego brakującego.

## 2. Implementacja
- Mały ticket (≤3 pliki, trywialny): sesja główna sama, wg zasad z `.claude/agents/implementer.md`.
- Inaczej: agent `implementer`, prompt = wynik `PARTS implementer T-NNN` bez zmian.
- Raport: pliki spoza `allow`, niejasność A → STOP (`delivery.md`). Zapamiętaj linię `Advisor:` do raportu końcowego.

## 3. Testy (`kind: logic`)
- Agent `tester`, prompt = wynik `PARTS tester T-NNN` bez zmian. Niczego z B nie dopisuj.
- Błąd w kodzie → poprawka w sesji głównej, testy ponownie; nie przechodzi po 1 próbie → STOP.

## 4. Review (`kind: logic`)
- Agent `reviewer`, prompt = wynik `PARTS reviewer T-NNN` bez zmian.
- Każde znalezisko: poprawka w sesji głównej, odrzucenie z powodem (do raportu) albo poza zakresem → szkic ticketu (`/ticket`) lub `QUESTIONS.md`.

## 5. Domknięcie
- AC odhaczone, `status: done`, dokumenty z „Docs do aktualizacji”, `STATE.md` jeśli trzeba, `python3 tools/docs_check.py --write`.
- `bash tools/ci.sh`, commit, push, `gh pr create`, `gh pr checks --watch`, zielone → `gh pr merge --squash`. GitHub nie uruchomił testów → `bash tools/ci.sh` lokalnie, `gh pr comment --body "tools/ci.sh lokalnie: OK (<sha>)"`, potem merge (`delivery.md`, ostatnia sekcja).

## 6. Raport dla właściciela (≤8 linii)
Ticket i PR (scalony / czeka i dlaczego), odstępstwa i odrzucone uwagi review, nowe pytania lub szkice ticketów, a na końcu linia `Advisor:` implementatora bez zmian (przy implementacji w sesji głównej: `Advisor (sesja główna): …` w tej samej formie).
