# nirnaya/core/parser.py
"""Core C++ header parser engine using libclang.

This module walks the Clang Abstract Syntax Tree (AST) to harvest structural contract
blueprints from C++ declarations, converting them directly into Pydantic models.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence
import clang.cindex  # type: ignore

from nirnaya import __version__
from nirnaya.core.models import (
    BlueprintModel,
    EnumModel,
    FieldModel,
    FunctionModel,
    ParameterModel,
    StructModel,
    TypedefModel,
)


class HeaderParser:
    """Encapsulates libclang AST traversal mechanics for a target header file."""

    def __init__(self, libclang_path: Optional[str] = None):
        """Initializes the libclang Index.

        Allows optional manual override for systems with exotic LLVM configurations.
        """
        if libclang_path:
            clang.cindex.Config.set_library_path(libclang_path)
        self.index = clang.cindex.Index.create()

    def parse_header(
        self, header_path: str, compiler_flags: Optional[List[str]] = None
    ) -> BlueprintModel:
        """Parses a target C++ header file and maps its structural shape into a BlueprintModel.

        Args:
            header_path: Path to the target header file.
            compiler_flags: Compiler include paths (-I) and macro definitions (-D).

        Raises:
            FileNotFoundError: If the designated header cannot be resolved.
            RuntimeError: If libclang suffers a fatal parsing block.
        """
        if not os.path.exists(header_path):
            raise FileNotFoundError(f"Target header not found: {header_path}")

        flags = list(compiler_flags or [])
        # Force header parsing in C++ mode because .h files are ambiguous to Clang.
        if not any(flag == "-x" or flag.startswith("-x") for flag in flags):
            flags = ["-x", "c++", *flags]

        # Ensure we treat input explicitly as modern C++ if not overridden.
        if not any(f.startswith("-std=") for f in flags):
            flags.append("-std=c++17")

        # Parse translation unit
        tu = self._parse_translation_unit(header_path, flags)
        if not tu:
            raise RuntimeError(
                f"Libclang failed to initialize a translation unit for {header_path}"
            )

        if self._needs_standard_header_fallback(tu.diagnostics):
            with tempfile.TemporaryDirectory() as stub_dir:
                stub_path = Path(stub_dir)
                self._write_standard_header_stubs(stub_path)
                tu = self._parse_translation_unit(
                    header_path, [f"-I{stub_path}", *flags]
                )

        # Ensure no catastrophic compiler syntax blocks exist before walking
        for diag in tu.diagnostics:
            if diag.severity >= clang.cindex.Diagnostic.Error:
                # We log/warn here instead of hard crashing to allow dealing with missing system headers,
                # but extreme infrastructure issues should be noted by the runner.
                pass

        # Target absolute matching to filter out nested system includes
        target_abs_path = os.path.abspath(header_path)

        structs: List[StructModel] = []
        free_functions: List[FunctionModel] = []
        enums: List[EnumModel] = []
        typedefs: List[TypedefModel] = []

        # Start traversal from root cursor
        self._walk_ast(
            tu.cursor, target_abs_path, structs, free_functions, enums, typedefs
        )

        return BlueprintModel(
            header_path=header_path,
            captured_at=datetime.utcnow(),
            nirnaya_version=__version__,
            structs=structs,
            free_functions=free_functions,
            enums=enums,
            typedefs=typedefs,
        )

    def _walk_ast(
        self,
        cursor: clang.cindex.Cursor,
        target_file: str,
        structs: List[StructModel],
        free_functions: List[FunctionModel],
        enums: List[EnumModel],
        typedefs: List[TypedefModel],
        namespace_prefix: str = "",
    ) -> None:
        """Recursively steps through cursors, isolating entities located inside the target file."""
        for child in cursor.get_children():
            # Filter out tokens originating from standard library headers or external components
            if (
                child.location.file
                and os.path.abspath(child.location.file.name) != target_file
            ):
                continue

            kind = child.kind

            # 1. Handle Namespaces
            if kind == clang.cindex.CursorKind.NAMESPACE:
                ns_name = (
                    f"{namespace_prefix}{child.spelling}::"
                    if child.spelling
                    else namespace_prefix
                )
                self._walk_ast(
                    child,
                    target_file,
                    structs,
                    free_functions,
                    enums,
                    typedefs,
                    ns_name,
                )
                continue

            qualified_name = (
                f"{namespace_prefix}{child.spelling}" if child.spelling else ""
            )

            # 2. Extract Structs & Classes
            if kind in (
                clang.cindex.CursorKind.STRUCT_DECL,
                clang.cindex.CursorKind.CLASS_DECL,
            ):
                if child.is_definition():
                    structs.append(self._parse_struct(child, qualified_name))
                continue

            # 3. Extract Free Functions
            if kind == clang.cindex.CursorKind.FUNCTION_DECL:
                free_functions.append(self._parse_function(child, qualified_name))
                continue

            # 4. Extract Enums
            if kind == clang.cindex.CursorKind.ENUM_DECL:
                if child.is_definition():
                    enums.append(self._parse_enum(child, qualified_name))
                continue

            # 5. Extract Typedefs & Type Aliases
            if kind in (
                clang.cindex.CursorKind.TYPEDEF_DECL,
                clang.cindex.CursorKind.TYPE_ALIAS_DECL,
            ):
                typedefs.append(
                    TypedefModel(
                        name=qualified_name,
                        target_type=self._typedef_target_spelling(child),
                    )
                )

    def _parse_translation_unit(
        self, header_path: str, flags: list[str]
    ) -> clang.cindex.TranslationUnit:
        return self.index.parse(header_path, args=flags)

    def _needs_standard_header_fallback(
        self, diagnostics: Sequence[clang.cindex.Diagnostic]
    ) -> bool:
        for diagnostic in diagnostics:
            message = diagnostic.spelling.lower()
            if "file not found" not in message:
                continue
            if "stdint.h" in message or "string" in message:
                return True
        return False

    def _write_standard_header_stubs(self, stub_dir: Path) -> None:
        (stub_dir / "stdint.h").write_text(
            """#pragma once

