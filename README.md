<div align="center">

# ⚙️ trybik-engine

**Proces pracy z agentem AI w Claude Code: Ty decydujesz, co budować, agent buduje, a reguł pilnuje kod.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Zależności: tylko stdlib](https://img.shields.io/badge/zale%C5%BCno%C5%9Bci-tylko%20stdlib-2ea44f)](#czego-potrzebujesz)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-hooki%20%C2%B7%20agenci%20%C2%B7%20skille-D97757)](https://claude.com/claude-code)
[![Licencja: MIT](https://img.shields.io/badge/licencja-MIT-blue.svg)](LICENSE)

[Jak to wygląda](#jak-to-wygląda-w-praktyce) · [Szybki start](#szybki-start) · [Słowniczek](#słowniczek) · [Jak to działa](HOW-IT-WORKS.md)

</div>

---

trybik-engine to zestaw plików, który wgrywasz do swojego projektu. Po instalacji agent w [Claude Code](https://claude.com/claude-code) pracuje według stałego procesu: najpierw opisuje, co ma powstać, czeka na Twoją zgodę, a potem buduje w małych krokach, z testami i przeglądem kodu. Działa z każdym językiem i technologią, a projekt może być nowy albo istniejący.

## Jak to wygląda w praktyce

1. **Instalujesz** trybik-engine w katalogu projektu i otwierasz go w Claude Code.
2. **Piszesz „zacznij projekt”.** Agent rozmawia z Tobą o produkcie i po kolei przygotowuje: wizję, wybór technologii, architekturę i opisy funkcji. Każdy dokument czeka na Twoją akceptację albo poprawki.
3. **Agent dzieli pracę na tickety**, czyli małe zadania z listą warunków, które muszą być spełnione. Ticket zatwierdzasz Ty.
4. **Piszesz „dostarcz kolejny feature”.** Agent bierze następny zatwierdzony ticket i sam przeprowadza go do końca: kod, testy, przegląd, pull request, CI, scalenie.
5. **Gdy czegoś nie wie, pyta**, a pytania zapisuje w `docs/QUESTIONS.md`. Nie zgaduje.

**Twoja rola:** akceptujesz dokumenty i tickety, odpowiadasz na pytania i przeglądasz efekty. Kodu nie musisz pisać.

Dlaczego tak: agent, któremu da się tylko instrukcje, prędzej czy później je pominie. Tutaj najważniejszych reguł pilnują automaty. Agent nie zapisze nic na głównej gałęzi, nie scali PR-a z czerwonymi testami i nie wyjdzie poza zakres ticketu. Testy pisze osobny agent, który nie widzi implementacji, więc sprawdzają zachowanie, a nie odbijają kod.

## Czego potrzebujesz

| Co | Po co | Kiedy jest potrzebne |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | z nim rozmawiasz, on prowadzi pracę | od początku |
| [Python](https://www.python.org/downloads/) 3.8 lub nowszy | instalator i automaty pilnujące reguł | od początku |
| [Git](https://git-scm.com/downloads) | historia zmian; agent sam z niego korzysta | od pierwszego zapisu pracy |
| Konto na GitHubie i [GitHub CLI](https://cli.github.com/) (`gh`) po `gh auth login` | pull requesty i ich scalanie | od pierwszego scalenia; bez tego agent zatrzyma się na tym kroku i powie, czego brakuje |

**Windows:** zainstaluj Git for Windows, bo zawiera Git Bash. Bez niego Claude Code używa PowerShella i automaty nie działają. Python może się uruchamiać jako `python` albo `py -3` zamiast `python3`. Agent wykryje to sam.

Opcjonalnie: `/advisor` w Claude Code. Agent konsultuje wtedy trudne decyzje z mocniejszym modelem.

## Szybki start

**1. Pobierz trybik-engine:** `git clone https://github.com/przemenZ/trybik-engine.git` albo na GitHubie *Code → Download ZIP* i rozpakuj.

**2. Zainstaluj go w swoim projekcie.** W katalogu trybik-engine uruchom:

```bash
python3 install.py ścieżka/do/projektu      # Windows: py -3 install.py ścieżka\do\projektu
```

Katalog projektu może być pusty albo może już zawierać kod lub dokumenty. Nie musi być repozytorium gita. Instalator dokłada pliki procesu (`CLAUDE.md`, `docs/`, `tools/`, `.claude/`, `.github/`) i niczego nie usuwa.

**3. Otwórz projekt w Claude Code i napisz:**

- **„zacznij projekt”**, jeśli zaczynasz od zera ([co się dzieje](template/docs/runbooks/kickoff.md)),
- **„przejmij projekt”**, jeśli jest już kod albo dokumenty ([co się dzieje](template/docs/runbooks/adoption.md)).

Agent zapyta o nazwę projektu, w razie potrzeby założy repozytorium gita i zaproponuje repozytorium na GitHubie. Potem prowadzi Cię krok po kroku.

**Masz dokumenty spoza projektu** (notatki, PDF, docx)? Przed „przejmij projekt” skopiuj je do `docs/sources/`. Agent je przeczyta, ale nie będzie ich zmieniał.

<details>
<summary><b>Instalator odmówił albo zostawił pliki <code>*.pre-kit</code></b></summary>

Instalator odmawia, gdy projekt jest repozytorium gita z niezapisanymi zmianami albo gdy repo z historią stoi na głównej gałęzi (`main`/`master`). W obu przypadkach wypisuje, co zrobić. Zwykle trzeba zacommitować zmiany i przejść na nową gałąź (`git switch -c docs/adoption`). Odmawia też, gdy zostały pliki `*.pre-kit` z poprzedniej instalacji albo gdy celem jest katalog samego trybik-engine.

Jak instalator traktuje pliki, które już są w projekcie:

| Sytuacja w projekcie | Co robi instalator |
|---|---|
| brak pliku | kopiuje |
| plik identyczny | pomija |
| inny `.gitignore` albo `.gitattributes` | dopisuje brakujące linie pod nagłówkiem `# trybik-engine` |
| własne `.env.example` lub workflow o tej samej nazwie | zostawia wersję projektu (workflow scala się w tickecie T-001) |
| inny plik o tej samej nazwie, np. `CLAUDE.md` | wersję projektu odkłada jako `CLAUDE.md.pre-kit`, a scala ją agent przy „przejmij projekt” |

</details>

### Aktualizacja trybik-engine w projekcie

Pobierz nową wersję trybik-engine (`git pull` albo nowy ZIP) i uruchom:

```bash
python3 install.py --upgrade ścieżka/do/projektu
```

Aktualizacja zmienia tylko pliki procesu: hooki, skille, agentów, `docs_check.py`, szablony, runbooki i `PROCESS.md`. Plik, którego projekt nie zmieniał, jest po prostu nadpisywany. Plik zmieniony w projekcie trafia do `*.pre-kit` do scalenia (możesz poprosić o to agenta). Twoje pliki (`CLAUDE.md`, `STATE.md`, `QUESTIONS.md`, `BACKLOG.md`, `journal.md`, `tools/ci.sh`, `.claude/settings.json`, workflowy) zostają bez zmian. Dla `settings.json` instalator wypisuje, co doszło w nowej wersji.

## Codzienna praca

| Mówisz agentowi | Co się dzieje |
|---|---|
| „zacznij projekt” | start od zera: wizja → technologia → architektura → opisy funkcji → szkielet aplikacji → tickety |
| „przejmij projekt” | to samo, ale na podstawie istniejącego kodu i dokumentów |
| „dostarcz kolejny feature” | agent bierze następny zatwierdzony ticket i prowadzi go do scalenia |
| „dostarcz T-012” | to samo dla wskazanego ticketu |
| `/ticket` | agent pisze szkic nowego ticketu do Twojej akceptacji |

Narzędzie `tools/docs_check.py` w terminalu przydaje się, gdy chcesz coś sprawdzić sam:

```bash
python3 tools/docs_check.py                 # czy dokumentacja jest spójna
python3 tools/docs_check.py --next          # który ticket jest następny
python3 tools/docs_check.py --new "Tytuł"   # nowy szkic ticketu
python3 tools/docs_check.py --check T-012   # czy szkic można już zatwierdzić
python3 tools/docs_check.py --write         # odśwież listę ticketów w docs/BACKLOG.md
bash tools/ci.sh                            # pełne sprawdzenie, to samo co CI na GitHubie
```

## Słowniczek

| Pojęcie | Znaczenie |
|---|---|
| **spec** | opis, jak ma działać jedna funkcja (`docs/specs/`); zawsze aktualny |
| **ticket** | jedno małe zadanie (`docs/tickets/T-NNN-…`); po wykonaniu zostaje jako historia |
| **statusy ticketu** | `draft` (szkic) → `ready` (zatwierdzony przez Ciebie) → `in-progress` → `done`, albo `dropped` |
| **warstwy A / B / C** | trzy części ticketu: A co i po co, B jak to zrobić, C jak sprawdzić; każdy agent dostaje tylko swoje |
| **AC1, AC2…** | kryteria akceptacji, czyli warunki, które zmiana musi spełnić; każde ma swój test |
| **`allow`** | lista plików, które agent może zmieniać w danym tickecie |
| **STOP** | sytuacja, w której agent przerywa i pyta Ciebie, np. niejasne wymaganie albo praca poza zakresem |
| **ADR** | zapisana decyzja architektoniczna, np. wybór technologii (`docs/adr/`) |
| **`STATE.md`** | krótki opis, gdzie projekt jest teraz |
| **`QUESTIONS.md`** | pytania do Ciebie; pytanie może blokować ticket, dopóki nie odpowiesz |
| **`BACKLOG.md`** | lista ticketów generowana automatycznie; nie edytuj ręcznie |

## Czego pilnują automaty

- Żadnych commitów ani pushy na główną gałąź. Praca idzie na osobnych gałęziach i trafia do głównej przez pull request.
- PR scala się dopiero po zielonym CI. Gdy GitHub nie uruchomi testów, bo np. skończyły się darmowe minuty, wystarczy lokalne `bash tools/ci.sh` dla tego samego commita.
- Agent piszący kod zmienia tylko pliki z `allow` ticketu i nie widzi scenariuszy testowych.
- Dokumentacja musi być spójna. Przed końcem każdej odpowiedzi agenta uruchamia się `docs_check.py`.
- Groźne komendy (`rm -rf`, `git reset --hard`, `git clean`) wymagają Twojego potwierdzenia, a pliki `.env` są dla agenta niedostępne.

To barierki dla agenta, a nie zabezpieczenie: zdeterminowany agent obejdzie je przez Bash czy skrypty. Szczegóły w [HOW-IT-WORKS.md](HOW-IT-WORKS.md#bramki-jakości).

## FAQ

<details>
<summary><b>Czy projekt musi być w Pythonie?</b></summary>

Nie. Python obsługuje tylko narzędzia procesu. Technologię projektu wybierasz z agentem na starcie, a komendy testów i lintera agent wpisuje w pierwszym tickecie (T-001).

</details>

<details>
<summary><b>Czy muszę znać gita?</b></summary>

Nie bardzo. Branche, commity, pull requesty i scalanie robi agent. Raz trzeba zainstalować gita i GitHub CLI oraz zalogować się (`gh auth login`). Jeśli instalator odmówi, bo w projekcie są niezapisane zmiany, wypisze, co zrobić.

</details>

<details>
<summary><b>Czy działa z prywatnym repo na darmowym planie GitHuba?</b></summary>

Tak. PR z samą dokumentacją zużywa ok. minuty CI. Gdy minut zabraknie, agent uruchamia to samo sprawdzenie lokalnie.

</details>

<details>
<summary><b>Czy mogę pracować ręcznie, bez agenta?</b></summary>

Tak. Automaty działają tylko w sesji Claude Code. Dokumenty, szablony i `docs_check.py` działają tak samo przy pracy ręcznej, a scalania w przeglądarce nic nie blokuje.

</details>

<details>
<summary><b>Kiedy agent się zatrzymuje?</b></summary>

Gdy wymaganie jest niejasne albo dokumenty sobie przeczą, gdy trzeba wyjść poza zakres ticketu, gdy poprawka po testach lub przeglądzie nie przechodzi za pierwszym razem i przed decyzją trudną do odwrócenia. Szczegóły: [`delivery.md`](template/docs/runbooks/delivery.md).

</details>

## Więcej

| Dokument | Zawartość |
|---|---|
| [`HOW-IT-WORKS.md`](HOW-IT-WORKS.md) | przepływ, budowa ticketu, role agentów, automaty, CI, struktura plików, zasady, roadmapa |
| [`docs/PROCESS.md`](template/docs/PROCESS.md) | proces z perspektywy agenta, mapa dokumentów, Definition of Done |
| [`docs/runbooks/`](template/docs/runbooks/) | krok po kroku: start od zera, przejęcie projektu, dostarczanie ticketu |
| [`docs/templates/`](template/docs/templates/) | szablony: spec, ticket, ADR, architektura, produkt |
| [`AUTOMATION-PROPOSALS.md`](AUTOMATION-PROPOSALS.md) | wdrożone automaty i kolejne pomysły |

## Współtworzenie

Zgłoszenia i pull requesty są mile widziane. Przy zmianie procesu opisz problem, który rozwiązuje, najlepiej na przykładzie z praktyki. Zasady pracy nad samym trybik-engine są w [`CLAUDE.md`](CLAUDE.md), a decyzje w [`dev/`](dev/). Przed wysłaniem PR uruchom testy:

```bash
python3 -m unittest discover -s tests -v
```

## Licencja

[MIT](LICENSE)
