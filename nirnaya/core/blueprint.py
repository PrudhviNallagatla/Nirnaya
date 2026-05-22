# nirnaya/core/blueprint.py
"""Blueprint serialization and deserialization engine.

Handles writing and reading the golden JSON contract files deterministically
to ensure zero layout noise when committed to version control.
"""

from pathlib import Path
from typing import Union
from nirnaya.core.models import BlueprintModel


class BlueprintEngine:
    """Manages file I/O and deterministic serialization for interface blueprints."""

    @staticmethod
    def serialize(blueprint: BlueprintModel) -> str:
        """Converts a BlueprintModel into a normalized, pretty-printed JSON string.

        Enforces sorted keys and deterministic order for reproducible git tracking.
        """
        return blueprint.model_dump_json(indent=2, round_trip=True)

    @classmethod
    def save_to_file(cls, blueprint: BlueprintModel, output_path: Union[str, Path]) -> None:
        """Serializes and saves a blueprint snapshot directly to a file destination.

        Creates parent directories automatically if they do not exist.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        json_data = cls.serialize(blueprint)
        path.write_text(json_data, encoding="utf-8")

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> BlueprintModel:
        """Reads a blueprint JSON file and reconstructs its verified BlueprintModel instance.

        Raises:
            FileNotFoundError: If the contract file doesn't exist.
            ValidationError: If the JSON structural validation fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Nirnaya contract blueprint file not found at: {path}")
            
        json_content = path.read_text(encoding="utf-8")
        return BlueprintModel.model_validate_json(json_content)