# nirnaya/storage/git.py
"""Git repository workspace context resolution.

Ensures Nirnaya tracks path boundaries relative to the active project version 
control root structure.
"""

import os
from pathlib import Path
from typing import Optional


class GitWorkspace:
    """Discovers repository boundaries and provides path normalization mechanics."""

    def __init__(self, start_path: Optional[Path] = None):
        self.start_path = Path(start_path or os.getcwd()).resolve()

    def find_repo_root(self) -> Optional[Path]:
        """Climbs directories upwards to discover the absolute location of the .git boundary."""
        current = self.start_path
        
        if (current / ".git").exists():
            return current

        for parent in current.parents:
            if (parent / ".git").exists():
                return parent

        return None

    def get_relative_path(self, absolute_path: Path) -> Path:
        """Converts an absolute system path to an clear path scoped relative to the repo root."""
        root = self.find_repo_root()
        if not root:
            return absolute_path.resolve()
        
        try:
            return absolute_path.resolve().relative_to(root)
        except ValueError:
            # Handle cross-drive mappings on Windows systems gracefully
            return absolute_path.resolve()