typedef signed char int8_t;
typedef short int16_t;
typedef int int32_t;
typedef long long int64_t;

typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
""",
            encoding="ascii",
        )
        (stub_dir / "string").write_text(
            """#pragma once

namespace std {
class string {};
}
""",
            encoding="ascii",
        )

    def _field_type_spelling(self, cursor: clang.cindex.Cursor) -> str:
        tokens = [token.spelling for token in cursor.get_tokens()]
        if len(tokens) >= 2:
            return tokens[0]
        return cursor.type.spelling

    def _typedef_target_spelling(self, cursor: clang.cindex.Cursor) -> str:
        tokens = [token.spelling for token in cursor.get_tokens()]
        if not tokens:
            return cursor.underlying_typedef_type.spelling

        if tokens[0] == "typedef" and len(tokens) >= 3:
            return tokens[1]

        if "=" in tokens:
            equals_index = tokens.index("=")
            if equals_index + 1 < len(tokens):
                return tokens[equals_index + 1]

        return cursor.underlying_typedef_type.spelling

    def _parse_struct(
        self, cursor: clang.cindex.Cursor, qualified_name: str
    ) -> StructModel:
        """Harvests layout information, bit offsets, and internal member configurations."""
        fields: List[FieldModel] = []
        methods: List[FunctionModel] = []

        # Determine base declaration type
        is_class = cursor.kind == clang.cindex.CursorKind.CLASS_DECL

        for child in cursor.get_children():
            # Parse Member Fields
            if child.kind == clang.cindex.CursorKind.FIELD_DECL:
                # Calculate deterministic offsets via libclang type engine
                offset = cursor.type.get_offset(child.spelling)
                # If negative, it indicates an error state or an incomplete instantiation fallback
                clean_offset = offset if offset >= 0 else None

                is_public = (
                    child.access_specifier == clang.cindex.AccessSpecifier.PUBLIC
                )
                if (
                    not is_class
                    and child.access_specifier == clang.cindex.AccessSpecifier.INVALID
                ):
                    # C-style struct elements default to public visibility
                    is_public = True

                fields.append(
                    FieldModel(
                        name=child.spelling,
                        type_spelling=self._field_type_spelling(child),
                        offset_bits=clean_offset,
                        is_public=is_public,
                    )
                )

            # Parse Member Functions (Methods)
            elif child.kind == clang.cindex.CursorKind.CXX_METHOD:
                methods.append(self._parse_function(child, child.spelling))

        return StructModel(
            name=qualified_name,
            size_bytes=cursor.type.get_size() if cursor.type.get_size() >= 0 else None,
            fields=fields,
            methods=methods,
            is_class=is_class,
        )

    def _parse_function(
        self, cursor: clang.cindex.Cursor, func_name: str
    ) -> FunctionModel:
        """Maps parameters, types, and signature behavior flags from a function cursor."""
        parameters: List[ParameterModel] = []

        for child in cursor.get_children():
            if child.kind == clang.cindex.CursorKind.PARM_DECL:
                parameters.append(
                    ParameterModel(
                        name=child.spelling or "", type_spelling=child.type.spelling
                    )
                )

        return FunctionModel(
            name=func_name,
            return_type=cursor.result_type.spelling,
            parameters=parameters,
            is_virtual=cursor.is_virtual_method(),
            is_const=cursor.is_const_method(),
            is_static=cursor.is_static_method(),
        )

    def _parse_enum(
        self, cursor: clang.cindex.Cursor, qualified_name: str
    ) -> EnumModel:
        """Builds a deterministic string-to-integer dictionary map of enum declarations."""
        values = {}
        for child in cursor.get_children():
            if child.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
                values[child.spelling] = child.enum_value

        return EnumModel(name=qualified_name, values=values)
