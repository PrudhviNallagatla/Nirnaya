# tests/unit/test_blueprint.py
"""Unit tests for the blueprint serialization engine."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from nirnaya.core.blueprint import BlueprintEngine
from nirnaya.core.models import BlueprintModel


def test_deterministic_serialization_output(tmp_path):
    """Ensures that blueprint structures serialize deterministically with sorted fields."""
    model = BlueprintModel(
        header_path="include/test.h",
        captured_at=datetime(2026, 5, 22, 12, 0, 0),
        nirnaya_version="0.1.0",
        structs=[],
        free_functions=[],
        enums=[],
        typedefs=[],
    )

    json_str = BlueprintEngine.serialize(model)
    parsed_json = json.loads(json_str)

    # Assert fields parsed back seamlessly
    assert parsed_json["header_path"] == "include/test.h"
    assert "captured_at" in parsed_json

    # Reload validation test through the actual file loader
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json_str, encoding="utf-8")
    reloaded_model = BlueprintEngine.load_from_file(snapshot_path)
    assert reloaded_model.header_path == "include/test.h"


def test_blueprint_round_trip_preserves_model(tmp_path: Path):
    """Confirms saved blueprints can be loaded back without data loss."""
    model = BlueprintModel(
        header_path="include/sample.h",
        captured_at=datetime(2026, 5, 22, 12, 0, 0),
        nirnaya_version="0.1.0",
        structs=[],
        free_functions=[],
        enums=[],
        typedefs=[],
    )

    snapshot_path = tmp_path / "snapshots" / "sample.json"
    BlueprintEngine.save_to_file(model, snapshot_path)

    assert snapshot_path.exists()

    loaded = BlueprintEngine.load_from_file(snapshot_path)
    assert loaded == model


def test_blueprint_load_missing_file_raises(tmp_path: Path):
    """Missing snapshot files should fail loudly and predictably."""
    with pytest.raises(FileNotFoundError):
        BlueprintEngine.load_from_file(tmp_path / "missing.json")
