import os
import subprocess
import sys
import tempfile
import unittest


def mcl(home, *args):
    env = dict(os.environ, MULTICLAUDE_HOME=home)
    return subprocess.run([sys.executable, "-m", "multiclaude.cli_main", *args],
                          env=env, capture_output=True, text=True)


class Smoke(unittest.TestCase):
    def test_lifecycle(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertEqual(mcl(home, "new", "a").returncode, 0)
            self.assertIn("a", mcl(home, "ls").stdout)
            self.assertEqual(mcl(home, "mv", "a", "b").returncode, 0)
            self.assertEqual(mcl(home, "rm", "b", "-y").returncode, 0)
            self.assertNotEqual(mcl(home, "new", "ls").returncode, 0)
            self.assertIn("mcl", mcl(home, "--version").stdout)


if __name__ == "__main__":
    unittest.main()
