# nirnaya/context/discovery.py
"""Automated workspace header file discovery tracking engine.

Recursively scans a project workspace directory tree to automatically harvest 
public C++ header configurations while gracefully skipping internal build artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Set

class HeaderDiscovery:
    """Recursively walks a workspace directory tree to discover trackable headers."""

    def __init__(self, workspace_root: Path):
        self.root = Path(workspace_root).resolve()
        # Common build, cache, and dependency folders to ignore
        self.ignored_dirs: Set[str] = {
            ".git",
            ".venv",
            "venv",
            "build",
            "out",
            "target",
            "bin",
            "obj",
            ".nirnaya",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache"
        }
        # C++ header file extensions we care about
        self.header_extensions: Set[str] = {".h", ".hpp", ".hxx", ".hh"}

    def discover_public_headers(self) -> list[Path]:
        """Crawls the workspace tree and returns a list of absolute header paths."""
        discovered: list[Path] = []
        self._crawl(self.root, discovered)
        return sorted(discovered)

    def _crawl(self, current_dir: Path, accumulator: list[Path]) -> None:
        """Recursive helper that avoids stepping into blacklisted directories."""
        try:
            for item in current_dir.iterdir():
                if item.is_symlink():  # skip all symlinks to prevent loop cycles
                    continue
                if item.is_dir():
                    if item.name in self.ignored_dirs:
                        continue
                    self._crawl(item, accumulator)
                elif item.is_file():
                    if item.suffix.lower() in self.header_extensions:
                        accumulator.append(item.resolve())
        except PermissionError:
            pass