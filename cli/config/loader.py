"""Configuration loading with layered precedence."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from cli.config.schema import MASWorldConfig


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base. Override values win for scalars and lists."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _redact_value(key: str, value: Any) -> Any:
    """Redact values that look like secrets."""
    secret_keys = {
        "password",
        "secret",
        "token",
        "key",
        "kubeconfig",
        "entitlement",
        "license",
        "credentials",
    }
    if isinstance(value, str):
        key_lower = key.lower()
        if any(sk in key_lower for sk in secret_keys):
            if value.startswith("secret://"):
                return value
            if value in ("PLACEHOLDER", "UNSET", ""):
                return value
            return "**REDACTED**"
    return value


def _redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _redact_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _redact_dict(item) if isinstance(item, dict) else _redact_value(key, item)
                for item in value
            ]
        else:
            result[key] = _redact_value(key, value)
    return result


def _diff_dicts(d1: dict[str, Any], d2: dict[str, Any], path: str = "") -> list[dict[str, str]]:
    diffs: list[dict[str, str]] = []
    all_keys = set(d1.keys()) | set(d2.keys())
    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key
        v1 = d1.get(key)
        v2 = d2.get(key)
        if isinstance(v1, dict) and isinstance(v2, dict):
            diffs.extend(_diff_dicts(v1, v2, current_path))
        elif v1 != v2:
            diffs.append({"path": current_path, "from": str(v1), "to": str(v2)})
    return diffs


class ConfigLoader:
    """Load and merge configuration with layered precedence."""

    def __init__(self, config_dir: str, environment: str = "development") -> None:
        self.config_dir = Path(config_dir)
        self.environment = environment

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        path = self.config_dir / filename
        if not path.exists():
            return {}
        with open(path) as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    def _load_env_yaml(self) -> dict[str, Any]:
        return self._load_yaml(f"environments/{self.environment}.yaml")

    def _load_cluster_credentials(self) -> list[dict[str, Any]]:
        """Build cluster config list from secrets/cluster-credentials.yml."""
        creds_path = self.config_dir.parent / "secrets" / "cluster-credentials.yml"
        if not creds_path.exists():
            return []
        try:
            with open(creds_path) as f:
                data = yaml.safe_load(f)
        except (OSError, yaml.YAMLError):
            return []
        if not isinstance(data, dict):
            return []
        cluster_creds = data.get("cluster_credentials", {})
        clusters: list[dict[str, Any]] = []
        for name, entry in cluster_creds.items():
            if not isinstance(entry, dict):
                continue
            cluster: dict[str, Any] = {
                "id": name,
                "enabled": entry.get("enabled", True),
                "purpose": entry.get("purpose", "attendee"),
                "seat_number": entry.get("seat_number"),
                "connection": {
                    "api_url": entry.get("api_url", ""),
                    "admin_auth_method": "password",
                    "admin_username": "cluster-admin",
                },
                "platform": {
                    "provider": "aws",
                    "aws_account_id": entry.get("aws_account_id", ""),
                    "aws_region": entry.get("aws_region", "us-east-2"),
                },
            }
            clusters.append(cluster)
        return clusters

    def load_raw(self) -> dict[str, Any]:
        """Load and merge all config layers into a raw dict."""
        defaults = self._load_yaml("defaults.yaml")
        env_config = self._load_env_yaml()
        event_config = self._load_yaml("event.yaml")
        credentials_config = self._load_yaml("credentials.yaml")
        components_config = self._load_yaml("components.yaml")
        aws_config = self._load_yaml("aws.yaml")
        showroom_config = self._load_yaml("showroom.yaml")

        merged = defaults
        merged = _deep_merge(merged, env_config)
        merged = _deep_merge(merged, event_config)
        merged = _deep_merge(merged, credentials_config)
        merged = _deep_merge(merged, components_config)
        merged = _deep_merge(merged, aws_config)
        merged = _deep_merge(merged, showroom_config)

        clusters = self._load_cluster_credentials()
        if clusters:
            merged["clusters"] = clusters

        return merged

    def load(self) -> MASWorldConfig:
        """Load, merge, and validate configuration."""
        raw = self.load_raw()
        return MASWorldConfig(**raw)

    def render_effective(
        self,
        config: MASWorldConfig,
        cluster_id: str | None = None,
        redact_secrets: bool = True,
    ) -> dict[str, Any]:
        """Render the effective configuration as a dict."""
        data = config.model_dump(mode="json")
        if cluster_id:
            data["clusters"] = [c for c in data.get("clusters", []) if c["id"] == cluster_id]
        if redact_secrets:
            data = _redact_dict(data)
        return data

    @staticmethod
    def diff(config_a: MASWorldConfig, config_b: MASWorldConfig) -> list[dict[str, str]]:
        """Compare two configurations and return differences."""
        dict_a = config_a.model_dump(mode="json")
        dict_b = config_b.model_dump(mode="json")
        return _diff_dicts(dict_a, dict_b)
