# Przejęcie istniejącego projektu

Kiedy: brak `docs/product/vision.md`, a w repo jest już kod projektu albo dokumenty o nim (legacy, zaczątek aplikacji, zbiór dokumentów — także ich mieszanka). Repo bez niczego poza kitem → `kickoff.md`.
Cel: jak w `kickoff.md` (wizja, stos, architektura, T-001, pierwsze tickety `ready`), ale z tego, co już jest, a nie od zera.

Zasady:
- Jak w `kickoff.md`: STOP i akceptacja po każdym kroku, pytania partiami z rekomendacją, krótkie dokumenty.
- **Kod mówi, co jest; dokumenty — co miało być.** Rozbieżność → `docs/QUESTIONS.md` z rekomendacją. Nie wybierasz po cichu.
- Każdy dokument z kroków 3–7: jest w kodzie → opisz stan obecny, nie projektuj na nowo; jest tylko w dokumentach → wyciągnij i daj do akceptacji; brak → krok z `kickoff.md` (podany przy kroku).
- Czytasz oszczędnie: manifesty (`package.json`, `pyproject.toml`, …), drzewo katalogów, punkty wejścia, konfigurację CI, katalogi testów, 1–2 reprezentatywne moduły — nie cały kod. Szeroki przegląd → agent `Explore`.
- `docs/sources/` (materiały zastane) czytasz w krokach 1–6; potem tylko, gdy wskazuje je spec lub ticket. Nie poprawiasz ich.
- Dług i problemy znalezione po drodze → szkice ticketów (`/ticket`) albo `docs/journal.md`; w `docs/STATE.md` najwyżej kilka linii.
- Git: kroki 1–7 (do akceptacji T-001) na branchu `docs/adoption`; potem PR, `bash tools/ci.sh`, `gh pr merge --squash`. T-001 i dalej — branch wg ticketu.

## 0. Właściciel (ręcznie, przed sesją)
Wg `README.md` kitu, „Istniejący projekt”: instalacja kitu na branchu `docs/adoption`, dokumenty spoza repo (notatki, PDF, docx) w `docs/sources/`, nazwa projektu w `CLAUDE.md`.

## 1. Inwentaryzacja (bez zmian w plikach)
Najpierw `CLAUDE.md.pre-kit` i pliki `CLAUDE.md` w podkatalogach: ich zasady bezpieczeństwa (np. czego nie uruchamiać) obowiązują od razu.
Raport dla właściciela (≤20 linii):
- kod: języki, framework, wielkość, moduły, punkty wejścia, jak się uruchamia;
- testy i CI: czy są, komendy, stan na głównej gałęzi (`gh run list --branch <main|master> --limit 3`; testy lokalnie tylko, gdy ruszają bez dodatkowej konfiguracji);
- dokumenty: lista z jednym zdaniem o każdym i oceną aktualności; pliki w `docs/` spoza mapy z `docs/PROCESS.md` → propozycja: `docs/sources/` albo żywy dokument z mapy;
- konflikty z instalacji (`*.pre-kit`, workflow i `.env.example` projektu), pliki `CLAUDE.md` w podkatalogach (ładują się same — sprzeczne z procesem → pytanie), istniejące ADR i ich miejsce;
- rozbieżności kod ↔ dokumenty i luki.

**STOP, gdy testy lub CI na głównej gałęzi są czerwone**: automat git nie scali żadnego PR, dopóki CI nie przejdzie. Co z nimi zrobić (naprawa, kwarantanna z ticketem) decyduje właściciel — pytanie w `QUESTIONS.md`.
**STOP: akceptacja** raportu (co jest aktualne, co pomijamy, np. kod zewnętrzny).

