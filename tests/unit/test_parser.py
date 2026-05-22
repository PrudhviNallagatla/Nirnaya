# tests/unit/test_parser.py
"""Unit tests for the libclang header parser engine."""

import os
import pytest
from nirnaya.core.parser import HeaderParser


@pytest.fixture
def parser() -> HeaderParser:
    """Provides a fresh instance of the HeaderParser."""
    return HeaderParser()


@pytest.fixture
def fixtures_dir() -> str:
    """Resolves the absolute path to the test fixtures directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures"))


def test_parse_simple_struct(parser: HeaderParser, fixtures_dir: str):
    """Verifies layout, type tracking, and accurate bitwise offset calculation."""
    header_path = os.path.join(fixtures_dir, "simple_struct.h")
    blueprint = parser.parse_header(header_path)

    assert blueprint.header_path == header_path
    assert len(blueprint.structs) == 1

    # Verify Struct Details
    struct_data = blueprint.structs[0]
    assert struct_data.name == "core::SimpleStruct"
    assert struct_data.is_class is False
    assert struct_data.size_bytes is not None
    assert struct_data.size_bytes >= 16  # Minimum size due to padding rules

    # Verify Field Details & Alignment Offsets
    fields = {f.name: f for f in struct_data.fields}
    assert "id" in fields
    assert "value" in fields
    assert "factor" in fields
    assert "is_active" in fields

    assert fields["id"].type_spelling == "uint8_t"
    assert fields["id"].offset_bits == 0
    assert fields["id"].is_public is True

    # Check that alignment padding skipped bits appropriately
    assert fields["value"].type_spelling == "int32_t"
    assert fields["value"].offset_bits == 32  # Aligned to 4 bytes, not 8 bits

    assert fields["factor"].type_spelling == "double"
    assert fields["factor"].offset_bits == 64

    # Verify Typedefs/Aliases
    typedefs = {t.name: t for t in blueprint.typedefs}
    assert "core::SystemHandle" in typedefs
    assert typedefs["core::SystemHandle"].target_type == "int32_t"


def test_parse_cpp_class(parser: HeaderParser, fixtures_dir: str):
    """Verifies class member visibilities, method qualifiers, and free functions."""
    header_path = os.path.join(fixtures_dir, "cpp_class.h")
    blueprint = parser.parse_header(header_path)

    # Verify Class Structure
    assert len(blueprint.structs) == 1
    class_data = blueprint.structs[0]
    assert class_data.name == "network::ConnectionManager"
    assert class_data.is_class is True

    # Verify Private vs Public Boundary
    fields = {f.name: f for f in class_data.fields}
    assert fields["m_socket_fd"].is_public is False
    assert fields["m_socket_fd"].type_spelling == "int32_t"

    # Verify Methods and Qualifiers
    methods = {m.name: m for m in class_data.methods}
    assert "connect" in methods
    assert methods["connect"].is_virtual is True
    assert len(methods["connect"].parameters) == 2
    assert methods["connect"].parameters[0].type_spelling == "const std::string &"

    assert "is_connected" in methods
    assert methods["is_connected"].is_const is True

    assert "get_active_connection_count" in methods
    assert methods["get_active_connection_count"].is_static is True

    # Verify Isolated Namespace Free Functions
    assert len(blueprint.free_functions) == 1
    func = blueprint.free_functions[0]
    assert func.name == "network::broadcast_payload"
    assert func.return_type == "void"


def test_parse_enums(parser: HeaderParser, fixtures_dir: str):
    """Verifies traditional unscoped and modern strongly-typed enum extraction."""
    header_path = os.path.join(fixtures_dir, "enums.h")
    blueprint = parser.parse_header(header_path)

    assert len(blueprint.enums) == 2
    enums = {e.name: e for e in blueprint.enums}

    # Test traditional enum scoping and tracking
    assert "data::StatusSeverity" in enums
    severity_vals = enums["data::StatusSeverity"].values
    assert severity_vals["SEVERITY_INFO"] == 0
    assert severity_vals["SEVERITY_ERROR"] == 10

    # Test modern enum class parsing
    assert "data::StorageFormat" in enums
    format_vals = enums["data::StorageFormat"].values
    assert format_vals["RAW_BINARY"] == 66  # ASCII for 'B'
    assert format_vals["COMPRESSED_ZSTD"] == 90  # ASCII for 'Z'


def test_missing_header_throws_exception(parser: HeaderParser):
    """Ensures a clean error path when targeting a non-existent file path."""
    with pytest.raises(FileNotFoundError):
        parser.parse_header("non_existent_file.h")