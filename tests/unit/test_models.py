"""Unit tests for Nirnaya core Pydantic models."""

from datetime import datetime

from nirnaya.core.models import (
    BlueprintModel,
    EnumModel,
    FieldModel,
    FunctionModel,
    ParameterModel,
    StructModel,
    TypedefModel,
)


def test_struct_fields_sort_by_offset():
    """Fields with offsets should be normalized into layout order."""
    struct_model = StructModel(
        name="Packet",
        size_bytes=16,
        fields=[
            FieldModel(
                name="tail", type_spelling="int", offset_bits=64, is_public=True
            ),
            FieldModel(name="head", type_spelling="int", offset_bits=0, is_public=True),
        ],
        methods=[],
        is_class=False,
    )

    assert [field.name for field in struct_model.fields] == ["head", "tail"]


def test_struct_methods_sort_by_signature():
    """Methods should be normalized into deterministic signature order."""
    struct_model = StructModel(
        name="Widget",
        size_bytes=None,
        fields=[],
        methods=[
            FunctionModel(
                name="zeta",
                return_type="void",
                parameters=[ParameterModel(name="value", type_spelling="int")],
            ),
            FunctionModel(
                name="alpha",
                return_type="void",
                parameters=[],
            ),
        ],
        is_class=True,
    )

    assert [method.name for method in struct_model.methods] == ["alpha", "zeta"]


def test_enum_values_are_sorted_by_key():
    """Enum value dictionaries should be serialized in key order."""
    enum_model = EnumModel(name="State", values={"z": 3, "a": 1, "m": 2})

    assert list(enum_model.values.keys()) == ["a", "m", "z"]


def test_blueprint_top_level_entities_sort_by_name():
    """Top-level blueprint collections should be deterministic by name."""
    blueprint = BlueprintModel(
        header_path="include/api.h",
        captured_at=datetime(2026, 5, 22, 12, 0, 0),
        nirnaya_version="0.1.0",
        structs=[
            StructModel(
                name="Zulu", size_bytes=None, fields=[], methods=[], is_class=False
            ),
            StructModel(
                name="Alpha", size_bytes=None, fields=[], methods=[], is_class=False
            ),
        ],
        free_functions=[
            FunctionModel(name="gamma", return_type="void", parameters=[]),
            FunctionModel(name="beta", return_type="void", parameters=[]),
        ],
        enums=[
            EnumModel(name="Mode", values={"A": 1}),
            EnumModel(name="State", values={"A": 1}),
        ],
        typedefs=[
            TypedefModel(name="ZType", target_type="int"),
            TypedefModel(name="AType", target_type="int"),
        ],
    )

    assert [struct.name for struct in blueprint.structs] == ["Alpha", "Zulu"]
    assert [func.name for func in blueprint.free_functions] == ["beta", "gamma"]
    assert [enum.name for enum in blueprint.enums] == ["Mode", "State"]
    assert [typedef.name for typedef in blueprint.typedefs] == ["AType", "ZType"]
