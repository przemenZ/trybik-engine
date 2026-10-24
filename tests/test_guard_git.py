"""K3, W1, D12: hook git — macierz poleceń na main i na gałęzi funkcji."""
import json
import unittest

from kit import ProjectCase, git, run

BLOCK, OK = 2, 0


class GuardCase(ProjectCase):
    def setUp(self):
        super().setUp()
        git(self.dir, "branch", "feat/T-001-x")

    def check(self, cases):
        for cmd, expected in cases:
            with self.subTest(cmd=cmd):
                r = self.hook("guard_git", {"tool_name": "Bash", "cwd": str(self.dir), "tool_input": {"command": cmd}})
                self.assertEqual(r.returncode, expected, r.stderr)


class OnMain(GuardCase):
    def test_matrix(self):
        self.check([
            ("git commit -m x", BLOCK),
            ("git --no-pager commit -m x", BLOCK),
            ("git -P commit -m x", BLOCK),
            ("git -c user.name=x commit -m x", BLOCK),
            ('git commit -m "a; git switch feat/T-001-x"', BLOCK),
            ("git cherry-pick abc", BLOCK),
            ("git rebase feat/T-001-x", BLOCK),
            ("git reset --hard HEAD~1", BLOCK),
            ("git revert HEAD", BLOCK),
            ("git push", BLOCK),
            ("git push origin HEAD", BLOCK),
            ("git push origin main", BLOCK),
            ("git push origin +main", BLOCK),
            ("git push origin feat/T-001-x:main", BLOCK),
            ("git push origin HEAD:refs/heads/main", BLOCK),
            ("git push --mirror", BLOCK),
            ("git push --all origin", BLOCK),
            ("git push origin --delete main", BLOCK),
            ("git push origin -d main", BLOCK),
            ("git merge feat/T-001-x", BLOCK),
            ("git status && git commit -m x 2>&1 | tail -1", BLOCK),
            # dozwolone
            ("git reset --hard origin/main", OK),
            ("git reset -- plik", OK),
            ("git reset", OK),
            ("git rebase --abort", OK),
            ("git merge origin/main", OK),
            ("git pull", OK),
            ("git push origin v1.0", OK),
            ("git push --tags", OK),
            ("git switch -c feat/T-002-y && git commit -m x", OK),
            ("git checkout -b feat/T-002-y && git commit -m x", OK),
            ("git switch feat/T-001-x && git commit -m x", OK),
            ("git log --oneline | head", OK),
        ])

    def test_switch_back_to_previous(self):
        git(self.dir, "switch", "-q", "feat/T-001-x")
        git(self.dir, "switch", "-q", "main")
        self.check([("git switch - && git commit -m x", OK)])
        git(self.dir, "switch", "-q", "feat/T-001-x")
        self.check([("git switch - && git commit -m x", BLOCK)])


class OnFeature(GuardCase):
    def setUp(self):
        super().setUp()
        git(self.dir, "switch", "-q", "feat/T-001-x")

    def test_matrix(self):
        self.check([
            ("git push origin +main", BLOCK),
            ("git push origin +feat/T-001-x", BLOCK),
            ("git push -f", BLOCK),
            ("git push --force origin feat/T-001-x", BLOCK),
            ("git push origin main", BLOCK),
            ("git push origin HEAD:main", BLOCK),
            ("git switch main && git commit -m x", BLOCK),
            ("git checkout main && git push", BLOCK),
            # dozwolone
            ("git push", OK),
            ("git push -u origin HEAD", OK),
            ("git push -u origin feat/T-001-x", OK),
            ("git push --force-with-lease", OK),
            ("git push origin --delete feat/old", OK),
            ("git commit -m x", OK),
            ("git checkout main -- plik && git commit -m x", OK),
            ("git rebase origin/main", OK),
            ("git reset --hard HEAD~1", OK),
        ])

    def test_cd_to_other_repo(self):
        other = self.dir / "other"
        other.mkdir()
        git(other, "init", "-q", "-b", "main")
        git(other, "commit", "-q", "--allow-empty", "-m", "init")
        self.check([
            ("cd other && git commit -m x", BLOCK),
            (f"git -C {other.as_posix()} commit -m x", BLOCK),
            ("cd other && git switch -c feat/z && git commit -m x", OK),
        ])


class Bootstrap(GuardCase):
    """Krok 0 kickoff/adoption: pierwsze wypchnięcie `main` idzie przez `gh repo create --push`, nie `git push`."""

    def test_publish_main_from_main(self):
        self.check([("gh repo create x --private --source=. --push", OK)])

    def test_publish_main_later_from_branch(self):
        git(self.dir, "switch", "-q", "feat/T-001-x")
        self.check([
            ("git switch main && gh repo create x --private --source=. --push && git switch feat/T-001-x", OK),
            ("git push -u origin main", BLOCK),
        ])


class Crash(ProjectCase):
    def test_crash_is_visible(self):
        r = self.py(".claude/hooks/guard_git.py", input="nie-json")
        self.assertEqual(r.returncode, 1)
        self.assertIn("NIE zadziałała", r.stderr)
        self.assertTrue((self.dir / ".git" / "trybik-hooks.log").exists())

    def test_gh_failure_blocks_merge(self):
        data = {"tool_name": "Bash", "cwd": str(self.dir), "tool_input": {"command": "gh pr merge --squash"}}
        r = self.hook("guard_git", data, env={"PATH": str(self.dir / "brak")})  # brak gh i git
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("gh", r.stderr)


if __name__ == "__main__":
    unittest.main()
