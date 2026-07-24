"""Kubernetes Secrets provider — for in-cluster execution."""

from __future__ import annotations

import base64
from typing import Any

from cli.secrets.provider import SecretProvider, ref_to_k8s_key


class K8sSecretProvider(SecretProvider):
    """Reads secrets from Kubernetes Secrets in a designated namespace."""

    def __init__(self, namespace: str = "mas-world-secrets", kubeconfig: str | None = None) -> None:
        self.namespace = namespace
        self._kubeconfig = kubeconfig
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from kubernetes import client, config

            if self._kubeconfig:
                config.load_kube_config(config_file=self._kubeconfig)
            else:
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
            self._client = client.CoreV1Api()
        return self._client

    def get_secret(self, ref: str) -> str:
        secret_name, key = ref_to_k8s_key(ref)
        v1 = self._get_client()
        secret = v1.read_namespaced_secret(name=secret_name, namespace=self.namespace)
        if secret.data is None or key not in secret.data:
            raise KeyError(f"Secret key not found: {ref} (secret={secret_name}, key={key})")
        return base64.b64decode(secret.data[key]).decode("utf-8")

    def set_secret(self, ref: str, value: str) -> None:
        from kubernetes import client
        from kubernetes.client.rest import ApiException

        secret_name, key = ref_to_k8s_key(ref)
        v1 = self._get_client()
        encoded = base64.b64encode(value.encode("utf-8")).decode("utf-8")

        try:
            existing = v1.read_namespaced_secret(name=secret_name, namespace=self.namespace)
            if existing.data is None:
                existing.data = {}
            existing.data[key] = encoded
            v1.replace_namespaced_secret(name=secret_name, namespace=self.namespace, body=existing)
        except ApiException as e:
            if e.status == 404:
                body = client.V1Secret(
                    metadata=client.V1ObjectMeta(name=secret_name),
                    data={key: encoded},
                )
                v1.create_namespaced_secret(namespace=self.namespace, body=body)
            else:
                raise

    def delete_secret(self, ref: str) -> None:
        from kubernetes.client.rest import ApiException

        secret_name, key = ref_to_k8s_key(ref)
        v1 = self._get_client()
        try:
            existing = v1.read_namespaced_secret(name=secret_name, namespace=self.namespace)
            if existing.data and key in existing.data:
                del existing.data[key]
                if existing.data:
                    v1.replace_namespaced_secret(
                        name=secret_name, namespace=self.namespace, body=existing
                    )
                else:
                    v1.delete_namespaced_secret(name=secret_name, namespace=self.namespace)
        except ApiException as e:
            if e.status != 404:
                raise

    def exists(self, ref: str) -> bool:
        from kubernetes.client.rest import ApiException

        secret_name, key = ref_to_k8s_key(ref)
        v1 = self._get_client()
        try:
            secret = v1.read_namespaced_secret(name=secret_name, namespace=self.namespace)
            return secret.data is not None and key in secret.data
        except ApiException:
            return False
