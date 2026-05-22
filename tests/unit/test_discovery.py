# tests/unit/test_discovery.py
"""Unit tests for the workspace header discovery engine."""

from pathlib import Path
from nirnaya.context.discovery import HeaderDiscovery


def test_header_discovery_crawling_and_ignores(tmp_path: Path):
    """Verifies that headers are captured while build/hidden zones are bypassed."""
    # Set up valid mock header files
    include_dir = tmp_path / "include"
    include_dir.mkdir()
    header_1 = include_dir / "api.h"
    header_1.write_text("// valid api")
    header_2 = include_dir / "utils.hpp"
    header_2.write_text("// valid utils")

    # Set up a fake file inside an ignored build directory
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    hidden_header = build_dir / "generated.h"
    hidden_header.write_text("// compile artifact")

    # Run discovery crawler
    discoverer = HeaderDiscovery(root_dir=tmp_path)
    found_headers = discoverer.discover_public_headers()

    # Assert accurate file matching
    assert len(found_headers) == 2
    assert header_1 in found_headers
    assert header_2 in found_headers
    assert hidden_header not in found_headers