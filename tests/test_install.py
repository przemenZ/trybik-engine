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
