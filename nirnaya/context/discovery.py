# nirnaya/context/discovery.py
"""Automated workspace header file discovery engine.

Crawls directory hierarchies to isolate and inventory public C/C++ interface
headers for contract assignment.
"""

from pathlib import Path
from typing import List, Set


class HeaderDiscovery:
    """Provides file-system crawling mechanics to find trackable public header files."""

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir).resolve()
        
        # Standard structural ignore patterns to avoid massive, unrelated scans
        self.ignored_directories: Set[str] = {
            ".git",
            ".github",
            ".nirnaya",
            "build",
            "out",
            "target",
            "node_modules",
            "vcpkg_installed",
            ".venv",
            "venv",
        }
        
        # Valid canonical C/C++ header extensions
        self.valid_extensions: Set[str] = {".h", ".hpp", ".hxx", ".hh", ".inl"}

    def discover_public_headers(self) -> List[Path]:
        """Scans the repository path recursively, collecting all viable C++ headers."""
        discovered_paths: List[Path] = []
        self._crawl(self.root_dir, discovered_paths)
        return sorted(discovered_paths)

    def _crawl(self, current_dir: Path, accumulator: List[Path]) -> None:
        """Recursively traverses directories while strictly enforcing ignore limits."""
        try:
            for item in current_dir.iterdir():
                if item.is_dir():
                    # Skip matching build folders or internal tracking repositories
                    if item.name in self.ignored_directories:
                        continue
                    self._crawl(item, accumulator)
                elif item.is_file():
                    if item.suffix.lower() in self.valid_extensions:
                        accumulator.append(item)
        except PermissionError:
            # Gracefully handle restricted systems folders or locked directories
            pass