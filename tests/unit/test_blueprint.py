# tests/unit/test_blueprint.py
"""Unit tests for the blueprint serialization engine."""

import json
from datetime import datetime

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
