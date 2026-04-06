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
pathreg list
```

## Python API

```python
from pathreg import add_path, remove_path, list_paths

add_path("/some/directory")     # idempotent — skips if already present
remove_path("/some/directory")  # no-op if not found
list_paths()                    # returns list[Path] of current PATH entries
```

`add_path` and `remove_path` modify the shell profile **and** the current process's `PATH` immediately.

## Behavior

- Paths are normalized: trailing separators stripped, slashes converted per platform.
- `add_path` is idempotent — does nothing if the entry already exists.
- `remove_path` is a no-op if the entry is absent or the profile file does not exist.

## Platform support

| Platform | Persistence target                                                                 |
| -------- | ---------------------------------------------------------------------------------- |
| Windows  | `HKCU\Environment` via `winreg`; broadcasts `WM_SETTINGCHANGE` to notify the shell |
| bash     | `~/.bash_profile` (falls back to `~/.profile` if it exists)                        |
| zsh      | `~/.zshenv`                                                                        |
| sh       | `~/.profile`                                                                       |

The active shell is detected from the `SHELL` environment variable.

No third-party dependencies required.
