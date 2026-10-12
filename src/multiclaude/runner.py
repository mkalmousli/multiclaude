"""Launch claude inside an instance's isolated environment."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import instances


def build_env(name: str) -> dict:
    """Environment for an instance; extend here to add per-instance settings."""
    env = dict(os.environ)
    env["CLAUDE_CONFIG_DIR"] = str(instances.path(name))
    return env


def find_claude() -> str:
    exe = os.environ.get("MULTICLAUDE_CLAUDE") or shutil.which("claude")
    if not exe:
        sys.exit("mcl: 'claude' not found in PATH")
    return exe


def run(name: str, args: list) -> None:
    env = build_env(name)
    exe = find_claude()
    if os.name == "nt":
        # No real exec() on Windows: run as a child and mirror its exit code.
        try:
            sys.exit(subprocess.call([exe, *args], env=env))
        except KeyboardInterrupt:
            sys.exit(130)
    os.execvpe(exe, [Path(exe).name, *args], env)
