"""AWS Secrets Manager provider."""

from __future__ import annotations

import contextlib
from typing import Any

from cli.secrets.provider import SecretProvider, ref_to_aws_sm_name


class AWSSecretsManagerProvider(SecretProvider):
    """Reads and writes secrets in AWS Secrets Manager."""

    def __init__(self, region: str = "us-east-2") -> None:
        self.region = region
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client("secretsmanager", region_name=self.region)
        return self._client

    def get_secret(self, ref: str) -> str:
        name = ref_to_aws_sm_name(ref)
        client = self._get_client()
        try:
            response = client.get_secret_value(SecretId=name)
            return response["SecretString"]
        except client.exceptions.ResourceNotFoundException:
            raise KeyError(f"Secret not found in AWS Secrets Manager: {ref}") from None

    def set_secret(self, ref: str, value: str) -> None:
        name = ref_to_aws_sm_name(ref)
        client = self._get_client()
        try:
            client.put_secret_value(SecretId=name, SecretString=value)
        except client.exceptions.ResourceNotFoundException:
            client.create_secret(Name=name, SecretString=value)

    def delete_secret(self, ref: str) -> None:
        name = ref_to_aws_sm_name(ref)
        client = self._get_client()
        with contextlib.suppress(client.exceptions.ResourceNotFoundException):
            client.delete_secret(SecretId=name, ForceDeleteWithoutRecovery=True)

    def exists(self, ref: str) -> bool:
        name = ref_to_aws_sm_name(ref)
        client = self._get_client()
        try:
            client.describe_secret(SecretId=name)
            return True
        except client.exceptions.ResourceNotFoundException:
            return False
