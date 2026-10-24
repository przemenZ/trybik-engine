"""W6, D13: tools/ci.sh — PR z samą dokumentacją i przycinanie .git/ci-passed."""
import shutil
import unittest

from kit import ProjectCase, git, run

BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "brak bash")
class CiScript(ProjectCase):
    def ci(self, env=None):
        return run([BASH, "tools/ci.sh"], self.dir, env=env)

    def pr(self, rel):
        git(self.dir, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(self.dir, "switch", "-q", "-c", "feat/x")
        self.write(rel, "x\n")
        git(self.dir, "add", "-A")
        git(self.dir, "commit", "-q", "-m", "x")
        return self.ci({"CI": "1", "GITHUB_BASE_REF": "main"})

    def test_docs_only_pr_skips_stack(self):
        r = self.pr("docs/specs/a.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Tylko dokumentacja", r.stdout)

    def test_code_pr_runs_stack(self):
        r = self.pr("src/a.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("Tylko dokumentacja", r.stdout)

    def test_missing_base_counts_as_code(self):
        r = self.ci({"CI": "1", "GITHUB_BASE_REF": "nie-ma"})
        self.assertNotIn("Tylko dokumentacja", r.stdout)

    def test_ci_passed_is_trimmed(self):
        f = self.dir / ".git" / "ci-passed"
        f.write_text("".join(f"{i}\n" for i in range(300)))
        r = self.ci({"CI": ""})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        lines = f.read_text().split()
        self.assertEqual(len(lines), 200)
        self.assertEqual(lines[-1], git(self.dir, "rev-parse", "HEAD^{tree}"))


if __name__ == "__main__":
    unittest.main()
