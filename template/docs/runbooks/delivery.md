# Dostarczanie ticketu

Domyślnie agent prowadzi cały cykl bez pytania o zgodę: implementacja → testy → PR → review → poprawki → merge. Zatrzymuje się tylko przy STOP z poniższej listy. Ticket musi być `ready`.

## Warstwy ticketu (`templates/ticket.md`)
- **A Produkt** (CO/DLACZEGO): jedyne źródło zakresu, bez kodu i plików. Nadrzędna.
- **B Implementacja** (JAK): pliki, wzorzec do naśladowania, ograniczenia. Nie zmienia A.
- **C Weryfikacja**: scenariusze zachowań mapowane na AC. Tickety `kind: plain` jej nie mają.
- **Scope guard** = „Out" w A + `allow` we front-matter. Praca poza nimi → STOP i pytanie.

## Kto co dostaje
| Rola | Dostaje | Nie dostaje |
|---|---|---|
| Implementator (agent `implementer`) | A + B | C |
| Tester (agent `tester`) | A (Cel, Zakres, Akceptacja) + C + lista zmienionych plików | B, reszta A |
| Reviewer (agent `reviewer`) | A (Cel, Zakres, Akceptacja) + diff względem głównej gałęzi + lista „Docs do aktualizacji" | B, C |

Sesja główna daje subagentowi jako prompt wynik `python3 .claude/skills/deliver/ticket_parts.py <rola> T-NNN` (nie każe mu czytać ticketu): skrypt wycina sekcje mechanicznie, co oszczędza odczyt i wymusza izolację. Kroki z komendami: skill `/deliver`. Tester bez B nie dopasowuje testów do implementacji. Definicje agentów (narzędzia, model, zasady): `.claude/agents/`.

## Przebieg
1. **Start**: `python3 tools/docs_check.py --next`; ticket → `in-progress` (pierwszy commit brancha `feat/T-NNN-slug`).
2. **Implementator** (agent `implementer`): A+B. Bez testów. Zapis tylko w `allow` (hook scope guard). Uruchamia tylko build/lint dotkniętego modułu. Commit `feat(...)`.
3. **Tester** (`kind: logic`; agent `tester`): A+C+`git show --stat HEAD`; czyta tylko wskazane pliki i sekcję „Testy” w `docs/architecture/overview.md`. Nie zmienia kodu produkcyjnego; bug → zgłasza. Uruchamia tylko swoje testy. Test zawiera ID kryterium (`T-NNN.ACn`). Commit `test(...)`.
4. **Review** (`kind: logic`; agent `reviewer`, mocniejszy model): diff + A. Raport ≤10 linii: bugi, odstępstwa od A, ryzyka, sprawdzenie „Docs do aktualizacji". Nie zmienia kodu. Poprawki robi sesja główna.
5. **Domknięcie**: AC odhaczone, ticket → `done`, `docs_check --write`, STATE jeśli trzeba; push i PR; `gh pr checks --watch`; zielone → `gh pr merge --squash`.

## STOP (zatrzymaj się i pytaj)
- A jest niejednoznaczne albo dwa dokumenty się wykluczają → wpis w `QUESTIONS.md` (ticket wraca do `draft`, jeśli zmienia zakres).
- Potrzebna praca poza zakresem/`allow`.
- Poprawka po review lub testach nie przechodzi po 1 próbie.
- Nowa decyzja trudna do odwrócenia → najpierw ADR i potwierdzenie.

## Advisor (mocniejszy konsultant)
Ustawiany przez `advisorModel` użytkownika i dziedziczony przez agentów. Nie przyjmuje parametrów: zawsze widzi całą rozmowę agenta, który go woła. Reguły dla implementatora: `.claude/agents/implementer.md`; jego raport kończy linia `Advisor: …`, którą sesja główna przekazuje właścicielowi.

Sesja główna: nie na starcie (ticket `ready` ma już zakres i decyzje). Wołaj, gdy: ticket jest niejednoznaczny, a odpowiedź nie wynika z A; ktoś zgłosił odstępstwo zmieniające zakres lub kontrakt; poprawka nie przechodzi po 1 próbie; review ma uwagi, których nie umiesz przyjąć lub odrzucić. Pytaj krótko — kontekst advisor już ma.

## Oszczędność kontekstu
- Agent nie czyta: kodu generowanego, zależności, lockfile, artefaktów builda, plików >300 linii bez potrzeby (offset/limit), dokumentów spoza „Kontekst do przeczytania". `CLAUDE.md` modułu ładuje się sam.
- B podaje konkretne ścieżki i wzorzec („jak `X`"), nie eksplorację repo.
- Raport agenta ≤10 linii: zmienione pliki, odstępstwa, pytania. Bez cytowania kodu.
- Agenci uruchamiają tylko własny zakres testów; pełny zestaw raz, na domknięciu.
- Mały ticket (≤3 pliki, trywialny): implementacja w sesji głównej; tester nadal osobny, jeśli jest logika.
- Bug z testów → poprawka w sesji głównej, nie w agencie testowym.
- `kind: plain` (docs, config, chore, layout): bez C, testera i review.

## Gdy GitHub nie uruchomi testów
PR tylko z dokumentacją nie uruchamia CI (oszczędność minut). Gdy na GitHubie zabraknie minut, zadanie kończy się po kilku sekundach bez kroków. W obu przypadkach: `bash tools/ci.sh` lokalnie na branchu (wszystko zacommitowane i wypchnięte), wynik w komentarzu PR, potem `gh pr merge --squash`. Błąd testów na GitHubie poprawiasz — lokalne przejście go nie zastępuje (automat git to rozróżnia).
