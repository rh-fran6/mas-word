# Security Review --- MAS World 2026

**Status**: DRAFT --- Phase 7
**Date**: 2026-07-19

---

## 1. Scope

This security review covers the following components of the MAS World 2026
workshop environment:

| Area | Description |
|------|-------------|
| Automation platform | Ansible-based fleet preparation, configuration validation, CLI tooling |
| Attendee clusters | 50 dedicated OpenShift clusters with MAS, logging, and identity |
| ACM hub | Advanced Cluster Management hub managing the full fleet |
| AWS resources | S3 buckets, IAM users and policies, region-scoped credentials |
| Showroom | Workshop UI, browser terminals, runtime automation (validate/solve/reset) |
| Credential management | Secret-provider abstraction, student accounts, rotation, revocation |
| CI/CD pipeline | Pre-commit hooks, secret scanning, dependency scanning, release gating |

The review evaluates the security posture of the preparation automation, the
runtime workshop environment, and the post-event teardown process.

---

## 2. Secret Management Review

### Provider abstraction

The project implements a `SecretProvider` abstract base class with four
concrete implementations:

| Provider | Class | Use case |
|----------|-------|----------|
| Environment variables | `EnvironmentSecretProvider` | Local development |
| Kubernetes Secrets | `KubernetesSecretProvider` | In-cluster execution |
| AWS Secrets Manager | `AWSSecretsManagerProvider` | Event and rehearsal environments |
| HashiCorp Vault | `VaultSecretProvider` | Optional enterprise integration |

### Secret reference format

All secret references use the URI scheme:

```
secret://<namespace>/<category>/<identifier>
```

Examples:

```
secret://mas-world/clusters/seat-01/admin-kubeconfig
secret://mas-world/students/seat-01
secret://mas-world/ibm/entitlement
secret://mas-world/aws/s3/seat-01
```

Secret references are resolved at runtime only. No secret values are stored in
configuration files, Git, or CI artifacts.

### Redaction patterns

The redaction engine strips the following patterns from all log output, reports,
and support bundles:

| Pattern | Description |
|---------|-------------|
| `AKIA[0-9A-Z]{16}` | AWS access key IDs |
| `eyJ[A-Za-z0-9_-]{10,}` | JWT tokens |
| `password\s*[:=]\s*\S+` | Password assignments |
| `token\s*[:=]\s*\S+` | Token assignments |
| `secret\s*[:=]\s*\S+` | Secret assignments |
| `[A-Fa-f0-9]{64}` | SHA-256 hashes that may be secret material |
| `-----BEGIN.*PRIVATE KEY-----` | Private key blocks |
| `ibm-entitlement-key\s*[:=]\s*\S+` | IBM entitlement keys |

### Ansible task protection

All Ansible tasks handling sensitive data use `no_log: true`. This covers:

- Credential retrieval tasks
- Secret injection into Kubernetes resources
- Password generation and storage
- Kubeconfig file operations
- IBM entitlement key handling
- S3 credential creation

### Temporary kubeconfig handling

| Control | Implementation |
|---------|----------------|
| File permissions | Mode `0600` |
| Storage location | Isolated temporary directory per cluster operation |
| Cleanup | Deleted immediately after each cluster operation completes |
| Logging | Contents never logged |
| Concurrency | Unique temporary path per concurrent operation |
| Failure cleanup | Finally block ensures deletion even on task failure |

### Finding

**IMPLEMENTED** --- needs live cluster testing to confirm no secret leakage in
actual Ansible output and Kubernetes event streams.

---

## 3. RBAC Model Review

### Role definitions

**Attendee**

- ClusterRole: `basic-user`
- Namespace admin in own namespace (`student-XX`) only
- No `cluster-admin` binding
- No ACM access
- No access to other student namespaces
- Cannot read protected secrets (kubeconfigs, entitlement keys, S3 credentials)

**Facilitator**

- ClusterRole: `cluster-admin`
- Required for live support and troubleshooting during the workshop
- Scoped to assigned facilitator and attendee clusters

**Automation service accounts**

- `cluster-admin` for installation operations (documented IBM requirement)
- Separate service accounts planned per function:
  - Fleet preparation
  - ACM import
  - Post-provision configuration
  - Runtime validation

**Showroom runtime**

- Minimal permissions for validate, solve, and reset operations
- Cannot escalate privileges
- Cannot modify operators or cluster-scoped resources
- Cannot read secrets outside designated namespaces

**ACM hub**

- Scoped presenter access for live demonstration
- No attendee access to the hub console or API
- Support staff access limited to Francis and Myles

