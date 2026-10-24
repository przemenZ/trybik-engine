# trybik-engine — praca nad samym kitem

To repo to kit procesu, a nie projekt prowadzony tym procesem.
- `template/` — ładunek kopiowany do projektów przez `install.py`. Instrukcje w `template/CLAUDE.md` i `template/docs/` są dla agenta w projekcie użytkownika, nie dla Ciebie.
- Korzeń: `install.py`, `tests/`, `dev/` (decyzje i plany kitu), README, CI kitu (`.github/workflows/kit-tests.yml`).

## Komendy
- testy: `python3 -m unittest discover -s tests -v` · jeden plik: `python3 -m unittest discover -s tests -p test_guard_git.py -v`
- ręczna próba instalacji: `python3 install.py <pusty-katalog-tymczasowy>`

## Zasady
- Kit musi działać na Linuksie, macOS i Windowsie (Git Bash). Python ≥ 3.8, tylko stdlib. CI kitu sprawdza ubuntu i windows.
- Każda poprawka hooka lub narzędzia z `template/` ma test w `tests/`. Testy instalują `template/` do katalogu tymczasowego i tam uruchamiają skrypty.
- Decyzje (co zrobione, zmienione albo celowo pominięte i dlaczego) → `dev/decisions.md`.
- Branche `feat|fix|chore|docs/<temat>`, bez commitów na `master`, do `master` przez PR (squash) po akceptacji właściciela.
