"""Unit tests for repository root and path normalization helpers."""

from pathlib import Path

from nirnaya.storage.git import GitWorkspace


def test_find_repo_root_from_nested_directory(tmp_path: Path):
    """Nested directories should resolve back to the nearest .git boundary."""
    repo_root = tmp_path / "repo"
    nested_dir = repo_root / "src" / "module"
    nested_dir.mkdir(parents=True)
    (repo_root / ".git").mkdir()

    workspace = GitWorkspace(start_path=nested_dir)

    assert workspace.find_repo_root() == repo_root


def test_get_relative_path_returns_repo_scoped_path(tmp_path: Path):
    """Absolute paths under the repo should be reduced to repo-relative paths."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()
    header = repo_root / "include" / "api.h"
    header.parent.mkdir()
    header.touch()

    workspace = GitWorkspace(start_path=repo_root)

    assert workspace.get_relative_path(header) == Path("include/api.h")


def test_get_relative_path_falls_back_outside_repo(tmp_path: Path):
    """Paths outside the repository should stay absolute."""
    workspace = GitWorkspace(start_path=tmp_path)
    external = tmp_path / "external.h"

    assert workspace.get_relative_path(external) == external.resolve()
