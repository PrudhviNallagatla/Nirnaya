"""Edge-case unit tests for the HeaderParser."""

import os
from nirnaya.core.parser import HeaderParser


def test_template_declaration_parsed(parser: HeaderParser, fixtures_dir: str):
    header = os.path.join(fixtures_dir, "templates.h")
    bp = parser.parse_header(header)

    # Expect at least one struct/class named 'Holder'
    names = [s.name for s in bp.structs]
    assert any("Holder" in n for n in names)


def test_function_overloads_parsed(parser: HeaderParser, fixtures_dir: str):
    header = os.path.join(fixtures_dir, "overloads.h")
    bp = parser.parse_header(header)

    funcs = [f.name for f in bp.free_functions]
    # Expect three overloads for api::func
    assert funcs.count("api::func") == 3


def test_typedefs_and_aliases(parser: HeaderParser, fixtures_dir: str):
    header = os.path.join(fixtures_dir, "typedefs.h")
    bp = parser.parse_header(header)

    typedef_names = [t.name for t in bp.typedefs]
    assert any(name.endswith("id_t") for name in typedef_names)

    # Struct should reference the typedef in its field
    struct = bp.structs[0]
    field_types = [f.type_spelling for f in struct.fields]
    assert any("id_t" in t or "s32" in t for t in field_types)
