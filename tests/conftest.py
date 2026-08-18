"""Shared test fixtures for MAS World 2026 tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create a temporary config directory with valid defaults."""
    config = tmp_path / "config"
    config.mkdir()
    envs = config / "environments"
    envs.mkdir()

    defaults = {
        "event": {
            "id": "test-event",
            "name": "Test Event",
            "date": "2026-08-17",
            "timezone": "America/Chicago",
        },
        "fleet": {
            "attendee_cluster_count": 2,
            "spare_cluster_count": 0,
            "facilitator_cluster_count": 0,
            "require_exact_cluster_counts": False,
            "preparation": {
                "max_concurrent_clusters": 1,
                "per_cluster_timeout_minutes": 60,
                "retry_count": 1,
                "retry_backoff_base_seconds": 5,
            },
            "assignment": {
                "first_seat_number": 1,
                "seat_number_padding": 2,
                "automatically_assign_spares": False,
            },
        },
        "components": {
            "mas": {
                "enabled": True,
                "version": "9.2.x",
                "channel": "9.2.x",
                "install_core": True,
                "install_manage": True,
                "catalog_source": "ibm-operator-catalog",
            },
            "logging": {
                "enabled": True,
                "collector": "vector",
                "collect_application": True,
                "collect_infrastructure": True,
                "collect_audit": True,
            },
            "loki": {
                "enabled": True,
                "object_storage_mode": "bucket-per-cluster",
                "size": "1x.extra-small",
                "retention_days": 7,
            },
            "keycloak": {"enabled": True, "deployment_mode": "per-cluster", "realm_name": "test"},
            "mas_edge": {"enabled": False},
            "showroom": {"enabled": True},
            "acm_registration": {"enabled": False, "hub_cluster_id": ""},
        },
        "secrets": {"provider": "env", "config": {}},
        "student_credentials": {
            "allow_shared_password": False,
            "default_profile": "attendee-default",
        },
        "student_credential_profiles": {
            "attendee-default": {
                "username_template": "user{{ seat_number | pad(2) }}",
                "display_name_template": "Test Attendee {{ seat_number }}",
                "authentication_provider": "htpasswd",
                "password": {
                    "mode": "generated",
                    "length": 18,
                    "secret_ref_template": "secret://test/students/seat-{{ seat_number | pad(2) }}",
                    "rotate_before_event": True,
                    "expire_after_event": True,
                },
                "access": {
                    "cluster_role": "basic-user",
                    "additional_cluster_roles": [],
                    "namespaces": [
                        {"name_template": "student-{{ seat_number | pad(2) }}", "role": "admin"}
                    ],
                },
                "restrictions": {
                    "allow_cluster_admin": False,
                    "allow_acm_access": False,
                    "allow_other_student_namespaces": False,
                    "allow_protected_secret_read": False,
                },
            }
        },
        "clusters": [],
        "aws": {
            "default_region": "us-east-2",
            "s3_bucket_prefix": "test",
            "s3_encryption": "AES256",
            "s3_lifecycle_expiration_days": 30,
        },
        "logging_config": {
            "log_level": "debug",
            "structured": True,
            "per_cluster_log_dir": "logs/clusters",
            "redact_secrets": True,
        },
    }

    with open(config / "defaults.yaml", "w") as f:
        yaml.dump(defaults, f, default_flow_style=False)

    with open(config / "event.yaml", "w") as f:
        yaml.dump({"event": {"id": "test-event"}}, f)

    for env_name in ("development", "rehearsal", "event"):
        with open(envs / f"{env_name}.yaml", "w") as f:
            yaml.dump({}, f)

    for name in ("credentials", "components", "aws", "showroom"):
        with open(config / f"{name}.yaml", "w") as f:
            yaml.dump({}, f)

    return config


@pytest.fixture
def sample_cluster() -> dict[str, Any]:
    """Return a sample cluster configuration dict."""
    return {
        "id": "lab-seat-01",
        "enabled": True,
        "purpose": "attendee",
        "seat_number": 1,
        "connection": {
            "api_url": "https://api.test-cluster.example.com:6443",
            "admin_auth_method": "password",
            "admin_username": "cluster-admin",
        },
        "platform": {
            "provider": "aws",
            "aws_account_id": "111111111111",
            "aws_region": "us-east-2",
        },
        "endpoints": {},
        "credentials": {"student_credential_profile": "attendee-default"},
        "metadata": {"event": "test-event", "environment": "workshop"},
    }
