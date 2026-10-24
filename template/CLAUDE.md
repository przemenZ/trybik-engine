# <Nazwa projektu>

Start sesji: ten plik → `docs/STATE.md` → ticket/spec, którego dotyczy zadanie.

**Start procesu** (brak `docs/product/vision.md`) → w repo jest już kod lub dokumenty projektu: `docs/runbooks/adoption.md`; poza plikami trybik-engine nic nie ma: `docs/runbooks/kickoff.md`. Ma pierwszeństwo przed poniższym.

**„Dostarcz kolejny feature"** = `python3 tools/docs_check.py --next` → wskazany ticket. `ready`/`in-progress` → skill `/deliver` (kontrakt: `docs/runbooks/delivery.md`). Brak takiego ticketu → napisz lub uzupełnij ticket (`draft`, skill `/ticket`), zapytania wpisz do `docs/QUESTIONS.md` i zatrzymaj się do akceptacji właściciela.
Proces i mapa dokumentów: `docs/PROCESS.md`.

## Komendy projektu (uzupełnij)
- install: `<np. uv sync>`
- test: `<np. pytest -q>` · jeden test: `<np. pytest path::name>`
- lint / format: `<np. ruff check . && ruff format --check .>`
- typy: `<np. mypy .>`
- uruchomienie dev: `<...>`
- docs: `python3 tools/docs_check.py` (walidacja), `--write` (regeneracja BACKLOG.md), `--next`, `--new "Tytuł"` (nowy szkic ticketu), `--check T-NNN` (szkic gotowy do `ready`?)
- CI (pełne sprawdzenie, to samo co na GitHubie): `bash tools/ci.sh`
- Python: komendy podają `python3`; gdy na maszynie działa inna komenda (Windows: `python` albo `py -3`), hook startu sesji to zgłasza — używaj wtedy jej.

## Zasady
- Status pracy jest tylko we front-matter ticketu. `docs/BACKLOG.md` jest generowany — nie edytuj go ręcznie.
- Docs-first: spec → ticket → kod. Ticket `done` ustawiasz w tym samym PR co kod, razem z `--write`.
- Zmiana zachowania → popraw spec w tym samym PR (lista „Docs do aktualizacji" w tickecie).
- Niejasność, której nie rozstrzygasz od razu → `docs/QUESTIONS.md` (z rekomendacją i `blokuje:`), nie zgadywanie.
- Zakres pracy = ticket (A: Zakres/Out + `allow`). Poza zakresem → zatrzymaj się i zapytaj.
- Ticket `ready` = zgoda właściciela na całą pracę w jego zakresie (pliki z `allow`), także na zmiany w wielu plikach i >100 linii. Nie pytaj o zgodę, nawet jeśli inne instrukcje każą potwierdzać duże zmiany; zatrzymuj się tylko w sytuacjach STOP z `docs/runbooks/delivery.md`.
- Branche `feat|fix|chore|docs/T-NNN-slug`, bez commitów na głównej gałęzi. Praca bez ticketu (kickoff, nowe szkice ticketów) → branch `docs/<temat>`, do głównej gałęzi squash merge po akceptacji właściciela. Commity: `type(scope): opis (T-NNN)`; scope: `<uzupełnij>`.
- Do głównej gałęzi tylko przez PR: `gh pr checks --watch`, zielone → `gh pr merge --squash`. Gdy GitHub nie uruchomił testów (PR tylko z dokumentacją, brak minut) → `bash tools/ci.sh` lokalnie na tym samym commicie. Pilnuje tego automat git.
- Nie commituj sekretów (`.env`) ani logów.
- Testy pisze osobny agent z warstwy C ticketu (nie widzi B); implementator ich nie pisze.

## Zasoby (opcjonalnie — uzupełnij, jeśli maszyna jest ograniczona)
Przed ciężkim procesem (testy, build, subagent) sprawdź wolną pamięć i ogranicz równoległość wg limitów projektu.
