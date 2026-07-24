"""Tests for secret provider abstraction."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
import yaml

from cli.secrets.env_provider import EnvSecretProvider
from cli.secrets.file_provider import FileSecretProvider
from cli.secrets.provider import (
    create_provider,
    parse_secret_ref,
    ref_to_aws_sm_name,
    ref_to_env_var,
    ref_to_k8s_key,
)


class TestSecretRefParsing:
    def test_valid_ref(self) -> None:
        ns, path = parse_secret_ref("secret://mas-world/clusters/seat-01/admin-kubeconfig")
        assert ns == "mas-world"
        assert path == "clusters/seat-01/admin-kubeconfig"

    def test_invalid_ref_no_scheme(self) -> None:
        with pytest.raises(ValueError, match="Invalid secret reference"):
            parse_secret_ref("not-a-ref")

    def test_invalid_ref_wrong_scheme(self) -> None:
        with pytest.raises(ValueError, match="Invalid secret reference"):
            parse_secret_ref("http://mas-world/test")

    def test_simple_ref(self) -> None:
        ns, path = parse_secret_ref("secret://mas-world/ibm/entitlement-key")
        assert ns == "mas-world"
        assert path == "ibm/entitlement-key"


class TestRefConversions:
    def test_ref_to_env_var(self) -> None:
        env_var = ref_to_env_var("secret://mas-world/ibm/entitlement-key")
        assert env_var == "MAS_WORLD_SECRET_IBM_ENTITLEMENT_KEY"

    def test_ref_to_k8s_key(self) -> None:
        secret_name, key = ref_to_k8s_key("secret://mas-world/clusters/seat-01/admin-kubeconfig")
        assert secret_name == "mas-world-clusters-seat-01"
        assert key == "admin-kubeconfig"

    def test_ref_to_aws_sm_name(self) -> None:
        name = ref_to_aws_sm_name("secret://mas-world/ibm/entitlement-key")
        assert name == "mas-world/ibm/entitlement-key"


class TestEnvSecretProvider:
    def test_get_existing_secret(self) -> None:
        os.environ["MAS_WORLD_SECRET_TEST_VALUE"] = "test123"
        try:
            provider = EnvSecretProvider()
            assert provider.get_secret("secret://mas-world/test/value") == "test123"
        finally:
            del os.environ["MAS_WORLD_SECRET_TEST_VALUE"]

    def test_get_missing_secret_raises(self) -> None:
        provider = EnvSecretProvider()
        with pytest.raises(KeyError):
            provider.get_secret("secret://mas-world/nonexistent/key")

    def test_set_and_get(self) -> None:
        provider = EnvSecretProvider()
        ref = "secret://mas-world/test/set-get"
        try:
            provider.set_secret(ref, "myvalue")
            assert provider.get_secret(ref) == "myvalue"
        finally:
            provider.delete_secret(ref)

    def test_exists_true(self) -> None:
        provider = EnvSecretProvider()
        ref = "secret://mas-world/test/exists"
        provider.set_secret(ref, "val")
        try:
            assert provider.exists(ref) is True
        finally:
            provider.delete_secret(ref)

    def test_exists_false(self) -> None:
        provider = EnvSecretProvider()
        assert provider.exists("secret://mas-world/test/nope") is False

    def test_delete(self) -> None:
        provider = EnvSecretProvider()
        ref = "secret://mas-world/test/delete"
        provider.set_secret(ref, "val")
        provider.delete_secret(ref)
        assert provider.exists(ref) is False


class TestFileSecretProvider:
    def test_get_existing_secret(self, tmp_path: Path) -> None:
        secrets_file = tmp_path / "shared.yaml"
        secrets_file.write_text("ibm/entitlement-key: my-ent-key-value\n")
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert provider.get_secret("secret://mas-world/ibm/entitlement-key") == "my-ent-key-value"

    def test_get_missing_secret_raises(self, tmp_path: Path) -> None:
        secrets_file = tmp_path / "shared.yaml"
        secrets_file.write_text("ibm/entitlement-key: value\n")
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        with pytest.raises(KeyError, match="not found"):
            provider.get_secret("secret://mas-world/nonexistent/ref")

    def test_exists_true(self, tmp_path: Path) -> None:
        secrets_file = tmp_path / "shared.yaml"
        secrets_file.write_text("ibm/license: lic-val\n")
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert provider.exists("secret://mas-world/ibm/license") is True

    def test_exists_false(self, tmp_path: Path) -> None:
        secrets_file = tmp_path / "shared.yaml"
        secrets_file.write_text("ibm/license: lic-val\n")
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert provider.exists("secret://mas-world/missing/key") is False

    def test_set_secret_creates_file(self, tmp_path: Path) -> None:
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        provider.set_secret("secret://mas-world/test/new-key", "new-val")
        assert provider.get_secret("secret://mas-world/test/new-key") == "new-val"
        written = yaml.safe_load((tmp_path / "masworld-secrets.yml").read_text())
        assert written["test/new-key"] == "new-val"

    def test_set_secret_preserves_existing(self, tmp_path: Path) -> None:
        secrets_file = tmp_path / "shared.yaml"
        secrets_file.write_text("ibm/license: keep-me\n")
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        provider.set_secret("secret://mas-world/ibm/new-ref", "added")
        assert provider.get_secret("secret://mas-world/ibm/license") == "keep-me"
        assert provider.get_secret("secret://mas-world/ibm/new-ref") == "added"

    def test_delete_secret(self, tmp_path: Path) -> None:
        secrets_file = tmp_path / "clusters.yaml"
        secrets_file.write_text(
            "clusters/seat-01/admin-password: pw1\nclusters/seat-02/admin-password: pw2\n"
        )
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        provider.delete_secret("secret://mas-world/clusters/seat-01/admin-password")
        assert provider.exists("secret://mas-world/clusters/seat-01/admin-password") is False
        assert provider.exists("secret://mas-world/clusters/seat-02/admin-password") is True

    def test_loads_multiple_files(self, tmp_path: Path) -> None:
        (tmp_path / "shared.yaml").write_text("ibm/entitlement-key: ent-val\n")
        (tmp_path / "clusters.yaml").write_text("clusters/seat-01/admin-password: pw-val\n")
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert provider.get_secret("secret://mas-world/ibm/entitlement-key") == "ent-val"
        assert provider.get_secret("secret://mas-world/clusters/seat-01/admin-password") == "pw-val"

    def test_skips_example_files(self, tmp_path: Path) -> None:
        (tmp_path / "shared.yaml.example").write_text("ibm/entitlement-key: REPLACE\n")
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert provider.exists("secret://mas-world/ibm/entitlement-key") is False

    def test_missing_directory_no_crash(self, tmp_path: Path) -> None:
        provider = FileSecretProvider(secrets_dir=str(tmp_path / "nonexistent"))
        assert provider.exists("secret://mas-world/any/key") is False

    def test_file_permissions_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        secrets_file = tmp_path / "shared.yaml"
        secrets_file.write_text("ibm/license: val\n")
        os.chmod(secrets_file, 0o644)
        with caplog.at_level(logging.WARNING):
            FileSecretProvider(secrets_dir=str(tmp_path))
        assert any("readable by group/others" in msg for msg in caplog.messages)

    def test_file_reference_resolves(self, tmp_path: Path) -> None:
        (tmp_path / "entitlement.dat").write_text("eyJhbGciOiJIUzI1NiJ9\n")
        (tmp_path / "shared.yaml").write_text('ibm/entitlement-key: "file://entitlement.dat"\n')
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert (
            provider.get_secret("secret://mas-world/ibm/entitlement-key") == "eyJhbGciOiJIUzI1NiJ9"
        )

    def test_file_reference_absolute_path(self, tmp_path: Path) -> None:
        dat_file = tmp_path / "license.dat"
        dat_file.write_text("license-content-here\n")
        (tmp_path / "shared.yaml").write_text(f'ibm/license: "file://{dat_file}"\n')
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert provider.get_secret("secret://mas-world/ibm/license") == "license-content-here"

    def test_file_reference_missing_file_returns_raw(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        (tmp_path / "shared.yaml").write_text('ibm/entitlement-key: "file://nonexistent.dat"\n')
        with caplog.at_level(logging.WARNING):
            provider = FileSecretProvider(secrets_dir=str(tmp_path))
        val = provider.get_secret("secret://mas-world/ibm/entitlement-key")
        assert val == "file://nonexistent.dat"
        assert any("Cannot read referenced file" in msg for msg in caplog.messages)

    def test_inline_value_not_treated_as_file_ref(self, tmp_path: Path) -> None:
        (tmp_path / "shared.yaml").write_text('AWS_ACCESS_KEY_ID: "AKIAEXAMPLE123"\n')
        provider = FileSecretProvider(secrets_dir=str(tmp_path))
        assert provider.get_secret("secret://mas-world/AWS_ACCESS_KEY_ID") == "AKIAEXAMPLE123"


class TestCreateProvider:
    def test_env_provider(self) -> None:
        provider = create_provider("env")
        assert isinstance(provider, EnvSecretProvider)

    def test_file_provider(self, tmp_path: Path) -> None:
        provider = create_provider("file", {"secrets_dir": str(tmp_path)})
        assert isinstance(provider, FileSecretProvider)

    def test_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown"):
            create_provider("redis")
