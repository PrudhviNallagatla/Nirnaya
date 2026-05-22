# nirnaya/core/diff.py
"""Nirnaya interface contract diffing engine.

Compares baseline golden blueprints against incoming local modifications to
pinpoint ABI-breaking alterations, signature drifts, and type remappings.
"""

from typing import Literal, List

from nirnaya.core.models import (
    BlueprintModel,
    EnumModel,
    FieldModel,
    FunctionModel,
    StructModel,
    TypedefModel,
    Violation,
)


class BlueprintDiffEngine:
    """Pure structural verification engine to analyze API stability contracts."""

    @staticmethod
    def _violation(
        *,
        severity: Literal["breaking", "warning", "info"],
        category: Literal[
            "struct_layout", "function_signature", "enum_value", "type_alias", "removal"
        ],
        entity_name: str,
        description: str,
        old_value: str | None = None,
        new_value: str | None = None,
        line_number: int | None = None,
        suggested_fix: str | None = None,
    ) -> Violation:
        return Violation(
            severity=severity,
            category=category,
            entity_name=entity_name,
            description=description,
            old_value=old_value,
            new_value=new_value,
            line_number=line_number,
            suggested_fix=suggested_fix,
        )

    @classmethod
    def diff_blueprints(
        cls, old: BlueprintModel, new: BlueprintModel
    ) -> List[Violation]:
        """Compares two blueprint snapshots and returns a comprehensive list of violations."""
        violations: List[Violation] = []

        # 1. Diff Enums
        cls._diff_enums(old.enums, new.enums, violations)

        # 2. Diff Typedefs and Type Aliases
        cls._diff_typedefs(old.typedefs, new.typedefs, violations)

        # 3. Diff Free Functions
        cls._diff_functions(
            old.free_functions, new.free_functions, "function_signature", violations
        )

        # 4. Diff Structs and Classes
        cls._diff_structs(old.structs, new.structs, violations)

        return violations

    @classmethod
    def _diff_enums(
        cls,
        old_list: List[EnumModel],
        new_list: List[EnumModel],
        violations: List[Violation],
    ) -> None:
        old_map = {e.name: e for e in old_list}
        new_map = {e.name: e for e in new_list}

        for name, old_enum in old_map.items():
            if name not in new_map:
                violations.append(
                    Violation(
                        severity="breaking",
                        category="removal",
                        entity_name=name,
                        description=f"Enum '{name}' has been completely removed from the public interface contract.",
                        old_value=None,
                        new_value=None,
                        line_number=None,
                        suggested_fix=None,
                    )
                )
                continue

            new_enum = new_map[name]
            # Check for value drift or value removals
            for key, old_val in old_enum.values.items():
                if key not in new_enum.values:
                    violations.append(
                        cls._violation(
                            severity="breaking",
                            category="enum_value",
                            entity_name=f"{name}::{key}",
                            description=f"Enum constant '{key}' was removed from enum '{name}'.",
                        )
                    )
                elif new_enum.values[key] != old_val:
                    violations.append(
                        cls._violation(
                            severity="breaking",
                            category="enum_value",
                            entity_name=f"{name}::{key}",
                            description=f"Enum constant '{key}' value changed from {old_val} to {new_enum.values[key]}.",
                            old_value=str(old_val),
                            new_value=str(new_enum.values[key]),
                            suggested_fix="Revert the underlying integer assignment to maintain backward evaluation compatibility.",
                        )
                    )

    @classmethod
    def _diff_typedefs(
        cls,
        old_list: List[TypedefModel],
        new_list: List[TypedefModel],
        violations: List[Violation],
    ) -> None:
        old_map = {t.name: t for t in old_list}
        new_map = {t.name: t for t in new_list}

        for name, old_td in old_map.items():
            if name not in new_map:
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category="removal",
                        entity_name=name,
                        description=f"Type alias '{name}' has been removed.",
                    )
                )
                continue

            new_td = new_map[name]
            if old_td.target_type != new_td.target_type:
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category="type_alias",
                        entity_name=name,
                        description=f"Type alias '{name}' target changed from '{old_td.target_type}' to '{new_td.target_type}'.",
                        old_value=old_td.target_type,
                        new_value=new_td.target_type,
                    )
                )

    @classmethod
    def _diff_functions(
        cls,
        old_list: List[FunctionModel],
        new_list: List[FunctionModel],
        category: Literal["function_signature", "struct_layout"],
        violations: List[Violation],
    ) -> None:
        old_map = {f.name: f for f in old_list}
        new_map = {f.name: f for f in new_list}

        for name, old_func in old_map.items():
            if name not in new_map:
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category="removal",
                        entity_name=name,
                        description=f"Function signature symbol '{name}' has been removed or renamed.",
                    )
                )
                continue

            new_func = new_map[name]

            # Check Return Types
            if old_func.return_type != new_func.return_type:
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category=category,
                        entity_name=name,
                        description=f"Function '{name}' return type changed from '{old_func.return_type}' to '{new_func.return_type}'.",
                        old_value=old_func.return_type,
                        new_value=new_func.return_type,
                    )
                )

            # Check Qualifiers
            if old_func.is_const != new_func.is_const:
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category=category,
                        entity_name=name,
                        description=f"Function '{name}' const qualifier mismatch.",
                        old_value=f"const={old_func.is_const}",
                        new_value=f"const={new_func.is_const}",
                    )
                )

            # Check Parameters Layout
            if len(old_func.parameters) != len(new_func.parameters):
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category=category,
                        entity_name=name,
                        description=f"Function '{name}' parameter count drifted from {len(old_func.parameters)} to {len(new_func.parameters)}.",
                    )
                )
            else:
                for idx, (old_p, new_p) in enumerate(
                    zip(old_func.parameters, new_func.parameters)
                ):
                    if old_p.type_spelling != new_p.type_spelling:
                        violations.append(
                            cls._violation(
                                severity="breaking",
                                category=category,
                                entity_name=name,
                                description=f"Function '{name}' parameter {idx} type changed from '{old_p.type_spelling}' to '{new_p.type_spelling}'.",
                                old_value=old_p.type_spelling,
                                new_value=new_p.type_spelling,
                            )
                        )

    @classmethod
    def _diff_structs(
        cls,
        old_list: List[StructModel],
        new_list: List[StructModel],
        violations: List[Violation],
    ) -> None:
        old_map = {s.name: s for s in old_list}
        new_map = {s.name: s for s in new_list}

        for name, old_struct in old_map.items():
            if name not in new_map:
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category="removal",
                        entity_name=name,
                        description=f"Struct/Class '{name}' layout configuration has been completely removed.",
                    )
                )
                continue

            new_struct = new_map[name]

            # 1. Structural Byte Footprint Change
            if old_struct.size_bytes != new_struct.size_bytes:
                violations.append(
                    cls._violation(
                        severity="breaking",
                        category="struct_layout",
                        entity_name=name,
                        description=f"Type memory footprint size shifted from {old_struct.size_bytes} to {new_struct.size_bytes} bytes. This breaks binary packaging structures.",
                        old_value=f"{old_struct.size_bytes} bytes",
                        new_value=f"{new_struct.size_bytes} bytes",
                    )
                )

            # 2. Field Alignment and Type Tracking
            old_fields = {f.name: f for f in old_struct.fields}
            new_fields = {f.name: f for f in new_struct.fields}

            for f_name, old_f in old_fields.items():
                if f_name not in new_fields:
                    violations.append(
                        cls._violation(
                            severity="breaking",
                            category="struct_layout",
                            entity_name=f"{name}::{f_name}",
                            description=f"Field member '{f_name}' was removed from structure layout '{name}'.",
                        )
                    )
                    continue

                new_f = new_fields[f_name]
                if old_f.offset_bits != new_f.offset_bits:
                    violations.append(
                        cls._violation(
                            severity="breaking",
                            category="struct_layout",
                            entity_name=f"{name}::{f_name}",
                            description=f"Field member '{f_name}' memory offset drifted from bit {old_f.offset_bits} to bit {new_f.offset_bits}. Spills alignment corruption to downstream consumers.",
                            old_value=f"bit {old_f.offset_bits}",
                            new_value=f"bit {new_f.offset_bits}",
                        )
                    )
                elif old_f.type_spelling != new_f.type_spelling:
                    violations.append(
                        cls._violation(
                            severity="breaking",
                            category="struct_layout",
                            entity_name=f"{name}::{f_name}",
                            description=f"Field member '{f_name}' underlying data representation cast modified from '{old_f.type_spelling}' to '{new_f.type_spelling}'.",
                            old_value=old_f.type_spelling,
                            new_value=new_f.type_spelling,
                        )
                    )

            # 3. Check for unexpected additions inside existing structs that alter fields layout
            for f_name in new_fields:
                if f_name not in old_fields:
                    violations.append(
                        cls._violation(
                            severity="breaking",
                            category="struct_layout",
                            entity_name=f"{name}::{f_name}",
                            description=f"Field member '{f_name}' was newly injected into the structural footprint of '{name}'. This alters alignment packaging boundaries.",
                        )
                    )

            # 4. Verify Internal Method Structures
            cls._diff_functions(
                old_struct.methods, new_struct.methods, "struct_layout", violations
            )
