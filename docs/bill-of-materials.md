# Bill of Materials

All tools, dependencies, services, and infrastructure required by the ROSA HCP Multi-Cluster Provisioning system.

> **Last updated:** 2026-07-20

---

## CLI Tools (Operator Workstation)

| Tool | Minimum Version | Purpose | Install |
|---|---|---|---|
| `rosa` | >= 1.2.x | ROSA cluster lifecycle management | `brew install rosa-cli` or [mirror.openshift.com](https://mirror.openshift.com/pub/openshift-v4/clients/rosa/latest/) |
| `aws` | >= 2.x | AWS API operations (STS identity, EC2 queries) | `brew install awscli` or [aws.amazon.com/cli](https://aws.amazon.com/cli/) |
| `ansible-playbook` | >= 2.14 | Playbook execution | `pip install ansible-core` |
| `python3` | >= 3.9 | Filter plugin, test runner | System or `brew install python` |
| `pre-commit` | >= 3.0 | Git hook management | `pip install pre-commit` |
| `ansible-vault` | >= 2.14 | Secret encryption/decryption | Included with `ansible-core` |
| `ansible-lint` | any | Playbook linting | `pip install ansible-lint` |
| `yamllint` | any | YAML linting | `pip install yamllint` |
| `pytest` | any | Unit test runner | `pip install pytest` |

## Python Dependencies (`pyproject.toml`)

| Package | Purpose |
|---|---|
| `ansible-core` | Ansible runtime |
| `ansible-lint` | Playbook linting |
| `yamllint` | YAML validation |
| `pytest` | Unit testing for filter plugin |
| `pre-commit` | Git hook framework |

## Ansible Galaxy Dependencies (`requirements.yml`)

| Collection/Role | Purpose |
|---|---|
| _(none currently)_ | All tasks use `ansible.builtin` modules |

## AWS Services Consumed (Per Cluster Account)

| Service | Usage | Cost Driver |
|---|---|---|
| EC2 | Worker node instances | Instance type x count x hours |
| EBS | Worker node storage | GB provisioned |
| ELB/NLB | Cluster API and app load balancers | Per LB + data processed |
| NAT Gateway | Outbound internet for private subnets | Per hour + data processed |
| Elastic IP | NAT Gateway attachment | Per EIP (free if attached) |
| IAM | Operator roles, OIDC provider | No direct cost |
| VPC | Networking infrastructure | No direct cost (pre-existing) |
| Route 53 | Cluster DNS (if applicable) | Per hosted zone + queries |

## Red Hat Services

| Service | Purpose | Credential |
|---|---|---|
| ROSA (Red Hat OpenShift on AWS) | Managed OpenShift control plane | ROSA offline access token |
| console.redhat.com | Token management, cluster visibility | Red Hat account |
| OCM (OpenShift Cluster Manager) | Backend API for ROSA CLI | Transparent (via ROSA CLI) |

## Infrastructure Prerequisites (Per AWS Account)

| Resource | Requirement | Notes |
|---|---|---|
| VPC | 1 per account | Created by `make setup-infra` |
| Public Subnets | 1 per AZ | Created by `make setup-infra` |
| Private Subnets | >= 2 (multi-AZ) or >= 1 (single-AZ) | Created by `make setup-infra` |
| Internet Gateway | 1 per VPC | Created by `make setup-infra` |
| NAT Gateway | 1 per AZ with private subnets | Created by `make setup-infra` |
| Route Tables | Configured for private subnet → NAT, public subnet → IGW | Created by `make setup-infra` |
| ROSA Enrollment | `rosa init` completed | Created by `make setup-infra` (via `rosa_account_setup` role) |
| Account Roles | HCP account-roles | Created by `make setup-infra` (via `rosa_account_setup` role) |
| Service-Linked Roles | ELB, EFS | Created by `rosa init` |
| EC2 Quota | Sufficient vCPUs for instance type x replicas | Per-account |

## Cost Estimation (Per Workshop)

Assuming 5 seat clusters + 1 hub + 1 facilitator, 8 hours:

| Component | Estimate |
|---|---|
| 7x ROSA HCP control planes | ~$1.68/hr total ($0.24/hr each) |
| 14x m5.large workers (seats, 2 each) | ~$1.34/hr |
| 4x m5.xlarge workers (facilitator, 2 each) | ~$0.77/hr |
| 4x m5.2xlarge workers (hub, 2 each) | ~$1.54/hr |
| 7x NAT Gateways | ~$0.32/hr |
| EBS, ELB, data transfer | ~$0.50/hr |
| **Total (8 hours)** | **~$49** |

*Estimates based on us-east-1 on-demand pricing. Actual costs vary by region and autoscaling activity.*

> **NAT Gateway Cost Warning:** Each NAT gateway costs ~$0.045/hour per gateway per account, and charges accrue for the entire time the gateway exists -- not just during workshop hours. After workshop completion, run `make destroy-infra` to tear down NAT gateways and other infrastructure to avoid ongoing charges.

## Project Files Inventory

```
rosa-hcp-multi-build/
├── ansible.cfg
├── Makefile
├── README.md
├── prompt.md
├── docs/blockers.md
├── pyproject.toml
├── requirements.yml
├── .gitignore
├── .pre-commit-config.yaml
├── .yamllint.yml
├── playbooks/
│   ├── provision.yml
│   ├── destroy.yml
│   ├── status.yml
│   ├── preflight.yml
│   ├── setup-infra.yml
│   └── destroy-infra.yml
├── roles/
│   ├── aws_infra/
│   │   ├── defaults/main.yml
│   │   └── tasks/main.yml
│   ├── rosa_account_setup/
│   │   ├── defaults/main.yml
│   │   └── tasks/main.yml
│   ├── rosa_preflight/
│   │   ├── defaults/main.yml
│   │   └── tasks/main.yml
│   └── rosa_cluster/
│       ├── defaults/main.yml
│       ├── vars/main.yml
│       ├── templates/cluster-report.j2
│       └── tasks/
│           ├── main.yml
│           ├── build_definitions.yml
│           ├── create.yml
│           ├── wait_ready.yml
│           ├── machinepool.yml
│           ├── verify.yml
│           ├── status.yml
│           ├── destroy.yml
│           └── destroy_cleanup.yml
├── plugins/filter/
│   └── cluster_helpers.py
├── group_vars/all/
│   ├── aws_infra_defaults.yml
│   ├── cluster_topology.yml
│   ├── infra_state.yml
│   └── rosa_defaults.yml
├── secrets/
│   ├── .gitkeep
│   ├── rosa-token.yml.example
│   └── cluster-credentials.yml.example
├── tests/
│   ├── test_filters.py
│   ├── test_syntax.sh
│   └── test_variables.yml
├── scripts/
│   ├── generate-credentials-template.sh
│   └── preflight.sh
└── docs/
    ├── architecture.md
    ├── aws-account-prerequisites.md
    ├── bill-of-materials.md
    ├── changelog.md
    ├── configuration-guide.md
    ├── decision-log.md
    ├── implementation-status.md
    ├── known-limitations.md
    ├── risk-register.md
    ├── security-review.md
    ├── teardown-guide.md
    ├── threat-model.md
    ├── troubleshooting.md
    └── workarounds.md
```


---

## Phase 2: MAS World Application Layer


**Status**: DRAFT — Phase 0
**Date**: 2026-07-19

---

## 1. Platform Components

| Component | Version | Channel / Source | Pin Method | Notes |
|-----------|---------|------------------|------------|-------|
| OpenShift Container Platform | 4.21 | Red Hat cluster provisioner | Cluster provisioner controls | MAS 9.1 supports OCP 4.16 -- 4.21; exact version determined by provisioner |
| IBM Maximo Application Suite | 9.1.x | `9.1.x` operator channel | Catalog tag pin | Core + Manage activated |
| IBM MAS Operator Catalog | v9-260625-amd64 | `ibm-operator-catalog` | Specific image tag | Single catalog image pins all IBM operator versions |
| IBM Db2 | 11.5 Standard Edition | Via Db2U operator | MAS-managed lifecycle | Deployed inside each attendee cluster |
| MongoDB | 7.0 or 8.0 Community Edition | In-cluster (MongoDBCommunity) | MAS-managed lifecycle | MAS prerequisites; CE supported for non-production |
| IBM Suite License Service (SLS) | 3.12.x | Bundled with MAS catalog | Catalog tag pin | License-token management |
| cert-manager | Red Hat Certificate Manager Operator | `stable` channel | OLM subscription pin | Replaces community cert-manager; required by MAS |
| Cloud Native PostgreSQL (EDB) | 1.25.x | Bundled with MAS catalog | Catalog tag pin | Used by SLS and internal MAS components |

---

## 2. Red Hat Operators

| Component | Version | Channel | Pin Method | Notes |
|-----------|---------|---------|------------|-------|
| Red Hat Advanced Cluster Management | 2.16 | `release-2.16` | OLM subscription pin | Hub cluster only; manages attendee fleet |
| OpenShift Logging | 6.6 | `stable-6.6` | OLM subscription pin | Log collection via Vector-based collector |
| Loki Operator | 6.6 | `stable-6.6` | OLM subscription pin | LokiStack CR for log storage |
| Cluster Observability Operator | latest stable | `stable` | OLM subscription pin | Metrics and dashboards |
| OpenShift GitOps | 1.21 | `gitops-1.21` | OLM subscription pin | ArgoCD-based fleet configuration |

---

## 3. Workshop Components

| Component | Version / Tag | Source | Pin Method | Notes |
|-----------|---------------|--------|------------|-------|
| RHBK Operator | stable-v26.0 | `redhat-operators` catalog (OLM) | OLM subscription pin | Deploys RHBK (Keycloak 26.x) for identity exercises |
| 389 Directory Server | c9s | `quay.io/389ds/dirsrv` container image | Image tag pin | Backend directory for group-sync exercises |
| Showroom Helm chart | `showroom-single-pod` v2.1.8 | RHDP Helm repository | Chart version pin | Single-pod deployment per attendee |
| Showroom UI theme | `rhdp_showroom_theme` v2.0.3 | quay.io/rhpds | Image tag pin | Standard RHDP branding |
| Showroom content container | `quay.io/rhpds/showroom-content:v1.4.2` | Quay.io | Image tag pin | Antora-rendered content served via nginx |
| Showroom terminal | `quay.io/rhpds/openshift-showroom-terminal-ocp` | Quay.io | Image digest pin | Browser-based terminal; pin to digest for reproducibility |
| Wetty | `quay.io/rhpds/wetty:v2.7.6` | Quay.io | Image tag pin | Web terminal backend |
| Git cloner | `quay.io/rhpds/git-cloner:v1.1.5` | Quay.io | Image tag pin | Init container for content repos |
| Antora builder | `quay.io/rhpds/antora:v1.3.0` | Quay.io | Image tag pin | AsciiDoc site generator |

---

## 4. Automation Tooling

| Component | Version | Source | Notes |
|-----------|---------|--------|-------|
| Python | 3.11+ | System or pyenv | Runtime for CLI tooling and tests |
| ansible-core | 2.17.x | PyPI | Playbook execution engine |
| `ibm.mas_devops` collection | v37.10.0 | Ansible Galaxy | IBM-supported MAS installation roles |
| `kubernetes.core` collection | latest stable | Ansible Galaxy | k8s module, helm module, kubectl |
| `community.general` collection | latest stable | Ansible Galaxy | General-purpose modules |
| `community.crypto` collection | latest stable | Ansible Galaxy | Certificate and key management |
| Pydantic | 2.x | PyPI | Configuration schema validation |
| Click | 8.x | PyPI | CLI framework |
| PyYAML | 6.x | PyPI | YAML parsing |
| boto3 | latest stable | PyPI | AWS SDK for S3 and IAM operations |
| Jinja2 | 3.x | PyPI | Template rendering |

---

## 5. CI/CD and Development Tools

| Tool | Purpose | Source |
|------|---------|--------|
| pre-commit | Git hook framework | PyPI |
| ruff | Python linter and formatter | PyPI |
| yamllint | YAML linting | PyPI |
| ansible-lint | Ansible best-practice linting | PyPI |
| shellcheck | Shell script static analysis | System package |
| gitleaks | Secret scanning in Git history | GitHub releases |
| pytest | Python test framework | PyPI |

---

## 6. Storage Dependencies

| Resource | Type | Configuration | Notes |
|----------|------|---------------|-------|
| AWS S3 | Object storage | Per-cluster buckets (`mas-world-2026-seat-NN-loki-<suffix>`) | AES256 server-side encryption; public-access block enforced |
| `gp3-csi` StorageClass | Block (RWO) | Default StorageClass on AWS clusters | Used by Db2, MongoDB, MAS PVCs |
| `efs` StorageClass | File (RWX) | AWS EFS CSI driver | Used by Maximo Manage for shared file access |

---

## 7. Version Pinning Strategy

Each artifact type uses the pinning method appropriate to its delivery mechanism:

| Artifact Type | Pin Method | Example |
|---------------|------------|---------|
| OLM operators | Subscription channel + `startingCSV` or catalog image tag | `channel: stable-6.6`, catalog `v9-260625-amd64` |
| Container images (critical) | Image digest (`sha256:...`) | Showroom terminal image |
| Container images (standard) | Immutable tag | `wetty:v2.7.6` |
| Helm charts | Chart version | `showroom-single-pod` v2.1.8 |
| Ansible collections | Version constraint in `requirements.yml` | `ibm.mas_devops: "==37.10.0"` |
| Python packages | Version constraint in `pyproject.toml` | `pydantic>=2.0,<3.0` |
| OpenShift platform | Cluster provisioner configuration | OCP 4.21 |

**Event-release rule**: No `latest`, no floating branches, no unpinned channels. Every artifact
referenced in the event release must resolve to a specific, reproducible version.

Digest pins are preferred for images that run in the attendee data path (terminal, Showroom content).
Tag pins are acceptable for build-time tooling where digest tracking adds operational overhead
without meaningful security benefit.

---

## 8. Unverified Versions

The following versions require live-cluster validation before the event release.
See `compatibility-matrix.md` Section 12 for the full verification plan.

| Component | Declared Version | Verification Blocker | Tracking |
|-----------|-----------------|----------------------|----------|
| IBM MAS 9.1.x on OCP 4.21 | 9.1.x | Requires IBM entitlement key and provisioned cluster | `BLOCKED_EXTERNAL_DEPENDENCY` |
| IBM MAS Catalog v9-260625-amd64 | v9-260625-amd64 | Requires IBM entitlement key | `BLOCKED_EXTERNAL_DEPENDENCY` |
| Db2 11.5 with MAS 9.1 on OCP 4.21 | 11.5 | Requires MAS installation | `BLOCKED_EXTERNAL_DEPENDENCY` |
| MongoDB 7.0/8.0 CE with MAS 9.1 | 7.0 / 8.0 | Requires MAS installation | `BLOCKED_EXTERNAL_DEPENDENCY` |
| Loki Operator 6.6 with OCP 4.21 | 6.6 | Requires provisioned cluster | `BLOCKED_EXTERNAL_DEPENDENCY` |
| OpenShift Logging 6.6 with OCP 4.21 | 6.6 | Requires provisioned cluster | `BLOCKED_EXTERNAL_DEPENDENCY` |
| RHACM 2.16 with OCP 4.21 hub | 2.16 | Requires hub cluster | `BLOCKED_EXTERNAL_DEPENDENCY` |
| Keycloak 26.x operator on OCP 4.21 | Community fast | Requires provisioned cluster | `BLOCKED_EXTERNAL_DEPENDENCY` |
| Showroom Helm chart v2.1.8 | v2.1.8 | Requires provisioned cluster | `BLOCKED_EXTERNAL_DEPENDENCY` |

All versions listed above are based on current IBM and Red Hat documentation as of the
document date. They will be confirmed or updated during Phase 2 (reference-cluster validation).
