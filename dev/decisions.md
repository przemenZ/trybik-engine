# Decyzje kitu

Każdy wpis: co zrobiono z punktem przeglądu albo propozycją i dlaczego. Najnowsze na górze.

## Przegląd 2026-10-24 (branch `chore/review-2026-10`)

Zewnętrzny przegląd całego repo: 3 punkty krytyczne (K), 6 ważnych (W), 14 drobnych (D). Kolumna „Decyzja”: **zrobione** = jak w przeglądzie, **zmienione** = zrobione inaczej niż proponował przegląd, **pominięte** = celowo nie zrobione.

| ID | Problem | Decyzja | Co i dlaczego |
|---|---|---|---|
| W3 | brak testów kitu; korzeń kitu był jednocześnie ładunkiem dla projektów | zrobione, **jako pierwsze** | Ładunek przeniesiony do `template/`, w korzeniu własny `CLAUDE.md`, `tests/` (unittest, stdlib) i CI kitu (ubuntu 3.8/3.13, windows, macos). Przegląd dawał W3 na trzecim miejscu. Przesunięte na pierwsze, żeby każda kolejna poprawka miała test. Testy instalują `template/` do katalogu tymczasowego przez `install.py`, więc sprawdzają też instalator. |
| K1 | `UnicodeEncodeError` na `→` przy cp1250 (Windows) | zrobione | `reconfigure(encoding="utf-8")` dla stdin/stdout/stderr we wszystkich skryptach, `PYTHONUTF8=1` w `env` w `settings.json`, `encoding="utf-8"` w wywołaniach `subprocess`. Doszło też stdin hooków (JSON od Claude Code), którego przegląd nie wymieniał. |
| K2 | na Windowsie brak `python3` → hooki po cichu nie działają | zmienione | Właściciel chciał wykrywania przy starcie zamiast stałej komendy. Wrapper `.claude/hooks/py.sh` wykrywa `python3` / `python` / `py -3` (≥ 3.8). Hook `SessionStart` wykrywa od nowa przy każdej sesji i, gdy to nie `python3`, mówi agentowi, jakiej komendy używać w CLAUDE.md i runbookach. Wynik jest zapisany **osobno dla każdej maszyny** w `.git/trybik-python`. Nie jest wpisywany do commitowanego `settings.json`, bo ten plik jest wspólny dla osób na różnych systemach. Brak Pythona → widoczny błąd. Hooki na Windowsie wymagają Git Bash (bez niego Claude Code używa PowerShella). |
| K3 | luki w hooku git (`+main`, `push origin main`, `--mirror`, `git -P commit`, rebase/reset na main…) | zmienione | Bez łatania regexów z przeglądu. Polecenie jest dzielone na kroki (`;`, `&&`, `\|`, nowa linia), hook śledzi `cd`, `git -C` i zmiany gałęzi, a dla `push` liczy **gałęzie docelowe** (main/master → blokada) zamiast szukać zakazanych wzorców. Ustalenia w przypadkach brzegowych: tagi i `--tags` dozwolone; `--delete` własnej gałęzi dozwolone, `--delete main` nie; `--force-with-lease` dozwolone (rebase własnego brancha), `--force`/`-f`/`+refspec` nie; `--mirror`/`--all`/`--prune` zakazane; `git checkout main -- plik` nie jest już traktowane jako przełączenie gałęzi. |
| — | ochrona gałęzi po stronie GitHuba | pominięte | Decyzja właściciela: to sprawa zespołu projektu (część projektów będzie prywatna). README mówi tylko, że automaty to barierki dla agenta i że ochronę po stronie serwera ustawia projekt. |
| W1 | awaria hooka = brak ochrony bez śladu | zrobione | Wspólne `hooklib.crashed`: exit 1 (nie blokuje, ale widać w transkrypcie) i wpis w `.git/trybik-hooks.log`. Błąd `gh pr view` (brak logowania, sieć) przy `gh pr merge` **blokuje** z komunikatem: lepiej poprosić o ponowienie niż wpuścić merge bez sprawdzenia CI. |
| W2 | ponowna instalacja podmieniała żywe dokumenty projektu | zrobione | `install.py --upgrade` i manifest `.claude/trybik-engine.json` (wersja i SHA-256 plików kitu). Podział na pliki kitu i pliki projektu jak w przeglądzie. `settings.json` należy do projektu; instalator wypisuje uprawnienia, hooki i `env`, które doszły w kicie. Projekty zainstalowane przed manifestem: zmienione pliki kitu trafiają do `*.pre-kit` (brak danych, żeby odróżnić zmianę projektu od starej wersji). |
| W4 | izolacja ról tylko częściowo egzekwowana | pominięte (opisane) | Hooki dla testera i reviewera, blokada Grep/Glob i Bash dla implementera: **nie**. Bash i tak omija każdą taką blokadę, a Grep jest implementerowi potrzebny. Pole `tests:` we front-matter też nie. Opisy w README, `PROCESS.md` i `AUTOMATION-PROPOSALS.md` poprawione, żeby nie obiecywały więcej, niż jest egzekwowane. |
| W5 | ticket z treścią szablonu przechodził jako `ready`; świeży szkic był czerwony | zmienione | `spec:` w szablonie puste z komentarzem. Zamiast porównywania linii z szablonem (wiąże walidator z dokładną treścią szablonu) `docs_check` wykrywa miejsca `...`/`…` z szablonu (`- ...`, `- [ ] AC2: ...`, `1. [AC1] ...`, `- **In:** ...`) w ticketach `ready`/`in-progress`/`done`. Opcjonalne „logic wymaga spec” pominięte. |
| W6 | PR z samą dokumentacją zawsze wymagał lokalnego CI; `ci-passed` może dopisać agent | zrobione (opcja A) | Bez `paths-ignore`; `tools/ci.sh` sam pomija testy, lint i typy przy samej dokumentacji (ok. 1 min Actions na PR). Błąd `git diff` liczy się jak zmiana kodu, żeby awaria nie wyłączała testów. Opis lokalnego wyniku jako deklaracji agenta, a nie dowodu, jest w README i docstringu hooka. |
| D1 | zależność od `dropped` blokowała po cichu | zrobione | Błąd w `docs_check`. |
| D2 | cudzysłowy i `\|` w tytule | zrobione | |
| D3 | dwie kolejności kroków w `delivery.md` | zrobione | review przed PR. |
| D4 | tester: `git show --stat HEAD` vs skrypt | zrobione | wg skryptu (cały branch). |
| D5 | trzy formaty ID kryterium w testach | zrobione | nazwa: `test_T012_AC2_…`; tagi/metadane: `T-012.AC2`. |
| D6 | wielkość liter statusów | zrobione | małe litery wszędzie. |
| D7 | brak przejść `in-progress → draft`, `→ dropped` | zrobione | |
| D8 | komentarz PR przy lokalnym CI tylko w runbooku | zrobione | także w skillu `/deliver`. |
| D9 | nazwa, wymagania w README | zrobione | Nazwa była już ujednolicona (`trybik-engine`) w #1. Doszło: `gh auth status`, advisor (opcjonalny), Windows (Git Bash, Python). |
| D10 | odwołanie do prywatnej „globalnej reguły” | zrobione | |
| D11 | `deny` tylko `./.env`, `ask` nie łapie `rm -fr` | zrobione | `.env.example` celowo czytelny. `cat .env` przez Bash dalej przechodzi; to opisane ograniczenie mechanizmu. |
| D12 | `cd X && …`, `git switch -` | zrobione | w ramach K3. |
| D13 | `.git/ci-passed` rośnie bez końca | zrobione | ostatnie 200 wpisów. |
| D14 | `.idea/`, `.vscode/` w `.gitignore` projektu | zrobione | usunięte; to decyzja projektu. |

Znane ograniczenia, które zostają:
- Hook git nie widzi poleceń w `bash -c "…"`, aliasów gita ani skryptów.
- Na Windowsie testy podmiany Pythona (atrapy w `PATH`) są pomijane; CI na `windows-latest` sprawdza resztę, w tym kodowanie i wrapper.
