"""Pydantic configuration models for MAS World 2026."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class AuthMethod(str, Enum):
    KUBECONFIG = "kubeconfig"
    TOKEN = "token"
    USERNAME_PASSWORD = "username-password"
    EXTERNAL = "external"


class ClusterPurpose(str, Enum):
    ATTENDEE = "attendee"
    SPARE = "spare"
    FACILITATOR = "facilitator"


class SecretProviderType(str, Enum):
    ENV = "env"
    K8S = "k8s"
    AWS_SM = "aws-sm"
    VAULT = "vault"


class PasswordMode(str, Enum):
    GENERATED = "generated"
    SECRET_REF = "secret-ref"
    EXTERNAL_IDP = "external-idp"
    DISABLED = "disabled"
    DETERMINISTIC = "deterministic"


class ObjectStorageMode(str, Enum):
    BUCKET_PER_CLUSTER = "bucket-per-cluster"
    SHARED_BUCKET = "shared-bucket"


class KeycloakMode(str, Enum):
    PER_CLUSTER = "per-cluster"
    SHARED = "shared"
    EXTERNAL = "external"


SECRET_REF_PATTERN = re.compile(r"^secret://[\w-]+/[\w-]+(/[\w-]+)*$")


def _is_secret_ref(value: str) -> bool:
    return bool(SECRET_REF_PATTERN.match(value))


class EventConfig(BaseModel):
    id: str = "mas-world-2026"
    name: str = "MAS World 2026"
    date: str = "2026-08-17"
    timezone: str = "America/Chicago"


class PreparationConfig(BaseModel):
    max_concurrent_clusters: int = Field(default=5, ge=1, le=50)
    per_cluster_timeout_minutes: int = Field(default=240, ge=30)
    retry_count: int = Field(default=3, ge=0)
    retry_backoff_base_seconds: int = Field(default=30, ge=1)


class AssignmentConfig(BaseModel):
    first_seat_number: int = Field(default=1, ge=1)
    seat_number_padding: int = Field(default=2, ge=1, le=4)
    automatically_assign_spares: bool = False


class FleetConfig(BaseModel):
    attendee_cluster_count: int = Field(default=1, ge=0)
    spare_cluster_count: int = Field(default=0, ge=0)
    facilitator_cluster_count: int = Field(default=1, ge=0, le=5)
    require_exact_cluster_counts: bool = False
    preparation: PreparationConfig = PreparationConfig()
    assignment: AssignmentConfig = AssignmentConfig()


class ClusterConnection(BaseModel):
    api_url: str
    admin_auth_method: AuthMethod = AuthMethod.KUBECONFIG
    admin_secret_ref: str

    @field_validator("admin_secret_ref")
    @classmethod
    def validate_secret_ref(cls, v: str) -> str:
        if v != "PLACEHOLDER" and not _is_secret_ref(v):
            raise ValueError(f"Invalid secret reference format: {v}")
        return v


class ClusterPlatform(BaseModel):
    provider: str = "aws"
    aws_account_id: str = "PLACEHOLDER"
    aws_region: str = "us-east-2"


class ClusterEndpoints(BaseModel):
    console_url: str | None = None
    mas_url: str | None = None
    showroom_url: str | None = None
    logging_url: str | None = None


class ClusterCredentials(BaseModel):
    student_credential_profile: str = "attendee-default"


class ClusterMetadata(BaseModel):
    event: str = "mas-world-2026"
    environment: str = "workshop"


class ClusterConfig(BaseModel):
    id: str
    enabled: bool = True
    purpose: ClusterPurpose = ClusterPurpose.ATTENDEE
    seat_number: int | None = None
    connection: ClusterConnection
    platform: ClusterPlatform = ClusterPlatform()
    endpoints: ClusterEndpoints = ClusterEndpoints()
    credentials: ClusterCredentials = ClusterCredentials()
    metadata: ClusterMetadata = ClusterMetadata()
    component_overrides: dict[str, Any] = Field(default_factory=dict)


class PasswordConfig(BaseModel):
    mode: PasswordMode = PasswordMode.GENERATED
    length: int = Field(default=18, ge=12, le=64)
    secret_ref_template: str = ""
    rotate_before_event: bool = True
    expire_after_event: bool = True


class NamespaceAccess(BaseModel):
    name_template: str
    role: str = "admin"


class AccessConfig(BaseModel):
    cluster_role: str = "basic-user"
    cluster_roles: list[str] = Field(default_factory=list)
    additional_cluster_roles: list[str] = Field(default_factory=list)
    namespaces: list[NamespaceAccess] = Field(default_factory=list)


class RestrictionConfig(BaseModel):
    allow_cluster_admin: bool = False
    allow_acm_access: bool = False
    allow_other_student_namespaces: bool = False
    allow_protected_secret_read: bool = False


class StudentCredentialProfile(BaseModel):
    username_template: str
    display_name_template: str = ""
    authentication_provider: str = "htpasswd"
    password: PasswordConfig = PasswordConfig()
    access: AccessConfig = AccessConfig()
    restrictions: RestrictionConfig = RestrictionConfig()


class StudentCredentialConfig(BaseModel):
    allow_shared_password: bool = False
    default_profile: str = "attendee-default"


class SecretProviderConfig(BaseModel):
    provider: SecretProviderType = SecretProviderType.ENV
    config: dict[str, Any] = Field(default_factory=dict)


class ComponentConfig(BaseModel):
    enabled: bool = True


class MASComponentConfig(ComponentConfig):
    version: str = "UNSET"
    channel: str = "UNSET"
    install_core: bool = True
    install_manage: bool = True
    catalog_source: str = "ibm-operator-catalog"


class LoggingComponentConfig(ComponentConfig):
    collector: str = "vector"
    collect_application: bool = True
    collect_infrastructure: bool = True
    collect_audit: bool = True


class LokiComponentConfig(ComponentConfig):
    object_storage_mode: ObjectStorageMode = ObjectStorageMode.BUCKET_PER_CLUSTER
    size: str = "1x.extra-small"
    retention_days: int = Field(default=7, ge=1, le=30)


class KeycloakComponentConfig(ComponentConfig):
    deployment_mode: KeycloakMode = KeycloakMode.PER_CLUSTER
    realm_name: str = "mas-world"


class MASEdgeComponentConfig(ComponentConfig):
    enabled: bool = False


class ComponentsConfig(BaseModel):
    mas: MASComponentConfig = MASComponentConfig()
    logging: LoggingComponentConfig = LoggingComponentConfig()
    loki: LokiComponentConfig = LokiComponentConfig()
    keycloak: KeycloakComponentConfig = KeycloakComponentConfig()
    mas_edge: MASEdgeComponentConfig = MASEdgeComponentConfig()
    showroom: ComponentConfig = ComponentConfig()
    acm_registration: ComponentConfig = ComponentConfig()


class LoggingConfig(BaseModel):
    log_level: str = "info"
    structured: bool = True
    per_cluster_log_dir: str = "logs/clusters"
    redact_secrets: bool = True


class AWSConfig(BaseModel):
    default_region: str = "us-east-2"
    s3_bucket_prefix: str = "mas-world-2026"
    s3_encryption: str = "AES256"
    s3_lifecycle_expiration_days: int = Field(default=30, ge=1)


class MASWorldConfig(BaseModel):
    event: EventConfig = EventConfig()
    fleet: FleetConfig = FleetConfig()
    components: ComponentsConfig = ComponentsConfig()
    secrets: SecretProviderConfig = SecretProviderConfig()
    student_credentials: StudentCredentialConfig = StudentCredentialConfig()
    student_credential_profiles: dict[str, StudentCredentialProfile] = Field(
        default_factory=dict
    )
    clusters: list[ClusterConfig] = Field(default_factory=list)
    aws: AWSConfig = AWSConfig()
    logging_config: LoggingConfig = LoggingConfig()

    @model_validator(mode="after")
    def validate_no_duplicate_cluster_ids(self) -> MASWorldConfig:
        ids = [c.id for c in self.clusters]
        duplicates = [x for x in ids if ids.count(x) > 1]
        if duplicates:
            raise ValueError(f"Duplicate cluster IDs: {set(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_no_duplicate_seat_numbers(self) -> MASWorldConfig:
        seats = [c.seat_number for c in self.clusters if c.seat_number is not None]
        duplicates = [x for x in seats if seats.count(x) > 1]
        if duplicates:
            raise ValueError(f"Duplicate seat numbers: {set(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_attendee_restrictions(self) -> MASWorldConfig:
        for name, profile in self.student_credential_profiles.items():
            if name == "facilitator":
                continue
            if profile.restrictions.allow_cluster_admin:
                raise ValueError(
                    f"Profile '{name}' grants cluster-admin to attendees — forbidden"
                )
        return self

    @model_validator(mode="after")
    def validate_shared_passwords(self) -> MASWorldConfig:
        if self.student_credentials.allow_shared_password:
            import sys

            print(
                "\n⚠️  WARNING: Shared student passwords are enabled.\n"
                "⚠️  This is NOT suitable for event use.\n",
                file=sys.stderr,
            )
        return self
