import sys
import tempfile
import unittest
from pathlib import Path

from kit import KIT, ProjectCase, run


class FreshInstall(ProjectCase):
    def test_copies_template_only(self):
        self.assertTrue(self.path("CLAUDE.md").exists())
        self.assertTrue(self.path("docs/templates/ticket.md").exists())
        self.assertTrue(self.path(".claude/hooks/guard_git.py").exists())
        for kit_only in ("install.py", "tests", "dev", "README.md", ".github/workflows/kit-tests.yml"):
            self.assertFalse(self.path(kit_only).exists(), kit_only)

    def test_docs_check_passes(self):
        r = self.py("tools/docs_check.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class Refusals(unittest.TestCase):
    def test_refuses_kit_dir(self):
        r = run([sys.executable, str(KIT / "install.py"), str(KIT / "template")], KIT)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()


class Upgrade(ProjectCase):
    def setUp(self):
        super().setUp()
        from kit import git
        git(self.dir, "switch", "-q", "-c", "chore/upgrade")
        self.git = lambda *a: git(self.dir, *a)

    def upgrade(self):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "stan")
        r = run([sys.executable, str(KIT / "install.py"), "--upgrade", str(self.dir)], KIT)
        self.assertEqual(r.returncode, 0, r.stdout)
        return r.stdout

    def test_manifest_written(self):
        self.assertTrue(self.path(".claude/trybik-engine.json").exists())

    def test_project_files_untouched(self):
        self.write("docs/QUESTIONS.md", "moje pytania\n")
        self.write("CLAUDE.md", "mój projekt\n")
        self.upgrade()
        self.assertEqual(self.path("docs/QUESTIONS.md").read_text(encoding="utf-8"), "moje pytania\n")
        self.assertEqual(self.path("CLAUDE.md").read_text(encoding="utf-8"), "mój projekt\n")
        self.assertFalse(list(self.dir.rglob("*.pre-kit")))

    def test_unchanged_kit_file_is_updated(self):
        # symulacja starej wersji kitu: plik i manifest zgodne, ale inne niż template/
        import hashlib, json
        rel = "docs/PROCESS.md"
        self.path(rel).write_bytes(b"stara wersja\r\n")  # CRLF jak po checkoutcie na Windowsie
        m = json.loads(self.path(".claude/trybik-engine.json").read_text(encoding="utf-8"))
        m["files"][rel] = hashlib.sha256(b"stara wersja\n").hexdigest()
        self.write(".claude/trybik-engine.json", json.dumps(m))
        self.upgrade()
        self.assertEqual(self.path(rel).read_bytes(), (KIT / "template" / rel).read_bytes())
        self.assertFalse(self.path(rel + ".pre-kit").exists())

    def test_locally_changed_kit_file_goes_to_pre_kit(self):
        rel = "docs/runbooks/delivery.md"
        self.write(rel, "zmiana projektu\n")
        self.upgrade()
        self.assertEqual(self.path(rel + ".pre-kit").read_text(encoding="utf-8"), "zmiana projektu\n")

    def test_settings_news_are_listed(self):
        import json
        s = json.loads(self.path(".claude/settings.json").read_text(encoding="utf-8"))
        s["permissions"]["allow"] = []
        self.write(".claude/settings.json", json.dumps(s))
        out = self.upgrade()
        self.assertIn("permissions.allow: Bash(bash tools/ci.sh)", out)
        self.assertEqual(json.loads(self.path(".claude/settings.json").read_text(encoding="utf-8"))["permissions"]["allow"], [])

    def test_refuses_without_kit(self):
        with tempfile.TemporaryDirectory() as d:
            r = run([sys.executable, str(KIT / "install.py"), "--upgrade", d], KIT)
            self.assertEqual(r.returncode, 1)
