"""Configuration validation beyond schema validation."""

from __future__ import annotations

import re
from typing import Any

from cli.config.schema import MASWorldConfig


SECRET_VALUE_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\."),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}$"),
]


class ConfigValidator:
    """Validate configuration for semantic correctness."""

    def validate(
        self, config: MASWorldConfig, cluster_id: str | None = None
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        errors.extend(self._check_cluster_counts(config))
        errors.extend(self._check_credential_profiles(config))
        errors.extend(self._check_secret_leaks(config))
        errors.extend(self._check_component_dependencies(config))
        errors.extend(self._check_shared_password_in_event(config))
        errors.extend(self._check_cluster_connections(config, cluster_id))
        return errors

    def _check_cluster_counts(self, config: MASWorldConfig) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        clusters = config.clusters
        attendee = [c for c in clusters if c.enabled and c.purpose.value == "attendee"]
        spare = [c for c in clusters if c.enabled and c.purpose.value == "spare"]
        facilitator = [c for c in clusters if c.enabled and c.purpose.value == "facilitator"]

        if config.fleet.require_exact_cluster_counts:
            if len(attendee) != config.fleet.attendee_cluster_count:
                errors.append({
                    "severity": "ERROR",
                    "message": (
                        f"Expected {config.fleet.attendee_cluster_count} attendee clusters, "
                        f"found {len(attendee)} enabled"
                    ),
                    "path": "fleet.attendee_cluster_count",
                })
            if len(spare) != config.fleet.spare_cluster_count:
                errors.append({
                    "severity": "ERROR",
                    "message": (
                        f"Expected {config.fleet.spare_cluster_count} spare clusters, "
                        f"found {len(spare)} enabled"
                    ),
                    "path": "fleet.spare_cluster_count",
                })
            if len(facilitator) != config.fleet.facilitator_cluster_count:
                errors.append({
                    "severity": "ERROR",
                    "message": (
                        f"Expected {config.fleet.facilitator_cluster_count} facilitator clusters, "
                        f"found {len(facilitator)} enabled"
                    ),
                    "path": "fleet.facilitator_cluster_count",
                })

        if config.fleet.spare_cluster_count == 0 and config.fleet.attendee_cluster_count > 5:
            errors.append({
                "severity": "WARNING",
                "message": "No spare clusters configured for a fleet with >5 attendee clusters",
                "path": "fleet.spare_cluster_count",
            })

        return errors

    def _check_credential_profiles(self, config: MASWorldConfig) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        profile_names = set(config.student_credential_profiles.keys())

        for cluster in config.clusters:
            profile_name = cluster.credentials.student_credential_profile
            if profile_name not in profile_names:
                errors.append({
                    "severity": "ERROR",
                    "message": (
                        f"Cluster '{cluster.id}' references undefined credential profile "
                        f"'{profile_name}'"
                    ),
                    "path": f"clusters[{cluster.id}].credentials.student_credential_profile",
                })

        if config.student_credentials.default_profile not in profile_names:
            if profile_names:
                errors.append({
                    "severity": "ERROR",
                    "message": (
                        f"Default profile '{config.student_credentials.default_profile}' "
                        f"not defined"
                    ),
                    "path": "student_credentials.default_profile",
                })

        return errors

    def _check_secret_leaks(self, config: MASWorldConfig) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        data = config.model_dump(mode="json")
        self._scan_dict_for_secrets(data, "", errors)
        return errors

    def _scan_dict_for_secrets(
        self, data: Any, path: str, errors: list[dict[str, Any]]
    ) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                self._scan_dict_for_secrets(value, current_path, errors)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._scan_dict_for_secrets(item, f"{path}[{i}]", errors)
        elif isinstance(data, str):
            for pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(data):
                    errors.append({
                        "severity": "ERROR",
                        "message": f"Possible secret value detected at {path}",
                        "path": path,
                    })
                    break

    def _check_component_dependencies(self, config: MASWorldConfig) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        if config.components.loki.enabled and not config.components.logging.enabled:
            errors.append({
                "severity": "ERROR",
                "message": "Loki is enabled but Logging is disabled — Loki requires Logging",
                "path": "components.loki.enabled",
            })
        return errors

    def _check_shared_password_in_event(self, config: MASWorldConfig) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        if config.student_credentials.allow_shared_password:
            errors.append({
                "severity": "WARNING",
                "message": (
                    "Shared student passwords enabled — not suitable for event use"
                ),
                "path": "student_credentials.allow_shared_password",
            })
        return errors

    def _check_cluster_connections(
        self, config: MASWorldConfig, cluster_id: str | None
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        clusters = config.clusters
        if cluster_id:
            clusters = [c for c in clusters if c.id == cluster_id]

        for cluster in clusters:
            if not cluster.enabled:
                continue
            if cluster.connection.api_url == "PLACEHOLDER":
                errors.append({
                    "severity": "WARNING",
                    "message": f"Cluster '{cluster.id}' has placeholder API URL",
                    "path": f"clusters[{cluster.id}].connection.api_url",
                })
            if cluster.connection.admin_secret_ref == "PLACEHOLDER":
                errors.append({
                    "severity": "ERROR",
                    "message": (
                        f"Cluster '{cluster.id}' has no admin credential reference"
                    ),
                    "path": f"clusters[{cluster.id}].connection.admin_secret_ref",
                })

        return errors
