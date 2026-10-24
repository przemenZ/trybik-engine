---
id: T-000
title: Krótki tytuł
status: draft
# draft | ready | in-progress | done | dropped  — to JEDYNE miejsce ze statusem
rank: 10
# niższy = wcześniej; kolejność ustala właściciel produktu
depends:
# T-001, T-002 (kolejny ticket do realizacji = najniższy rank spośród ready z ukończonymi zależnościami)
spec: docs/specs/<feature>.md
kind: logic
# logic = ma warstwę C i osobny test; plain = docs/config/chore/czysty layout (bez C)
allow:
# scope guard, globy po przecinku, np.: src/orders/**, tests/orders/**
---

<!-- Rozmiar: ≲10 plików, ≲100 linii; większe → podziel na tickety. Warstwa A jest nadrzędna, B i C jej nie zmieniają.
     Niejasność w A → STOP: pytanie do docs/QUESTIONS.md z `blokuje: T-000`, ticket zostaje draft. -->

# A. Produkt (CO / DLACZEGO) — bez plików, frameworków i kodu

## Cel
Jedno-dwa zdania: jaki problem użytkownika rozwiązujemy i jaki efekt.

## Zakres
- **In:** ...
- **Out:** ... (konkrety; praca poza zakresem lub poza `allow` → zatrzymaj się i zapytaj)

## Do zrobienia
- ...

## Decyzje
- Rozstrzygnięte w trakcie pisania (jedno zdanie + powód; `Q-NNN`, jeśli było pytanie).

## Akceptacja
- [ ] AC1: testowalne kryterium (zachowanie, nie implementacja)
- [ ] AC2: ...

---

# B. Implementacja (JAK) — czyta tylko agent implementujący

## Kontekst do przeczytania (tylko to; nie eksploruj repo)
- spec / ADR / plik-wzorzec do naśladowania (ścieżki, ew. zakres linii)

## Cel techniczny
1–2 zdania.

## Artefakty (typ + ścieżka)
- ...

## Zachowanie i integracje
Struktura, stany (loading/error/empty), teksty dla użytkownika, kontrakt API, obsługa błędów (klasa błędu → zachowanie).

## Ograniczenia
Czego NIE robić (bez nice-to-have, bez optymalizacji „przy okazji", bez testów — to warstwa C).

## Docs do aktualizacji
- spec / architektura / runbook, które ta zmiana czyni nieaktualnymi (reviewer sprawdza, czy zostały poprawione). `STATE.md` tylko gdy zmienia się stan lub ograniczenia.

---

# C. Weryfikacja — czyta agent testowy; NIE widzi sekcji B

## Co zostało zaimplementowane (3–5 punktów, język domenowy, bez nazw klas)
- ...

## Scenariusze (5–9; happy path → edge → walidacja → negatywne; każdy AC musi być pokryty)
1. [AC1] ...
2. [AC1] ...
3. [AC2] ...

## Struktura testów
- Przewaga testów jednostkowych (szybkie, logika), mniej integracyjnych, E2E tylko dla pełnego flow, jeśli niezbędny.
- Nazwa/oznaczenie testu zawiera ID kryterium (np. `T-012.AC2`), żeby dało się sprawdzić pokrycie.

## Anty-wzorce
- testowanie implementacji lub frameworka; scenariusze typu „mockuj X, wywołaj Y"; ciężki kontekst aplikacji do testu samej logiki.
