# tests/unit/test_diff.py
"""Unit tests for the contract blueprint diff verification core."""

from datetime import datetime
from nirnaya.core.models import BlueprintModel, StructModel, FieldModel, EnumModel
from nirnaya.core.diff import BlueprintDiffEngine


def test_clean_identical_blueprints_yields_zero_violations():
    """Confirms that comparing identical interfaces yields zero warnings."""
    struct_item = StructModel(name="Sample", size_bytes=4, fields=[
        FieldModel(name="id", type_spelling="int", offset_bits=0, is_public=True)
    ], is_class=False)

    blueprint_a = BlueprintModel(
        header_path="api.h", captured_at=datetime.utcnow(), nirnaya_version="0.1.0",
        structs=[struct_item]
    )
    blueprint_b = BlueprintModel(
        header_path="api.h", captured_at=datetime.utcnow(), nirnaya_version="0.1.0",
        structs=[struct_item]
    )

    violations = BlueprintDiffEngine.diff_blueprints(blueprint_a, blueprint_b)
    assert len(violations) == 0


def test_detects_struct_layout_size_and_offset_drift():
    """Verifies that field shifts and sizing spikes are instantly flagged as breaking."""
    old_struct = StructModel(name="Packet", size_bytes=4, fields=[
        FieldModel(name="flag", type_spelling="char", offset_bits=0, is_public=True),
        FieldModel(name="code", type_spelling="int", offset_bits=32, is_public=True)
    ], is_class=False)

    new_struct = StructModel(name="Packet", size_bytes=8, fields=[
        FieldModel(name="flag", type_spelling="char", offset_bits=0, is_public=True),
        # Simulated padding shifting the 'code' bit alignment offset downstream
        FieldModel(name="code", type_spelling="int", offset_bits=64, is_public=True)
    ], is_class=False)

    bp_old = BlueprintModel(header_path="a.h", captured_at=datetime.utcnow(), nirnaya_version="0.1.0", structs=[old_struct])
    bp_new = BlueprintModel(header_path="a.h", captured_at=datetime.utcnow(), nirnaya_version="0.1.0", structs=[new_struct])

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)
    
    categories = [v.category for v in violations]
    assert "struct_layout" in categories
    assert any("offset drifted" in v.description for v in violations)


def test_detects_enum_constant_value_mutation():
    """Flags mutations to hard-coded underlying enum assignments."""
    old_enum = EnumModel(name="Status", values={"OK": 0, "ERROR": 1})
    new_enum = EnumModel(name="Status", values={"OK": 0, "ERROR": 99})  # ABI breaking change

    bp_old = BlueprintModel(header_path="a.h", captured_at=datetime.utcnow(), nirnaya_version="0.1.0", enums=[old_enum])
    bp_new = BlueprintModel(header_path="a.h", captured_at=datetime.utcnow(), nirnaya_version="0.1.0", enums=[new_enum])

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)
    assert len(violations) == 1
    assert violations[0].category == "enum_value"
    assert violations[0].severity == "breaking"