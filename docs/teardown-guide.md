# Teardown Guide — MAS World 2026

**Status**: DRAFT — Phase 8
**Date**: 2026-07-19

This guide describes the post-event cleanup sequence for the MAS World 2026
workshop environment. Follow the phases in order. Each phase depends on the
successful completion of the previous one.

**Estimated total teardown time**: 2 to 4 hours, depending on fleet size and
API rate limits.

---

## 1. Overview

After the event concludes, the following must be completed:

1. Disable all student accounts.
2. Revoke cloud credentials created for the event.
3. Remove S3 buckets and stored log data.
4. Unregister clusters from the ACM hub.
5. Delete event workloads from clusters.
6. Verify that no active credentials or data remain.
7. Produce a cost report.
8. Document lessons learned.

No teardown step should be started until the event is confirmed complete and
the facilitator team has approved cleanup.

---

## 2. Pre-teardown checklist

Complete the following before beginning teardown:

| Item                                              | Owner   | Done |
|---------------------------------------------------|---------|------|
| Confirm the event session is complete             | Ernie   |      |
| Export final fleet status report                  | Francis |      |
| Export final seat assignment map                  | Francis |      |
| Export diagnostic bundles for any failed clusters  | Francis |      |
| Export timing and metrics data                    | Francis |      |
| Confirm no attendees still need environment access | Ernie   |      |
| Obtain facilitator approval to begin teardown     | Ernie   |      |
| Confirm the cost reporting period is understood    | Francis |      |
| Back up any incident records                      | Myles   |      |

Export the final fleet report for archival:

```bash
masworld reports fleet-status --env event --format json > reports/final-fleet-status.json
masworld reports fleet-status --env event --format markdown > reports/final-fleet-status.md
```

Export the final seat map:

```bash
masworld seats export --env event --format json > reports/final-seat-map.json
```

---

## 3. Phase 1 — Disable student accounts

Disable authentication for all student accounts across the fleet. This
prevents further access but preserves the accounts for audit purposes.

```bash
masworld students disable --env event --all
```

Verify that all accounts are disabled:

```bash
masworld students validate --env event
```

Expected output: every student account reports `DISABLED`. No account should
report `ACTIVE`.

If any accounts remain active, investigate and disable them individually:

```bash
masworld students disable --seat <N>
```

---

## 4. Phase 2 — Revoke cloud credentials

Revoke all IAM credentials created for the event. This includes per-cluster
S3 access credentials and any temporary IAM users or roles.

Run the credential revocation playbook:

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags iam-revocation \
  -e @config/environments/event.yaml
```

This playbook:

- Deletes IAM access keys created for each cluster's S3 access.
- Deletes IAM users created for the event (prefixed with
  `mas-world-2026-seat-*`).
- Deletes IAM policies scoped to event S3 buckets.
- Removes Kubernetes secrets containing the revoked credentials.

Verify no active IAM credentials remain:

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags iam-verify \
  -e @config/environments/event.yaml
```

If any credentials cannot be revoked automatically, record them in
`reports/teardown-exceptions.md` and revoke them manually through the AWS
console.

---

## 5. Phase 3 — Remove S3 buckets

Delete all S3 buckets created for event log storage.

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags s3-cleanup \
  -e @config/environments/event.yaml
```

This playbook:

- Deletes all objects in each event bucket.
- Deletes the buckets themselves.
- Uses the naming convention `mas-world-2026-seat-<NN>-loki-*` to identify
  event buckets.

Verify that no event buckets remain:

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags s3-verify \
  -e @config/environments/event.yaml
```

If any data must be preserved for compliance or post-event analysis, export
it before running the cleanup:

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags s3-export \
  -e @config/environments/event.yaml \
  -e s3_export_path=reports/s3-export/
```

---

## 6. Phase 4 — Unregister from ACM

Remove all managed clusters from the ACM hub and delete event-specific ACM
resources.

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags acm-cleanup \
  -e @config/environments/event.yaml
```

This playbook:

- Detaches each managed cluster from the ACM hub.
- Deletes the `mas-world-2026` ManagedClusterSet.
- Deletes all Placement and PlacementBinding resources created for the event.
- Deletes all governance policies prefixed with `policy-mas-world-`.
- Removes event labels from any clusters that remain registered.

Verify ACM cleanup:

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags acm-verify \
  -e @config/environments/event.yaml
```

---

## 7. Phase 5 — Delete event workloads

Remove event workloads from each cluster. This can be done in two ways
depending on whether the clusters will be reused or deleted.

### 7.1 Option A — Remove workloads, preserve clusters

If clusters will be returned to a pool or reused:

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags workload-cleanup \
  -e @config/environments/event.yaml
```

This removes:

