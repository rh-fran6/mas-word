"""Environment variable secret provider — for local development."""

from __future__ import annotations

import os

from cli.secrets.provider import SecretProvider, ref_to_env_var


class EnvSecretProvider(SecretProvider):
    """Reads secrets from environment variables.

    Useful for local development and CI pipelines.
    Secret ref ``secret://mas-world/ibm/entitlement-key`` maps to
    ``MAS_WORLD_SECRET_IBM_ENTITLEMENT_KEY``.
    """

    def get_secret(self, ref: str) -> str:
        env_var = ref_to_env_var(ref)
        value = os.environ.get(env_var)
        if value is None:
            raise KeyError(f"Secret not found: {ref} (expected env var: {env_var})")
        return value

    def set_secret(self, ref: str, value: str) -> None:
        env_var = ref_to_env_var(ref)
        os.environ[env_var] = value

    def delete_secret(self, ref: str) -> None:
        env_var = ref_to_env_var(ref)
        os.environ.pop(env_var, None)

    def exists(self, ref: str) -> bool:
        env_var = ref_to_env_var(ref)
        return env_var in os.environ
