# tests/unit/test_compile_commands.py
"""Unit tests for the compile commands context flag resolver."""

import json
from pathlib import Path
from nirnaya.context.compile_commands import CompileCommandsReader


def test_fallback_flags_when_db_missing():
    """Verifies that reader supplies default standards when no database file exists."""
    reader = CompileCommandsReader(start_dir=Path("/non/existent/path"))
    flags = reader.get_flags_for_header("include/api.h")
    assert flags == ["-std=c++17"]


def test_flags_extraction_and_filtering(tmp_path: Path):
    """Verifies finding database records and filtering out raw compiler fluff flags."""
    db_file = tmp_path / "compile_commands.json"
    
    mock_db = [
        {
            "directory": "/all_codes/Nirnaya",
            "command": "g++ -std=c++20 -I./include -DDEBUG -c src/main.cpp -o build/main.o",
            "file": str(tmp_path / "src/main.cpp")
        }
    ]
    
    db_file.write_text(json.dumps(mock_db))
    
    reader = CompileCommandsReader(start_dir=tmp_path)
    flags = reader.get_flags_for_header(str(tmp_path / "include/api.h"), db_path=db_file)
    
    # Assert flags we care about were successfully retained
    assert "-std=c++20" in flags
    assert "-I./include" in flags
    assert "-DDEBUG" in flags
    
    # Assert compiler fluff inputs and outputs were stripped away
    assert "g++" not in flags
    assert "-c" not in flags
    assert "-o" not in flags