### RBAC finding summary

| Item | Expected | Implemented | Status |
|------|----------|-------------|--------|
| Attendee cannot access other namespaces | Enforced | RoleBinding scoped to own namespace | IMPLEMENTED_NOT_TESTED |
| Attendee is not cluster-admin | Enforced | No ClusterRoleBinding created | IMPLEMENTED_NOT_TESTED |
| Attendee cannot access ACM | Enforced | No ACM RBAC granted | IMPLEMENTED_NOT_TESTED |
| Attendee cannot read protected secrets | Enforced | RBAC rules deny secret read in system namespaces | IMPLEMENTED_NOT_TESTED |
| Facilitator has cluster-admin | Required | ClusterRoleBinding created | IMPLEMENTED_NOT_TESTED |
| Automation uses separate SAs | Planned | Service account definitions scaffolded | SCAFFOLDED |
| Showroom uses minimal permissions | Required | ServiceAccount with scoped Role | IMPLEMENTED_NOT_TESTED |
| ACM hub presenter access scoped | Required | ClusterRole with limited verbs | SCAFFOLDED |

---

## 4. Network Boundaries

### Architecture

| Boundary | Control |
|----------|---------|
| Per-cluster isolation | Each attendee operates on a dedicated OpenShift cluster; no shared cluster multi-tenancy |
| No cluster-to-cluster paths | Attendee clusters have no direct network connectivity to each other |
| ACM connectivity | Clusters communicate with the ACM hub only through managed agent channels |
| S3 access | Each cluster's IAM credentials are scoped to its own bucket |
| Showroom terminal | Browser terminal session is restricted to the assigned cluster API |
| Ingress | Each cluster has its own ingress controller and wildcard certificate |
| DNS | Per-cluster DNS entries; no shared ingress domains across attendees |

### Lateral movement assessment

An attendee with access to their browser terminal can reach:

- Their own cluster API (authenticated as `basic-user`)
- Their own Maximo instance
- Their own Loki query endpoint (through the OpenShift console)
- Public internet (for documentation references)

An attendee cannot reach:

- Other attendee cluster APIs (no network path, no credentials)
- The ACM hub API (no credentials, no Showroom tab)
- Other attendee S3 buckets (IAM policy restriction)
- Other attendee Showroom instances (separate URLs, separate credentials)

### Finding

**IMPLEMENTED_NOT_TESTED** --- the architectural controls are in place but
require live validation on provisioned clusters to confirm no unintended
network paths exist.

---

## 5. S3 Isolation Review

### Bucket model

The project uses a per-cluster bucket model:

```
mas-world-2026-{cluster-id}-loki-{unique-suffix}
```

Each attendee cluster writes logs to its own dedicated S3 bucket. No shared
bucket with prefix-based isolation.

### Per-cluster IAM controls

| Control | Implementation |
|---------|----------------|
| IAM user | One IAM user per cluster (`mas-world-2026-{cluster-id}-loki`) |
| IAM policy | Bucket-specific `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`, `s3:DeleteObject` |
| Policy resource | `arn:aws:s3:::mas-world-2026-{cluster-id}-loki-*` only |
| Public access block | `BlockPublicAcls`, `BlockPublicPolicy`, `IgnorePublicAcls`, `RestrictPublicBuckets` all enabled |
| Encryption | AES-256 server-side encryption at rest |
| Lifecycle policy | Objects expire after configurable retention period (default 30 days post-event) |
| HTTPS | Enforced for all S3 API calls |

### Negative testing requirement

A negative security test must prove that:

- Cluster A's IAM credentials cannot list Cluster B's bucket
- Cluster A's IAM credentials cannot read objects from Cluster B's bucket
- Cluster A's IAM credentials cannot write objects to Cluster B's bucket
- Cluster A's IAM credentials cannot delete Cluster B's bucket

### Finding

**SCAFFOLDED** --- IAM policy templates and bucket creation automation are
implemented. Requires AWS resources to create actual buckets and run negative
tests.

---

## 6. Pre-commit and CI Security

### Pre-commit hooks

| Hook | Purpose |
|------|---------|
| gitleaks | Scans staged changes for secrets, API keys, and credentials |
| no-commit-to-branch | Prevents direct commits to `main` |
| yamllint | Validates YAML syntax (catches malformed secret references) |
| ansible-lint | Validates Ansible best practices including `no_log` usage |
| check-added-large-files | Prevents accidental commit of large binary files |

### Gitleaks configuration

The `.gitleaks.toml` configuration includes rules for:

