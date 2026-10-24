#!/usr/bin/env bash
# Pełne sprawdzenie projektu — to samo na GitHubie (.github/workflows/ci.yml) i lokalnie: bash tools/ci.sh
# Lokalnie, gdy wszystko jest zacommitowane, zapamiętuje wynik dla tego commita (.git/ci-passed).
# Automat git (.claude/hooks/guard_git.py) wpuszcza wtedy PR do main także wtedy, gdy GitHub nie uruchomił
# testów (PR tylko z dokumentacją, brak minut). Błąd na GitHubie blokuje scalenie niezależnie od tego wyniku.
set -euo pipefail
cd "$(dirname "$0")/.."

tree=""
if [ -z "${CI:-}" ] && git rev-parse --git-dir >/dev/null 2>&1 && [ -z "$(git status --porcelain)" ]; then
  tree=$(git rev-parse -q --verify 'HEAD^{tree}' 2>/dev/null || true)
fi

run() { echo "▶ $*"; bash -c "$*"; }

run bash .claude/hooks/py.sh tools/docs_check.py  # python3 / python / py -3 — co działa na tej maszynie

# PR na GitHubie tylko z dokumentacją (docs/, *.md) → bez testów, lintu i typów (oszczędność minut).
docs_only=""
if [ -n "${GITHUB_BASE_REF:-}" ]; then
  # błąd gita (np. brak historii) = traktuj jak zmianę kodu
  changed=$(git diff --name-only "origin/$GITHUB_BASE_REF...HEAD") || changed="?"
fi
if [ -n "${changed:-}" ] && ! grep -qvE '^docs/|\.md$' <<<"$changed"; then
  docs_only=1
  echo "Tylko dokumentacja — pomijam testy, lint i typy."
fi

if [ -z "$docs_only" ]; then
# --- Stos: uzupełnia T-001 (te same komendy co w CLAUDE.md) w miejsce tego bloku ---
if grep -qs '^status: *done' docs/tickets/T-001-*.md; then
  echo "BŁĄD: T-001 jest done, a testy/lint/typy nie są skonfigurowane — uzupełnij tools/ci.sh."; exit 1
fi
echo "UWAGA: testy, lint i typy nie są jeszcze skonfigurowane (ticket T-001)."
# run "<lint>"
# run "<typy>"
# run "<testy>"
fi

if [ -n "$tree" ]; then
  f="$(git rev-parse --git-common-dir)/ci-passed"
  echo "$tree" >>"$f" && tail -n 200 "$f" >"$f.tmp" && mv "$f.tmp" "$f"  # ostatnie 200 wyników
  echo "OK: wynik zapamiętany dla commita $(git rev-parse --short HEAD)."
elif [ -z "${CI:-}" ]; then
  echo "OK, ale wynik nie został zapamiętany (niezacommitowane zmiany albo brak repo git)."
fi
