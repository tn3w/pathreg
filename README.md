# pathreg

Persistently add or remove directories from `PATH` on Windows, Linux, and macOS.

## Installation

```sh
pip install pathreg
```

## CLI Usage

```sh
pathreg add /some/directory
pathreg remove /some/directory
pathreg set /a /b /c            # replace PATH with given directories
pathreg list
pathreg check /some/directory   # prints "yes" or "no"
pathreg find python             # prints full path or "not found"
pathreg clean                   # removes duplicates and non-existent entries
```

## Python API

```python
from pathreg import add_path, remove_path, list_paths, in_path, find_executable, clean_path

add_path("/some/directory")       # idempotent, skips if already present
remove_path("/some/directory")    # no-op if not found
set_path(["/a", "/b", "/c"])      # replace PATH entirely with given list
list_paths()                      # returns list[Path] of current PATH entries
in_path("/some/directory")        # returns True if directory is in PATH
find_executable("python")         # returns Path to first match, or None
clean_path()                      # removes duplicates and non-existent dirs, returns cleaned list[Path]
```

`add_path` and `remove_path` modify the shell profile **and** the current process's `PATH` immediately.

## Behavior

- Paths are normalized: trailing separators stripped, slashes converted per platform.
- `add_path` is idempotent, does nothing if the entry already exists.
- `remove_path` is a no-op if the entry is absent or the profile file does not exist.
- `list_paths` reflects the current process `PATH`; it does not read the profile file.
- `in_path` normalizes trailing separators before comparing, matching `add_path` behaviour.
- `find_executable` walks PATH entries in order and returns the first regular file that is executable, or `None`.
- `clean_path` removes non-existent directories and duplicates (resolved via symlinks) from the current process PATH in-place, and returns the cleaned list.

## Platform support

| Platform | Persistence target                                                                 |
| -------- | ---------------------------------------------------------------------------------- |
| Windows  | `HKCU\Environment` via `winreg`; broadcasts `WM_SETTINGCHANGE` to notify the shell |
| bash     | `~/.bash_profile` (falls back to `~/.profile` if it exists)                        |
| zsh      | `~/.zshenv`                                                                        |
| sh       | `~/.profile`                                                                       |

The active shell is detected from the `SHELL` environment variable.

No third-party dependencies required.