| Component            | Namespaces and resources removed                          |
|----------------------|-----------------------------------------------------------|
| Showroom             | Showroom namespace and all resources                      |
| OpenLDAP             | OpenLDAP namespace and persistent volumes                 |
| Keycloak             | Keycloak namespace and persistent volumes                 |
| ClusterLogForwarder  | ClusterLogForwarder custom resources                      |
| LokiStack            | LokiStack custom resource and storage                     |
| Logging Operator     | Logging operator subscription and CSV                     |
| Loki Operator        | Loki operator subscription and CSV                        |
| Student accounts     | htpasswd identity provider entries and RBAC               |
| Student namespaces   | `student-*` namespaces                                    |
| Event metadata       | Event labels, ConfigMaps, and annotations                 |

MAS removal is handled separately due to its complexity. If MAS must be
removed:

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags mas-cleanup \
  -e @config/environments/event.yaml
```

### 7.2 Option B — Hand clusters to provisioner for deletion

If the clusters will be deleted entirely, hand them back to the external
provisioner. Provide the provisioner with:

- The list of cluster IDs.
- Confirmation that IAM credentials and S3 buckets have been cleaned up.
- Confirmation that ACM registration has been removed.

The provisioner handles full cluster deletion. No further workload cleanup
is required.

---

## 8. Phase 6 — Verify cleanup

Run the teardown verification to confirm that no active resources remain:

```bash
masworld fleet validate --env event --teardown-check
```

This check verifies:

| Check                                    | Expected result |
|------------------------------------------|-----------------|
| All student accounts disabled or deleted | PASS            |
| No active IAM credentials for event      | PASS            |
| No event S3 buckets exist                | PASS            |
| No clusters registered in ACM for event  | PASS            |
| No event governance policies remain      | PASS            |
| No event ManagedClusterSet exists        | PASS            |
| Showroom removed from all clusters       | PASS            |
| Student namespaces removed               | PASS            |
| Event ConfigMaps removed                 | PASS            |

If any checks fail, investigate and remediate before marking teardown
complete.

Record the final teardown verification result:

```bash
masworld fleet validate --env event --teardown-check --format json \
  > reports/teardown-verification.json
```

---

## 9. Phase 7 — Cost reporting

Export AWS cost data for the event period.

```bash
ansible-playbook playbooks/decommission-workshop.yml \
  --tags cost-report \
  -e @config/environments/event.yaml \
  -e cost_report_start="2026-08-01" \
  -e cost_report_end="2026-08-31"
```

The cost report covers:

- EC2 compute costs per cluster.
- S3 storage and request costs.
- Data transfer costs.
- IAM and KMS costs if applicable.
- Total cost and per-seat cost.

The report template is at:

```text
operations/cost-reporting/cost-report-template.md
```

The generated report is written to:

```text
reports/cost-report-2026-08.md
```

Review the cost report with the event stakeholders and archive it.

---

## 10. Phase 8 — Lessons learned

After teardown is complete, document the following:

### 10.1 Incident record

Record every incident that occurred during the event:

| Time  | Seat | Cluster  | Issue                    | Resolution             | Duration |
|-------|------|----------|--------------------------|------------------------|----------|
|       |      |          |                          |                        |          |

### 10.2 Timing data

Record preparation and operation timing:

| Metric                              | Value    |
|-------------------------------------|----------|
| Total fleet preparation time        |          |
| Average per-cluster preparation     |          |
| Clusters requiring repair           |          |
| Spare replacements performed        |          |
| Credential rotations performed      |          |
| Exercise resets performed           |          |
| Total teardown time                 |          |

### 10.3 Improvement items

Document improvements for future events:

| Area              | Observation                         | Recommendation          |
|-------------------|-------------------------------------|-------------------------|
| Automation        |                                     |                         |
| Showroom content  |                                     |                         |
| Runbooks          |                                     |                         |
| Tooling           |                                     |                         |
| Infrastructure    |                                     |                         |

### 10.4 Archival

Archive the following before closing out:

- Final fleet status report
- Final seat assignment map
- Cost report
- Incident records
- Timing data
- Teardown verification report
- Any diagnostic bundles collected during the event

Store archived materials in the location agreed upon by the facilitator team.
Do not archive credentials, kubeconfigs, or secret values.

---

## Teardown completion

Teardown is complete when:

1. All student accounts are disabled or deleted.
2. All event IAM credentials are revoked.
3. All event S3 buckets and data are removed.
4. All clusters are unregistered from ACM.
5. Event workloads are removed or clusters are handed to the provisioner.
6. The teardown verification check passes with no failures.
7. The cost report is produced and reviewed.
8. Lessons learned are documented.
9. Archival is complete.

Mark the event as closed in the project tracking system.
