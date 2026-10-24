# process-kit

Neutralny technologicznie szablon procesu agentowego dostarczania oprogramowania (spec → pytania → ticket A/B/C → implementacja → test → review → merge), wyciągnięty z projektu `lodka` i poprawiony pod kątem rozjeżdżania się dokumentacji.

## Użycie
Wymaga `python3` ≥3.8 (tylko stdlib) i `git`. `README.md`, `AUTOMATION-PROPOSALS.md` i `install.py` zostają w kicie.

**Nowy projekt** (pusty katalog):
1. `python3 install.py ../nowy-projekt`
2. W nowym repo: nazwa projektu w `CLAUDE.md`, `git init`, pierwszy commit na `main`, potem `gh repo create <nazwa> --private --source=. --push`.
3. Claude Code: „zacznij projekt” — agent prowadzi `docs/runbooks/kickoff.md`: wizja → stos (ADR-0001) → architektura → spece → T-001 szkielet aplikacji → tickety funkcji.

**Istniejący projekt** (legacy, zaczątek aplikacji, zbiór dokumentów):

Kod projektu zostaje tam, gdzie jest — instalator niczego nie przenosi, tylko dokłada obok pliki kitu (`CLAUDE.md`, `docs/`, `tools/`, `.claude/`, `.github/`). Instalator nic o projekcie nie wie; projekt poznaje agent po komendzie „przejmij projekt” (`docs/runbooks/adoption.md`): opisuje to, co zastał, krok po kroku, każdy krok do Twojej akceptacji.

1. W projekcie: wszystko zacommitowane, `git switch -c docs/adoption`.
2. Z katalogu kitu: `python3 install.py ../projekt`. Niczego nie nadpisuje: plik projektu o tej samej nazwie co plik kitu (np. `CLAUDE.md`) odkłada jako `CLAUDE.md.pre-kit` — scala go agent; `.gitignore` uzupełnia o brakujące linie; `.env.example` i workflow CI o tej samej nazwie zostawia. Odmawia przy niezacommitowanych zmianach i na `main`.
3. Ręcznie: dokumenty projektu spoza repo (notatki, PDF, docx) skopiuj do `docs/sources/` — tylko dokumenty, nie kod. Nazwa projektu w `CLAUDE.md`.
4. Claude Code: „przejmij projekt” — agent prowadzi `docs/runbooks/adoption.md`: inwentaryzacja → wizja → stos → architektura z kodu → T-001 podpięcie procesu (komendy, CI) → tickety.

Brak repo (np. sam folder z dokumentami): `python3 install.py ../projekt`, dokumenty → `docs/sources/`, nazwa w `CLAUDE.md`, `git init`, pierwszy commit na `main`, `gh repo create <nazwa> --private --source=. --push`, `git switch -c docs/adoption`, dalej krok 4.

## Co jest w `.claude/`
- `settings.json` — hooki i uprawnienia (opis: `docs/PROCESS.md`, „Sesja z agentem”).
- `hooks/stop_check.py` — `docs_check` przed zakończeniem odpowiedzi agenta.
- `hooks/guard_git.py` — do `main`/`master` tylko przez PR i tylko po zielonym CI; zakaz force push.
- `hooks/scope_guard.py` — tylko dla agenta `implementer`: zapis wyłącznie w `allow` ticketu, bez dostępu do `docs/tickets/`.
- `agents/implementer.md`, `agents/tester.md`, `agents/reviewer.md` — role z `docs/runbooks/delivery.md`.
- `skills/ticket/` — skill `/ticket` (szkic ticketu; plik i kolejne ID tworzy `tools/docs_check.py --new`).
- `skills/deliver/` — skill `/deliver` (kroki dostarczania) i `ticket_parts.py` (wycina z ticketu część dla roli).

## CI
- `tools/ci.sh` — pełne sprawdzenie: dokumentacja, a od T-001 testy, lint i typy. To samo na GitHubie i lokalnie.
- `.github/workflows/ci.yml` — uruchamia `tools/ci.sh` na każdym PR z kodem (PR z samą dokumentacją pomija, oszczędza minuty).
- Gdy GitHub nie uruchomi testów (brak minut, PR z dokumentacją), agent uruchamia `tools/ci.sh` lokalnie. Automat git przepuszcza `gh pr merge` do `main` tylko po zielonym CI na GitHubie albo po lokalnym przejściu tego samego commita; błąd testów na GitHubie blokuje zawsze.
- Prywatne repo na darmowym planie GitHuba nie blokuje scalenia czerwonego PR (brak ochrony gałęzi), więc tę rolę pełni automat git. Dotyczy agenta — właściciel nadal może scalić ręcznie w przeglądarce.

## Co zmieniono względem lodki
| Problem w lodce | Rozwiązanie |
|---|---|
| Status w 4 miejscach (ticket, `[x]` w BACKLOG, `done/`, STATE) | Status tylko w front-matter ticketu; `BACKLOG.md` generowany; brak `done/`; `done` w tym samym PR co kod |
| Osobne PR-y „docs: X done" | zbędne (jw.) |
| Dwa magazyny pytań i sprzeczne instrukcje | Jeden `QUESTIONS.md`, pytanie ma `blokuje:` → ticket nie może być `ready` (sprawdza narzędzie) |
| `OPEN_QUESTIONS` mieszał decyzje, fakty, bezpieczeństwo, review | Tylko pytania produktowe; wnioski z review w `docs/reviews/` z rozstrzygnięciem |
| `STATE.md` powielał specyfikacje (146 linii) | Limit 40 linii, bez opisu działania funkcji |
| Spec vs ticket: niejasne, co jest aktualne | Spec żywy, ticket historyczny; „Docs do aktualizacji" w B sprawdza reviewer |
| Scope guard tylko prozą | `allow` w front-matter (maszynowo; podstawa pod hook) |
| Kolejność = pierwszy niezaznaczony | `rank` + `depends`; `--next` wybiera pierwszy odblokowany |
| Brak śladu AC → scenariusz | AC numerowane (AC1…), narzędzie wymaga pokrycia w C |
| Reguły tylko jako tekst | `docs_check.py`, automaty w `.claude/`, CI (`tools/ci.sh`); dalsze propozycje w `AUTOMATION-PROPOSALS.md` |
| PR scalany mimo czerwonego CI (#120: GitHub nie uruchomił testów — płatności/limit) | automat git sprawdza CI przed `gh pr merge`; gdy GitHub nie ruszy, wymaga lokalnego `tools/ci.sh` |
| `autonomous-run`, archiwa z jednego etapu | pominięte; autonomia jest domyślnym trybem w `delivery.md` |
