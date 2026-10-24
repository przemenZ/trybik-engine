# Start projektu od zera

Kiedy: brak `docs/product/vision.md`, a poza plikami trybik-engine repo jest puste (jest kod lub dokumenty projektu → `adoption.md`). Ma pierwszeństwo przed „Dostarcz kolejny feature” z `CLAUDE.md`.
Cel: dojść do pierwszych ticketów funkcji `ready`, mając wizję, stos, architekturę i działający szkielet aplikacji, na którym kolejne tickety się wzorują.

Zasady:
- Każdy krok kończy się **STOP: akceptacja właściciela**. Bez niej nie idziesz dalej.
- Pytania zadajesz partiami po 1–3, każde z rekomendacją (właściciel może odpowiedzieć „tak”). Nierozstrzygnięte → `docs/QUESTIONS.md`.
- Dokumenty krótkie: piszesz to, czego agent potrzebuje do pracy, nie podręcznik.
- Git: kroki 1–5 (do akceptacji T-001) na branchu `docs/kickoff`; potem PR, `bash tools/ci.sh` (PR z samą dokumentacją nie uruchamia CI na GitHubie) i `gh pr merge --squash`. T-001 i dalej — branch wg ticketu.

## 0. Właściciel (ręcznie, przed sesją)
Instaluje trybik-engine (`README.md` i `install.py` z repo trybik-engine), wpisuje nazwę w `CLAUDE.md`, `git init`, pierwszy commit na `main` (hook git przepuszcza pierwszy commit; każdy następny idzie na branchu), repo na GitHubie: `gh repo create <nazwa> --private --source=. --push`.

## 1. Wizja → `docs/product/vision.md`
Z `docs/templates/product.md`. Rozmowa z właścicielem: problem, użytkownicy, cele, poza zakresem, MVP, ograniczenia, słownik pojęć. Zakres MVP to lista funkcji (każda dostanie spec), nie ticketów.
**STOP: akceptacja** (`Status: accepted`).

## 2. Stos → `docs/adr/0001-stos-technologiczny.md`
Z `docs/templates/adr.md`: język, framework, baza, uruchamianie i wdrożenie (gdzie działa aplikacja), narzędzia test/lint/typy/format. 2–3 opcje z rekomendacją, dopasowane do ograniczeń z wizji.
**STOP: akceptacja** (`Status: accepted`). Potem uzupełnij w `CLAUDE.md` komendy (część oznaczysz „do potwierdzenia w T-001”) i scope commitów.

## 3. Architektura → `docs/architecture/overview.md`
Z `docs/templates/architecture.md`: moduły i granice, przepływ danych, konwencje (język kodu/commitów/dokumentacji, błędy, logi, konfiguracja), testy.
**STOP: akceptacja.**

## 4. Spece funkcji MVP → `docs/specs/<funkcja>.md`
Z `docs/templates/spec.md`, po jednym na funkcję z MVP. Niejasności → `QUESTIONS.md` z `blokuje: -` (tickety jeszcze nie istnieją).
**STOP: akceptacja** (każdy spec `Status: accepted`).

## 5. T-001 Szkielet aplikacji
Ticket: `python3 tools/docs_check.py --new "Szkielet aplikacji"` (szablon `docs/templates/ticket.md`), `kind: plain`, `spec:` puste, `allow` obejmuje cały szkielet, `rank` najniższy. Do zrobienia:
- struktura katalogów wg architektury, menedżer zależności, `.gitignore` uzupełniony o stos;
- lint/format, typy, runner testów z jednym testem przykładowym (nazwa wg konwencji z architektury);
- najprostszy przepływ end-to-end (np. strona/endpoint/komenda „health”) uruchamiany komendą dev;
- `.env.example` z pierwszymi zmiennymi;
- komendy w `CLAUDE.md` sprawdzone w praktyce;
- CI: te same komendy w `tools/ci.sh` (w miejsce bloku `UWAGA`), przygotowanie środowiska w `.github/workflows/ci.yml`. PR T-001 przechodzi CI na GitHubie; jeśli GitHub nie uruchomi zadania — `bash tools/ci.sh` lokalnie i wpis w `STATE.md`, że przygotowanie środowiska w `ci.yml` czeka na pierwsze uruchomienie na GitHubie.

Kod T-001 jest wzorcem, na który wskazują sekcje B kolejnych ticketów.
**STOP: akceptacja** (`draft` → `ready`), potem dostarczenie wg `docs/runbooks/delivery.md`.

## 6. Tickety funkcji
Skill `/ticket`: ze speców, pionowe wycinki (`docs/PROCESS.md`, „Lejek wymagań”); zależne od T-001 (`depends: T-001`). Uzupełnij `docs/STATE.md` („Gdzie jesteśmy”: MVP i najbliższy kamień milowy).
**STOP: akceptacja.** Dalej standardowo: „Dostarcz kolejny feature”.