## 2. Porządki po instalacji
- Pliki z `docs/` spoza mapy — wg decyzji z kroku 1.
- `*.pre-kit` poza `CLAUDE.md.pre-kit`: treść projektu przenieś do wersji kitu (np. uprawnienia i hooki w `.claude/settings.json`), potem usuń `*.pre-kit`.
- Lint, typy lub pre-commit projektu obejmują całe repo → wyłącz z nich `.claude/` i `tools/` (pliki kitu), inaczej PR adopcji będzie czerwony.
- `CLAUDE.md.pre-kit` rozbierasz w krokach 4–5 (komendy, konwencje); reguły sprzeczne z procesem → pytanie. Usuwasz go po kroku 5.

## 3. Wizja → `docs/product/vision.md`
Z `docs/templates/product.md`, ze źródeł i rozmowy. Działający system: „Zakres MVP” = najbliższy kamień milowy (co zmieniamy lub dodajemy), nie katalog tego, co już działa. Brak materiału → `kickoff.md` krok 1.
**STOP: akceptacja** (`Status: accepted`).

## 4. Stos → ADR „stos technologiczny”
Numer: kolejny wolny w `docs/adr/` (`0001`, gdy pusty); zastane ADR zostają bez zmian. Kod jest → ADR opisuje zastany stos (Kontekst: „przyjęty z istniejącego kodu”), alternatywy tylko dla brakujących elementów (np. runner testów, linter). Brak kodu → `kickoff.md` krok 2.
Komendy (z manifestów, CI, `CLAUDE.md.pre-kit`) → `CLAUDE.md`, oznaczone „do potwierdzenia w T-001”; scope commitów.
**STOP: akceptacja.**

## 5. Architektura → `docs/architecture/overview.md`
Z `docs/templates/architecture.md`. Kod jest → stan obecny: moduły, przepływ, konwencje faktycznie stosowane (także z `CLAUDE.md.pre-kit`), testy (gdzie są, czego brak). Nie projektujesz docelowej — zmiany struktury to tickety i ADR. Brak kodu → `kickoff.md` krok 3.
**STOP: akceptacja.**

## 6. Spece
- Funkcje planowane (z wizji) → `kickoff.md` krok 4; materiał z `docs/sources/`, jeśli jest.
- Funkcje działające → nie opisujesz z góry. Spec powstaje przed pierwszym ticketem, który funkcję zmienia: najpierw obecne zachowanie (z kodu, akceptuje właściciel), potem zmiana.
**STOP: akceptacja.**

## 7. T-001
Brak kodu aplikacji → `kickoff.md` krok 5 (szkielet). Jest kod → T-001 „Podpięcie procesu”: `python3 tools/docs_check.py --new "Podpięcie procesu"`, `kind: plain`, `spec:` puste, `allow` = konfiguracja (CI, narzędzia, manifest, testy). Do zrobienia:
- komendy w `CLAUDE.md` sprawdzone w praktyce (install, testy, jeden test, lint, typy, dev);
- te same komendy w `tools/ci.sh` w miejsce bloku `UWAGA`; lint/typy, które nie przechodzą na całym kodzie → tylko zmienione pliki albo baseline (naprawa całości → osobne tickety);
- brak testów → runner wg ADR i jeden test dymny (np. start aplikacji), żeby tester miał wzorzec;
- CI na GitHubie: jeden workflow przygotowuje środowisko i woła `bash tools/ci.sh` (komendy tylko w `ci.sh`). Instalator zostawił workflow projektu o tej samej nazwie → dopisz do niego ten krok; kit dodał `ci.yml` obok innych workflowów → scal je;
- `.env.example` z bieżącymi zmiennymi.
Wzorzec dla sekcji B kolejnych ticketów: moduły wskazane w architekturze.
**STOP: akceptacja** (`draft` → `ready`), potem dostarczenie wg `docs/runbooks/delivery.md`.

## 8. Tickety
Jak `kickoff.md` krok 6 (skill `/ticket`). Dług z inwentaryzacji → szkice ticketów lub `journal.md`.
**STOP: akceptacja.** Dalej standardowo: „Dostarcz kolejny feature”.
