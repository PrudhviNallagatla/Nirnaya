# nirnaya/storage/vault.py
"""Nirnaya storage vault manager.

Governs structural initialization, active contract snapshot tracking, and
configuration properties persisted inside the .nirnaya/ subsystem.
"""

import re
import tomllib
from datetime import datetime
from pathlib import Path
from typing import List, Union

from nirnaya.core.blueprint import BlueprintEngine
from nirnaya.core.models import BlueprintModel


class StorageVault:
    """Manages file-system serialization boundaries inside the local .nirnaya folder."""

    def __init__(self, project_root: Union[str, Path]):
        self.root = Path(project_root).resolve()
        self.vault_dir = self.root / ".nirnaya"
        self.blueprint_dir = self.vault_dir / "blueprints"
        self.history_dir = self.vault_dir / "history"
        self.config_path = self.vault_dir / "config.toml"

    @classmethod
    def initialize(
        cls, project_root: Union[str, Path], project_name: str
    ) -> "StorageVault":
        """Generates a fresh, populated contract storage vault structure on disk."""
        vault = cls(project_root)
        vault.blueprint_dir.mkdir(parents=True, exist_ok=True)
        vault.history_dir.mkdir(parents=True, exist_ok=True)

        if not vault.config_path.exists():
            default_config = {
                "project": {"name": project_name, "version": "1"},
                "tracking": {"headers": [], "compile_commands": ""},
            }
            vault.config_path.write_text(
                vault._dump_config(default_config), encoding="utf-8"
            )

        return vault

    def _slugify_path(self, header_path: Union[str, Path]) -> str:
        """Generates a clean, flat string file handle replacing separators with markers."""
        path_str = self._normalize_header_path(header_path)
        slug = path_str.replace("/", "__").replace("\\", "__")
        return f"{slug}.json"

    def _normalize_header_path(self, header_path: Union[str, Path]) -> str:
        """Returns a stable project-relative POSIX path for a header reference."""
        path = Path(header_path)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(self.root)
            except ValueError:
                path = path.resolve()
        else:
            path = Path(str(path))

        path_str = path.as_posix().strip()
        return re.sub(r"^[./\\]+", "", path_str)

    def save_blueprint(self, blueprint: BlueprintModel) -> None:
        """Saves a blueprint, archiving old historical snapshots automatically."""
        slug = self._slugify_path(blueprint.header_path)
        active_target = self.blueprint_dir / slug

        # Archive old active blueprint state to historical audit stack if it exists
        if active_target.exists():
            try:
                old_blueprint = BlueprintEngine.load_from_file(active_target)
                timestamp = old_blueprint.captured_at.strftime("%Y%m%d__%H%M%S")
            except Exception:
                timestamp = datetime.utcnow().strftime("%Y%m%d__%H%M%S")

            archive_folder = self.history_dir / slug.replace(".json", "")
            archive_folder.mkdir(parents=True, exist_ok=True)
            active_target.rename(archive_folder / f"{timestamp}.json")

        # Persist new golden contract blueprint
        BlueprintEngine.save_to_file(blueprint, active_target)

    def load_blueprint(self, header_path: Union[str, Path]) -> BlueprintModel:
        """Retrieves the active baseline contract blueprint data model."""
        slug = self._slugify_path(header_path)
        target = self.blueprint_dir / slug
        return BlueprintEngine.load_from_file(target)

    def get_tracked_headers(self) -> List[str]:
        """Harvests list configurations currently registered inside config.toml."""
        if not self.config_path.exists():
            return []
        try:
            config = tomllib.loads(self.config_path.read_text(encoding="utf-8"))
            return config.get("tracking", {}).get("headers", [])
        except Exception:
            return []

    def track_headers(self, paths: List[str]) -> None:
        """Appends unique header target paths cleanly into tracking config settings."""
        if not self.config_path.exists():
            return

        config = tomllib.loads(self.config_path.read_text(encoding="utf-8"))
        current_headers = set(config.get("tracking", {}).get("headers", []))

        for p in paths:
            current_headers.add(self._normalize_header_path(p))

        config["tracking"]["headers"] = sorted(list(current_headers))
        self.config_path.write_text(self._dump_config(config), encoding="utf-8")

    def _dump_config(self, config: dict[str, object]) -> str:
        """Serializes the small vault config structure into deterministic TOML."""
        project = config.get("project", {})
        tracking = config.get("tracking", {})

        project_name = ""
        project_version = ""
        headers: list[str] = []
        compile_commands = ""

        if isinstance(project, dict):
            project_name = str(project.get("name", ""))
            project_version = str(project.get("version", ""))

        if isinstance(tracking, dict):
            raw_headers = tracking.get("headers", [])
            if isinstance(raw_headers, list):
                headers = [str(item) for item in raw_headers]
            compile_commands = str(tracking.get("compile_commands", ""))

        header_lines = ", ".join(f'"{header}"' for header in headers)
        return (
            "[project]\n"
            f'name = "{project_name}"\n'
            f'version = "{project_version}"\n\n'
            "[tracking]\n"
            f"headers = [{header_lines}]\n"
            f'compile_commands = "{compile_commands}"\n'
        )
