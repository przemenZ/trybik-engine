# Architektura

- Data: RRRR-MM-DD
- Decyzje: ADR 0001

<!-- Mapa dla agentów: gdzie co jest i jak się tu pisze kod. Żywy dokument — poprawiany w ticketach, które zmieniają strukturę
     (lista „Docs do aktualizacji”). Bez opisu działania funkcji (to spec) i bez uzasadnień decyzji (to ADR). -->

## Moduły i granice
| Moduł / katalog | Odpowiada za | Nie robi |
|---|---|---|
| ... | ... | ... |

## Przepływ danych
Główne ścieżki: wejście → przetwarzanie → zapis/wyjście (lista kroków albo prosty diagram).

## Konwencje
- Język: kod i identyfikatory …; komunikaty commitów …; dokumentacja …
- Nazewnictwo plików i symboli: …
- Błędy: jak zgłaszamy i obsługujemy (rodzaj błędu → zachowanie): …
- Logi: co logujemy; czego nigdy (sekrety, dane osobowe): …
- Konfiguracja: zmienne środowiskowe w `.env.example`, wartości domyślne: …

## Testy
- Gdzie leżą i jak się nazywają (ID kryterium w nazwie, np. `test_T012_AC2_…`): …
- Jak uruchomić jeden test i całość → komendy w `CLAUDE.md`.
- Dane testowe / fixtures: …
- Co mockujemy, a czego nie: …

## Uruchomienie i wdrożenie
Lokalnie → komendy w `CLAUDE.md`. Wdrożenie → `docs/runbooks/` (jeśli istnieje).
