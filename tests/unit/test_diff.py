# tests/unit/test_diff.py
"""Unit tests for the contract blueprint diff verification core."""

from datetime import datetime
from nirnaya.core.models import (
    BlueprintModel,
    EnumModel,
    FieldModel,
    FunctionModel,
    ParameterModel,
    StructModel,
)
from nirnaya.core.diff import BlueprintDiffEngine


def test_clean_identical_blueprints_yields_zero_violations():
    """Confirms that comparing identical interfaces yields zero warnings."""
    struct_item = StructModel(
        name="Sample",
        size_bytes=4,
        fields=[
            FieldModel(name="id", type_spelling="int", offset_bits=0, is_public=True)
        ],
        is_class=False,
    )

    blueprint_a = BlueprintModel(
        header_path="api.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[struct_item],
    )
    blueprint_b = BlueprintModel(
        header_path="api.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[struct_item],
    )

    violations = BlueprintDiffEngine.diff_blueprints(blueprint_a, blueprint_b)
    assert len(violations) == 0


def test_detects_struct_layout_size_and_offset_drift():
    """Verifies that field shifts and sizing spikes are instantly flagged as breaking."""
    old_struct = StructModel(
        name="Packet",
        size_bytes=4,
        fields=[
            FieldModel(
                name="flag", type_spelling="char", offset_bits=0, is_public=True
            ),
            FieldModel(
                name="code", type_spelling="int", offset_bits=32, is_public=True
            ),
        ],
        is_class=False,
    )

    new_struct = StructModel(
        name="Packet",
        size_bytes=8,
        fields=[
            FieldModel(
                name="flag", type_spelling="char", offset_bits=0, is_public=True
            ),
            # Simulated padding shifting the 'code' bit alignment offset downstream
            FieldModel(
                name="code", type_spelling="int", offset_bits=64, is_public=True
            ),
        ],
        is_class=False,
    )

    bp_old = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[old_struct],
    )
    bp_new = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[new_struct],
    )

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)

    categories = [v.category for v in violations]
    assert "struct_layout" in categories
    assert any("offset drifted" in v.description for v in violations)


def test_detects_enum_constant_value_mutation():
    """Flags mutations to hard-coded underlying enum assignments."""
    old_enum = EnumModel(name="Status", values={"OK": 0, "ERROR": 1})
    new_enum = EnumModel(
        name="Status", values={"OK": 0, "ERROR": 99}
    )  # ABI breaking change

    bp_old = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        enums=[old_enum],
    )
    bp_new = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        enums=[new_enum],
    )

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)
    assert len(violations) == 1
    assert violations[0].category == "enum_value"
    assert violations[0].severity == "breaking"


def test_treats_equivalent_integer_aliases_as_same_type():
    """Prevents alias-only noise for common fixed-width integer spellings."""
    old_struct = StructModel(
        name="SocketState",
        size_bytes=4,
        fields=[
            FieldModel(
                name="socket_fd",
                type_spelling="int32_t",
                offset_bits=0,
                is_public=False,
            )
        ],
        is_class=True,
    )
    new_struct = StructModel(
        name="SocketState",
        size_bytes=4,
        fields=[
            FieldModel(
                name="socket_fd", type_spelling="int", offset_bits=0, is_public=False
            )
        ],
        is_class=True,
    )

    old_func = FunctionModel(
        name="connect",
        return_type="void",
        parameters=[ParameterModel(name="port", type_spelling="int32_t")],
    )
    new_func = FunctionModel(
        name="connect",
        return_type="void",
        parameters=[ParameterModel(name="port", type_spelling="int")],
    )

    bp_old = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[old_struct],
        free_functions=[old_func],
    )
    bp_new = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[new_struct],
        free_functions=[new_func],
    )

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)
    assert violations == []


def test_reports_enum_additions_removals_and_removed_enum():
    old_enum = EnumModel(name="Mode", values={"A": 0, "B": 1})
    new_enum = EnumModel(name="Mode", values={"A": 0, "C": 2})
    removed_enum = EnumModel(name="Gone", values={"Z": 9})

    bp_old = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        enums=[old_enum, removed_enum],
    )
    bp_new = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        enums=[new_enum],
    )

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)

    descriptions = [v.description for v in violations]
    assert any("removed from enum 'Mode'" in d for d in descriptions)
    assert any("New enum constant 'C'" in d for d in descriptions)
    assert any(v.category == "removal" and v.entity_name == "Gone" for v in violations)


