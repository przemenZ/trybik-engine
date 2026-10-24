"""Wspólne narzędzia testów: instalacja template/ do katalogu tymczasowego i uruchamianie skryptów kitu."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_NOSYSTEM": "1"}


def run(args, cwd, input=None, env=None, check=False):
    e = {**os.environ, **GIT_ENV, **(env or {})}
    return subprocess.run(args, cwd=str(cwd), input=input, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=e, check=check)


def git(cwd, *args):
    return run(["git", *args], cwd, check=True).stdout.strip()


class ProjectCase(unittest.TestCase):
    """Świeży projekt z zainstalowanym kitem (repo git z jednym commitem na `main`)."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="trybik-"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        r = run([sys.executable, str(KIT / "install.py"), str(self.dir)], KIT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        git(self.dir, "init", "-q", "-b", "main")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "init")

    def path(self, rel):
        return self.dir / rel

    def write(self, rel, text):
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def py(self, rel, *args, input=None, env=None):
        return run([sys.executable, str(self.path(rel)), *args], self.dir, input=input, env=env)

    def hook(self, name, data, env=None):
        return self.py(f".claude/hooks/{name}.py", input=json.dumps(data), env=env)
