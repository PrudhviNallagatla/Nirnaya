# tests/unit/test_vault.py
"""Unit tests for storage vault serialization and tracking configuration."""

from datetime import datetime
from pathlib import Path
from nirnaya.core.models import BlueprintModel
from nirnaya.storage.vault import StorageVault


def test_vault_initialization_and_flow(tmp_path: Path):
    """Verifies layout creation, template configuration, and archiving cycles."""
    # Initialize vault
    vault = StorageVault.initialize(tmp_path, "test_project")
    
    assert vault.config_path.exists()
    assert vault.blueprint_dir.exists()
    assert vault.history_dir.exists()
    assert vault.get_tracked_headers() == []

    # Configure tracked records
    vault.track_headers(["include/core.h", "include/utils.h"])
    assert vault.get_tracked_headers() == ["include/core.h", "include/utils.h"]

    # Save active snapshot contract
    model = BlueprintModel(
        header_path="include/core.h",
        captured_at=datetime(2026, 5, 22, 12, 0, 0),
        nirnaya_version="0.1.0"
    )
    vault.save_blueprint(model)
    
    # Reload validation check
    loaded = vault.load_blueprint("include/core.h")
    assert loaded.header_path == "include/core.h"

    # Save tracking rotation update to trigger audit archive transition
    updated_model = BlueprintModel(
        header_path="include/core.h",
        captured_at=datetime(2026, 5, 22, 13, 0, 0),
        nirnaya_version="0.1.0"
    )
    vault.save_blueprint(updated_model)

    # Check history backup folder contains the archived cycle record
    archive_dir = vault.history_dir / "include__core.h"
    assert archive_dir.exists()
    assert len(list(archive_dir.glob("*.json"))) == 1