def test_reports_typedef_removal_and_target_change():
    from nirnaya.core.models import TypedefModel

    bp_old = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        typedefs=[
            TypedefModel(name="Handle", target_type="int"),
            TypedefModel(name="Legacy", target_type="short"),
        ],
    )
    bp_new = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        typedefs=[TypedefModel(name="Handle", target_type="long")],
    )

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)

    assert any(
        v.category == "removal" and v.entity_name == "Legacy" for v in violations
    )
    assert any(
        v.category == "type_alias" and v.entity_name == "Handle" for v in violations
    )


def test_reports_function_return_const_and_removal_changes():
    old_methods = [
        FunctionModel(
            name="Widget::size",
            return_type="int",
            parameters=[],
            is_const=False,
        ),
        FunctionModel(
            name="Widget::mode",
            return_type="int",
            parameters=[],
            is_const=True,
        ),
    ]
    new_methods = [
        FunctionModel(
            name="Widget::size",
            return_type="long",
            parameters=[],
            is_const=False,
        ),
        FunctionModel(
            name="Widget::mode",
            return_type="int",
            parameters=[],
            is_const=False,
        ),
    ]
    old_free = [
        FunctionModel(
            name="parse",
            return_type="int",
            parameters=[ParameterModel(name="value", type_spelling="int")],
        ),
        FunctionModel(
            name="removed_fn",
            return_type="void",
            parameters=[],
        ),
    ]
    new_free = [
        FunctionModel(
            name="parse",
            return_type="int",
            parameters=[ParameterModel(name="value", type_spelling="int")],
        )
    ]

    bp_old = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        free_functions=old_free,
        structs=[
            StructModel(
                name="Widget",
                size_bytes=4,
                fields=[],
                methods=old_methods,
                is_class=True,
            )
        ],
    )
    bp_new = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        free_functions=new_free,
        structs=[
            StructModel(
                name="Widget",
                size_bytes=4,
                fields=[],
                methods=new_methods,
                is_class=True,
            )
        ],
    )

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)

    assert any(
        v.category == "removal" and v.entity_name == "removed_fn()" for v in violations
    )
    assert any("return type changed" in v.description for v in violations)
    assert any("const qualifier mismatch" in v.description for v in violations)


def test_reports_struct_removal_and_field_changes():
    old_struct = StructModel(
        name="Packet",
        size_bytes=8,
        fields=[
            FieldModel(name="id", type_spelling="int", offset_bits=0, is_public=True),
            FieldModel(
                name="flag", type_spelling="char", offset_bits=32, is_public=True
            ),
            FieldModel(
                name="kind", type_spelling="int", offset_bits=64, is_public=True
            ),
        ],
        is_class=False,
    )
    new_struct = StructModel(
        name="Packet",
        size_bytes=12,
        fields=[
            FieldModel(name="id", type_spelling="int", offset_bits=16, is_public=True),
            FieldModel(
                name="kind", type_spelling="long", offset_bits=64, is_public=True
            ),
            FieldModel(
                name="extra", type_spelling="int", offset_bits=96, is_public=True
            ),
        ],
        is_class=False,
    )

    bp_old = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[
            old_struct,
            StructModel(name="Gone", size_bytes=4, fields=[], is_class=False),
        ],
    )
    bp_new = BlueprintModel(
        header_path="a.h",
        captured_at=datetime.utcnow(),
        nirnaya_version="0.1.0",
        structs=[new_struct],
    )

    violations = BlueprintDiffEngine.diff_blueprints(bp_old, bp_new)

    assert any(v.category == "removal" and v.entity_name == "Gone" for v in violations)
    assert any("memory offset drifted" in v.description for v in violations)
    assert any("underlying data representation" in v.description for v in violations)
    assert any("was removed from structure layout" in v.description for v in violations)
    assert any(
        "newly injected into the structural footprint" in v.description
        for v in violations
    )
