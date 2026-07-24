# Pre-Event Preparation Runbook -- MAS World 2026

| Field              | Value                                              |
|--------------------|----------------------------------------------------|
| Event              | MAS World 2026                                     |
| Date               | August 17, 2026                                    |
| Timezone           | America/Chicago                                    |
| Max Attendance     | 50                                                 |
| Fleet              | 50 attendee + 5 spare + 1 facilitator clusters     |
| Runbook Owner      | Francis Anyaegbu (Lab Environment Owner)            |
| Last Updated       | YYYY-MM-DD (update on each revision)               |
| Related Runbooks   | `event-morning.md`, `during-event.md`, `post-event.md` |

---

## Document Conventions

- Commands prefixed with `$` are run from the monorepo root (`mas-world-2026-automation/`).
- All `masworld` commands respect the `--environment` flag. When omitted, the active environment from `MASWORLD_ENVIRONMENT` is used. This runbook assumes the `event` environment unless stated otherwise.
- Placeholder values are marked as `PLACEHOLDER_*`. Replace them with actual values from the approved secret provider before execution. Never hard-code secrets into commands, scripts, or configuration files.
- Steps marked **(IDEMPOTENT)** are safe to rerun without side effects.
- Steps marked **(DESTRUCTIVE)** alter state and require the documented rollback procedure if they must be reversed.
- Timing estimates assume reasonable network latency and no upstream outages. Add buffer time for the first execution of each procedure.

---

## Table of Contents

