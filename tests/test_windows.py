"""K1/K2: skrypty działają przy kodowaniu Windowsa (cp1250) i bez komendy `python3`."""
import os
import shutil
import stat
import unittest
from pathlib import Path

from kit import ProjectCase, run

BASH = shutil.which("bash")


class Encoding(ProjectCase):
    CP1250 = {"PYTHONIOENCODING": "cp1250", "PYTHONUTF8": "0"}

    def test_ticket_parts_with_arrow(self):
        self.assertEqual(self.py("tools/docs_check.py", "--new", "Próba").returncode, 0)
        for role in ("implementer", "tester", "reviewer"):
            with self.subTest(role=role):
                r = self.py(".claude/skills/deliver/ticket_parts.py", role, "T-001", env=self.CP1250)
                self.assertEqual(r.returncode, 0, r.stderr)
        r = self.py(".claude/skills/deliver/ticket_parts.py", "tester", "T-001", env=self.CP1250)
        self.assertIn("→", r.stdout)

    def test_docs_check_cycle_message(self):
        for i in (1, 2):
            self.py("tools/docs_check.py", "--new", f"T{i}")
        for i, dep in ((1, "T-002"), (2, "T-001")):
            p = next(self.path("docs/tickets").glob(f"T-00{i}-*.md"))
            p.write_text(p.read_text(encoding="utf-8").replace("depends:\n", f"depends: {dep}\n", 1), encoding="utf-8")
        r = self.py("tools/docs_check.py", env=self.CP1250)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("T-001", r.stdout + r.stderr)


@unittest.skipUnless(BASH, "brak bash")
class PyWrapper(ProjectCase):
    def fake_bin(self, names):
        """Katalog PATH z atrapami: każda nazwa z `names` to działający Python, reszta nie istnieje."""
        b = self.dir / "fakebin"
        b.mkdir()
        real = shutil.which("python3") or shutil.which("python")
        for n in names:
            f = b / n
            f.write_text(f'#!{shutil.which("bash")}\n[ "${{1:-}}" = "-3" ] && shift\nexec "{real}" "$@"\n')
            f.chmod(f.stat().st_mode | stat.S_IEXEC)
        for tool in ("git", "cat", "dirname"):
            src = shutil.which(tool)
            if src:
                os.symlink(src, b / tool)
        return {"PATH": str(b), "CLAUDE_PROJECT_DIR": str(self.dir)}

    def wrapper(self, *args, env):
        return run([BASH, str(self.path(".claude/hooks/py.sh")), *args], self.dir, env=env)

    @unittest.skipIf(os.name == "nt", "atrapy PATH tylko na POSIX")
    def test_falls_back_to_py_launcher(self):
        env = self.fake_bin(["py"])
        r = self.wrapper("--session", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("`py -3`", r.stdout)
        self.assertEqual((self.dir / ".git" / "trybik-python").read_text().strip(), "py -3")
        r = self.wrapper("tools/docs_check.py", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    @unittest.skipIf(os.name == "nt", "atrapy PATH tylko na POSIX")
    def test_no_python_is_visible_error(self):
        r = self.wrapper("--session", env=self.fake_bin([]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("NIE działają", r.stderr)

    def test_exit_code_passes_through(self):
        self.write("exit2.py", "import sys; sys.exit(2)\n")
        r = self.wrapper(str(self.path("exit2.py")), env={"CLAUDE_PROJECT_DIR": str(self.dir)})
        self.assertEqual(r.returncode, 2, r.stderr)


if __name__ == "__main__":
    unittest.main()
