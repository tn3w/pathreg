import argparse
import os
import sys
from collections.abc import Callable
from pathlib import Path

_WINDOWS = sys.platform in ("win32", "cygwin")
_PROFILES = {
    "bash": ("~/.bash_profile", "~/.profile"),
    "sh": ("~/.profile",),
    "zsh": ("~/.zshenv",),
}

if _WINDOWS:
    import ctypes
    import winreg  # type: ignore

    def _reg_path():
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, "Path")[0]

    def _reg_set(value):
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
        ) as k:
            winreg.SetValueEx(k, "Path", 0, winreg.REG_EXPAND_SZ, value)

        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF, 0x1A, 0, "Environment", 2, 5000, None
        )


def _profile(shell: str) -> Path:
    """Return the best existing profile file for *shell*, or the first candidate."""
    if shell not in _PROFILES:
        raise NotImplementedError(f"Unsupported shell: {shell}")

    candidates = [Path(c).expanduser() for c in _PROFILES[shell]]
    return next((p for p in candidates if p.exists()), candidates[0])


def _shell() -> str:
    return os.environ.get("SHELL", "").rsplit("/", 1)[-1]


def _entry(directory: str) -> str:
    return f'PATH="{directory}:$PATH"\n'


def _add_path_windows(directory: str) -> None:
    """Prepend *directory* to the user PATH in the Windows registry. Idempotent."""
    directory = directory.strip().replace("/", "\\").removesuffix("\\")

    current = _reg_path()
    parts = current.split(os.pathsep)

    if directory not in parts and directory + "\\" not in parts:
        _reg_set(directory + os.pathsep + current)
        os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")


def _add_path_unix(directory: str) -> None:
    """Append a PATH entry for *directory* to the shell profile file. Idempotent."""
    directory = directory.strip().replace("\\", "/").removesuffix("/")

    profile = _profile(_shell())
    text = profile.read_text() if profile.exists() else ""

    if _entry(directory) not in text:
        profile.write_text(text + _entry(directory))
        os.environ["PATH"] = directory + ":" + os.environ.get("PATH", "")


def _remove_path_windows(directory: str) -> None:
    """Remove *directory* from the user PATH in the Windows registry."""
    directory = directory.strip().replace("/", "\\").removesuffix("\\")

    parts = [
        p for p in _reg_path().split(os.pathsep) if p.removesuffix("\\") != directory
    ]
    _reg_set(os.pathsep.join(parts))

    os.environ["PATH"] = os.pathsep.join(
        p
        for p in os.environ.get("PATH", "").split(os.pathsep)
        if p.removesuffix("\\") != directory
    )


def _remove_path_unix(directory: str) -> None:
    """Remove the PATH entry for *directory* from the shell profile file."""
    directory = directory.strip().replace("\\", "/").removesuffix("/")

    profile = _profile(_shell())
    if not profile.exists():
        return

    content = profile.read_text()
    for variant in (f"export {_entry(directory)}", _entry(directory)):
        content = content.replace(variant, "")
    profile.write_text(content)

    os.environ["PATH"] = ":".join(
        p for p in os.environ.get("PATH", "").split(":") if p != directory
    )


add_path: Callable[[str], None] = _add_path_windows if _WINDOWS else _add_path_unix
"""Add *directory* to PATH persistently and in the current process. Idempotent."""

remove_path: Callable[[str], None] = (
    _remove_path_windows if _WINDOWS else _remove_path_unix
)
"""Remove *directory* from PATH persistently and in the current process."""


def list_paths() -> list[Path]:
    """Return the current PATH entries as a list of Path objects."""
    raw = os.environ.get("PATH", "")
    sep = ";" if _WINDOWS else ":"

    return [Path(p) for p in raw.split(sep) if p]


def in_path(directory: str) -> bool:
    """Return True if *directory* is present in PATH."""
    sep = ";" if _WINDOWS else ":"
    suffix = "\\" if _WINDOWS else "/"
    target = directory.strip().removesuffix(suffix)

    return any(
        p.removesuffix(suffix) == target
        for p in os.environ.get("PATH", "").split(sep)
        if p
    )


def main():
    parser = argparse.ArgumentParser(prog="pathreg", description="Manage PATH entries.")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("add", "Add a directory to PATH"),
        ("remove", "Remove a directory from PATH"),
        ("check", "Check if a directory is in PATH"),
    ):
        sub.add_parser(name, help=help_text).add_argument("directory")

    sub.add_parser("list", help="List all PATH entries")

    args = parser.parse_args()

    if args.command == "list":
        for path in list_paths():
            print(path)
        return

    if args.command == "check":
        print("yes" if in_path(args.directory) else "no")
        return

    actions = {"add": (add_path, "Added"), "remove": (remove_path, "Removed")}
    action, verb = actions[args.command]
    action(args.directory)
    print(f"{verb} {args.directory!r}")


if __name__ == "__main__":
    main()
