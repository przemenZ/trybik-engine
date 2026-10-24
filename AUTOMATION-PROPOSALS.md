# Propozycje automatyzacji

Plik poza `docs/` — dotyczy trybik-engine, nie kopiuje się do projektu. Kolejność = rekomendowana kolejność wdrażania.

**Wdrożone w trybik-engine** (`.claude/`, oznaczone ✔ niżej): hook `Stop` (docs_check), hook git (commit/scalanie na `main`/`master`, force push, bramka CI przy `gh pr merge`), CI (`tools/ci.sh` + `.github/workflows/ci.yml`), uprawnienia (`.env`, `BACKLOG.md`, potwierdzanie destrukcyjnych komend), agenci `implementer` (z hookiem scope guard), `tester` i `reviewer`, skille `/deliver` i `/ticket` (z `docs_check.py --new`). Reszta to nadal propozycje.

## Jak działa Claude Code (tyle, ile potrzeba)
- **CLAUDE.md** — ładowany na starcie sesji; też z podkatalogów, gdy agent pracuje w nich (stąd reguły modułów w `moduł/CLAUDE.md`). To tylko tekst: agent może go zignorować.
- **Hooks** — polecenia powłoki uruchamiane przez *program*, nie przez model, na zdarzeniach (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop` …). Mogą zablokować akcję (kod wyjścia 2 + komunikat do agenta) lub wstrzyknąć kontekst. Konfiguracja w `.claude/settings.json`. **To jedyny sposób na egzekwowanie reguł, a nie tylko proszenie o nie.**
- **Subagenci** — pliki `.claude/agents/<nazwa>.md` z frontmatterem (`name`, `description`, `tools`, `model`) i promptem systemowym. Mają osobny kontekst i ograniczone narzędzia.
- **Skills / komendy** — `.claude/skills/<nazwa>/SKILL.md`; wywoływane przez `/nazwa` lub automatycznie wg opisu. Pakują powtarzalny workflow, żeby nie siedział w CLAUDE.md.
- **Permissions** — listy `allow`/`deny` w `settings.json` (np. zakaz `git push --force`, edycji `.env`).
- **MCP** — zewnętrzne narzędzia (tracker, przeglądarka, baza).
- **Worktrees** — równoległe kopie repo na osobnych branchach.

## 1. Hooki — egzekwowanie reguł procesu (najwyższa wartość)
| Zdarzenie | Co robi | Zastępuje regułę tekstową |
|---|---|---|
| ✔ `Stop` | uruchamia `docs_check`; przy błędzie (poza szkicami) blokuje zakończenie i podaje błędy agentowi | „pamiętaj o `--write`, STATE i spójności ticketów" |
| ✔ `PreToolUse` (Edit/Write; hook agenta `implementer`) | czyta aktywny ticket (z nazwy brancha `…/T-NNN-…`) i odrzuca edycję pliku spoza `allow` z front-matter | scope guard |
| ✔ `PreToolUse` (Bash) | blokuje commit, scalanie i push wprost na główną gałąź, force push oraz `gh pr merge` bez zielonego CI; destrukcyjne komendy → `ask` w uprawnieniach | „bez commitów na master", „merge po zielonym CI" |
| ✔ uprawnienia `deny` (zamiast hooka) | blokuje ręczną edycję `docs/BACKLOG.md` | „nie edytuj generowanych" |
| `PostToolUse` (Edit/Write) | formatuje/lintuje edytowany plik (np. `ruff`) | „odpal lint przed commitem" |
| `SessionStart` | wstrzykuje początek `STATE.md` i wynik `--next` | „zacznij od STATE i backlogu" |

Konfiguracja: `.claude/settings.json` (scope guard: frontmatter `.claude/agents/implementer.md`), skrypty w `.claude/hooks/`. Hook `Stop` blokuje najwyżej raz na turę (`stop_hook_active`), bo nie każdy błąd agent może naprawić sam (np. ticket właściciela), i pomija błędy szkiców. Awaria skryptu hooka nigdy nie blokuje (exit 0).

## 2. ✔ CI jako bramka (bez tego reszta jest kosmetyką)
Wdrożone: `tools/ci.sh` (docs_check + komendy stosu z T-001) uruchamiany przez `.github/workflows/ci.yml` na PR z kodem i lokalnie. Branch protection nie jest dostępna dla prywatnych repo na darmowym planie, więc bramką jest hook git przy `gh pr merge`: zielone CI na GitHubie albo — gdy GitHub nie uruchomił zadania (brak minut: zadanie bez runnera i kroków; PR z samą dokumentacją) — lokalny `tools/ci.sh` dla tego samego stanu (`.git/ci-passed`). Ręczne scalenie przez właściciela w przeglądarce pozostaje nieblokowane. Do rozważenia: przy płatnym planie włączyć branch protection jako drugą linię.

## 3. Subagenci jako pliki
`.claude/agents/{implementer,tester,reviewer}.md`:
- ✔ **tester** — model tańszy (`sonnet`); zapis tylko testów na razie z promptu — do rozważenia hook ograniczający zapis do katalogu testów;
- ✔ **reviewer** — tylko odczyt (`Read`, `Grep`, `Glob`, `Bash` do `git diff`), model mocniejszy (`opus`);
- ✔ **implementer** — model `sonnet` z advisorem; zapis ograniczony hookiem scope guard do `allow`, bez dostępu do `docs/tickets/` (zapis przez Bash zakazany tylko promptem).
Daje to izolację ról „z urzędu", zamiast kopiowania promptów z runbooka. Runbook zostaje jako opis kontraktu.

## 4. Skills (workflow na żądanie)
- ✔ `/ticket` — szkic ticketu ze speca, znaleziska lub prośby właściciela; plik, ID i rank tworzy `docs_check.py --new`, skill pilnuje treści (warstwy, rozmiar, `allow`, pytania). `docs_check.py --check T-NNN` sprawdza szkic jak `ready`, zanim właściciel zmieni status.
- ✔ `/deliver` — pętla z `delivery.md` (start → impl → test → review → domknięcie).
- `/triage-review` — przetwarza `docs/reviews/*`: każde znalezisko → `fixed` / ticket / pytanie / `wontfix`.
Odchudza to CLAUDE.md do samych niezmienników.

## 5. Jakość testów pisanych bez wiedzy o implementacji
Izolacja testera ma słabość: testy mogą przechodzić „na pusto". Proponowane przeciwwagi:
- **mutation testing** (w Pythonie: `mutmut`/`cosmic-ray`) na zmienionych plikach — wynik w raporcie testera; niski wskaźnik = testy za słabe;
- **property-based** (`hypothesis`) dla czystej logiki (np. podziały kwot, walidacje);
- **ślad AC → test**: znacznik w testach (`@pytest.mark.ac("T-012.AC2")`) i rozszerzenie `docs_check` o sprawdzenie, że każdy AC ma test (dziś narzędzie sprawdza tylko pokrycie scenariuszami C).

## 6. Równoległość
Skoro tickety mają `depends` i `rank`, niezależne `ready` można robić równolegle w osobnych **git worktree** (po jednym agencie na ticket, własny branch). Wymaga: rozłącznych `allow` (narzędzie mogłoby to sprawdzać) i limitu zasobów.

## 7. Weryfikacja uruchomieniem
Dla ticketów z UI/CLI: krok „uruchom i zobacz" (skill `run`, przeglądarka/MCP, zrzut ekranu) przed merge — testy jednostkowe nie wykrywają, że ekran nie wygląda lub nie działa.

## 8. Pętla uczenia
Po każdym reviewie powtarzający się błąd → jedna linia w `CLAUDE.md` (lub, lepiej, reguła w linterze/hooku). Raz na jakiś czas przegląd CLAUDE.md pod kątem zbędnych i przestarzałych reguł (skill `claude-md-improver`). Reguła, którą da się zamienić na test lub linter, nie powinna żyć jako tekst.

## 9. Uprawnienia
Allow-lista bezpiecznych komend (testy, lint, `git status/diff`, `docs_check`) ogranicza liczbę pytań o zgodę; deny-lista dla `git push --force`, `rm -rf`, edycji `.env`. Skill `fewer-permission-prompts` potrafi zaproponować listę na podstawie historii.

## Czego świadomie NIE proponuję
- Zewnętrznego trackera zadań (dodaje źródło prawdy, które się rozjedzie z repo).
- Rozbudowanego frameworka wieloagentowego: obecny podział (impl / test / review) wystarcza, a każdy kolejny agent to koszt kontekstu.
