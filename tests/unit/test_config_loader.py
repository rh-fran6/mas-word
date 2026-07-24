"""Tests for configuration loading and merging."""

from __future__ import annotations

from pathlib import Path

import yaml

from cli.config.loader import ConfigLoader, _deep_merge, _redact_dict


class TestDeepMerge:
    def test_scalar_override(self) -> None:
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        assert _deep_merge(base, override) == {"a": 1, "b": 3}

    def test_nested_merge(self) -> None:
        base = {"a": {"x": 1, "y": 2}}
        override = {"a": {"y": 3, "z": 4}}
        assert _deep_merge(base, override) == {"a": {"x": 1, "y": 3, "z": 4}}

    def test_list_replacement(self) -> None:
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        assert _deep_merge(base, override) == {"items": [4, 5]}

    def test_new_key_added(self) -> None:
        base = {"a": 1}
        override = {"b": 2}
        assert _deep_merge(base, override) == {"a": 1, "b": 2}

    def test_does_not_mutate_base(self) -> None:
        base = {"a": {"x": 1}}
        override = {"a": {"x": 2}}
        _deep_merge(base, override)
        assert base["a"]["x"] == 1


class TestRedactDict:
    def test_redacts_password_field(self) -> None:
        data = {"password": "supersecret"}
        result = _redact_dict(data)
        assert result["password"] == "**REDACTED**"

    def test_preserves_secret_refs(self) -> None:
        data = {"secret_ref": "secret://mas-world/test"}
        result = _redact_dict(data)
        assert result["secret_ref"] == "secret://mas-world/test"

    def test_preserves_placeholders(self) -> None:
        data = {"password": "PLACEHOLDER"}
        result = _redact_dict(data)
        assert result["password"] == "PLACEHOLDER"

    def test_preserves_non_secret_fields(self) -> None:
        data = {"name": "test-cluster", "region": "us-east-2"}
        result = _redact_dict(data)
        assert result == data

    def test_nested_redaction(self) -> None:
        data = {"connection": {"admin_secret_key": "abcdef123"}}
        result = _redact_dict(data)
        assert result["connection"]["admin_secret_key"] == "**REDACTED**"


class TestConfigLoader:
    def test_loads_defaults(self, config_dir: Path) -> None:
        loader = ConfigLoader(config_dir=str(config_dir), environment="development")
        config = loader.load()
        assert config.event.id == "test-event"

    def test_environment_override(self, config_dir: Path) -> None:
        env_file = config_dir / "environments" / "development.yaml"
        with open(env_file, "w") as f:
            yaml.dump({"fleet": {"attendee_cluster_count": 3}}, f)

        loader = ConfigLoader(config_dir=str(config_dir), environment="development")
        config = loader.load()
        assert config.fleet.attendee_cluster_count == 3

    def test_render_effective_redacts(self, config_dir: Path) -> None:
        loader = ConfigLoader(config_dir=str(config_dir), environment="development")
        config = loader.load()
        rendered = loader.render_effective(config, redact_secrets=True)
        assert isinstance(rendered, dict)

    def test_diff_detects_changes(self, config_dir: Path) -> None:
        loader1 = ConfigLoader(config_dir=str(config_dir), environment="development")
        config1 = loader1.load()

        env_file = config_dir / "environments" / "rehearsal.yaml"
        with open(env_file, "w") as f:
            yaml.dump({"fleet": {"attendee_cluster_count": 5}}, f)

        loader2 = ConfigLoader(config_dir=str(config_dir), environment="rehearsal")
        config2 = loader2.load()

        diffs = ConfigLoader.diff(config1, config2)
        paths = [d["path"] for d in diffs]
        assert "fleet.attendee_cluster_count" in paths
