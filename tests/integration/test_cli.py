# tests/integration/test_cli.py
"""Integration test suite for the Nirnaya Typer CLI workflow."""

import os
import shutil
from pathlib import Path
from typer.testing import CliRunner
import pytest

from nirnaya.cli import app

runner = CliRunner()


@pytest.fixture
def clean_workspace(tmp_path: Path):
    """Mocks a clean workspace containing a dummy .git folder and test target fixtures."""
    # Mock a repository boundary so GitWorkspace resolves successfully
    (tmp_path / ".git").mkdir()
    
    # Write a clean target verification mock header
    include_dir = tmp_path / "include"
    include_dir.mkdir()
    header = include_dir / "api.h"
    header.write_text("""
    namespace test {
        struct Data {
            int id;
            float weight;
        };
    }
    """, encoding="utf-8")
    
    # Change current working directory to the temporary workspace path context safely
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield tmp_path, header
    
    # Restore environmental state context cleanups
    os.chdir(old_cwd)


def test_end_to_end_cli_lifecycle(clean_workspace):
    """Validates init execution tracking, clean checking, and drift error processing."""
    workspace_root, header_path = clean_workspace
    relative_header = "include/api.h"

    # 1. Execute 'init' scaffolding run
    init_result = runner.invoke(app, ["init", relative_header, "--name", "integration_test"])
    assert init_result.exit_code == 0
    assert "Captured immutable baseline profile snapshot" in init_result.stdout

    # 2. Execute 'check' audit loop on an unmodified project (Should return clear pass)
    check_clean = runner.invoke(app, ["check"])
    assert check_clean.exit_code == 0
    assert "All public interface layout commitments verified perfectly" in check_clean.stdout

    # 3. Introduce an ABI layout crash by appending a layout size extension field
    header_path.write_text("""
    namespace test {
        struct Data {
            int id;
            int newly_injected_breaking_field;
            float weight;
        };
    }
    """, encoding="utf-8")

    # 4. Re-execute check audit loop (Should successfully flag layout crash violation)
    check_drifted = runner.invoke(app, ["check"])
    assert check_drifted.exit_code == 1
    assert "ABI CONTRACT VIOLATIONS DETECTED" in check_drifted.stdout

    # 5. Execute 'update' to explicitly acknowledge the layout increment
    update_result = runner.invoke(app, ["update", relative_header])
    assert update_result.exit_code == 0

    # 6. Re-execute check (Should pass again since contract baseline evolved)
    check_post_update = runner.invoke(app, ["check"])
    assert check_post_update.exit_code == 0