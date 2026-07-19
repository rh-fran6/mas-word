"""Tests for secret provider abstraction."""

from __future__ import annotations

import os

import pytest

from cli.secrets.provider import (
    parse_secret_ref,
    ref_to_env_var,
    ref_to_k8s_key,
    ref_to_aws_sm_name,
    create_provider,
)
from cli.secrets.env_provider import EnvSecretProvider


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


class TestCreateProvider:
    def test_env_provider(self) -> None:
        provider = create_provider("env")
        assert isinstance(provider, EnvSecretProvider)

    def test_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown"):
            create_provider("redis")