1. [T-30 Days: Infrastructure Readiness and Version Freeze](#t-30-days-infrastructure-readiness-and-version-freeze)
2. [T-14 Days: Reference Cluster and Fleet Preparation](#t-14-days-reference-cluster-and-fleet-preparation)
3. [T-7 Days: Fleet Validation, Student Accounts, and ACM](#t-7-days-fleet-validation-student-accounts-and-acm)
4. [T-3 Days: Rehearsal and Facilitator Walkthrough](#t-3-days-rehearsal-and-facilitator-walkthrough)
5. [T-1 Day: Final Validation and Event Staging](#t-1-day-final-validation-and-event-staging)
6. [Appendix A: Escalation Contacts](#appendix-a-escalation-contacts)
7. [Appendix B: Consolidated Sign-Off Sheet](#appendix-b-consolidated-sign-off-sheet)
8. [Appendix C: Rollback Quick Reference](#appendix-c-rollback-quick-reference)

---

## T-30 Days: Infrastructure Readiness and Version Freeze

**Target date:** July 18, 2026
**Estimated duration:** 4--6 hours
**Owner:** Lab Environment Owner (Francis Anyaegbu)

### Objective

Confirm that all infrastructure dependencies are available, compatible, and version-locked. Freeze component versions for the event release. Verify that secret-provider access, image registries, cloud accounts, and the ACM hub are operational. No cluster modifications are made at this stage.

### Prerequisites

- Monorepo cloned and `masworld` CLI installed per the developer guide.
- AWS credentials configured for the event AWS account (via environment variable or AWS profile).
- IBM entitlement key stored in the secret provider (not on the local filesystem).
- ACM hub cluster provisioned and API-reachable.
- Cluster inventory file (`config/clusters.yaml`) populated with all 56 cluster entries (50 attendee, 5 spare, 1 facilitator).
- All 56 OpenShift clusters provisioned and API-reachable.
- `MASWORLD_ENVIRONMENT=event` exported or passed to every command.

### Procedures

#### 30.1 -- Validate the configuration model

**(IDEMPOTENT)** -- Estimated time: 5 minutes

```bash
$ export MASWORLD_ENVIRONMENT=event
$ masworld config validate
```

Expected output:

```
Configuration validation: PASSED
  Event configuration:      VALID
  Fleet counts:             VALID (50 attendee, 5 spare, 1 facilitator)
  Cluster inventory:        56 clusters defined, 56 enabled
  Credential references:    56/56 resolvable
  Component configuration:  VALID
  Schema validation:        PASSED
  Secret references:        56 cluster refs, 50 student refs, 3 facilitator refs
  Duplicate check:          No duplicates found
```

If validation fails, resolve every reported error before continuing. Do not proceed with a partially valid configuration.

#### 30.2 -- Render and review effective configuration

**(IDEMPOTENT)** -- Estimated time: 10 minutes

```bash
$ masworld config render --redact > /tmp/effective-config-t30.yaml
```

Open `/tmp/effective-config-t30.yaml` and confirm:

- `fleet.attendee_cluster_count` is `50`.
- `fleet.spare_cluster_count` is `5`.
- `fleet.facilitator_cluster_count` is `1`.
- `fleet.preparation.max_concurrent_clusters` is `5`.
- Every component version in the `components` section is pinned (no `latest`, no unqualified `stable` channels).
- All secret references use `secret://` URIs. No inline cleartext values.
- `aws.default_region` matches the provisioned region.
- `student_credentials.allow_shared_password` is `false`.
- `loki.object_storage_mode` is `bucket-per-cluster`.

Distribute the redacted rendering to all three facilitators. Have each facilitator confirm the configuration matches the agreed event plan.

#### 30.3 -- Verify the compatibility matrix

Review `docs/compatibility-matrix.md` against the pinned versions in `config/components.yaml`.

Confirm the following version locks:

| Component              | Pinned Version / Channel        | Source Document                |
|------------------------|---------------------------------|--------------------------------|
| OpenShift              | 4.18 -- 4.22                    | IBM MAS support matrix         |
| MAS                    | 9.1.x                          | IBM MAS release notes          |
| MAS Operator Catalog   | v9-260625-amd64                 | IBM catalog tags               |
| OpenShift Logging      | stable-6.6                      | Red Hat documentation          |
| Loki Operator          | stable-6.6                      | Red Hat documentation          |
| ACM                    | 2.16                            | Red Hat documentation          |
| MongoDB                | 7.0                             | IBM MAS prerequisites          |
| SLS                    | 3.x                             | IBM SLS documentation          |
| Db2                    | 11.5                            | IBM Db2 documentation          |

Action: If any upstream advisory, CVE, or deprecation notice affects a pinned version since the matrix was last reviewed, evaluate the impact. Any version change after T-30 requires explicit sign-off from all three facilitators and must be re-validated against the compatibility matrix.

#### 30.4 -- Verify image registry access

**(IDEMPOTENT)** -- Estimated time: 10 minutes

Test registry access from the reference cluster:

```bash
$ masworld cluster validate seat-01 --checks registry-access
```

This validates pull access to:

- `icr.io/cpopen/` -- IBM operator catalog images
- `registry.redhat.io/` -- Red Hat operator and base images
- `quay.io/` -- community and Red Hat project images

Expected result: all registries return `PASS`.

If a cluster cannot reach a registry, investigate proxy configuration, image-content-source policies, and pull-secret configuration before proceeding. Registry access failures will block all downstream installation stages.

#### 30.5 -- Verify secret-provider connectivity

**(IDEMPOTENT)** -- Estimated time: 5 minutes

```bash
$ masworld config validate --checks secret-provider
```

This confirms that the configured secret provider (AWS Secrets Manager for the event environment) is reachable and that every referenced secret path exists. It does not print or log secret values.

Expected output:

```
Secret provider: aws-sm (us-east-2)
  Cluster admin credentials:  56/56 resolvable
  Student credentials:        50/50 resolvable
  Facilitator credentials:    3/3 resolvable
  IBM entitlement:            resolvable
  AWS S3 credentials:         56/56 resolvable
```

If any reference is unresolvable, coordinate with the platform team to populate the secret store. Do not create placeholder secrets containing dummy values in the production secret provider.

#### 30.6 -- Verify AWS account and S3 access

**(IDEMPOTENT)** -- Estimated time: 5 minutes

```bash
$ masworld config validate --checks aws-access
```

Confirm:

- The automation IAM principal can create, list, and delete S3 buckets with the configured prefix (`mas-world-2026-`).
- The automation IAM principal can create scoped IAM policies for per-cluster S3 access.
- The target AWS region (`us-east-2`) is accessible.
- S3 encryption (AES256) and public-access-block settings are enforceable.
- S3 lifecycle policy for 30-day expiration is creatable.

If any AWS permission is missing, open a request with the cloud infrastructure team immediately. IAM policy changes can take time to propagate.

#### 30.7 -- Pin container images and verify no floating references

**(IDEMPOTENT)** -- Estimated time: 10 minutes

Scan all configuration files for floating image references:

```bash
$ grep -rn "latest" config/ | grep -v "\.md"
$ grep -rn ":stable$" config/ | grep -v "\.md"
```

Expected output: no matches. If any `latest` or bare `stable` references exist, replace them with fully qualified pinned versions and update `docs/compatibility-matrix.md`.

Verify that the MAS catalog image uses an immutable tag:

```bash
$ grep "catalog_tag" config/components.yaml
```

Expected: `catalog_tag: "v9-260625-amd64"` (or the current pinned tag).

#### 30.8 -- Pre-pull critical images on the reference cluster

**(IDEMPOTENT)** -- Estimated time: 30 minutes

```bash
$ masworld cluster prepare seat-01 --stage image-prepull --dry-run
```

Review the dry-run output. Confirm the image list matches the pinned versions. Then execute:

```bash
$ masworld cluster prepare seat-01 --stage image-prepull
```

Record pre-pull results. If any image fails to pull, verify the entitlement key, pull secrets, and network access to the relevant registry before proceeding.

#### 30.9 -- Verify ACM hub health

**(IDEMPOTENT)** -- Estimated time: 5 minutes

```bash
$ masworld cluster validate hub-acm --checks api,health,operators
```

Confirm:

- ACM hub API is reachable.
- `MultiClusterHub` CR is in `Running` phase.
- ACM operator pods are healthy and not in crash loops.
- Search API is responsive.
- Governance framework is operational.
- Sufficient compute capacity exists for managing 56 clusters (review hub node utilization).

#### 30.10 -- Verify DNS and ingress for all clusters

**(IDEMPOTENT)** -- Estimated time: 15 minutes (parallelized across clusters)

```bash
$ masworld fleet validate --checks dns,ingress --max-concurrent 10
```

This confirms that every cluster's API URL resolves via DNS and that the default ingress controller is healthy. Record any failures for immediate remediation with the infrastructure team.

#### 30.11 -- Verify all 56 cluster API endpoints

**(IDEMPOTENT)** -- Estimated time: 10 minutes (parallelized)

```bash
$ masworld fleet validate --checks api --max-concurrent 10
```

Every cluster must return `PASS` for API reachability. Unreachable clusters must be reported to the provisioning team immediately -- replacement clusters take time to provision.

#### 30.12 -- Generate and archive the T-30 baseline report

```bash
$ masworld report fleet-status --format json > reports/t-30-infrastructure-baseline.json
$ masworld report fleet-status --format markdown > reports/t-30-infrastructure-baseline.md
```

Archive both reports. They serve as the baseline for comparison at T-14 and beyond.

### Validation Criteria

All of the following must be true to complete T-30:

- [ ] `masworld config validate` passes with zero errors.
- [ ] Effective configuration rendered, reviewed, and confirmed by all three facilitators.
- [ ] Compatibility matrix reviewed against current upstream documentation.
- [ ] All 56 cluster API endpoints are reachable.
- [ ] Image registry access confirmed on the reference cluster.
- [ ] Secret-provider connectivity confirmed for all secret references.
- [ ] AWS account and S3 access confirmed.
- [ ] ACM hub is healthy with sufficient capacity.
- [ ] DNS and ingress validated for all 56 clusters.
- [ ] No `latest` or floating image tags exist in configuration.
- [ ] Critical images pre-pulled on the reference cluster.
- [ ] T-30 baseline report generated and archived.
- [ ] Version freeze communicated to all facilitators.

### Rollback / Recovery

No destructive actions are taken at T-30. All steps are read-only validation and non-destructive pre-pulls.

- **Cluster unreachable:** Coordinate with the provisioning team for replacement. Update `config/clusters.yaml` with the replacement cluster details and re-run `masworld config validate`.
- **Registry inaccessible:** Check proxy, pull-secret, and network egress configuration. If the registry itself is experiencing an outage, monitor its status page and retry.
- **Secret reference unresolvable:** Populate the missing secret in the secret provider. Do not store the secret value anywhere other than the approved provider.
- **Component version must change:** Update `config/components.yaml`, update `docs/compatibility-matrix.md`, obtain sign-off from all three facilitators, and re-run validation.

### Sign-Off

| Role                         | Name               | Date       | Status         |
|------------------------------|--------------------|------------|----------------|
| Lab Environment Owner        | Francis Anyaegbu   | __________ | PASS / BLOCKED |
| Presenter                    | Ernie Steagall     | __________ | PASS / BLOCKED |
| Observability Lead           | Myles Vivian       | __________ | PASS / BLOCKED |

If any facilitator signs `BLOCKED`, document the blocking issue and the remediation plan before proceeding to T-14.

---

## T-14 Days: Reference Cluster and Fleet Preparation

**Target date:** August 3, 2026
**Estimated duration:** 24--48 hours (fleet preparation runs with controlled concurrency)
**Owner:** Lab Environment Owner (Francis Anyaegbu)

### Objective

Fully prepare and validate one reference cluster through the entire preparation lifecycle. Confirm idempotency by re-running preparation. Once the reference cluster passes all readiness gates, begin fleet-wide preparation with controlled concurrency. By the end of this phase, all 56 clusters should be in `READY` or `PREPARING` state with a clear path to completion.

### Prerequisites

- All T-30 sign-offs complete with no unresolved `BLOCKED` status.
- No outstanding blockers in `docs/blockers.md` that affect cluster preparation.
- Secret provider populated with all required credentials.
- Facilitator agreement on the reference cluster ID (default: `seat-01`).
- Sufficient time allocated for the fleet preparation pipeline to complete (20--40 hours at 5 concurrent).

### Procedures

#### 14.1 -- Prepare the reference cluster

**(IDEMPOTENT)** -- Estimated time: 3--4 hours (MAS installation is the long pole)

First, run a dry-run to review the full preparation plan:

```bash
$ masworld cluster prepare seat-01 --dry-run
```

Review the dry-run output. Confirm that all stages are listed and the component versions match the pinned configuration. Look for any warnings about existing resources or potential conflicts.

Then execute the full preparation:

```bash
$ masworld cluster prepare seat-01
```

This executes the complete preparation lifecycle in order:

1. Configuration validation
2. Cluster preflight (version, capacity, storage, network)
3. ACM registration and label assignment
4. ManagedClusterSet membership
5. MAS prerequisites (MongoDB, SLS, IBM Certificate Manager)
6. MAS Core installation
7. Maximo Manage installation and activation
8. Database configuration and validation
9. OpenShift Logging Operator installation
10. LokiStack deployment
11. S3 bucket creation, encryption, and credential injection
12. ClusterLogForwarder configuration
13. Keycloak deployment and realm configuration
14. Student namespace creation
15. Sample workload staging for exercises
16. Showroom deployment and parameterization

Monitor progress via structured log output. Each stage reports its status upon completion. If a stage fails, the preparation halts at that stage with diagnostic output.

#### 14.2 -- Validate the reference cluster

**(IDEMPOTENT)** -- Estimated time: 15 minutes

```bash
$ masworld cluster validate seat-01
```

Expected output:

```
Cluster: seat-01
Overall Status: READY
Validated At: 2026-08-03T14:00:00Z

Check                        Status
----                         ------
openshift_api                PASS
openshift_console            PASS
mas_core                     PASS
maximo_manage                PASS
database                     PASS
logging_operator             PASS
lokistack                    PASS
cluster_log_forwarder        PASS
s3_write_read                PASS
historical_log_query         PASS
identity                     PASS
showroom                     PASS
runtime_automation           PASS
student_authentication       PASS
student_rbac                 PASS
mas_edge                     NOT_APPLICABLE
```

Every mandatory check must show `PASS` or `NOT_APPLICABLE`. Any `FAIL` or `WARNING` must be resolved before proceeding to fleet preparation.

See [Cluster Repair Procedures](../repair-procedures/) for component-specific troubleshooting.

#### 14.3 -- Confirm idempotency on the reference cluster

**(IDEMPOTENT)** -- Estimated time: 30--60 minutes

Re-run preparation to confirm that a second pass produces no destructive changes and completes cleanly:

```bash
$ masworld cluster prepare seat-01
```

The second run should complete faster (most stages detect existing resources and skip). Validate again:

```bash
$ masworld cluster validate seat-01
```

All checks must still return `PASS`. If any check regresses, investigate the cause before proceeding. A non-idempotent stage must be fixed in the automation before fleet rollout.

#### 14.4 -- Generate the reference cluster report

```bash
$ masworld cluster validate seat-01 --format json > reports/reference-cluster-validation.json
$ masworld cluster validate seat-01 --format markdown > reports/reference-cluster-validation.md
```

Distribute the markdown report to all three facilitators. This is the baseline for what every cluster should look like.

#### 14.5 -- Run negative security tests on the reference cluster

**(IDEMPOTENT)** -- Estimated time: 10 minutes

```bash
$ masworld student validate --cluster seat-01 --include-negative-tests
```

This validates that the student account on `seat-01`:

- Can authenticate successfully.
- Can access the assigned student namespace (`student-01`).
- Cannot access other student namespaces (`student-02`, `student-03`, etc.).
- Cannot access ACM administration resources.
- Is not bound to `cluster-admin`.
- Cannot retrieve secrets in protected namespaces.
- Cannot modify cluster-scoped operators.

Every negative test must return the expected denial. Any unexpected access is a security defect that must be resolved before fleet preparation.

#### 14.6 -- Begin fleet preparation

**(IDEMPOTENT, LONG-RUNNING)** -- Estimated time: 20--40 hours for 55 remaining clusters

Start with conservative concurrency to detect systemic issues early:

```bash
$ masworld fleet prepare --max-concurrent 3
```

Monitor the fleet preparation dashboard in a separate terminal:

```bash
$ masworld report fleet-status
```

Expected output during initial preparation:

```
Fleet Status: PREPARING
  Ready:       1
  Preparing:   3
  Pending:     52
  Failed:      0
  Total:       56
```

After the first batch of 3 clusters completes successfully (all `READY`), increase concurrency to the configured maximum:

```bash
$ masworld fleet prepare --max-concurrent 5
```

If any cluster fails during the first batch, do not increase concurrency. Investigate the failure first.

#### 14.7 -- Handle preparation failures

If a cluster fails during fleet preparation:

1. Review the per-cluster log:
   ```bash
   $ cat logs/clusters/CLUSTER_ID/prepare.log
   ```

2. Determine whether the failure is cluster-specific or systemic:
   - **Cluster-specific** (hardware, configuration, pre-existing conflict): Repair and retry individually:
     ```bash
     $ masworld cluster repair CLUSTER_ID --component FAILED_COMPONENT
     $ masworld cluster prepare CLUSTER_ID
     ```
   - **Systemic** (registry throttling, secret-provider outage, API rate limits): Reduce concurrency, wait for the upstream issue to resolve, and retry:
     ```bash
     $ masworld fleet prepare --max-concurrent 2
     ```

3. If a cluster fails 3 consecutive preparation attempts and cannot be repaired:
   - Mark it as failed in the inventory (`enabled: false`).
   - Request a replacement cluster from the provisioning team.
   - Add the replacement to `config/clusters.yaml`.
   - Run `masworld config validate` after updating the inventory.
   - Prepare the replacement:
     ```bash
     $ masworld cluster prepare REPLACEMENT_CLUSTER_ID
     ```

#### 14.8 -- Monitor for API and registry throttling

During fleet preparation, watch the structured logs for throttling indicators:

- **AWS API throttling:** `ThrottlingException` or `TooManyRequestsException` in S3/IAM/Secrets Manager calls.
- **IBM registry rate limits:** `429 Too Many Requests` or `TOOMANYREQUESTS` from `icr.io`.
- **Red Hat registry rate limits:** `429` responses from `registry.redhat.io`.
- **OpenShift API server overload:** `429` or `503` responses from any cluster API.
- **ACM hub throttling:** Slow or failed import operations.

If throttling is detected:

```bash
# Reduce concurrency immediately
$ masworld fleet prepare --max-concurrent 2
```

Record throttling incidents. If persistent, adjust the retry backoff in `config/defaults.yaml`:

```yaml
fleet:
  preparation:
    max_concurrent_clusters: 3    # reduced from 5
    retry_backoff_base_seconds: 60  # increased from 30
```

#### 14.9 -- Track fleet preparation progress

Run status checks every 1--2 hours during active preparation:

```bash
$ masworld report fleet-status
```

Target: all 56 clusters in `READY` state by August 7 (T-10). This provides a 3-day buffer before the T-7 milestone.

Generate a progress report at the end of each day:

```bash
$ masworld report fleet-status --format markdown > reports/fleet-preparation-progress-$(date +%Y%m%d).md
```

### Validation Criteria

- [ ] Reference cluster (`seat-01`) passes all mandatory readiness checks.
- [ ] Reference cluster preparation is confirmed idempotent (second run clean).
- [ ] Reference cluster negative security tests pass.
- [ ] Reference cluster report distributed to all facilitators.
- [ ] Fleet preparation initiated with controlled concurrency.
- [ ] No systemic failures blocking fleet preparation.
- [ ] Throttling thresholds identified and concurrency adjusted if needed.
- [ ] Progress tracked and reported to facilitators daily.
- [ ] Failed clusters documented with repair or replacement plans.

### Rollback / Recovery

- **Reference cluster preparation failure:** Review stage-level logs. Fix the root cause and rerun `masworld cluster prepare seat-01`. The command resumes from the last incomplete stage.
- **Fleet-wide systemic failure:** Halt preparation (Ctrl+C is safe -- the tool checkpoints per cluster). Fix the systemic issue. Rerun `masworld fleet prepare` to resume all incomplete clusters.
- **Unrecoverable cluster:** Set `enabled: false` in `config/clusters.yaml`, add the replacement cluster entry, run `masworld config validate`, then prepare the replacement.
- **Component version issue discovered:** If a version must change after T-30, update `config/components.yaml`, update `docs/compatibility-matrix.md`, obtain facilitator sign-off, re-validate the reference cluster, and re-prepare any affected fleet clusters.

### Sign-Off

| Role                         | Name               | Date       | Status         |
|------------------------------|--------------------|------------|----------------|
| Lab Environment Owner        | Francis Anyaegbu   | __________ | PASS / BLOCKED |

T-14 requires only the Lab Environment Owner sign-off. The reference cluster report is distributed to all facilitators for awareness, but fleet preparation is an operational responsibility.

---

## T-7 Days: Fleet Validation, Student Accounts, and ACM

**Target date:** August 10, 2026
**Estimated duration:** 6--8 hours
**Owner:** Lab Environment Owner (Francis Anyaegbu), with Presenter (Ernie Steagall) for ACM verification

### Objective

Complete fleet preparation if any clusters remain. Validate all 56 clusters. Create and validate student accounts. Rotate credentials. Configure ACM policies and fleet metadata. Verify S3 isolation. Assign all 50 seats. Ensure the entire fleet is in `READY` state with validated student access.

### Prerequisites

- T-14 sign-off complete.
- Fleet preparation substantially complete (target: 56/56 clusters `READY`).
- Secret provider fully populated with all student and facilitator credential references.

### Procedures

#### 7.1 -- Complete any remaining fleet preparation

**(IDEMPOTENT)** -- Estimated time: varies

```bash
$ masworld fleet prepare --max-concurrent 5
```

If any clusters remain in `FAILED` state, repair individually:

```bash
$ masworld cluster repair CLUSTER_ID
$ masworld cluster prepare CLUSTER_ID
```

Continue until `masworld report fleet-status` shows all 56 clusters as `READY`, or a documented and accepted exception exists (e.g., a cluster being replaced by the provisioning team).

#### 7.2 -- Validate the full fleet

**(IDEMPOTENT)** -- Estimated time: 30--45 minutes (parallelized)

```bash
$ masworld fleet validate --max-concurrent 10 --format json > reports/fleet-validation-t7.json
$ masworld fleet validate --max-concurrent 10 --format markdown > reports/fleet-validation-t7.md
```

Review the markdown report. Every attendee and spare cluster must pass all mandatory checks with `PASS` or `NOT_APPLICABLE`. The facilitator cluster may have intentional configuration differences that are documented as expected.

Distribute the report to all facilitators.

#### 7.3 -- Create student accounts on all attendee clusters

**(IDEMPOTENT)** -- Estimated time: 15 minutes

```bash
$ masworld student create --all-attendee-clusters
```

This creates one student account per attendee cluster using the `attendee-default` credential profile:

- Usernames: `user01` through `user50` (generated from `username_template`)
- Passwords: cryptographically generated, 18 characters each
- Storage: each password stored in the configured secret provider at the path defined by `secret_ref_template`
- Identity provider: htpasswd configured on each cluster
- Namespace: `student-01` through `student-50`, each with `admin` role
- Cluster role: `basic-user` (not `cluster-admin`)
- Isolation: access restricted to own namespace only

Verify account creation across the fleet:

```bash
$ masworld student validate --all-attendee-clusters
```

Expected output:

```
Student Account Validation:
  seat-01 | user01 | Auth: PASS | Namespace: PASS | RBAC: PASS | Isolation: PASS
  seat-02 | user02 | Auth: PASS | Namespace: PASS | RBAC: PASS | Isolation: PASS
  ...
  seat-50 | user50 | Auth: PASS | Namespace: PASS | RBAC: PASS | Isolation: PASS

Summary: 50/50 PASS
```

Every cluster must show `PASS` for all four categories. Any failure must be resolved before proceeding.

#### 7.4 -- Create facilitator accounts

**(IDEMPOTENT)** -- Estimated time: 5 minutes

Create facilitator accounts on the facilitator cluster:

```bash
$ masworld student create --profile facilitator --cluster facilitator-01
```

Facilitator accounts use the `facilitator` credential profile with `cluster-admin` access and 24-character generated passwords.

Validate facilitator access:

```bash
$ masworld student validate --profile facilitator --cluster facilitator-01
```

Optionally, create facilitator support accounts on attendee clusters if direct support access is required during the event:

```bash
$ masworld student create --profile facilitator --all-attendee-clusters
```

#### 7.5 -- Rotate all credentials (initial rotation)

**(DESTRUCTIVE -- invalidates any previously generated passwords)** -- Estimated time: 15 minutes

Generate fresh passwords for all student and facilitator accounts:

```bash
$ masworld student rotate --all-attendee-clusters
$ masworld student rotate --profile facilitator --cluster facilitator-01
```

After rotation, validate that the new credentials work:

```bash
$ masworld student validate --all-attendee-clusters
$ masworld student validate --profile facilitator --cluster facilitator-01
```

**Rollback:** If rotation fails partway through, rerun `masworld student rotate` for the affected clusters. The operation is designed to be resumable. If a specific cluster's htpasswd update fails:

```bash
$ masworld cluster repair CLUSTER_ID --component identity
$ masworld student rotate --cluster CLUSTER_ID
$ masworld student validate --cluster CLUSTER_ID
```

#### 7.6 -- Verify ACM registration and labels

**(IDEMPOTENT)** -- Estimated time: 10 minutes

Confirm all clusters are registered with the ACM hub and carry correct labels:

```bash
$ masworld cluster validate hub-acm --checks managed-clusters,labels
```

Expected labels on each managed cluster:

```yaml
event: mas-world-2026
workload: maximo
environment: workshop
seat: "NN"              # varies per cluster (01-50 for attendee, spare-01 etc.)
purpose: attendee        # or: spare, facilitator
logging: enabled
idp: preconfigured
readiness: ready
```

If labels are missing or incorrect on any cluster:

```bash
$ masworld cluster prepare CLUSTER_ID --stage acm-registration
```

#### 7.7 -- Deploy ACM governance policies

**(IDEMPOTENT)** -- Estimated time: 10 minutes

```bash
$ masworld cluster prepare hub-acm --stage acm-policies
```

This deploys the baseline governance policy hierarchy:

```
policy-mas-world-baseline
  - verify-mas-namespace
  - verify-logging-operator
  - verify-lokistack
  - verify-cluster-log-forwarder
  - verify-mas-edge
  - enforce-event-marker
```

Validate policy deployment and compliance:

```bash
$ masworld cluster validate hub-acm --checks policies,compliance
```

Expected output:

```
ACM Policy Compliance:
  policy-mas-world-baseline:
    verify-mas-namespace ........... 56/56 Compliant
    verify-logging-operator ........ 56/56 Compliant
    verify-lokistack ............... 56/56 Compliant
    verify-cluster-log-forwarder ... 56/56 Compliant
    verify-mas-edge ................ N/A (component disabled)
    enforce-event-marker ........... 56/56 Compliant

Overall: COMPLIANT
```

All 56 clusters should be compliant at this point. The intentional drift for the ACM demo is staged at T-1, not now.

#### 7.8 -- Verify S3 isolation (cross-cluster security test)

**(IDEMPOTENT)** -- Estimated time: 20 minutes (parallelized)

This is a critical security validation. Run the S3 cross-account isolation test to prove that one cluster's Loki credentials cannot access another cluster's S3 bucket:

```bash
$ masworld fleet validate --checks s3-isolation --max-concurrent 5
```

The test performs pairwise cross-access attempts using each cluster's scoped IAM credentials against other clusters' buckets. Every cross-access attempt must return `ACCESS_DENIED`.

Expected output:

```
S3 Isolation Validation:
  Cross-access tests: 2970 pairs tested
  Results: 2970/2970 correctly DENIED
  Overall: PASS
```

If any cross-access test returns a result other than `ACCESS_DENIED`, this is a **critical security defect**. Do not proceed. Investigate the IAM policy for the affected cluster, correct the bucket policy, and rerun the test. Escalate to the platform security contact if the root cause is not immediately clear.

#### 7.9 -- Verify the historical log query exercise

**(IDEMPOTENT)** -- Estimated time: 30 minutes

Validate the observability exercise end to end on a sample of 3--5 clusters:

```bash
$ masworld exercise reset seat-01 --module observability
$ masworld cluster validate seat-01 --checks historical-log-query

$ masworld exercise reset seat-25 --module observability
$ masworld cluster validate seat-25 --checks historical-log-query

$ masworld exercise reset seat-50 --module observability
$ masworld cluster validate seat-50 --checks historical-log-query
```

For each cluster, confirm that:

1. The sample logging workload can be deployed.
2. Logs are ingested by the Vector collector and forwarded to Loki via S3.
3. The workload can be deleted.
4. The workload can be recreated with a new run ID.
5. Historical logs from the first run remain queryable in Loki.
6. The exercise does not interfere with MAS or other cluster workloads.

#### 7.10 -- Assign seats

**(IDEMPOTENT per seat)** -- Estimated time: 10 minutes

Assign the 50 attendee clusters to seats:

```bash
$ for i in $(seq -w 1 50); do
    masworld seat assign --seat $i --cluster seat-$i
  done
```

Verify the seat map:

```bash
$ masworld seat export-map --format markdown > reports/seat-map-t7.md
$ masworld seat export-map --format json > reports/seat-map-t7.json
$ masworld seat export-map --format csv > reports/seat-map-t7.csv
```

Review the seat map and confirm:

- Every seat (1--50) has exactly one cluster assigned.
- No cluster is assigned to multiple seats.
- All 50 assigned clusters are in `READY` state.
- Spare clusters (`spare-01` through `spare-05`) are unassigned and available.
- The facilitator cluster (`facilitator-01`) is not assigned to a seat.

```bash
$ masworld report seat-report
```

#### 7.11 -- Generate the T-7 fleet status report

```bash
$ masworld report fleet-status --format markdown > reports/fleet-status-t7.md
$ masworld report seat-report --format markdown > reports/seat-report-t7.md
```

Distribute both reports to all facilitators.

### Validation Criteria

- [ ] All 56 clusters pass `masworld fleet validate` with no mandatory failures.
- [ ] Student accounts created and validated on all 50 attendee clusters (auth, namespace, RBAC, isolation all PASS).
- [ ] Facilitator accounts created and validated.
- [ ] Student credentials rotated and re-validated post-rotation.
- [ ] ACM labels correct on all 56 managed clusters.
- [ ] ACM governance policies deployed and all 56 clusters showing `Compliant`.
- [ ] S3 isolation test passes -- no cross-cluster access (2970/2970 denied).
- [ ] Historical log query exercise validated on 3 or more sample clusters.
- [ ] All 50 seats assigned to attendee clusters.
- [ ] 5 spare clusters available, unassigned, and `READY`.
- [ ] Seat map exported in markdown, JSON, and CSV formats and reviewed.
- [ ] Fleet status and seat reports generated and distributed.

### Rollback / Recovery

- **Student account creation failure on a single cluster:**
  ```bash
  $ masworld cluster repair CLUSTER_ID --component identity
  $ masworld student create --cluster CLUSTER_ID
  $ masworld student validate --cluster CLUSTER_ID
  ```

- **ACM policy deployment failure:**
  Review ACM hub logs. Rerun policy deployment:
  ```bash
  $ masworld cluster prepare hub-acm --stage acm-policies
  $ masworld cluster validate hub-acm --checks policies,compliance
  ```

- **Cluster drops to FAILED after previously being READY:**
  Run full validation to identify the regression:
  ```bash
  $ masworld cluster validate CLUSTER_ID
  ```
  Repair the failed component and revalidate. If unrecoverable after 3 repair attempts, replace with a spare:
  ```bash
  $ masworld seat replace --seat N --cluster spare-XX
  $ masworld student create --cluster spare-XX
  $ masworld student validate --cluster spare-XX
  ```

- **S3 isolation test failure:**
  This is a critical security finding. Do not proceed. Investigate the IAM policy and S3 bucket policy for the affected cluster. Ensure each cluster's credentials are scoped to only its own bucket. Escalate to the platform security contact if the root cause is unclear.

- **Seat assignment error (wrong cluster):**
  ```bash
  $ masworld seat unassign --seat N
  $ masworld seat assign --seat N --cluster CORRECT_CLUSTER_ID
  ```

### Sign-Off

| Role                         | Name               | Date       | Status         |
|------------------------------|--------------------|------------|----------------|
| Lab Environment Owner        | Francis Anyaegbu   | __________ | PASS / BLOCKED |
| Presenter                    | Ernie Steagall     | __________ | PASS / BLOCKED |
| Observability Lead           | Myles Vivian       | __________ | PASS / BLOCKED |

---

## T-3 Days: Rehearsal and Facilitator Walkthrough

**Target date:** August 14, 2026
**Estimated duration:** 4--6 hours
**Owner:** All three facilitators

### Objective

Execute a full end-to-end rehearsal of the workshop on a representative subset of clusters. All three facilitators walk through every module, exercise, validation, solve, and reset procedure. Validate timing. Test support workflows including spare cluster replacement. Identify and document any content, automation, or timing issues.

### Prerequisites

- All T-7 sign-offs complete with no unresolved `BLOCKED` status.
- All 56 clusters in `READY` state.
- All student and facilitator accounts created and validated.
- ACM policies deployed and all clusters compliant.
- All three facilitators available for a 4--6 hour continuous rehearsal block.
- Each facilitator has the `masworld` CLI installed and configured on their workstation.

### Procedures

#### 3.1 -- Select rehearsal clusters

Use a small subset of clusters for the rehearsal. Do not use all 50 attendee clusters -- preserve their clean state for the event.

Recommended rehearsal set:

| Facilitator        | Role in rehearsal          | Cluster         |
|--------------------|----------------------------|-----------------|
| Ernie Steagall     | Presenter view             | `facilitator-01`|
| Francis Anyaegbu   | Attendee experience        | `seat-01`       |
| Myles Vivian       | Attendee experience        | `seat-02`       |

#### 3.2 -- Pre-rehearsal fleet check

**(IDEMPOTENT)** -- Estimated time: 5 minutes

```bash
$ masworld fleet validate --format text
$ masworld report fleet-status
```

Confirm all 56 clusters are `READY`. If any cluster is not ready, repair it before starting the rehearsal.

#### 3.3 -- Reset all exercises on rehearsal clusters

**(IDEMPOTENT)** -- Estimated time: 5 minutes

```bash
$ for cluster in seat-01 seat-02; do
    for module in navigation acm updates observability identity; do
      masworld exercise reset $cluster --module $module
    done
  done
```

Confirm clean state:

```bash
$ masworld cluster validate seat-01
$ masworld cluster validate seat-02
```

#### 3.4 -- Rehearse Module 1: Navigation and Search (target: 10 minutes)

**Start the timer.**

**Presenter (Ernie):** Share screen showing `facilitator-01`. Present the introductory slide. Demonstrate Maximo navigation, search, and key UI areas.

**Attendees (Francis, Myles):** Follow along on `seat-01` and `seat-02` respectively, using the Showroom instructions as a real attendee would.

After completing the exercise, validate:

```bash
$ masworld cluster validate seat-01 --checks navigation-exercise
$ masworld cluster validate seat-02 --checks navigation-exercise
```

Test the solve automation (simulate a stuck attendee):

```bash
$ masworld exercise reset seat-01 --module navigation
# Then run the solve path per Showroom instructions
```

**Record timing:** ______ minutes (target: 10 minutes)

#### 3.5 -- Rehearse Module 2: ACM Fleet Management (target: 10 minutes)

**Start the timer.**

**Presenter (Ernie):** Demonstrate from the ACM hub console on `facilitator-01`.

Walk through the full ACM demo flow:

1. Show the fleet inventory -- all clusters visible in ACM.
2. Demonstrate cluster labels and ManagedClusterSet.
3. Run an ACM Search query across managed clusters.
4. Show the governance policy dashboard.
5. Highlight the deliberately noncompliant facilitator cluster (staged at T-7 or staged now for rehearsal).
6. Show the drift condition detail (event marker ConfigMap absent).
7. Remediate the drift (either enforce mode or manual action).
8. Show the return to full compliance.
9. Transition narrative into the logging lab.

If drift is not yet staged on `facilitator-01` (it is formally staged at T-1), stage it temporarily for rehearsal:

```bash
$ masworld cluster prepare facilitator-01 --stage acm-drift-staging
```

**Attendees (Francis, Myles):** Verify the propagated event marker or policy result on their own clusters per the Showroom instructions.

Validate the ACM demo state:

```bash
$ masworld cluster validate hub-acm --checks policies,compliance,drift-staging
```

**Record timing:** ______ minutes (target: 10 minutes)

#### 3.6 -- Rehearse Module 3: Updates (target: 20 minutes)

**Start the timer.**

**Presenter (Ernie):** Present the introductory slide. Demonstrate the update exercise from the Showroom content.

**Attendees (Francis, Myles):** Execute the bounded update exercise on their clusters, following the Showroom instructions exactly as written.

Validate after completion:

```bash
$ masworld cluster validate seat-01 --checks updates-exercise
$ masworld cluster validate seat-02 --checks updates-exercise
```

Test the solve automation:

```bash
# Simulate a failed exercise state, then run solve
```

Test the reset automation:

```bash
$ masworld exercise reset seat-01 --module updates
$ masworld exercise reset seat-02 --module updates
```

Confirm the cluster returns to a clean exercise-ready state after reset.

**Record timing:** ______ minutes (target: 20 minutes)

#### 3.7 -- Rehearse Module 4: Observability and Logging (target: ~20 minutes of the 40-minute segment)

**Start the timer.**

**Myles leads this section.**

Execute the full observability exercise on `seat-01` and `seat-02`:

1. Deploy the sample logging workload with a unique run ID and seat ID.
2. Verify logs appear in the Loki query interface.
3. Delete the sample workload.
4. Redeploy the sample workload with a new run ID.
5. Query Loki for historical logs from the first run. Confirm they are still present.
6. Explore the Loki query interface (label selectors, time ranges, grep).

Validate:

```bash
$ masworld cluster validate seat-01 --checks logging-operator,lokistack,cluster-log-forwarder,s3-write-read,historical-log-query
$ masworld cluster validate seat-02 --checks logging-operator,lokistack,cluster-log-forwarder,s3-write-read,historical-log-query
```

Test the solve automation for a stuck attendee.

Test the reset automation:

```bash
$ masworld exercise reset seat-01 --module observability
$ masworld exercise reset seat-02 --module observability
```

**Record timing:** ______ minutes (target: ~20 minutes)

#### 3.8 -- Rehearse Module 5: Identity Integration (target: ~20 minutes of the 40-minute segment)

**Start the timer.**

Execute the identity exercise on `seat-01` and `seat-02`:

1. Inspect the preconfigured Keycloak client (sanitized view -- no admin credentials exposed to attendees).
2. Inspect OAuth server integration on the cluster.
3. Review secret references and identity mappings.
4. Test the OIDC authentication flow.
5. Inspect the LDAP group-sync configuration.
6. Run the bounded group-sync demonstration (where supported on the platform).
7. Validate resulting group membership.

Validate:

```bash
$ masworld cluster validate seat-01 --checks identity
$ masworld cluster validate seat-02 --checks identity
```

Test the solve and reset automation:

```bash
$ masworld exercise reset seat-01 --module identity
$ masworld exercise reset seat-02 --module identity
```

Note any HCP OAuth limitations encountered during the exercise. Confirm these are clearly documented in the Showroom content.

**Record timing:** ______ minutes (target: ~20 minutes)

#### 3.9 -- Test spare cluster replacement

**(DESTRUCTIVE -- temporarily reassigns a seat)** -- Estimated time: 10 minutes

Simulate a mid-event cluster failure and replacement:

```bash
# Show current assignment for seat 2
$ masworld seat show --seat 2

# Replace seat 2 with a spare
$ masworld seat replace --seat 2 --cluster spare-01
```

Verify the replacement:

```bash
$ masworld seat show --seat 2
$ masworld student validate --cluster spare-01
$ masworld cluster validate spare-01
```

Confirm that:

- The previous cluster (`seat-02`) is marked quarantined in the inventory.
- The spare (`spare-01`) is now assigned to seat 2.
- Student credentials work on the spare cluster.
- Showroom is accessible and correctly parameterized on the spare.
- Maximo is accessible on the spare.
- The OpenShift console is accessible on the spare.

After testing, restore the original assignment:

```bash
$ masworld seat replace --seat 2 --cluster seat-02
```

Verify restoration:

```bash
$ masworld seat show --seat 2
$ masworld student validate --cluster seat-02
$ masworld report seat-report
```

Confirm that `spare-01` is returned to the unassigned spare pool and `seat-02` is active again.

#### 3.10 -- Test concurrent browser terminal access

Have all three facilitators simultaneously:

1. Open Showroom on their assigned rehearsal cluster.
2. Open the browser terminal tab.
3. Run a basic command (e.g., `oc whoami`).
4. Open the OpenShift console tab.
5. Open the Maximo tab.
6. Navigate through 2--3 Showroom module pages.
7. Copy and paste a command from the Showroom instructions into the browser terminal.

Confirm:

- Browser terminal loads within 10 seconds and is responsive.
- `oc` CLI is authenticated as the student user (`user01`, `user02`).
- OpenShift console tab loads the cluster-specific console.
- Maximo tab loads the cluster-specific Maximo URL.
- Commands from Showroom instructions execute correctly.
- No cross-contamination between facilitator sessions.

#### 3.11 -- Test exercise reset across all modules

**(IDEMPOTENT)** -- Estimated time: 5 minutes

```bash
$ for module in navigation acm updates observability identity; do
    masworld exercise reset seat-01 --module $module
    masworld exercise reset seat-02 --module $module
  done
```

After reset, validate that the clusters return to a clean, exercise-ready state:

```bash
$ masworld cluster validate seat-01
$ masworld cluster validate seat-02
```

All checks must still return `PASS`.

#### 3.12 -- Review timing and adjust content

After the rehearsal, compile the recorded timings:

| Module                       | Target   | Actual   | Delta   | Status          |
|------------------------------|----------|----------|---------|-----------------|
| Navigation and Search        | 10 min   | ____ min | ____ min | OK / OVER / UNDER |
| ACM Fleet Management         | 10 min   | ____ min | ____ min | OK / OVER / UNDER |
| Updates                      | 20 min   | ____ min | ____ min | OK / OVER / UNDER |
| Observability and Logging    | ~20 min  | ____ min | ____ min | OK / OVER / UNDER |
| Identity Integration         | ~20 min  | ____ min | ____ min | OK / OVER / UNDER |
| **Total**                    | ~80 min  | ____ min | ____ min |                 |

Guidelines:

- If any module exceeds its target by more than 30%, discuss content reduction with all three facilitators.
- If any module completes in under 50% of its target, consider adding depth or discussion points.
- Record all timing decisions in `docs/decision-log.md`.

#### 3.13 -- Document rehearsal findings

Record all findings from the rehearsal:

| ID  | Description               | Severity          | Owner       | Status          |
|-----|---------------------------|--------------------|-------------|-----------------|
| R01 | (example) Loki query UI label is misleading | MEDIUM | Myles | OPEN |
| R02 | (example) ACM search query in step 3 returns extra results | LOW | Francis | OPEN |

Severity levels:

- **CRITICAL:** Blocks the event. Must be resolved before T-1.
- **HIGH:** Degrades the attendee experience significantly. Should be resolved before T-1.
- **MEDIUM:** Minor issue. Resolve if time permits, otherwise document as known limitation.
- **LOW:** Cosmetic or minor. Resolve after the event.

All CRITICAL and HIGH findings must have an assigned owner and a resolution plan.

#### 3.14 -- Clean up rehearsal state

Reset all exercises on rehearsal clusters to leave them clean:

```bash
$ for cluster in seat-01 seat-02; do
    for module in navigation acm updates observability identity; do
      masworld exercise reset $cluster --module $module
    done
  done
```

If ACM drift was staged on `facilitator-01` for the rehearsal, remove it (it will be formally staged at T-1):

```bash
$ masworld exercise reset facilitator-01 --module acm
```

Confirm clean state:

```bash
$ masworld cluster validate seat-01
$ masworld cluster validate seat-02
$ masworld cluster validate facilitator-01
$ masworld report seat-report
```

### Validation Criteria

- [ ] All three facilitators participated in the complete rehearsal.
- [ ] Every workshop module was executed end to end through the Showroom interface.
- [ ] Every module's validation automation ran successfully.
- [ ] Every module's solve automation ran successfully.
- [ ] Every module's reset automation ran successfully and left the cluster clean.
- [ ] Spare cluster replacement tested and verified (assign, validate, restore).
- [ ] Concurrent browser terminal access confirmed for 3 simultaneous users.
- [ ] Showroom content, tabs, and commands verified by all facilitators.
- [ ] Module timing recorded and within acceptable bounds (no module exceeds target by >30%).
- [ ] All rehearsal findings documented with severity, owner, and status.
- [ ] All CRITICAL findings have a resolution plan with target date (before T-1).
- [ ] Rehearsal state cleaned up on all used clusters.

### Rollback / Recovery

- **Rehearsal cluster left in dirty state:**
  ```bash
  $ for module in navigation acm updates observability identity; do
      masworld exercise reset CLUSTER_ID --module $module
    done
  $ masworld cluster validate CLUSTER_ID
  ```

- **Spare cluster consumed during rehearsal testing:**
  Restore the original assignment:
  ```bash
  $ masworld seat replace --seat N --cluster ORIGINAL_CLUSTER_ID
  ```
  Verify the spare is returned to the unassigned pool:
  ```bash
  $ masworld report seat-report
  ```

- **ACM drift not cleaned up after rehearsal:**
  ```bash
  $ masworld exercise reset facilitator-01 --module acm
  $ masworld cluster validate hub-acm --checks compliance
  ```

### Sign-Off

| Role                         | Name               | Date       | Status         |
|------------------------------|--------------------|------------|----------------|
| Lab Environment Owner        | Francis Anyaegbu   | __________ | PASS / BLOCKED |
| Presenter                    | Ernie Steagall     | __________ | PASS / BLOCKED |
| Observability Lead           | Myles Vivian       | __________ | PASS / BLOCKED |

All three facilitators must sign off on the rehearsal. If any facilitator signs `BLOCKED`, the blocking issue must be resolved before proceeding to T-1.

---

## T-1 Day: Final Validation and Event Staging

**Target date:** August 16, 2026
**Estimated duration:** 3--4 hours
**Owner:** Lab Environment Owner (Francis Anyaegbu)

### Objective

Perform final end-to-end fleet validation. Resolve any remaining rehearsal findings. Rotate credentials one final time. Generate the production attendee access cards. Stage the ACM drift condition for the live demonstration. Reset all exercises to clean state. Freeze all changes. Confirm event readiness with an explicit go/no-go decision.

### Prerequisites

- All T-3 sign-offs complete with no unresolved `BLOCKED` status.
- All CRITICAL rehearsal findings resolved and verified.
- All HIGH rehearsal findings resolved or accepted as known limitations with documented workarounds.
- All 56 clusters in `READY` state.
- All three facilitators available for the go/no-go decision.

### Procedures

#### 1.1 -- Revalidate the full fleet

**(IDEMPOTENT)** -- Estimated time: 30--45 minutes

```bash
$ masworld fleet validate --max-concurrent 10 --format json > reports/fleet-validation-final.json
$ masworld fleet validate --max-concurrent 10 --format markdown > reports/fleet-validation-final.md
```

Review the report. Every attendee and spare cluster must pass all mandatory checks with `PASS` or `NOT_APPLICABLE`. Zero `FAIL` results are acceptable at this stage.

Compare with the T-7 validation report to identify any regressions:

```bash
$ diff reports/fleet-validation-t7.md reports/fleet-validation-final.md
```

If any cluster has regressed:

1. Identify the failed check and investigate root cause.
2. Attempt repair:
   ```bash
   $ masworld cluster repair CLUSTER_ID --component FAILED_COMPONENT
   $ masworld cluster validate CLUSTER_ID
   ```
3. If repair fails and the cluster is assigned to a seat, replace with a spare:
   ```bash
   $ masworld seat replace --seat N --cluster spare-XX
   $ masworld student create --cluster spare-XX
   $ masworld student validate --cluster spare-XX
   $ masworld cluster validate spare-XX
   ```
4. Document the replacement in the event log.
5. After any replacements, confirm that at least 2 spare clusters remain available. Fewer than 2 spares is a risk that must be discussed during the go/no-go decision.

#### 1.2 -- Rotate student credentials (final rotation)

**(DESTRUCTIVE -- invalidates all previous passwords)** -- Estimated time: 15 minutes

This is the final credential rotation before the event. The passwords generated in this step are the ones attendees will use on event day.

```bash
$ masworld student rotate --all-attendee-clusters
```

Validate every student account after rotation:

```bash
$ masworld student validate --all-attendee-clusters
```

Also rotate facilitator credentials:

```bash
$ masworld student rotate --profile facilitator --cluster facilitator-01
$ masworld student validate --profile facilitator --cluster facilitator-01
```

**IMPORTANT:** Do not rotate credentials again after this step unless a security incident requires it. Any rotation after access cards are generated in step 1.6 will invalidate the printed/distributed cards.

**Rollback:** If rotation fails on a specific cluster:

```bash
$ masworld cluster repair CLUSTER_ID --component identity
$ masworld student rotate --cluster CLUSTER_ID
$ masworld student validate --cluster CLUSTER_ID
```

If rotation fails fleet-wide (e.g., secret provider outage), do not proceed with partial rotation. Wait for the secret provider to recover, then retry the full rotation. If the secret provider cannot be restored before the event, use the pre-rotation credentials and skip this step. Document the decision.

#### 1.3 -- Run final negative security tests

**(IDEMPOTENT)** -- Estimated time: 20 minutes

```bash
$ masworld student validate --all-attendee-clusters --include-negative-tests
```

For every attendee cluster, confirm:

- Student authentication succeeds with current credentials: `PASS`
- Student can access own namespace: `PASS`
- Student cannot access other student namespaces: `DENIED`
- Student cannot access ACM administration resources: `DENIED`
- Student is not bound to cluster-admin: `CONFIRMED`
- Student cannot retrieve protected secrets: `DENIED`
- Student cannot modify cluster-scoped operators: `DENIED`

Run the S3 isolation test one final time:

```bash
$ masworld fleet validate --checks s3-isolation --max-concurrent 10
```

Expected: all cross-access attempts return `ACCESS_DENIED`.

**Any security test failure at this stage is a blocker.** Do not proceed to access card generation until every security test passes. If a security defect is found:

1. Fix the root cause (RBAC binding, IAM policy, namespace policy).
2. Rerun the affected test.
3. Confirm the fix does not introduce regressions in other tests.
4. Document the finding and the fix.

#### 1.4 -- Verify ACM compliance (pre-drift-staging)

**(IDEMPOTENT)** -- Estimated time: 5 minutes

Before staging the drift, confirm all 56 clusters are compliant:

```bash
$ masworld cluster validate hub-acm --checks policies,compliance
```

Expected: 56/56 clusters compliant for all policies. If any cluster is noncompliant, investigate and resolve the root cause before staging the intentional drift.

#### 1.5 -- Reset all exercises on all attendee clusters

**(IDEMPOTENT)** -- Estimated time: 20 minutes (parallelized)

Ensure every attendee cluster is in a clean, exercise-ready state:

```bash
$ masworld exercise reset --all-attendee-clusters --module navigation
$ masworld exercise reset --all-attendee-clusters --module acm
$ masworld exercise reset --all-attendee-clusters --module updates
$ masworld exercise reset --all-attendee-clusters --module observability
$ masworld exercise reset --all-attendee-clusters --module identity
```

If fleet-wide reset is not supported, use a loop:

```bash
$ for module in navigation acm updates observability identity; do
    for i in $(seq -w 1 50); do
      masworld exercise reset seat-$i --module $module
    done
  done
```

After reset, spot-check a few clusters to confirm clean state:

```bash
$ masworld cluster validate seat-01
$ masworld cluster validate seat-25
$ masworld cluster validate seat-50
```

#### 1.6 -- Generate attendee access cards

**(IDEMPOTENT)** -- Estimated time: 10 minutes (including review)

```bash
$ masworld student export-cards --format html > reports/access-cards-final.html
$ masworld student export-cards --format json > reports/access-cards-final.json
```

Each access card contains:

- Seat number
- Showroom URL
- OpenShift console URL
- Maximo URL
- Student username
- Student password
- Basic support instructions (e.g., "Raise your hand for help" or a support channel reference)

**Review the generated cards carefully:**

1. Open `reports/access-cards-final.html` in a browser.
2. Check a minimum of 3 cards: seat 01, seat 25, and seat 50.
3. For each reviewed card, confirm:
   - Seat number is correct.
   - URLs point to the correct cluster (not a different seat's cluster).
   - Username matches the expected pattern (`user01`, `user25`, `user50`).
   - Password is present (not blank, not a placeholder).
   - No cluster-admin credentials appear.
   - No AWS credentials, IBM entitlement keys, or internal URLs appear.
   - No secret-provider paths or internal operational metadata appear.
   - Support instructions are accurate.

4. Cross-reference one card against the secret provider:
   ```bash
   $ masworld seat show --seat 1
   ```
   Visually confirm (on your own screen only -- never project or share) that the credentials match.

Generate the facilitator-only seat inventory:

```bash
$ masworld seat export-map --format markdown > reports/seat-map-final.md
$ masworld seat export-map --format csv > reports/seat-map-final.csv
$ masworld seat export-map --format json > reports/seat-map-final.json
```

Prepare the access cards for distribution:

- If printing physical cards, print them now. Print 3--5 extra blank cards from spare cluster assignments in case of day-of replacements.
- If distributing digitally, prepare the distribution mechanism but do not send until event morning.

#### 1.7 -- Stage ACM drift for the live demonstration

**(DESTRUCTIVE -- introduces intentional noncompliance on the facilitator cluster)** -- Estimated time: 5 minutes

The ACM demo requires exactly one cluster to show a harmless drift condition that the presenter (Ernie) can remediate live during the workshop.

```bash
$ masworld cluster prepare facilitator-01 --stage acm-drift-staging
```

This stages a drift condition on the facilitator cluster by removing a harmless resource (the event marker ConfigMap). The result:

- `facilitator-01` shows `NonCompliant` for `enforce-event-marker`.
- All other 55 clusters remain `Compliant`.

Verify the drift is correctly staged:

```bash
$ masworld cluster validate hub-acm --checks compliance,drift-staging
```

Expected output:

```
ACM Compliance Summary:
  Compliant:      55/56
  NonCompliant:   1/56 (facilitator-01 -- INTENTIONAL DRIFT)

Drift staging: VERIFIED
  Cluster:     facilitator-01
  Policy:      enforce-event-marker
  Condition:   event marker ConfigMap absent
  Remediation: enforce mode (automatic) or manual presenter action
```

**IMPORTANT:** The drift must be staged only on the facilitator cluster. Never stage drift on attendee or spare clusters. Confirm with `masworld cluster validate hub-acm --checks compliance` that exactly 1 cluster is noncompliant.

**Rollback:** If the drift staging must be undone:

```bash
$ masworld exercise reset facilitator-01 --module acm
$ masworld cluster validate hub-acm --checks compliance
```

To re-stage after undoing:

```bash
$ masworld cluster prepare facilitator-01 --stage acm-drift-staging
```

#### 1.8 -- Verify Showroom accessibility (spot checks)

**(IDEMPOTENT)** -- Estimated time: 10 minutes

```bash
$ masworld cluster validate seat-01 --checks showroom
$ masworld cluster validate seat-25 --checks showroom
$ masworld cluster validate seat-50 --checks showroom
$ masworld cluster validate spare-01 --checks showroom
```

Manually open one Showroom URL in a browser (use `masworld seat show --seat 1` to get the URL). Confirm:

- The Showroom landing page / readiness page loads.
- The readiness check shows all green (all component checks PASS).
- The browser terminal tab opens and provides a working shell prompt.
- Running `oc whoami` in the terminal returns the student username.
- The OpenShift console tab loads the correct cluster console.
- The Maximo tab loads the correct Maximo URL.
- Module navigation works (click through 2--3 modules).
- Copy-paste from instruction code blocks works in the browser terminal.

#### 1.9 -- Verify Maximo accessibility (spot checks)

**(IDEMPOTENT)** -- Estimated time: 10 minutes

```bash
$ masworld cluster validate seat-01 --checks mas-core,maximo-manage
$ masworld cluster validate seat-25 --checks mas-core,maximo-manage
$ masworld cluster validate seat-50 --checks mas-core,maximo-manage
```

Manually log in to Maximo on one cluster using the student credentials:

1. Navigate to the Maximo URL from the access card.
2. Enter the student username and password.
3. Confirm the login page loads without certificate errors.
4. Confirm authentication succeeds.
5. Confirm the Maximo Manage application is accessible.
6. Confirm the starting point for the Navigation and Search exercise is reachable.

#### 1.10 -- Generate the final fleet status report

```bash
$ masworld report fleet-status > reports/fleet-status-final.txt
$ masworld report fleet-status --format json > reports/fleet-status-final.json
$ masworld report seat-report > reports/seat-report-final.txt
```

Expected fleet status:

```
Fleet Status: READY

  Total clusters:   56
  Ready:            56
  Preparing:        0
  Failed:           0
  Quarantined:      0

  Assigned seats:   50 (seat-01 through seat-50)
  Unassigned spare: 5  (spare-01 through spare-05)
  Facilitator:      1  (facilitator-01)

  Last validated:   2026-08-16Txx:xx:xxZ
```

If the status does not match the expected output, investigate and resolve before the freeze.

#### 1.11 -- Freeze all changes

After all validations pass and all reports are generated:

1. **Do not** modify any cluster configuration after this point.
2. **Do not** rotate credentials again (unless a security incident requires it).
3. **Do not** update any operator, component version, or container image.
4. **Do not** redeploy or modify Showroom content.
5. **Do not** modify ACM policies or labels.
6. **Do not** reassign seats (unless a cluster fails during final checks).
7. **Do not** run `masworld fleet prepare` or `masworld cluster prepare` on any cluster.

Document the freeze:

```
CHANGE FREEZE IN EFFECT
Effective: 2026-08-16 [TIME] America/Chicago
Lifted: After the event concludes on 2026-08-17

Any emergency change during the freeze requires:
  - Verbal approval from at least two of the three facilitators
  - Documentation in the event incident log
  - Re-validation of every affected cluster
  - Regeneration of affected access cards if credentials changed
```

#### 1.12 -- Prepare support workstations

Each facilitator must confirm the following on their laptop:

- [ ] `masworld` CLI installed, configured, and tested.
- [ ] `MASWORLD_ENVIRONMENT=event` configured.
- [ ] Can run `masworld cluster validate seat-01 --checks api` successfully from their current network.
- [ ] Terminal access to run repair, reset, and replacement commands.
- [ ] Bookmarked or saved: ACM hub console URL.
- [ ] Offline or printed copy of `during-event.md` runbook.
- [ ] Offline or printed copy of the final seat map.
- [ ] Copy of the access cards (for reprinting if needed).
- [ ] Conference Wi-Fi credentials obtained (if available before event day).

Test CLI connectivity from the expected venue network (if accessible):

```bash
$ masworld cluster validate seat-01 --checks api
$ masworld cluster validate hub-acm --checks api
```

If venue network is not accessible before event day, test from a representative external network (e.g., mobile hotspot).

#### 1.13 -- Prepare the presenter environment

Confirm with Ernie that the following are ready:

- [ ] Facilitator account credentials for `facilitator-01` are accessible (from the secret provider or securely communicated).
- [ ] ACM hub console URL is bookmarked and accessible.
- [ ] ACM console shows the expected view: 55 compliant, 1 noncompliant (facilitator-01).
- [ ] Presentation slides are loaded, tested, and backed up.
- [ ] Screen-sharing software is configured and tested.
- [ ] The ACM drift remediation action is rehearsed and the presenter is confident in the flow.
- [ ] The Maximo demonstration flow is rehearsed.
- [ ] A backup plan exists if the projector/screen-share fails (e.g., attendees follow along on their own clusters).

#### 1.14 -- Prepare backup access method

Ensure fallback access if the primary venue network is unavailable:

- [ ] VPN access to the cluster network confirmed (if applicable).
- [ ] Mobile hotspot available as backup for conference Wi-Fi.
- [ ] At least one facilitator has tested cluster access over the backup network.
- [ ] Pre-downloaded offline copies of critical reference materials (troubleshooting guide, repair procedures).
- [ ] Confirmed that `masworld` CLI can operate over the backup network path.

#### 1.15 -- Go / No-Go decision

Convene all three facilitators for the final go/no-go decision. Review:

1. Fleet validation report: all clusters READY.
2. Student credentials: rotated and validated.
3. Security tests: all passed.
4. ACM drift: staged correctly.
5. Exercises: reset to clean state.
6. Access cards: generated, reviewed, ready for distribution.
7. Spare capacity: at least 2 spares available (5 preferred).
8. Showroom and Maximo: spot-checked and accessible.
9. Support workstations: prepared and tested.
10. Outstanding findings: no unresolved CRITICAL or HIGH issues.

Decision:

```
GO / NO-GO Decision
Date: August 16, 2026
Time: __________ America/Chicago

Decision: GO / NO-GO

If NO-GO:
  Reason: _______________________________________________
  Remediation plan: _____________________________________
  Revised go/no-go time: ________________________________
```

### Validation Criteria

- [ ] `masworld fleet validate` passes on all 56 clusters with zero mandatory failures.
- [ ] Student credentials rotated (final rotation) and validated on all 50 attendee clusters.
- [ ] Facilitator credentials rotated and validated.
- [ ] All negative security tests pass (namespace isolation, ACM denial, RBAC, S3 isolation).
- [ ] ACM compliance verified: 55 compliant, 1 intentional drift on `facilitator-01`.
- [ ] All exercises reset to clean state on all 50 attendee clusters.
- [ ] Access cards generated, reviewed (spot-checked seats 01, 25, 50), and ready for distribution.
- [ ] Final seat map exported in markdown, CSV, and JSON formats.
- [ ] ACM drift staged on facilitator cluster and verified.
- [ ] Showroom accessible and functional on spot-checked clusters.
- [ ] Maximo accessible and login verified on at least one cluster.
- [ ] Fleet status report generated showing 56/56 READY.
- [ ] Change freeze in effect and documented.
- [ ] All three facilitator workstations prepared and tested.
- [ ] Presenter environment confirmed.
- [ ] Backup network access method tested.
- [ ] Go/no-go decision made and recorded.

### Rollback / Recovery

- **Cluster fails final validation:**
  Attempt repair, then replace with spare if repair fails:
  ```bash
  $ masworld cluster repair CLUSTER_ID --component FAILED_COMPONENT
  $ masworld cluster validate CLUSTER_ID
  # If repair fails:
  $ masworld seat replace --seat N --cluster spare-XX
  $ masworld student create --cluster spare-XX
  $ masworld student validate --cluster spare-XX
  $ masworld cluster validate spare-XX
  $ masworld student export-cards --format html > reports/access-cards-final.html
  ```
  Reprint or regenerate the affected access card.

- **Credential rotation fails fleet-wide:**
  This is a critical incident. Do not proceed with partial rotation. Investigate the root cause (secret-provider connectivity, htpasswd update mechanism). If the secret provider is down:
  - Option A: Wait for the provider to recover and retry.
  - Option B: Use the pre-rotation credentials (they remain valid until overwritten). Skip the final rotation. Document the decision and the risk.

- **ACM drift staging breaks the facilitator cluster:**
  ```bash
  $ masworld exercise reset facilitator-01 --module acm
  $ masworld cluster validate facilitator-01
  # After the cluster is healthy, re-stage:
  $ masworld cluster prepare facilitator-01 --stage acm-drift-staging
  ```

- **Showroom inaccessible on a cluster:**
  ```bash
  $ masworld cluster repair CLUSTER_ID --component showroom
  $ masworld cluster validate CLUSTER_ID --checks showroom
  ```

- **Access cards contain incorrect data:**
  Investigate the source of the error (seat map, credential store, URL resolution). Fix the root cause, then regenerate:
  ```bash
  $ masworld student export-cards --format html > reports/access-cards-final.html
  ```
  If cards were already printed, reprint only the affected cards.

- **Go/No-Go is NO-GO:**
  Execute the remediation plan. Schedule a revised go/no-go review no later than August 17 at 06:00 America/Chicago (3 hours before the event).

### Sign-Off

| Role                         | Name               | Date       | Status              |
|------------------------------|--------------------|------------|---------------------|
| Lab Environment Owner        | Francis Anyaegbu   | __________ | PASS / BLOCKED      |
| Presenter                    | Ernie Steagall     | __________ | PASS / BLOCKED      |
| Observability Lead           | Myles Vivian       | __________ | PASS / BLOCKED      |

**Go/No-Go Decision:** GO / NO-GO

**Signed:** ____________________________ (Lab Environment Owner)

---

## Appendix A: Escalation Contacts

| Issue Category                        | Primary Contact Role                | Escalation Role                     |
|---------------------------------------|-------------------------------------|-------------------------------------|
| Cluster provisioning / infrastructure | Platform Engineering Lead           | Cloud Account Owner                 |
| OpenShift platform issues             | Lab Environment Owner               | Red Hat Support (case required)     |
| IBM MAS installation / licensing      | IBM Technical Contact               | IBM Support (case required)         |
| AWS account / IAM / S3 issues         | Cloud Infrastructure Lead           | AWS Account Owner                   |
| ACM hub issues                        | Lab Environment Owner               | Red Hat ACM Engineering             |
| Showroom content / deployment         | Lab Environment Owner               | RHDP Platform Team                  |
| Observability / Logging / Loki        | Observability Lead (Myles Vivian)   | Lab Environment Owner               |
| Identity / Keycloak / OAuth           | Lab Environment Owner               | Red Hat Identity Engineering        |
| Network / DNS / Ingress               | Platform Engineering Lead           | Cloud Infrastructure Lead           |
| Security incident                     | Lab Environment Owner               | Security Team Lead                  |
| Event logistics / venue               | Presenter (Ernie Steagall)          | Event Coordinator                   |

**Escalation protocol:**

1. Attempt self-service resolution using the repair procedures in `../repair-procedures/`.
2. If unresolved within 15 minutes, escalate to the Primary Contact Role.
3. If unresolved within 30 minutes, escalate to the Escalation Role.
4. For any security incident, escalate immediately to the Lab Environment Owner and Security Team Lead regardless of severity.
5. Document all escalations in the event incident log (see `../incident-templates/`).

Escalation contact details (phone numbers, email addresses, chat handles) are maintained separately in the secure operations channel. Do not store personal contact information in this document.

---

## Appendix B: Consolidated Sign-Off Sheet

This sheet tracks completion of each pre-event milestone.

| Milestone       | Target Date       | Lab Owner (Francis) | Presenter (Ernie) | Observability (Myles) |
|-----------------|-------------------|---------------------|--------------------|-----------------------|
| T-30 Complete   | July 18, 2026     | Date:               | Date:              | Date:                 |
| T-14 Complete   | August 3, 2026    | Date:               | (informational)    | (informational)       |
| T-7 Complete    | August 10, 2026   | Date:               | Date:              | Date:                 |
| T-3 Complete    | August 14, 2026   | Date:               | Date:              | Date:                 |
| T-1 Complete    | August 16, 2026   | Date:               | Date:              | Date:                 |

**Final Event Readiness Declaration:**

> We, the undersigned facilitators, confirm that the MAS World 2026 workshop environment has been validated end to end and is ready for attendee use on August 17, 2026. All mandatory readiness checks pass, student credentials are active, access cards are generated, the ACM demonstration is staged, and changes are frozen.

| Role                         | Name               | Date       | Signature          |
|------------------------------|--------------------|------------|--------------------|
| Lab Environment Owner        | Francis Anyaegbu   | __________ | __________________ |
| Presenter                    | Ernie Steagall     | __________ | __________________ |
| Observability Lead           | Myles Vivian       | __________ | __________________ |

---

## Appendix C: Rollback Quick Reference

| Scenario                                  | Command                                                                   |
|-------------------------------------------|---------------------------------------------------------------------------|
| Validate a single cluster                 | `masworld cluster validate CLUSTER_ID`                                    |
| Repair a single component                 | `masworld cluster repair CLUSTER_ID --component COMPONENT`                |
| Re-prepare a single cluster               | `masworld cluster prepare CLUSTER_ID`                                     |
| Replace a failed seat with a spare        | `masworld seat replace --seat N --cluster spare-XX`                       |
| Reset one exercise module                 | `masworld exercise reset CLUSTER_ID --module MODULE`                      |
| Recreate a student account                | `masworld student create --cluster CLUSTER_ID`                            |
| Rotate one student credential             | `masworld student rotate --cluster CLUSTER_ID`                            |
| Validate one student account              | `masworld student validate --cluster CLUSTER_ID`                          |
| Disable a compromised student account     | `masworld student disable --cluster CLUSTER_ID`                           |
| Redeploy Showroom                         | `masworld cluster repair CLUSTER_ID --component showroom`                 |
| Stage ACM drift                           | `masworld cluster prepare facilitator-01 --stage acm-drift-staging`       |
| Remove ACM drift                          | `masworld exercise reset facilitator-01 --module acm`                     |
| Regenerate access cards                   | `masworld student export-cards --format html > reports/access-cards-final.html` |
| View current seat assignment              | `masworld seat show --seat N`                                             |
| Unassign a seat                           | `masworld seat unassign --seat N`                                         |
| Export full seat map                      | `masworld seat export-map --format markdown`                              |
| Full fleet revalidation                   | `masworld fleet validate --max-concurrent 10`                             |
| Fleet status overview                     | `masworld report fleet-status`                                            |
| Seat report                               | `masworld report seat-report`                                             |
| Validate configuration                    | `masworld config validate`                                                |
| Render effective configuration (redacted) | `masworld config render --redact`                                         |

---

*End of pre-event runbook. For event-day procedures, continue to [event-morning.md](event-morning.md) and [during-event.md](during-event.md).*
