# Operator Guide — MAS World 2026

**Status**: DRAFT — Phase 4
**Date**: 2026-07-19

This guide covers day-2 operations for the MAS World 2026 workshop
environment. It assumes the fleet has been prepared and validated using the
`masworld` CLI and that the operator has access to the event configuration
and secret provider.

---

## 1. Fleet monitoring

Display the current state of every cluster in the fleet:

```bash
masworld reports fleet-status --env event
```

The report shows each cluster with one of the following status values:

| Status        | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| READY         | All mandatory readiness checks pass; eligible for assignment   |
| PREPARING     | Cluster preparation is in progress                             |
| WARNING       | One or more non-mandatory checks failed; review recommended    |
| FAILED        | One or more mandatory checks failed; not eligible for seating  |
| ASSIGNED      | Cluster is assigned to an attendee seat                        |
| UNASSIGNED    | Cluster is ready but has no seat assignment                    |
| SPARE         | Cluster is held in reserve for replacement                     |
| QUARANTINED   | Cluster has been removed from service after a failure          |

The fleet dashboard aggregates these counts and displays:

```text
Total clusters:    56
  Ready:           50
  Preparing:        0
  Warning:          1
  Failed:           0
  Assigned:        48
  Unassigned:       2
  Spare:            5
  Quarantined:      0
Last validated:   2026-08-17T07:45:00Z
```

To filter by status:

```bash
masworld reports fleet-status --env event --status FAILED
masworld reports fleet-status --env event --status WARNING
```

To get machine-readable output:

```bash
masworld reports fleet-status --env event --format json
```

---

## 2. Common repair procedures

### 2.1 Single component failure

When one component on a cluster has failed (for example, the logging stack),
repair only that component:

```bash
masworld cluster repair --cluster seat-01 --component logging
```

Supported component values: `mas_core`, `maximo_manage`, `logging`,
`lokistack`, `log_forwarding`, `identity`, `showroom`, `student_accounts`,
`s3`, `acm_registration`.

The repair operation is idempotent. It detects the current state of the
component, reconciles it to the desired configuration, and re-validates.

### 2.2 Full cluster re-preparation

If multiple components have failed or the cluster state is unclear, run the
full preparation sequence:

```bash
masworld cluster prepare --cluster seat-01 --env event
```

This re-runs every preparation stage, skipping resources that are already in
the desired state. It does not destroy existing workloads unless they are in
a broken state that requires replacement.

### 2.3 Extended repair procedures

Detailed repair workflows for specific failure scenarios are documented in:

```text
operations/repair-procedures/cluster-repair.md
```

---

## 3. Credential rotation

### 3.1 Rotate all student credentials

Rotate passwords for every student account across the fleet:

```bash
masworld students rotate --env event
```

This generates new passwords, updates the secret provider, patches the
htpasswd identity provider on each cluster, and regenerates access cards.

### 3.2 Rotate a single seat

Rotate credentials for one attendee only:

```bash
masworld students rotate --seat 12
```

### 3.3 Verify credentials after rotation

Confirm that every student can authenticate with the new credentials:

```bash
masworld students validate --env event
```

The validation checks:

- Authentication succeeds with the new password
- The OpenShift console is accessible
- The student namespace is accessible
- Other student namespaces are not accessible
- The student is not cluster-admin

---

## 4. Exercise reset

Reset a module on a specific cluster to its starting state so the attendee
can retry the exercise:

```bash
masworld exercises reset --cluster seat-01 --module observability
```

```bash
masworld exercises reset --cluster seat-01 --module identity
```

Available modules:

| Module          | What the reset does                                         |
|-----------------|-------------------------------------------------------------|
| `navigation`    | Restores sample resources used in the navigation exercise   |
| `acm`           | Resets the ACM verification marker on the cluster           |
| `updates`       | Restores the pre-update state of the staged component       |
| `observability` | Deletes generated logs, re-stages the sample log workload   |
| `identity`      | Resets Keycloak client state and group-sync results         |

To reset all modules on a cluster:

```bash
masworld exercises reset --cluster seat-01 --module all
```

The reset operation does not affect MAS, the logging stack, or the identity
provider installation. It resets only the exercise-specific resources.

---

## 5. Spare replacement

When an assigned cluster fails during the event, replace it with a spare:

```bash
masworld seats replace --seat 12 --cluster spare-02
```

This command performs the following steps as a single transaction:

1. Disables the student credential on the failed cluster (`seat-12`).
2. Creates or activates the student credential on the replacement cluster
   (`spare-02`).
