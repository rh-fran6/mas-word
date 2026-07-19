"""Tests for configuration validation."""

from __future__ import annotations

import pytest

from cli.config.schema import MASWorldConfig, ClusterConfig, ClusterConnection
from cli.config.validator import ConfigValidator


def _make_config(**overrides) -> MASWorldConfig:
    """Create a valid MASWorldConfig with optional overrides."""
    defaults = {
        "event": {"id": "test", "name": "Test", "date": "2026-08-17", "timezone": "UTC"},
        "fleet": {"attendee_cluster_count": 0, "spare_cluster_count": 0, "facilitator_cluster_count": 0},
        "student_credential_profiles": {
            "attendee-default": {
                "username_template": "user{{ seat }}",
                "authentication_provider": "htpasswd",
            }
        },
    }
    defaults.update(overrides)
    return MASWorldConfig(**defaults)


class TestSchemaValidation:
    def test_rejects_duplicate_cluster_ids(self) -> None:
        cluster = {
            "id": "seat-01",
            "connection": {"api_url": "https://api.test:6443", "admin_secret_ref": "secret://test/clusters/seat-01/kc"},
        }
        with pytest.raises(ValueError, match="Duplicate cluster IDs"):
            _make_config(clusters=[cluster, cluster])

    def test_rejects_duplicate_seat_numbers(self) -> None:
        c1 = {
            "id": "seat-01",
            "seat_number": 1,
            "connection": {"api_url": "https://api1:6443", "admin_secret_ref": "secret://test/c1/kc"},
        }
        c2 = {
            "id": "seat-02",
            "seat_number": 1,
            "connection": {"api_url": "https://api2:6443", "admin_secret_ref": "secret://test/c2/kc"},
        }
        with pytest.raises(ValueError, match="Duplicate seat numbers"):
            _make_config(clusters=[c1, c2])

    def test_rejects_attendee_cluster_admin(self) -> None:
        profiles = {
            "attendee-default": {
                "username_template": "user{{ seat }}",
                "authentication_provider": "htpasswd",
                "restrictions": {"allow_cluster_admin": True},
            }
        }
        with pytest.raises(ValueError, match="cluster-admin"):
            _make_config(student_credential_profiles=profiles)

    def test_valid_minimal_config(self) -> None:
        config = _make_config()
        assert config.event.id == "test"

    def test_password_length_minimum(self) -> None:
        profiles = {
            "attendee-default": {
                "username_template": "user{{ seat }}",
                "authentication_provider": "htpasswd",
                "password": {"length": 8},
            }
        }
        with pytest.raises(ValueError):
            _make_config(student_credential_profiles=profiles)


class TestConfigValidator:
    def test_detects_missing_credential_profile(self) -> None:
        cluster = {
            "id": "seat-01",
            "connection": {"api_url": "https://api:6443", "admin_secret_ref": "secret://test/c/kc"},
            "credentials": {"student_credential_profile": "nonexistent"},
        }
        config = _make_config(clusters=[cluster])
        validator = ConfigValidator()
        errors = validator.validate(config)
        messages = [e["message"] for e in errors]
        assert any("nonexistent" in m for m in messages)

    def test_warns_on_no_spares_large_fleet(self) -> None:
        config = _make_config(
            fleet={"attendee_cluster_count": 10, "spare_cluster_count": 0, "facilitator_cluster_count": 0}
        )
        validator = ConfigValidator()
        errors = validator.validate(config)
        warnings = [e for e in errors if e["severity"] == "WARNING"]
        assert any("spare" in w["message"].lower() for w in warnings)

    def test_detects_loki_without_logging(self) -> None:
        config = _make_config(
            components={"logging": {"enabled": False}, "loki": {"enabled": True}}
        )
        validator = ConfigValidator()
        errors = validator.validate(config)
        assert any("Loki" in e["message"] for e in errors)

    def test_warns_on_placeholder_api_url(self) -> None:
        cluster = {
            "id": "seat-01",
            "connection": {"api_url": "PLACEHOLDER", "admin_secret_ref": "secret://test/c/kc"},
        }
        config = _make_config(clusters=[cluster])
        validator = ConfigValidator()
        errors = validator.validate(config)
        assert any("placeholder" in e["message"].lower() for e in errors)

    def test_detects_embedded_aws_key(self) -> None:
        cluster = {
            "id": "seat-01",
            "connection": {"api_url": "https://api:6443", "admin_secret_ref": "AKIAIOSFODNN7EXAMPLE1"},
        }
        config = _make_config(clusters=[cluster])
        validator = ConfigValidator()
        errors = validator.validate(config)
        assert any("secret value" in e["message"].lower() or "Invalid secret" in e["message"] for e in errors)
