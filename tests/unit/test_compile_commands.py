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
            "file": str(tmp_path / "src/main.cpp"),
        }
    ]

    db_file.write_text(json.dumps(mock_db))

    reader = CompileCommandsReader(start_dir=tmp_path)
    flags = reader.get_flags_for_header(
        str(tmp_path / "include/api.h"), db_path=db_file
    )

    # Assert flags we care about were successfully retained
    assert "-std=c++20" in flags
    assert "-I./include" in flags
    assert "-DDEBUG" in flags

    # Assert compiler fluff inputs and outputs were stripped away
    assert "g++" not in flags
    assert "-c" not in flags
    assert "-o" not in flags


def test_find_database_prefers_build_directory(tmp_path: Path):
    """The reader should discover compile_commands.json in a parent build folder."""
    build_db = tmp_path / "build" / "compile_commands.json"
    build_db.parent.mkdir(parents=True)
    build_db.write_text("[]", encoding="utf-8")

    reader = CompileCommandsReader(start_dir=tmp_path / "src" / "module")

    assert reader.find_database() == build_db


def test_malformed_database_falls_back_to_default_flags(tmp_path: Path):
    """Invalid JSON should degrade to the safe default standard flag."""
    db_file = tmp_path / "compile_commands.json"
    db_file.write_text("not-json", encoding="utf-8")

    reader = CompileCommandsReader(start_dir=tmp_path)

    assert reader.get_flags_for_header("include/api.h", db_path=db_file) == [
        "-std=c++17"
    ]


def test_arguments_entries_and_malformed_records_are_handled(tmp_path: Path):
    """Arguments arrays should be accepted and malformed entries skipped."""
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    header = source_dir / "api.h"
    header.write_text("// header", encoding="utf-8")

    db_file = tmp_path / "compile_commands.json"
    db_file.write_text(
        json.dumps(
            [
                {},
                {
                    "directory": str(source_dir),
                    "arguments": [
                        "g++",
                        "-std=c++23",
                        "-Iinclude",
                        "-DTRACE",
                        "-c",
                        str(source_dir / "api.cpp"),
                        "-o",
                        str(source_dir / "api.o"),
                    ],
                    "file": str(source_dir / "api.cpp"),
                },
            ]
        ),
        encoding="utf-8",
    )

    reader = CompileCommandsReader(start_dir=tmp_path)
    flags = reader.get_flags_for_header(str(header), db_path=db_file)

    assert flags == ["-std=c++23", "-Iinclude", "-DTRACE"]
