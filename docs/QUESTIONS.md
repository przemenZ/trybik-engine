# Pytania do właściciela produktu

Jedyne miejsce na nierozstrzygnięte kwestie produktowe i domenowe. Fakty do sprawdzenia w kodzie, wnioski z przeglądów i zadania techniczne tu NIE trafiają (→ ticket albo `docs/reviews/`).

Zasady:
- Pytanie ma rekomendację agenta; właściciel może przyjąć ją hurtem („przyjmuję rekomendacje").
- `blokuje:` wskazuje tickety, które nie mogą być `ready`, dopóki pytanie jest `open` (egzekwuje `tools/docs_check.py`). Pytanie niczego nie blokujące: `blokuje: -`.
- Po odpowiedzi: `status: resolved`, `odpowiedź:` z datą, a SKUTEK wpisz tam, gdzie żyje wiedza (spec / ADR / ticket). Pytanie zostaje jako ślad decyzji, nie jako jej źródło.
- ID rosną, nie są używane ponownie.

<!-- Format wpisu (każde pole w jednej linii):

## Q-001 — Krótki tytuł pytania
- status: open
- blokuje: T-003, T-004
- pytanie: Co dokładnie jest niejasne i jakie są opcje.
- rekomendacja: Co proponuje agent i dlaczego.
- odpowiedź:

-->
