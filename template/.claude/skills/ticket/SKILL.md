---
name: ticket
description: Pisze szkic ticketu (`draft`) ze speca, znaleziska z review albo prośby właściciela. Użyj, gdy brak ticketu `ready` do dostarczenia, gdy właściciel prosi o ticket(y) do funkcji lub speca, albo gdy w `/deliver` wyszła praca poza zakresem.
---

# Pisanie ticketu

Ticket to jedyne wejście implementera (A+B) i testera (A+C); obaj nie znają tej rozmowy. Struktura: `docs/templates/ticket.md` (komentarze w szablonie są instrukcją). Podział i rozmiar: `docs/PROCESS.md`, „Lejek wymagań”. Branch: `CLAUDE.md` (w `/deliver` — bieżący branch ticketu).

## 1. Źródło
- Spec `docs/specs/…`; zmiana zachowania bez speca → najpierw spec albo pytanie do właściciela. Działająca funkcja bez speca → najpierw spec obecnego zachowania (z kodu, akceptuje właściciel), potem zmiana.
- `docs/BACKLOG.md`: nie dubluj — istniejący szkic uzupełnij zamiast pisać nowy.
- Wzorzec dla B: `docs/architecture/overview.md` i kod T-001 albo podobnego modułu (tylko wskazane fragmenty).

## 2. Podział
Pionowe wycinki: każdy daje obserwowalny efekt i mieści się w ≲10 plikach / ≲100 liniach. Kolejność wykonania → `depends` (tickety funkcji co najmniej `T-001`).

## 3. Plik
Na każdy ticket: `python3 tools/docs_check.py --new "Tytuł"` → ścieżka nowego pliku (kolejne `T-NNN`, `draft`, rank na końcu kolejki, BACKLOG odświeżony). Wypełnij:
- `spec:` ścieżka speca; puste, gdy brak (np. `kind: plain`);
- `kind:` `logic`, gdy jest zachowanie do przetestowania; inaczej `plain` (bez warstwy C);
- `allow:` najwęższe globy obejmujące „Artefakty” z B (dla `logic` także testy);
- `rank:` zostaw, chyba że właściciel podał kolejność.

## 4. Samoocena
Treść sprawdzasz sam (strukturę sprawdza `--check` w kroku 6):
- [ ] A: bez ścieżek, klas i frameworków; „Out” konkretny; każde AC to jedno obserwowalne zachowanie.
- [ ] B: „Kontekst do przeczytania” to konkretne ścieżki i wzorzec, nie „przejrzyj repo”; „Artefakty” zgodne z `allow`; „Docs do aktualizacji” zawiera spec, gdy zmienia się zachowanie.
- [ ] C (`logic`): zrozumiała bez B (żadnych nazw plików i klas z B); scenariusze z konkretnymi danymi i oczekiwanym wynikiem.
- [ ] Rozmiar: „Artefakty” ≤10 plików; więcej → podziel.
- [ ] Każda niejasność w A rozstrzygnięta w „Decyzje” (z powodem) albo zamieniona w pytanie (krok 5). Nie zgadujesz.

## 5. Pytania
Po `--new` (potrzebne ID): wpis w `docs/QUESTIONS.md` wg formatu z pliku — kolejne `Q-NNN`, `blokuje: T-NNN`, rekomendacja.

## 6. Domknięcie
- `python3 tools/docs_check.py --write`, potem dla każdego nowego ticketu `python3 tools/docs_check.py --check T-NNN` — bez błędów poza otwartymi pytaniami z kroku 5. Na końcu `python3 tools/docs_check.py` (hook `Stop` pomija szkice, CI nie).
- Status zostaje `draft`; `ready` ustawia właściciel.
- Raport (≤6 linii): ID, tytuł, `depends`, nowe `Q-NNN`. **STOP: akceptacja właściciela.** Wywołany z `/deliver` → wróć do jego kroku; szkic trafia do raportu końcowego.
