# nirnaya/core/blueprint.py
"""Blueprint serialization and deserialization engine.

Handles writing and reading the golden JSON contract files deterministically
to ensure zero layout noise when committed to version control.
"""

from pathlib import Path
from typing import Union
from nirnaya.core.models import BlueprintModel
import json


class BlueprintEngine:
    """Manages file I/O and deterministic serialization for interface blueprints."""

    @staticmethod
    def serialize(blueprint: BlueprintModel) -> str:
        """Converts a BlueprintModel into a normalized, pretty-printed JSON string.

        Enforces sorted keys and deterministic order for reproducible git tracking.
        """
        # model_dump with round_trip=True safely handles datetime/special types,
        # then json.dumps with sort_keys=True enforces true key-level determinism.
        raw = blueprint.model_dump(mode="json", round_trip=True)
        return json.dumps(raw, indent=2, sort_keys=True)

    @classmethod
    def save_to_file(cls, blueprint: BlueprintModel, output_path: Union[str, Path]) -> None:
        """Serializes and saves a blueprint snapshot directly to a file destination.

        Creates parent directories automatically if they do not exist.
        Writes atomically via a temp file to prevent blueprint corruption on crash.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        json_data = cls.serialize(blueprint)

        # Write to a sibling temp file first, then atomically replace the target.
        # This prevents a partially written blueprint file if the process is interrupted.
        tmp_path = path.with_suffix(".tmp")
        try:
            tmp_path.write_text(json_data, encoding="utf-8")
            tmp_path.replace(path)  # atomic on POSIX; best-effort on Windows
        except Exception:
            tmp_path.unlink(missing_ok=True)  # clean up temp on failure
            raise

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