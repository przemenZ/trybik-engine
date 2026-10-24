# Proces

Zasada naczelna: **każdy fakt ma jedno miejsce**. Reszta linkuje, nie kopiuje. Status pracy wpisujesz tylko w tickecie; wszystkie inne widoki są generowane lub linkowane. `python3 tools/docs_check.py` pilnuje spójności (automatycznie: hook `Stop` w `.claude/` i CI — `tools/ci.sh`).

## Gdzie co żyje
| Co | Gdzie | Jak się zmienia |
|---|---|---|
| Wizja, zakres MVP, słownik pojęć | `docs/product/vision.md` | agent pisze szkic, właściciel akceptuje |
| Pomysły przed decyzją | `docs/journal.md` | dojrzały → spec, martwy → skreśl |
| Docelowe zachowanie funkcji | `docs/specs/<feature>.md` | żywy; poprawiany razem z ticketem zmieniającym zachowanie |
| Decyzja trudna do odwrócenia + powód | `docs/adr/NNNN-tytul.md` | niezmienna; kurs się zmienia nowym ADR (`Supersedes`) |
| Jedna zmiana do wykonania **i jej status** | `docs/tickets/T-NNN-slug.md` | front-matter = jedyne źródło statusu |
| Kolejka i „następny" | `docs/BACKLOG.md` | **generowany** (`--write`), nie edytować |
| Pytania do właściciela | `docs/QUESTIONS.md` | jedno miejsce, patrz niżej |
| Stan bieżący (≤40 linii) | `docs/STATE.md` | ręcznie: gdzie jesteśmy, w toku, ograniczenia |
| Moduły, konwencje kodu, testy | `docs/architecture/overview.md` | żywy; poprawiany w ticketach zmieniających strukturę |
| Jak zacząć / dostarczać / wdrażać | `docs/runbooks/` | ręcznie |
| Wnioski z przeglądów kodu | `docs/reviews/` | każde znalezisko ma rozstrzygnięcie |
| Materiały zastane (dokumenty sprzed procesu) | `docs/sources/` | tylko do odczytu, nie są źródłem prawdy (obowiązują wizja, spec, ADR); czytane, gdy wskazuje je spec lub ticket |

Nowy plik md trafia do katalogu z tabeli, nie do roota. Spec nie wylicza ticketów, a ticket wskazuje spec (`spec:`) — w jedną stronę, żeby nie było dwóch list do synchronizacji.

## Lejek wymagań
1. **Pomysł** → `journal.md` (opcjonalnie).
2. **Spec** (`templates/spec.md`): cel, zachowanie, kryteria akceptacji, kontrakt, przypadki brzegowe, poza zakresem.
3. **Niejasność** → wpis w `QUESTIONS.md` z rekomendacją i `blokuje:`. Nie zgadujemy. Pytania zadajemy partiami, każde z propozycją, tak by właściciel mógł odpowiedzieć „tak".
4. **ADR**, gdy decyzja jest trudna do odwrócenia albo dotyczy wielu funkcji.
5. **Podział na tickety**: pionowe wycinki, ≲10 plików i ≲100 linii na ticket; rozmiar większy → podział.
6. **Akceptacja**: ticket powstaje jako `draft`; właściciel akceptuje → `ready`. `ready` jest niemożliwy, dopóki blokuje go otwarte pytanie (sprawdza narzędzie).

## Ticket: cykl życia
`draft` → `ready` → `in-progress` → `done` (albo `dropped`).

| Przejście | Kto | Kiedy |
|---|---|---|
| → draft | agent/właściciel | ticket napisany |
| draft → ready | **właściciel** | po akceptacji, pytania zamknięte (`docs_check.py --check T-NNN` przechodzi) |
| ready → in-progress | agent | początek implementacji (w pierwszym commicie brancha) |
| in-progress → done | agent | **w tym samym PR co kod**: AC odhaczone, `--write`, STATE jeśli trzeba |

Zmiana statusu nie wymaga osobnego PR „docs: done" ani przenoszenia plików — ticket zostaje w `docs/tickets/`, a `BACKLOG.md` jest widokiem. Po zmianie ticketów/pytań: `python3 tools/docs_check.py --write`.

Struktura ticketu i podział ról: `templates/ticket.md`, `runbooks/delivery.md`. Nowy ticket: skill `/ticket` (plik tworzy `python3 tools/docs_check.py --new "Tytuł"`). Warstwa A (CO) jest nadrzędna wobec B (JAK) i C (weryfikacja). Zakończony ticket jest zapisem historycznym — aktualne zachowanie opisuje spec.

## Definition of Done
- Wszystkie AC odhaczone; każde pokryte scenariuszem (C) i testem (`kind: logic`).
- CI zielone: na GitHubie albo — gdy GitHub go nie uruchomił — `bash tools/ci.sh` lokalnie.
- Spec i dokumenty z sekcji „Docs do aktualizacji" zgodne z rzeczywistością; nowa decyzja ma ADR; nowe pytania są w `QUESTIONS.md`.
- Ticket `done`, `BACKLOG.md` zregenerowany, `docs_check` przechodzi.
- Brak sekretów, logów i artefaktów builda w commicie.

## Wnioski z przeglądów
Plik `docs/reviews/RRRR-MM-DD-<zakres>.md`; znaleziska mają ID `R-1…` i **rozstrzygnięcie**: `fixed` | `T-NNN` | `Q-NNN` | `wontfix: powód`. Znalezisko bez rozstrzygnięcia jest otwarte. Weryfikacje „sprawdź w kodzie" to znaleziska albo tickety, nie osobna lista.

## Git
- Bez commitów na `main`/`master`. Branch: `feat|fix|chore|docs/T-NNN-slug`. Jeden branch może zmieniać API i jego konsumenta.
- Commit: `type(scope): opis (T-NNN)`; scope definiuje projekt w `CLAUDE.md`. Squash merge przez PR (`gh pr merge --squash`).
- Zasada „zmiana API i konsumenta w jednym branchu" i generacja klienta — jeśli projekt ma kontrakt (OpenAPI itp.).

## Sesja z agentem
- Start: `CLAUDE.md` → `docs/STATE.md` → `python3 tools/docs_check.py --next` → ticket. Start procesu: `runbooks/kickoff.md` (od zera) albo `runbooks/adoption.md` (jest kod lub dokumenty).
- W trakcie: stan zmieniamy w plikach, nie w rozmowie.
- Koniec: ticket/pytania/STATE zaktualizowane, `docs_check` zielony, commit na branchu.
- Automaty (`.claude/settings.json`, skrypty w `.claude/hooks/`):
  - przed zakończeniem odpowiedzi `docs_check`; błędy (poza szkicami) wracają do agenta, najwyżej raz na turę;
  - zakaz commitu, lokalnego scalania i wypychania wprost na `main`/`master` (poza pierwszym commitem) oraz force push;
  - `gh pr merge` do `main` tylko po zielonym CI na GitHubie; gdy GitHub testów nie uruchomił — po `tools/ci.sh` dla tego samego commita;
  - `.env` niedostępny, `BACKLOG.md` tylko przez `--write`, destrukcyjne komendy wymagają potwierdzenia;
  - agent `implementer` zapisuje tylko pliki z `allow` ticketu i nie ma dostępu do `docs/tickets/` (hook w jego definicji).

## Higiena
- Sekrety tylko w `.env` (poza gitem), wzorzec w `.env.example`.
- Opis działania funkcji → spec lub kod, nie `STATE.md`.
- Zaakceptowanych ADR nie edytujemy.
