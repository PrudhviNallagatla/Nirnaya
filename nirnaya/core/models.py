# nirnaya/core/models.py
"""Core data models for Nirnaya.

This module defines the schema for the C++ contract blueprints and contract
violations. All models use Pydantic v2 and ensure deterministic serialization
order to keep Git diffs completely noise-free.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class ParameterModel(BaseModel):
    """Represents a single function parameter."""
    name: str = Field(..., description="Name of the parameter variable")
    type_spelling: str = Field(..., description="The exact literal type spelling from C++ source")


class FieldModel(BaseModel):
    """Represents a field inside a struct or class layout."""
    name: str = Field(..., description="Name of the member field")
    type_spelling: str = Field(..., description="The exact literal type spelling from C++ source")
    offset_bits: int | None = Field(
        None, 
        description="The precise memory offset in bits. Calculated via libclang to account for padding/packing."
    )
    is_public: bool = Field(..., description="True if public; False if private or protected")


class FunctionModel(BaseModel):
    """Represents either a class method or a global free function."""
    name: str = Field(..., description="Fully qualified or relative name of the function")
    return_type: str = Field(..., description="The return type signature")
    parameters: list[ParameterModel] = Field(default_factory=list, description="Ordered parameter list")
    is_virtual: bool = Field(default=False, description="True if marked virtual")
    is_const: bool = Field(default=False, description="True if marked const (for member functions)")
    is_static: bool = Field(default=False, description="True if marked static")


class StructModel(BaseModel):
    """Represents a structured data layout (struct or class)."""
    name: str = Field(..., description="Fully qualified name of the struct/class")
    size_bytes: int | None = Field(None, description="Total size of the type in bytes")
    fields: list[FieldModel] = Field(default_factory=list, description="Tracked fields")
    methods: list[FunctionModel] = Field(default_factory=list, description="Tracked member functions")
    is_class: bool = Field(..., description="True if declared as 'class'; False if declared as 'struct'")

    @field_validator("fields")
    @classmethod
    def sort_fields_by_offset(cls, v: list[FieldModel]) -> list[FieldModel]:
        """Ensures that fields are permanently ordered by memory layout offset.

        If offset data is unavailable, it gracefully preserves text sequence.
        """
        if all(f.offset_bits is not None for f in v):
            return sorted(v, key=lambda x: x.offset_bits or 0)
        return v

    @field_validator("methods")
    @classmethod
    def sort_methods_by_signature(cls, v: list[FunctionModel]) -> list[FunctionModel]:
        """Normalizes method ordering by name and signature string to guarantee determinism."""
        return sorted(v, key=lambda x: (x.name, str(x.parameters)))


class EnumModel(BaseModel):
    """Represents an enumerated type."""
    name: str = Field(..., description="Fully qualified name of the enum")
    values: dict[str, int] = Field(..., description="Mapping of literal names to their underlying integer values")

    @field_validator("values")
    @classmethod
    def alphabetize_enum_keys(cls, v: dict[str, int]) -> dict[str, int]:
        """Enforces deterministic alphabetization on dictionary keys for reproducible JSON outputs."""
        return dict(sorted(v.items()))


class TypedefModel(BaseModel):
    """Represents a type alias or typedef declaration."""
    name: str = Field(..., description="The declared alias or typedef name")
    target_type: str = Field(..., description="The original underlying type spelling being mapped to")


class BlueprintModel(BaseModel):
    """The Golden Blueprint — the full contract snapshot of an individual header file."""
    header_path: str = Field(..., description="Relative file path to the C++ header being tracked")
    captured_at: datetime = Field(..., description="Timestamp of when this blueprint snapshot was generated")
    nirnaya_version: str = Field(..., description="Version of the Nirnaya tool used to run the extraction")
    structs: list[StructModel] = Field(default_factory=list)
    free_functions: list[FunctionModel] = Field(default_factory=list)
    enums: list[EnumModel] = Field(default_factory=list)
    typedefs: list[TypedefModel] = Field(default_factory=list)

    @field_validator("structs", "free_functions", "enums", "typedefs", mode="after")
    @classmethod
    def enforce_global_determinism(cls, v: list) -> list:
        """Sorts all top-level lists uniformly by their name attribute.

        This ensures that shuffling the file order or include stack does not inject false 
        diff anomalies when running structural Git checks.
        """
        if not v:
            return v
        return sorted(v, key=lambda x: x.name)


class Violation(BaseModel):
    """A single contract violation pinpointed by the diff engine."""
    severity: Literal["breaking", "warning", "info"] = Field(
        ..., 
        description="The threat level of the change: 'breaking' breaks layout/ABI, 'warning' modifies footprints, 'info' adds safe expansions."
    )
    category: Literal["struct_layout", "function_signature", "enum_value", "type_alias", "removal"] = Field(
        ..., 
        description="The architectural subsystem experiencing structural drift"
    )
    entity_name: str = Field(..., description="Fully qualified name of the affected entity")
    description: str = Field(..., description="A human-readable breakdown explaining exactly what drifted")
    old_value: str | None = Field(None, description="The structural state captured in the source baseline")
    new_value: str | None = Field(None, description="The incoming configuration discovered in local adjustments")
    line_number: int | None = Field(None, description="Line number of the violation location if trackable")
    suggested_fix: str | None = Field(None, description="Actionable C++ refactoring tip to avoid consumer ABI crashes")