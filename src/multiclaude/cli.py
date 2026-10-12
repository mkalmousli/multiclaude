"""Entry point: mcl <instance-name> [claude-args...]  |  mcl <command> ..."""
import sys
import time
from pathlib import Path

from . import __version__, instances, runner

USAGE = """\
mcl - run multiple Claude Code logins side by side

usage:
  mcl <name> [claude-args...]    start claude as instance <name>
  mcl ls                         list instances and their accounts
  mcl new <name> [--share[=DIR]] create an instance; --share links settings,
                                 CLAUDE.md, commands, agents, skills (default DIR: ~/.claude)
  mcl mv <old> <new>             rename an instance
  mcl rm <name> [-y]             delete an instance and its login
  mcl path <name>                print the instance's config dir
  mcl run <name> [args...]       same as 'mcl <name>' (for names clashing with commands)
  mcl --version | --help
"""


def _ago(ts: float) -> str:
    if not ts:
        return "never"
    s = max(0, int(time.time() - ts))
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return f"{s // n}{unit} ago"
    return "just now"


def cmd_ls(_args: list) -> None:
    rows = [(n, instances.account(instances.root() / n) or "-",
             _ago(instances.last_used(instances.root() / n))) for n in instances.names()]
    if not rows:
        print("no instances yet - try: mcl new work")
        return
    w = max(len(r[0]) for r in rows)
    w2 = max(len(r[1]) for r in rows)
    for n, acct, used in rows:
        print(f"{n:<{w}}  {acct:<{w2}}  {used}")


def cmd_new(args: list) -> None:
    share = None
    names = []
    for a in args:
        if a == "--share":
            share = Path.home() / ".claude"
        elif a.startswith("--share="):
            share = Path(a.split("=", 1)[1]).expanduser()
        else:
            names.append(a)
    if len(names) != 1:
        raise ValueError("usage: mcl new <name> [--share[=DIR]]")
    p = instances.create(names[0], share)
    print(f"created {p}\nnext: mcl {names[0]}   (log in on first run)")


def cmd_rm(args: list) -> None:
    yes = "-y" in args
    names = [a for a in args if a != "-y"]
    if len(names) != 1:
        raise ValueError("usage: mcl rm <name> [-y]")
    instances.existing(names[0])
    if not yes and input(f"delete '{names[0]}' and its login/history? [y/N] ").lower() != "y":
        sys.exit("aborted")
    instances.remove(names[0])
    print(f"removed {names[0]}")


def cmd_mv(args: list) -> None:
    if len(args) != 2:
        raise ValueError("usage: mcl mv <old> <new>")
    instances.rename(*args)
    print(f"renamed {args[0]} -> {args[1]}")


def cmd_path(args: list) -> None:
    if len(args) != 1:
        raise ValueError("usage: mcl path <name>")
    print(instances.existing(args[0]))


COMMANDS = {"ls": cmd_ls, "list": cmd_ls, "new": cmd_new, "rm": cmd_rm,
            "mv": cmd_mv, "path": cmd_path}


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE, end="", file=sys.stderr if not argv else sys.stdout)
        sys.exit(2 if not argv else 0)
    if argv[0] in ("-V", "--version", "version"):
        print(f"mcl {__version__}")
        return
    try:
        if argv[0] in COMMANDS:
            COMMANDS[argv[0]](argv[1:])
        elif argv[0] == "run":
            if len(argv) < 2:
                raise ValueError("usage: mcl run <name> [args...]")
            runner.run(argv[1], argv[2:])
        else:
            runner.run(argv[0], argv[1:])
    except ValueError as e:
        sys.exit(f"mcl: {e}")
    except (KeyboardInterrupt, EOFError):
        sys.exit(130)