3. Updates Showroom endpoint data on the replacement cluster.
4. Validates the replacement cluster passes all mandatory readiness checks.
5. Updates the seat assignment inventory.
6. Regenerates the attendee access card for seat 12.
7. Marks the failed cluster as `QUARANTINED`.

If any step fails, the entire operation rolls back. The seat continues to
point to the original cluster until a successful replacement completes.

To verify the replacement:

```bash
masworld seats show --seat 12
```

To list available spares:

```bash
masworld reports fleet-status --env event --status SPARE
```

---

## 6. Student account management

### 6.1 Create student accounts

Create accounts for every configured attendee seat:

```bash
masworld students create --env event
```

### 6.2 Disable a single student account

Disable authentication for one seat without deleting the account:

```bash
masworld students disable --seat 12
```

### 6.3 Delete all student accounts

Remove all student accounts from every cluster in the fleet:

```bash
masworld students delete --env event
```

This is a destructive operation. Use it only during teardown.

### 6.4 Export access cards

Generate printable access cards containing Showroom URL, console URL, Maximo
URL, username, and password:

```bash
masworld students export-cards --env event --format pdf
```

Supported formats: `pdf`, `csv`, `json`.

Access cards never contain administrative credentials, AWS credentials,
IBM entitlement keys, or internal operational metadata.

---

## 7. Showroom redeployment

To redeploy Showroom on a single cluster without re-running the full
preparation:

```bash
masworld cluster prepare --cluster seat-01 --env event --tags showroom
```

This reinstalls the Showroom instance with the current configuration for
that seat, including updated endpoint URLs and student credentials.

---

## 8. Log collection for troubleshooting

### 8.1 Per-cluster logs

Every cluster operation writes structured logs to:

```text
logs/clusters/<cluster-id>/
```

For example:

```text
logs/clusters/seat-01/
  prepare-2026-08-17T0730.json
  validate-2026-08-17T0745.json
  repair-2026-08-17T0812.json
```

### 8.2 Structured JSON logs

All log files use structured JSON format with the following fields:

| Field       | Description                                  |
|-------------|----------------------------------------------|
| `timestamp` | ISO 8601 timestamp                           |
| `level`     | `DEBUG`, `INFO`, `WARNING`, `ERROR`          |
| `cluster`   | Cluster identifier                           |
| `stage`     | Preparation stage or operation name          |
| `message`   | Human-readable message                       |
| `duration`  | Duration in seconds (where applicable)       |

Secret values are redacted automatically. Redacted fields appear as
`[REDACTED]`.

### 8.3 Collecting a diagnostic bundle

To collect diagnostic information for a support case:

```bash
masworld cluster diagnose --cluster seat-01 --output diagnostics/seat-01/
```

The bundle includes cluster operator status, pod status, operator logs,
readiness check results, and event metadata. It never includes credentials,
kubeconfigs, or secret values.

---

## 9. Emergency procedures

Detailed emergency procedures are documented in the event runbooks:

```text
operations/runbooks/
  event-morning.md
  during-event.md
  after-event.md
  emergency-spare-replacement.md
  emergency-credential-rotation.md
  escalation-matrix.md
```

Key emergency contacts and escalation paths are in
`operations/runbooks/escalation-matrix.md`.

---

## 10. Common troubleshooting

| Symptom                                     | Likely cause                            | Resolution                                                             |
|---------------------------------------------|-----------------------------------------|------------------------------------------------------------------------|
| Student cannot log in                       | Credentials rotated, not synced         | `masworld students rotate --seat <N>` then redistribute access card    |
| Showroom shows connection error             | Showroom pod restarted or misconfigured | `masworld cluster prepare --cluster <id> --env event --tags showroom`  |
| Loki query returns no results               | ClusterLogForwarder misconfigured       | `masworld cluster repair --cluster <id> --component log_forwarding`    |
| Maximo UI unreachable                       | Route or certificate issue              | `masworld cluster repair --cluster <id> --component mas_core`          |
| Fleet dashboard shows WARNING               | Non-critical check failed               | Review the specific warning with `masworld cluster validate --cluster <id>` |
| Fleet dashboard shows FAILED                | Mandatory check failed                  | Attempt repair; if unsuccessful, replace with a spare                  |
| Exercise validation fails after completion  | Attendee missed a step                  | Run the solve: `masworld exercises solve --cluster <id> --module <m>`  |
| ACM shows cluster as not compliant          | Expected for facilitator drift demo     | Confirm cluster is the facilitator; if not, investigate                 |
| S3 write test fails                         | IAM credential expired or bucket issue  | `masworld cluster repair --cluster <id> --component s3`                |
| Multiple clusters failing simultaneously    | Upstream service issue                  | Check AWS, IBM registry, ACM hub; escalate per runbook                 |
