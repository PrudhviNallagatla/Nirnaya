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
    discoverer = HeaderDiscovery(tmp_path)
    found_headers = discoverer.discover_public_headers()

    # Assert accurate file matching
    assert len(found_headers) == 2
    assert header_1 in found_headers
    assert header_2 in found_headers
    assert hidden_header not in found_headers


def test_header_discovery_skips_nested_ignored_dirs(tmp_path: Path):
    """Ignored directories should be skipped even when nested under the workspace."""
    nested_header = tmp_path / "include" / "sub" / "api.hpp"
    nested_header.parent.mkdir(parents=True)
    nested_header.write_text("// valid nested api", encoding="utf-8")

    git_header = tmp_path / ".git" / "ignored.h"
    git_header.parent.mkdir()
    git_header.write_text("// ignored", encoding="utf-8")

    nirnaya_header = tmp_path / ".nirnaya" / "ignored.hh"
    nirnaya_header.parent.mkdir()
    nirnaya_header.write_text("// ignored", encoding="utf-8")

    discoverer = HeaderDiscovery(tmp_path)
    found_headers = discoverer.discover_public_headers()

    assert found_headers == [nested_header.resolve()]


def test_header_discovery_handles_permission_error(tmp_path: Path, monkeypatch):
    """A permission error in one subtree should not abort discovery."""
    visible_header = tmp_path / "visible.h"
    visible_header.write_text("// visible", encoding="utf-8")

    blocked_dir = tmp_path / "blocked"
    blocked_dir.mkdir()
    (blocked_dir / "hidden.h").write_text("// hidden", encoding="utf-8")

    original_iterdir = Path.iterdir

    def patched_iterdir(self: Path):
        if self.name == "blocked":
            raise PermissionError("blocked")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", patched_iterdir)

    discoverer = HeaderDiscovery(tmp_path)
    found_headers = discoverer.discover_public_headers()

    assert visible_header.resolve() in found_headers
    assert (blocked_dir / "hidden.h").resolve() not in found_headers
