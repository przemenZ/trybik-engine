#!/usr/bin/env bash
# Uruchamia skrypt Pythonem działającym na tej maszynie (python3 / python / py -3, wersja >= 3.8), w trybie UTF-8.
# Na Windowsie zwykle nie ma `python3` (albo jest atrapą ze Sklepu), stąd wykrywanie zamiast stałej komendy.
#
#   bash py.sh skrypt.py [arg…]   uruchamia skrypt; kod wyjścia skryptu przechodzi bez zmian (2 = blokada hooka)
#   bash py.sh --session          hook SessionStart: wykrywa od nowa i mówi agentowi, jakiej komendy używać
#
# Wynik wykrycia jest zapisany osobno dla każdej maszyny w .git/trybik-python (nie trafia do repo),
# bo commitowany settings.json jest wspólny dla Linuksa, macOS i Windowsa.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cache=""
if gitdir=$(git -C "$root" rev-parse --git-common-dir 2>/dev/null); then
  case "$gitdir" in /* | [A-Za-z]:*) ;; *) gitdir="$root/$gitdir" ;; esac
  cache="$gitdir/trybik-python"
fi
missing="trybik-engine: nie znaleziono Pythona >= 3.8 (python3, python, py -3) — hooki procesu NIE działają."

detect() {
  local c
  for c in python3 python "py -3"; do
    # $c bez cudzysłowu: `py -3` = program + argument
    if $c -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
      [ -z "$cache" ] || echo "$c" >"$cache" 2>/dev/null
      echo "$c"
      return 0
    fi
  done
  return 1
}

if [ "${1:-}" = "--session" ]; then
  py=$(detect) || { echo "$missing" >&2; exit 1; }
  if [ "$py" != "python3" ]; then
    echo "Na tej maszynie Python uruchamia się komendą \`$py\`: w komendach z CLAUDE.md, runbooków i skilli zamiast \`python3\` używaj \`$py\`."
  fi
  exit 0
fi

py=""
[ -z "$cache" ] || [ ! -f "$cache" ] || py=$(cat "$cache" 2>/dev/null)
[ -n "$py" ] || py=$(detect) || { echo "$missing" >&2; exit 1; }
exec $py "$@"
