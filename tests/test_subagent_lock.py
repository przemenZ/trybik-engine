"""Blokada tools/ci.sh na czas pracy subagentów (hooki SubagentStart/SubagentStop)."""
import json
import shutil
import time
import unittest

from kit import ProjectCase, run

BASH = shutil.which("bash")
AGENT = {"agent_id": "x", "agent_type": "tester"}


@unittest.skipUnless(BASH, "brak bash")
class SubagentLock(ProjectCase):
    def lock(self, arg, data=None, raw=None):
        inp = raw if raw is not None else json.dumps(data or {})
        return self.py(".claude/hooks/subagent_lock.py", arg, input=inp)

    @property
    def file(self):
        return self.dir / ".git" / "subagents-active"

    def test_start_check_stop(self):
        self.assertEqual(self.lock("--check").returncode, 0)
        self.assertEqual(self.lock("start", AGENT).returncode, 0)
        r = self.lock("--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("tester", r.stderr)
        self.assertIn("subagents-active", r.stderr)
        self.assertEqual(self.lock("stop", AGENT).returncode, 0)
        self.assertEqual(self.lock("--check").returncode, 0)

    def test_start_replaces_same_id_and_stop_removes_only_it(self):
        self.lock("start", AGENT)
        self.lock("start", AGENT)
        self.lock("start", {"agent_id": "y", "agent_type": "reviewer"})
        self.assertEqual(len(self.file.read_text().splitlines()), 2)
        self.lock("stop", AGENT)
        self.assertEqual(self.lock("--check").returncode, 1)
        self.lock("stop", {"agent_id": "y"})
        self.assertEqual(self.lock("--check").returncode, 0)

    def test_session_id_fallback(self):
        self.lock("start", {"session_id": "s1"})
        self.assertIn(" s1 ", self.file.read_text())

    def test_old_entry_is_ignored(self):
        self.file.write_text(f"{int(time.time()) - 31 * 60} x tester\n")
        self.assertEqual(self.lock("--check").returncode, 0)

    def test_garbage_stdin_never_blocks(self):
        self.assertEqual(self.lock("start", raw="nie json").returncode, 0)
        self.assertEqual(self.lock("stop", raw="").returncode, 0)

    def test_ci_sh_blocked_locally_not_on_github(self):
        self.lock("start", AGENT)
        r = run([BASH, "tools/ci.sh"], self.dir, env={"CI": ""})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("CI wstrzymane", r.stderr)
        r = run([BASH, "tools/ci.sh"], self.dir, env={"CI": "1"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.lock("stop", AGENT)
        r = run([BASH, "tools/ci.sh"], self.dir, env={"CI": ""})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_settings_register_hooks(self):
        s = json.loads(self.path(".claude/settings.json").read_text(encoding="utf-8"))
        for ev, arg in (("SubagentStart", "start"), ("SubagentStop", "stop")):
            cmd = s["hooks"][ev][0]["hooks"][0]["command"]
            self.assertTrue(cmd.endswith(f"subagent_lock.py\" {arg}"), cmd)


if __name__ == "__main__":
    unittest.main()