- AWS access keys and secret keys
- IBM entitlement keys
- Generic API keys and tokens
- Private keys (RSA, EC, DSA, OpenSSH)
- Passwords in YAML and JSON
- Kubeconfig embedded credentials
- JWT tokens

### CI security jobs

| Job | Description |
|-----|-------------|
| Secret scanning | Runs gitleaks against the full diff on every pull request |
| Dependency scanning | Dependabot configured for Python, GitHub Actions, and Ansible collections |
| YAML schema validation | Validates configuration against JSON Schema (catches embedded secrets) |
| Container image scanning | Planned for release pipeline |

### Finding

**IMPLEMENTED_NOT_TESTED** --- hooks and CI jobs are configured but have not
been exercised against a live CI pipeline with intentional secret injection
tests.

---

## 7. Credential Rotation and Revocation

### Student credentials

| Property | Implementation |
|----------|----------------|
| Generation | Cryptographically secure random generator (`secrets` module) |
| Length | 18 characters (configurable) |
| Character set | Uppercase, lowercase, digits, limited special characters |
| Uniqueness | Per-student unique password; shared passwords disabled by default |
| Storage | Secret provider only; never in Git or logs |
| Rotation | `rotate-student-credentials` command regenerates all passwords |
| Validation | `validate-student-access` confirms authentication after rotation |

### S3 IAM credentials

| Property | Implementation |
|----------|----------------|
| Generation | Per-cluster IAM user with programmatic access key |
| Scope | Bucket-specific IAM policy |
| Rotation | `rotate-credentials` playbook regenerates access keys |
| Revocation | Post-event automation deletes IAM users and access keys |

### Post-event lifecycle

| Step | Action |
|------|--------|
| 1 | Disable all student accounts (remove htpasswd entries) |
| 2 | Revoke all S3 IAM access keys |
| 3 | Delete S3 IAM users |
| 4 | Apply S3 lifecycle policy for data expiration |
| 5 | Revoke temporary kubeconfigs and tokens |
| 6 | Unregister clusters from ACM |
| 7 | Verify cleanup with automated checks |
| 8 | Produce credential revocation report |

### Finding

**IMPLEMENTED_NOT_TESTED** --- credential lifecycle automation is implemented
but requires live clusters and AWS resources to validate the full
create-rotate-revoke cycle.

---

## 8. Findings Summary

| ID | Finding | Severity | Status | Notes |
|----|---------|----------|--------|-------|
| F-01 | Shared passwords allowed in development environment | Medium | Mitigated | Security warning displayed when enabled; blocked in event environment by configuration validation |
| F-02 | Cluster-admin required for MAS installation | Medium | Accepted | Documented IBM requirement; no supported alternative for MAS operator installation |
| F-03 | Static S3 IAM access keys used if IRSA unavailable | Medium | Mitigated | Keys are per-cluster scoped, rotatable, and revoked post-event; IRSA preferred when platform supports it |
| F-04 | Community Keycloak operator used for identity demo | Low | Accepted | Workshop demonstration only; not used for production authentication; documented in production guidance |
| F-05 | Negative security tests not yet executed | High | Open | Blocked on live cluster availability; test playbooks are implemented and ready to run |
| F-06 | No vulnerability scanning of container images yet | Medium | Open | Planned for CI release pipeline; Trivy or equivalent scanner to be integrated |
| F-07 | Break-glass access procedure not tested | Medium | Open | Procedure documented in runbook; requires rehearsal environment to validate |

---

## 9. Recommendations

| Priority | Recommendation | Target phase |
|----------|---------------|--------------|
| 1 | Execute negative security tests on live clusters (F-05) | Phase 7 rehearsal |
| 2 | Integrate container image scanning into CI pipeline (F-06) | Phase 7 |
| 3 | Test break-glass access procedure during rehearsal (F-07) | Phase 7 rehearsal |
| 4 | Validate secret redaction with intentional secret injection in Ansible runs | Phase 7 |
| 5 | Confirm no secrets appear in Kubernetes event streams after MAS installation | Phase 7 |
| 6 | Run S3 negative isolation tests with actual AWS buckets and IAM users | Phase 7 |
| 7 | Verify post-event credential revocation completes without manual intervention | Phase 7 rehearsal |
| 8 | Evaluate IRSA (IAM Roles for Service Accounts) as replacement for static S3 keys | Phase 7 |
| 9 | Add runtime monitoring for unauthorized API calls from attendee accounts | Phase 7 |
| 10 | Conduct facilitator security briefing covering incident response procedures | Pre-event |
