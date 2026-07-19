"""Secret provider abstraction."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any


class SecretProvider(ABC):
    """Abstract base class for secret providers."""

    @abstractmethod
    def get_secret(self, ref: str) -> str:
        """Retrieve a secret value by reference. Never cache to disk."""

    @abstractmethod
    def set_secret(self, ref: str, value: str) -> None:
        """Store a secret value."""

    @abstractmethod
    def delete_secret(self, ref: str) -> None:
        """Delete a secret value."""

    @abstractmethod
    def exists(self, ref: str) -> bool:
        """Check if a secret exists without retrieving it."""


SECRET_REF_REGEX = re.compile(r"^secret://(?P<namespace>[\w-]+)/(?P<path>.+)$")


def parse_secret_ref(ref: str) -> tuple[str, str]:
    """Parse a secret:// reference into (namespace, path)."""
    match = SECRET_REF_REGEX.match(ref)
    if not match:
        raise ValueError(f"Invalid secret reference: {ref}")
    return match.group("namespace"), match.group("path")


def ref_to_env_var(ref: str) -> str:
    """Convert a secret reference to an environment variable name."""
    _, path = parse_secret_ref(ref)
    return "MAS_WORLD_SECRET_" + path.upper().replace("/", "_").replace("-", "_")


def ref_to_k8s_key(ref: str) -> tuple[str, str]:
    """Convert a secret reference to (K8s Secret name, key)."""
    namespace, path = parse_secret_ref(ref)
    parts = path.split("/")
    secret_name = f"{namespace}-{'-'.join(parts[:-1])}" if len(parts) > 1 else namespace
    key = parts[-1]
    return secret_name, key


def ref_to_aws_sm_name(ref: str) -> str:
    """Convert a secret reference to an AWS Secrets Manager secret name."""
    namespace, path = parse_secret_ref(ref)
    return f"{namespace}/{path}"


def create_provider(provider_type: str, config: dict[str, Any] | None = None) -> SecretProvider:
    """Factory: create a SecretProvider by type name."""
    config = config or {}
    if provider_type == "env":
        from cli.secrets.env_provider import EnvSecretProvider

        return EnvSecretProvider()
    elif provider_type == "k8s":
        from cli.secrets.k8s_provider import K8sSecretProvider

        return K8sSecretProvider(
            namespace=config.get("namespace", "mas-world-secrets"),
            kubeconfig=config.get("kubeconfig"),
        )
    elif provider_type == "aws-sm":
        from cli.secrets.aws_sm_provider import AWSSecretsManagerProvider

        return AWSSecretsManagerProvider(
            region=config.get("aws_region", "us-east-2"),
        )
    elif provider_type == "vault":
        from cli.secrets.vault_provider import VaultSecretProvider

        return VaultSecretProvider(
            addr=config.get("vault_addr", ""),
            token_env=config.get("vault_token_env", "VAULT_TOKEN"),
        )
    else:
        raise ValueError(f"Unknown secret provider type: {provider_type}")
