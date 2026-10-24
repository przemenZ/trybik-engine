"""Wspólne dla hooków trybik-engine: widoczna awaria zamiast cichego wyłączenia ochrony."""
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def crashed(name):
    """Nie blokuje (exit 1), ale zostawia komunikat w transkrypcie i wpis w .git/trybik-hooks.log."""
    try:
        p = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, capture_output=True,
                           text=True, timeout=5)
        if p.returncode == 0:
            with open(ROOT / p.stdout.strip() / "trybik-hooks.log", "a", encoding="utf-8") as f:
                f.write(f"--- {name}\n{traceback.format_exc()}\n")
    except Exception:
        pass
    print(f"trybik-engine: hook {name} uległ awarii — ochrona NIE zadziałała (log: .git/trybik-hooks.log)",
          file=sys.stderr)
    return 1
