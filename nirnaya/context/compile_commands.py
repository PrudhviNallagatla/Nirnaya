# nirnaya/context/compile_commands.py
"""Compilation database flags extractor for C++ headers.

Looks up relevant compilation arguments from compile_commands.json to supply 
the libclang parser with precise architecture include context.
"""

import json
import os
import shlex
from pathlib import Path
from typing import List, Optional


class CompileCommandsReader:
    """Discovers compile_commands.json and maps compilation flags to header files."""

    def __init__(self, start_dir: Optional[Path] = None):
        self.start_dir = Path(start_dir or os.getcwd()).resolve()

    def find_database(self) -> Optional[Path]:
        """Climbs the directory tree upwards looking for a compile_commands.json file."""
        current = self.start_dir
        # Check current directory, common build sub-directories, and go upwards
        search_patterns = [
            current / "compile_commands.json",
            current / "build" / "compile_commands.json",
            current / "out" / "compile_commands.json",
        ]
        
        for path in search_patterns:
            if path.exists():
                return path

        # Walk upwards towards root folder
        for parent in current.parents:
            check_path = parent / "compile_commands.json"
            if check_path.exists():
                return check_path
            build_path = parent / "build" / "compile_commands.json"
            if build_path.exists():
                return build_path

        return None

    def get_flags_for_header(self, header_path: str, db_path: Optional[Path] = None) -> List[str]:
        """Extracts the best matching compilation flags from the database for a header.

        Falls back to default flags if no compilation database is discovered.
        """
        resolved_db = db_path or self.find_database()
        if not resolved_db or not resolved_db.exists():
            return ["-std=c++17"]  # Default sensible fallback flag

        try:
            with open(resolved_db, "r", encoding="utf-8") as f:
                db_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return ["-std=c++17"]

        target_abs = os.path.abspath(header_path)
        target_dir = os.path.dirname(target_abs)

        best_match_entry = None
        best_prefix_len = -1

        # Search for the best sibling match in compile_commands.json
        for entry in db_data:
            if "file" not in entry:
                continue
                
            entry_file_abs = os.path.abspath(entry["file"])
            entry_dir = os.path.dirname(entry_file_abs)

            # Perfect match: A source file sits in the exact same directory as our header
            if entry_dir == target_dir:
                best_match_entry = entry
                break

            # Prefix match: Find a source file that shares the closest directory path hierarchy
            common_prefix = os.path.commonpath([entry_dir, target_dir])
            if common_prefix and len(common_prefix) > best_prefix_len:
                best_prefix_len = len(common_prefix)
                best_match_entry = entry

        if not best_match_entry:
            return ["-std=c++17"]

        # Parse command or arguments list
        raw_args: List[str] = []
        if "arguments" in best_match_entry:
            raw_args = best_match_entry["arguments"]
        elif "command" in best_match_entry:
            raw_args = shlex.split(best_match_entry["command"])

        return self._filter_flags(raw_args)

    def _filter_flags(self, args: List[str]) -> List[str]:
        """Filters out compiler engine invocations, outputs, and inputs.

        Keeps only include paths (-I, -isystem), macro defines (-D), and standard constraints (-std).
        """
        clean_flags: List[str] = []
        skip_next = False

        for i, arg in enumerate(args):
            if skip_next:
                skip_next = False
                continue

            # Skip compiler executable path entirely
            if i == 0 and not arg.startswith("-"):
                continue

            # Strip compilation input source targets and binary outputs
            if arg in ("-o", "-c"):
                if arg == "-o":
                    skip_next = True  # Skip the output file name coming next
                continue
            if not arg.startswith("-") and arg.endswith((".cpp", ".cc", ".cxx", ".c")):
                continue

            # Retain relevant preprocessor and language parameters
            if arg.startswith(("-I", "-D", "-std=", "-isystem", "--sysroot")):
                clean_flags.append(arg)

        return clean_flags