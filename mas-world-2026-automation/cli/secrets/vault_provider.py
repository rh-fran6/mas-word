"""HashiCorp Vault provider — optional."""

from __future__ import annotations

import os

from cli.secrets.provider import SecretProvider, parse_secret_ref


class VaultSecretProvider(SecretProvider):
    """Reads and writes secrets in HashiCorp Vault (KV v2).

    Requires the ``hvac`` package: ``pip install mas-world-2026[vault]``
    """

    def __init__(self, addr: str, token_env: str = "VAULT_TOKEN") -> None:
        self.addr = addr
        self.token_env = token_env
        self._client = None

    def _get_client(self):  # type: ignore[no-untyped-def]
        if self._client is None:
            try:
                import hvac
            except ImportError:
                raise RuntimeError(
                    "HashiCorp Vault support requires the 'hvac' package. "
                    "Install with: pip install mas-world-2026[vault]"
                )
            token = os.environ.get(self.token_env)
            if not token:
                raise RuntimeError(f"Vault token not found in env var: {self.token_env}")
            self._client = hvac.Client(url=self.addr, token=token)
        return self._client

    def get_secret(self, ref: str) -> str:
        namespace, path = parse_secret_ref(ref)
        client = self._get_client()
        parts = path.rsplit("/", 1)
        mount = namespace
        secret_path = parts[0] if len(parts) > 1 else path
        key = parts[-1] if len(parts) > 1 else "value"
        response = client.secrets.kv.v2.read_secret_version(
            mount_point=mount, path=secret_path
        )
        data = response.get("data", {}).get("data", {})
        if key not in data:
            raise KeyError(f"Secret key not found: {ref}")
        return data[key]

    def set_secret(self, ref: str, value: str) -> None:
        namespace, path = parse_secret_ref(ref)
        client = self._get_client()
        parts = path.rsplit("/", 1)
        mount = namespace
        secret_path = parts[0] if len(parts) > 1 else path
        key = parts[-1] if len(parts) > 1 else "value"
        try:
            existing = client.secrets.kv.v2.read_secret_version(
                mount_point=mount, path=secret_path
            )
            data = existing.get("data", {}).get("data", {})
        except Exception:
            data = {}
        data[key] = value
        client.secrets.kv.v2.create_or_update_secret(
            mount_point=mount, path=secret_path, secret=data
        )

    def delete_secret(self, ref: str) -> None:
        namespace, path = parse_secret_ref(ref)
        client = self._get_client()
        parts = path.rsplit("/", 1)
        mount = namespace
        secret_path = parts[0] if len(parts) > 1 else path
        try:
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                mount_point=mount, path=secret_path
            )
        except Exception:
            pass

    def exists(self, ref: str) -> bool:
        try:
            self.get_secret(ref)
            return True
        except (KeyError, Exception):
            return False
