"""Instance storage: each instance is a directory used as its CLAUDE_CONFIG_DIR."""
import json
import os
import re
import shutil
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
RESERVED = {"ls", "list", "new", "rm", "mv", "path", "run", "help", "version"}
# Config worth sharing between instances (logins/history are never shared).
SHAREABLE = ("settings.json", "CLAUDE.md", "commands", "agents", "skills")


def root() -> Path:
    """Base directory for all instances (override with MULTICLAUDE_HOME)."""
    return Path(os.environ.get("MULTICLAUDE_HOME", Path.home() / ".multiclaude"))


def validate(name: str) -> str:
    if not NAME_RE.match(name):
        raise ValueError(f"invalid instance name: {name!r}")
    if name in RESERVED:
        raise ValueError(f"{name!r} is a reserved command name")
    return name


def path(name: str) -> Path:
    """Return the instance's config dir, creating it on first use."""
    p = root() / validate(name)
    p.mkdir(parents=True, exist_ok=True)
    return p


def existing(name: str) -> Path:
    p = root() / validate(name)
    if not p.is_dir():
        raise ValueError(f"no such instance: {name}")
    return p


def names() -> list:
    r = root()
    if not r.is_dir():
        return []
    return sorted(p.name for p in r.iterdir() if p.is_dir() and NAME_RE.match(p.name))


def account(p: Path) -> str:
    """Logged-in account email for an instance dir, or '' if not logged in."""
    for f in (p / ".claude.json", p / ".claude" / ".claude.json"):
        try:
            return json.loads(f.read_text()).get("oauthAccount", {}).get("emailAddress", "")
        except (OSError, ValueError, AttributeError):
            continue
    return ""


def last_used(p: Path) -> float:
    """Most recent mtime of the instance's top-level files (0 if empty)."""
    times = [c.stat().st_mtime for c in p.iterdir() if not c.is_symlink()]
    return max(times, default=0.0)


def _link(src: Path, dst: Path) -> None:
    """Symlink, falling back to a copy where symlinks aren't permitted (Windows)."""
    try:
        dst.symlink_to(src, target_is_directory=src.is_dir())
    except (OSError, NotImplementedError):
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def create(name: str, share_from: Path = None) -> Path:
    p = root() / validate(name)
    if p.exists():
        raise ValueError(f"instance already exists: {name}")
    p.mkdir(parents=True)
    if share_from:
        for item in SHAREABLE:
            src = share_from / item
            if src.exists():
                _link(src.resolve(), p / item)
    return p


def _force(func, path, _exc) -> None:
    """rmtree error hook: clear read-only bits (Windows) and retry."""
    os.chmod(path, 0o700)
    func(path)


def remove(name: str) -> None:
    shutil.rmtree(existing(name), onerror=_force)


def rename(old: str, new: str) -> None:
    src = existing(old)
    dst = root() / validate(new)
    if dst.exists():
        raise ValueError(f"instance already exists: {new}")
    src.rename(dst)
