"""File-based secret provider — reads from gitignored YAML files."""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import Any

import yaml

from cli.secrets.provider import SecretProvider, parse_secret_ref

logger = logging.getLogger(__name__)


class FileSecretProvider(SecretProvider):
    """Reads secrets from local YAML files in a gitignored directory.

    Each file contains flat key-value pairs where keys match the path
    portion of a ``secret://`` reference.  For example, the reference
    ``secret://mas-world/ibm/entitlement-key`` resolves to the YAML
    key ``ibm/entitlement-key`` in any loaded file.
    """

    def __init__(self, secrets_dir: str = "secrets") -> None:
        self._secrets_dir = Path(secrets_dir)
        self._store: dict[str, str] = {}
        self._source_map: dict[str, Path] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self._secrets_dir.is_dir():
            logger.warning("Secrets directory does not exist: %s", self._secrets_dir)
            return

        for path in sorted(self._secrets_dir.iterdir()):
            if path.suffix in (".yaml", ".yml") and not path.name.endswith(".example"):
                self._check_permissions(path)
                self._load_file(path)

    def _check_permissions(self, path: Path) -> None:
        try:
            mode = path.stat().st_mode
            if mode & (stat.S_IRGRP | stat.S_IROTH):
                logger.warning(
                    "Secret file %s is readable by group/others (mode %o). Run: chmod 600 %s",
                    path,
                    stat.S_IMODE(mode),
                    path,
                )
        except OSError:
            pass

    def _resolve_value(self, value: str) -> str:
        """Resolve a value that may be a file:// reference."""
        if not value.startswith("file://"):
            return value
        file_path = Path(value[7:])
        if not file_path.is_absolute():
            file_path = self._secrets_dir / file_path
        try:
            lines = [
                ln
                for ln in file_path.read_text().splitlines()
                if ln.strip() and not ln.lstrip().startswith("#")
            ]
            return "\n".join(lines).strip()
        except OSError as exc:
            logger.warning("Cannot read referenced file %s: %s", file_path, exc)
            return value

    def _load_file(self, path: Path) -> None:
        try:
            with open(path) as fh:
                data = yaml.safe_load(fh)
        except (OSError, yaml.YAMLError) as exc:
            logger.warning("Failed to load secret file %s: %s", path, exc)
            return

        if not isinstance(data, dict):
            return

        for key, value in data.items():
            if isinstance(value, str):
                self._store[str(key)] = self._resolve_value(value)
                self._source_map[str(key)] = path

    def _write_file(self, path: Path, entries: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            yaml.safe_dump(entries, fh, default_flow_style=False, sort_keys=True)
        os.chmod(path, 0o600)

    def _rebuild_file(self, path: Path) -> None:
        entries = {k: v for k, v in self._store.items() if self._source_map.get(k) == path}
        if entries:
            self._write_file(path, entries)
        elif path.exists():
            path.unlink()

    def _ref_to_key(self, ref: str) -> str:
        _, path = parse_secret_ref(ref)
        return path

    def get_secret(self, ref: str) -> str:
        key = self._ref_to_key(ref)
        value = self._store.get(key)
        if value is None:
            raise KeyError(f"Secret not found in file provider: {ref} (key: {key})")
        return value

    def set_secret(self, ref: str, value: str) -> None:
        key = self._ref_to_key(ref)
        default_file = self._secrets_dir / "masworld-secrets.yml"
        target = self._source_map.get(key, default_file)
        self._store[key] = value
        self._source_map[key] = target
        self._rebuild_file(target)

    def delete_secret(self, ref: str) -> None:
        key = self._ref_to_key(ref)
        source = self._source_map.pop(key, None)
        self._store.pop(key, None)
        if source:
            self._rebuild_file(source)

    def exists(self, ref: str) -> bool:
        key = self._ref_to_key(ref)
        return key in self._store
