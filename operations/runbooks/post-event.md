# Post-Event Teardown Runbook -- MAS World 2026

**Status**: DRAFT
**Date**: 2026-07-19
**Event**: MAS World 2026
**Event date**: August 17, 2026
**Timezone**: America/Chicago

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Order of Operations](#3-order-of-operations)
4. [Phase 1: Immediate -- Within 1 Hour of Session End](#4-phase-1-immediate----within-1-hour-of-session-end)
5. [Phase 2: Same Day -- Within 4 Hours](#5-phase-2-same-day----within-4-hours)
6. [Phase 3: Within 48 Hours](#6-phase-3-within-48-hours)
7. [Phase 4: Within 1 Week](#7-phase-4-within-1-week)
8. [Data Retention Policy](#8-data-retention-policy)
9. [Lessons Learned Template](#9-lessons-learned-template)
10. [Cross-References](#10-cross-references)

---

## 1. Overview

This runbook covers the complete teardown and cleanup of the MAS World 2026
workshop environment after the event concludes. It covers 50 attendee
clusters, up to 5 spare clusters, 1 facilitator cluster, and 1 ACM hub
cluster, each running IBM Maximo Application Suite, OpenShift Logging with
LokiStack backed by S3 storage, ACM fleet management, and Keycloak identity
integration.

**Responsible parties**:

| Person | Role | Teardown responsibilities |
|--------|------|--------------------------|
| Francis Anyaegbu | Lab owner, Red Hat | Credential revocation, cluster cleanup, ACM deregistration, Showroom removal, final verification |
| Ernie Steagall | Presenter, ONEOK | Confirm presenter accounts are disabled, review lessons learned |
| Myles Vivian | Observability, Cohesive | Logging data export, S3 cleanup, observability teardown review |

**Timing summary**:

| Phase | Window | Estimated effort |
|-------|--------|------------------|
| Phase 1 | Within 1 hour | 15--20 minutes |
| Phase 2 | Within 4 hours | 45--60 minutes |
| Phase 3 | Within 48 hours | 2--3 hours |
| Phase 4 | Within 1 week | 3--4 hours |

---

## 2. Prerequisites

Before beginning teardown, confirm the following:

- [ ] Access to the `masworld` CLI tool on the operations workstation
- [ ] Access to the fleet configuration directory (`config/`)
- [ ] Administrative access to the ACM hub cluster
- [ ] AWS console or CLI access for S3 and IAM operations
- [ ] Access to the secret provider holding cluster credentials
- [ ] The event configuration is loaded (not development or rehearsal)

```bash
masworld config validate --environment event
```

Confirm the current fleet state before making any changes:

```bash
masworld report fleet-status --output json > /tmp/pre-teardown-fleet-status.json
masworld report fleet-status
```

---

## 3. Order of Operations

Teardown operations have strict ordering dependencies. The diagram below shows
what must complete before each subsequent step can begin.

```text
Phase 1 (Immediate)
  1.1 Disable student accounts
  1.2 Capture fleet status snapshot
  1.3 Export diagnostics and session metrics
  1.4 Secure incident reports
       |
       v
Phase 2 (Same Day)
  2.1 Revoke S3 IAM credentials         <-- depends on 1.3 (diagnostics exported first)
  2.2 Revoke temporary cloud credentials <-- depends on 1.1 (students disabled first)
  2.3 Export Loki logs                   <-- depends on 2.1 NOT yet complete (needs S3 access)
  2.4 Document unresolved incidents      <-- depends on 1.4
       |
       v
Phase 3 (Within 48 Hours)
  3.1 Clean up S3 buckets               <-- depends on 2.3 (log export complete)
  3.2 Unregister clusters from ACM      <-- depends on 1.1 (students disabled)
  3.3 Remove event workloads            <-- depends on 3.2 (ACM deregistered first)
  3.4 Remove student accounts           <-- depends on 1.1 (already disabled)
  3.5 Remove Showroom deployments       <-- depends on 3.4 (students removed)
  3.6 Verify credential revocation      <-- depends on 2.1, 2.2, 3.4
       |
       v
Phase 4 (Within 1 Week)
  4.1 Generate cost report              <-- depends on 3.1 (S3 cleanup for final metering)
  4.2 Compile lessons learned           <-- depends on 2.4 (incidents documented)
  4.3 Create post-event report          <-- depends on 4.1, 4.2
  4.4 Archive configuration and logs    <-- depends on 4.3 (report finalized)
  4.5 Final cleanup verification        <-- depends on all prior phases
```

**Critical ordering constraint**: Loki log export (step 2.3) must complete
before S3 bucket cleanup (step 3.1). If you clean up S3 buckets before
exporting logs, the log data is permanently lost.

**Critical ordering constraint**: ACM deregistration (step 3.2) should
complete before removing event workloads (step 3.3) to avoid ACM reporting
spurious policy violations during teardown.

---

## 4. Phase 1: Immediate -- Within 1 Hour of Session End

**Estimated time**: 15--20 minutes
**Responsible**: Francis Anyaegbu

### 4.1 Disable All Attendee Credentials

Disable all student and facilitator accounts across the fleet. This prevents
any further access but does not delete the accounts, preserving the ability
to investigate if needed.

```bash
masworld student disable --environment event --all
```

To verify that accounts are disabled:

```bash
masworld student validate --environment event --expect-disabled
```

Expected output for each seat:

```text
seat-01: user01 authentication DISABLED   OK
seat-02: user02 authentication DISABLED   OK
...
seat-50: user50 authentication DISABLED   OK
```

If any account fails to disable, target it individually:

```bash
masworld student disable --environment event --seat 17
```

Verify facilitator accounts are also disabled:

```bash
masworld student disable --environment event --role facilitator
masworld student disable --environment event --role presenter
```

**Estimated time**: 5 minutes

### 4.2 Capture Fleet Status Snapshot

Record the final state of every cluster before any teardown operations modify
the environment.

```bash
masworld report fleet-status \
  --environment event \
  --output json \
  > /tmp/post-event-fleet-status-$(date +%Y%m%dT%H%M%S).json

masworld report fleet-status \
  --environment event \
  --output markdown \
  > /tmp/post-event-fleet-status-$(date +%Y%m%dT%H%M%S).md
```

Export the final seat map:

```bash
masworld seat export-map \
  --environment event \
  --output json \
  > /tmp/post-event-seat-map-$(date +%Y%m%dT%H%M%S).json

masworld seat export-map \
  --environment event \
  --output csv \
  > /tmp/post-event-seat-map-$(date +%Y%m%dT%H%M%S).csv
```

**Estimated time**: 3 minutes

### 4.3 Export Diagnostics and Session Metrics

Collect fleet-wide diagnostics while the environment is still fully
operational. This data is needed for the post-event report and for
troubleshooting any issues that arose during the session.

```bash
masworld report fleet-status \
  --environment event \
  --include-diagnostics \
  --output json \
  > /tmp/post-event-diagnostics-$(date +%Y%m%dT%H%M%S).json
```

Export the seat report with timing and validation data:

```bash
masworld report seat-report \
  --environment event \
  --output json \
  > /tmp/post-event-seat-report-$(date +%Y%m%dT%H%M%S).json
```

Collect credential operation audit logs:

```bash
# Copy the credential operation audit log from the automation workspace
cp logs/credential-audit-*.json /tmp/post-event-credential-audit.json 2>/dev/null || true
```

**Estimated time**: 5 minutes

### 4.4 Secure Incident Reports

If any incidents occurred during the event, ensure they are captured before
memory fades and before environment changes make investigation harder.

For each incident:

1. Confirm that the incident template was filled out during the event.
   See `mas-world-2026-operations/incident-templates/`.

2. If an incident was handled without a template, create one now:

```text
File: mas-world-2026-operations/incident-templates/incident-YYYYMMDD-NNN.md

## Incident Summary
- Time detected:
- Time resolved:
- Affected seats:
- Affected clusters:
- Severity: [critical | major | minor]
- Responder:

## Description
[What happened]

## Root cause
[Known or suspected cause]

## Resolution
[What was done to fix it]

## Follow-up actions
[Any remaining work]
```

3. If a cluster was replaced during the event, document the replacement:

```bash
# Check for quarantined clusters that indicate replacements occurred
masworld report fleet-status --environment event | grep -i quarantined
```

**Estimated time**: 5 minutes (longer if incidents occurred)

### Phase 1 Verification Checklist

- [ ] All 50 attendee accounts are disabled
- [ ] All facilitator accounts are disabled
- [ ] All presenter accounts are disabled
- [ ] Fleet status snapshot saved (JSON and Markdown)
- [ ] Seat map exported (JSON and CSV)
- [ ] Diagnostics exported
- [ ] Seat report exported
- [ ] Credential audit log preserved
- [ ] All incidents from the event are documented
- [ ] No student can authenticate to any cluster

Verification command:

```bash
# Attempt login as a sample student -- must fail
oc login https://api.PLACEHOLDER_CLUSTER_DOMAIN:6443 \
  --username=user01 \
  --password=PLACEHOLDER_STUDENT_PASSWORD 2>&1 | grep -i "unauthorized\|forbidden\|failed"
```

---

## 5. Phase 2: Same Day -- Within 4 Hours

**Estimated time**: 45--60 minutes
**Responsible**: Francis Anyaegbu (credentials), Myles Vivian (log export)

### 5.1 Revoke AWS IAM Credentials (S3 Access Keys)

**Important**: Complete step 5.3 (Loki log export) BEFORE revoking S3
credentials if you need to export any log data from Loki. Once S3 credentials
are revoked, Loki cannot read from its object store.

If log export is not needed, proceed with revocation immediately.

Revoke the per-cluster S3 IAM access keys that were created for LokiStack
object storage. Each attendee cluster has its own IAM user or role with access
scoped to its S3 bucket.

```bash
# List all S3 IAM credentials managed by the automation
masworld config render --environment event --section aws.s3_credentials --redact
```

Revoke credentials using the automation tooling:

```bash
# Revoke all S3 IAM access keys across the fleet
# This deactivates the IAM access keys but does not delete the IAM users
masworld student rotate --environment event --component s3 --action revoke
```

If the `masworld` CLI does not support direct IAM revocation, use the AWS CLI:

```bash
# For each cluster seat-01 through seat-50 plus spares
for SEAT_NUM in $(seq -w 1 50); do
  AWS_ACCESS_KEY_ID=$(aws secretsmanager get-secret-value \
    --secret-id mas-world/clusters/seat-${SEAT_NUM}/AWS_ACCESS_KEY_ID \
    --query SecretString --output text 2>/dev/null || echo "NOT_FOUND")

  if [ "$AWS_ACCESS_KEY_ID" != "NOT_FOUND" ]; then
    IAM_USER="mas-world-2026-seat-${SEAT_NUM}-loki"
    aws iam update-access-key \
      --user-name "$IAM_USER" \
      --access-key-id "$AWS_ACCESS_KEY_ID" \
      --status Inactive \
      --region PLACEHOLDER_AWS_REGION
    echo "Deactivated access key for seat-${SEAT_NUM}"
  fi
done
```

Repeat for spare clusters:

```bash
for SPARE_NUM in $(seq -w 1 5); do
  IAM_USER="mas-world-2026-spare-${SPARE_NUM}-loki"
  # Same deactivation pattern as above
done
```

**Estimated time**: 10 minutes

### 5.2 Revoke Temporary Cloud Credentials

Revoke any additional temporary credentials that were created for the event:

1. **Temporary cluster-admin tokens**: These should have been short-lived and
   already expired. Verify:

```bash
# Check for any unexpired service account tokens created for event operations
for SEAT_NUM in $(seq -w 1 50); do
  echo "--- seat-${SEAT_NUM} ---"
  oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH get secrets \
    -n mas-world-automation \
    -l app.kubernetes.io/part-of=mas-world-2026 \
    --no-headers 2>/dev/null | grep token || echo "No event tokens found"
done
```

2. **AWS STS temporary credentials**: If any `assume-role` sessions were
   created for event-day operations, they expire automatically but should be
   confirmed:

```bash
# Verify no active STS sessions for the event IAM role
aws sts get-caller-identity --region PLACEHOLDER_AWS_REGION
```

3. **Container registry tokens**: If temporary pull-secret tokens were
   distributed, revoke them:

```bash
# Verify IBM entitlement key usage -- do not revoke the key itself,
# but remove it from cluster pull secrets during Phase 3
echo "IBM entitlement key revocation is handled during workload removal (Phase 3)"
```

**Estimated time**: 10 minutes

### 5.3 Export Loki Logs If Needed

**Prerequisite**: S3 credentials must still be active. Perform this step
BEFORE step 5.1 if log export is required.

Determine whether Loki log data needs to be preserved for post-mortem
analysis, compliance, or lessons learned. If not, skip to step 5.4.

For each cluster that requires log export:

```bash
# Port-forward to the Loki gateway on the target cluster
oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH \
  port-forward -n openshift-logging svc/logging-loki-gateway-http 3100:8080 &
LOKI_PF_PID=$!

# Query application logs from the event window (adjust timestamps)
# Event date: 2026-08-17, session approximately 09:00-17:00 CDT (14:00-22:00 UTC)
curl -s "http://localhost:3100/api/logs/v1/application/loki/api/v1/query_range" \
  --data-urlencode 'query={kubernetes_namespace_name=~"student-.*"}' \
  --data-urlencode 'start=2026-08-17T14:00:00Z' \
  --data-urlencode 'end=2026-08-17T22:00:00Z' \
  --data-urlencode 'limit=10000' \
  > /tmp/post-event-loki-export-seat-NN.json

kill $LOKI_PF_PID 2>/dev/null
```

For bulk export across all clusters, use the fleet tooling if available:

```bash
masworld report fleet-status \
  --environment event \
  --include-log-summary \
  --log-window "2026-08-17T14:00:00Z/2026-08-17T22:00:00Z" \
  --output json \
  > /tmp/post-event-log-summary.json
```

**Estimated time**: 15--20 minutes (depends on volume and cluster count)

### 5.4 Document Unresolved Incidents

Review all incidents from step 4.4 and classify their resolution status:

| Status | Action |
|--------|--------|
| Resolved during event | Document root cause and resolution |
| Workaround applied | Document permanent fix needed |
| Unresolved | Escalate and assign owner |
| Investigation needed | Assign owner and deadline |

Create or update the incident summary:

```text
File: mas-world-2026-operations/incident-templates/incident-summary-post-event.md

## Incident Summary -- MAS World 2026

### Resolved incidents
| ID | Seats affected | Description | Resolution |
|----|----------------|-------------|------------|

### Unresolved incidents
| ID | Seats affected | Description | Assigned to | Deadline |
|----|----------------|-------------|-------------|----------|

### Lessons learned from incidents
[Reference to Section 9 of this runbook]
```

**Estimated time**: 10--15 minutes

### Phase 2 Verification Checklist

- [ ] S3 IAM access keys for all 50 attendee clusters are deactivated
- [ ] S3 IAM access keys for all 5 spare clusters are deactivated
- [ ] S3 IAM access keys for the facilitator cluster are deactivated
- [ ] No temporary STS sessions are active for event IAM roles
- [ ] Loki log data exported (if required by retention policy)
- [ ] All incidents from the event are classified and documented
- [ ] Unresolved incidents have assigned owners and deadlines

Verification command for S3 credential revocation:

```bash
# Attempt to list objects in an attendee bucket -- must fail
aws s3 ls s3://mas-world-2026-seat-01-loki-PLACEHOLDER_SUFFIX/ \
  --profile mas-world-seat-01 2>&1 | grep -i "access denied\|invalid\|expired"
```

---

## 6. Phase 3: Within 48 Hours

**Estimated time**: 2--3 hours
**Responsible**: Francis Anyaegbu

### 6.1 Clean Up S3 Buckets

**Prerequisite**: Loki log export (step 5.3) must be complete before
proceeding. Deleting S3 bucket contents is irreversible.

Follow the data retention policy in Section 8 of this runbook to determine
which buckets to empty and which to preserve.

**Option A -- Delete bucket contents, retain bucket structure** (recommended
for immediate cleanup with deferred bucket deletion):

```bash
for SEAT_NUM in $(seq -w 1 50); do
  BUCKET="mas-world-2026-seat-${SEAT_NUM}-loki-PLACEHOLDER_SUFFIX"
  echo "Emptying bucket: ${BUCKET}"
  aws s3 rm "s3://${BUCKET}" --recursive --region PLACEHOLDER_AWS_REGION
done
```

Repeat for spare and facilitator buckets:

```bash
for SPARE_NUM in $(seq -w 1 5); do
  BUCKET="mas-world-2026-spare-${SPARE_NUM}-loki-PLACEHOLDER_SUFFIX"
  aws s3 rm "s3://${BUCKET}" --recursive --region PLACEHOLDER_AWS_REGION
done

BUCKET="mas-world-2026-facilitator-01-loki-PLACEHOLDER_SUFFIX"
aws s3 rm "s3://${BUCKET}" --recursive --region PLACEHOLDER_AWS_REGION
```

**Option B -- Delete buckets entirely**:

```bash
for SEAT_NUM in $(seq -w 1 50); do
  BUCKET="mas-world-2026-seat-${SEAT_NUM}-loki-PLACEHOLDER_SUFFIX"
  aws s3 rb "s3://${BUCKET}" --force --region PLACEHOLDER_AWS_REGION
done
```

**Option C -- Apply lifecycle policy for automatic expiry** (if bucket
deletion is deferred):

```bash
for SEAT_NUM in $(seq -w 1 50); do
  BUCKET="mas-world-2026-seat-${SEAT_NUM}-loki-PLACEHOLDER_SUFFIX"
  aws s3api put-bucket-lifecycle-configuration \
    --bucket "${BUCKET}" \
    --lifecycle-configuration '{
      "Rules": [{
        "ID": "post-event-expiry",
        "Status": "Enabled",
        "Expiration": {"Days": 7},
        "Filter": {"Prefix": ""}
      }]
    }' \
    --region PLACEHOLDER_AWS_REGION
done
```

**Estimated time**: 15--30 minutes

### 6.2 Unregister Clusters from ACM Hub

Remove all managed clusters from the ACM hub. This prevents the hub from
attempting to enforce policies on clusters that are being torn down.

Remove the ManagedClusterSet first, then individual cluster registrations:

```bash
# Connect to the ACM hub cluster
export KUBECONFIG=PLACEHOLDER_HUB_KUBECONFIG_PATH

# Remove the event ManagedClusterSet binding
oc delete managedclustersetbinding mas-world-2026 \
  -n mas-world-2026-policies 2>/dev/null || true

# Remove placements and placement bindings
oc delete placementbinding -n mas-world-2026-policies -l event=mas-world-2026
oc delete placement -n mas-world-2026-policies -l event=mas-world-2026

# Remove governance policies
oc delete policy -n mas-world-2026-policies -l event=mas-world-2026

# Remove the policy namespace
oc delete namespace mas-world-2026-policies 2>/dev/null || true

# Detach managed clusters (this removes the agent from each cluster)
for SEAT_NUM in $(seq -w 1 50); do
  echo "Detaching seat-${SEAT_NUM} from ACM hub"
  oc delete managedcluster seat-${SEAT_NUM} --wait=false 2>/dev/null || true
done

for SPARE_NUM in $(seq -w 1 5); do
  oc delete managedcluster spare-${SPARE_NUM} --wait=false 2>/dev/null || true
done

oc delete managedcluster facilitator-01 --wait=false 2>/dev/null || true

# Remove the ManagedClusterSet
oc delete managedclusterset mas-world-2026 2>/dev/null || true
```

Wait for detachment to complete:

```bash
echo "Waiting for managed cluster detachment..."
oc get managedclusters -l event=mas-world-2026 --no-headers 2>/dev/null
# Expected: no resources found
```

**Note**: Detaching a managed cluster removes the ACM agent from the managed
cluster. The managed cluster itself continues to run. If the clusters will be
deleted by the external provisioner, this step is still recommended to ensure
clean state on the hub.

**Estimated time**: 20--30 minutes

### 6.3 Remove Event Workloads from Clusters

Remove workshop-specific workloads from each cluster. This does not remove
MAS or OpenShift Logging if the cluster will be reused. If the clusters are
being handed to the external provisioner for deletion, this step can be
skipped.

**If clusters will be deleted** (typical for RHDP-provisioned environments):

```text
Skip this step. The cluster deletion process will remove all workloads.
Proceed to step 6.4.
```

**If clusters will be reused or returned**:

Use the decommission playbook:

```bash
masworld cluster decommission \
  --environment event \
  --scope event-workloads \
  --cluster all
```

Or run the Ansible playbook directly:

```bash
ansible-playbook \
  mas-world-2026-automation/playbooks/decommission-workshop.yml \
  -e environment=event \
  -e decommission_scope=event-workloads
```

The decommission scope `event-workloads` removes:

- Student namespaces (`student-01` through `student-50`)
- Event marker ConfigMaps and labels
- Demo drift resources from the facilitator cluster
- Sample logging workloads
- Exercise staging data
- Showroom deployment (handled separately in step 6.5)
- Event-specific RBAC (ClusterRoleBindings, RoleBindings)

The decommission scope does NOT remove:

- MAS Core or Maximo Manage (use scope `mas` for that)
- OpenShift Logging or LokiStack (use scope `logging` for that)
- Keycloak (use scope `identity` for that)
- Cluster-level operators

For full workload removal:

```bash
masworld cluster decommission \
  --environment event \
  --scope all \
  --cluster all
```

**Estimated time**: 30--45 minutes

### 6.4 Remove Student Accounts

Permanently delete student accounts from all clusters. This removes the
HTPasswd identity provider entries and associated RBAC bindings.

**Prerequisite**: Accounts must already be disabled (Phase 1, step 4.1).

```bash
masworld student delete --environment event --all
```

Verify removal:

```bash
masworld student validate --environment event --expect-absent
```

Expected output:

```text
seat-01: user01 account ABSENT   OK
seat-02: user02 account ABSENT   OK
...
seat-50: user50 account ABSENT   OK
facilitator-01: facilitator1 account ABSENT   OK
```

Delete student credentials from the secret provider:

```bash
# Credentials are stored at: secret://mas-world/students/seat-NN/password
# The student delete command should handle this, but verify:
masworld config render --environment event --section student_credentials --redact 2>&1 \
  | grep -c "NOT_FOUND"
# Expected: count matches total number of students + facilitators
```

**Estimated time**: 10 minutes

### 6.5 Remove Showroom Deployments

Remove Showroom from each attendee cluster:

```bash
masworld cluster decommission \
  --environment event \
  --scope showroom \
  --cluster all
```

Or target a specific cluster:

```bash
masworld cluster decommission \
  --environment event \
  --scope showroom \
  --cluster seat-01
```

Verify Showroom removal:

```bash
for SEAT_NUM in $(seq -w 1 50); do
  oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH \
    get namespace showroom --no-headers 2>/dev/null && \
    echo "WARNING: Showroom still present on seat-${SEAT_NUM}" || \
    echo "OK: Showroom removed from seat-${SEAT_NUM}"
done
```

**Estimated time**: 15 minutes

### 6.6 Verify Credential Revocation

Run a comprehensive verification to confirm that all credentials from Phases
1 and 2 have been successfully revoked.

```bash
masworld fleet validate \
  --environment event \
  --validation-profile post-event-teardown
```

Manual verification checklist:

**Student credentials**:
```bash
# Pick 3 random seats and attempt login -- all must fail
for SEAT_NUM in 07 23 41; do
  echo "--- Testing seat-${SEAT_NUM} ---"
  oc login https://api.PLACEHOLDER_CLUSTER_DOMAIN:6443 \
    --username=user${SEAT_NUM} \
    --password=PLACEHOLDER_STUDENT_PASSWORD 2>&1 \
    | grep -i "unauthorized\|forbidden\|failed\|error" && echo "PASS" || echo "FAIL"
done
```

**S3 credentials**:
```bash
# Attempt to access a bucket with revoked credentials -- must fail
aws s3 ls s3://mas-world-2026-seat-01-loki-PLACEHOLDER_SUFFIX/ \
  --profile mas-world-seat-01 2>&1 \
  | grep -i "access denied\|invalid\|expired" && echo "PASS" || echo "FAIL"
```

**Facilitator credentials**:
```bash
oc login https://api.PLACEHOLDER_CLUSTER_DOMAIN:6443 \
  --username=facilitator1 \
  --password=PLACEHOLDER_FACILITATOR_PASSWORD 2>&1 \
  | grep -i "unauthorized\|forbidden\|failed\|error" && echo "PASS" || echo "FAIL"
```

**Estimated time**: 10 minutes

### Phase 3 Verification Checklist

- [ ] S3 buckets emptied or lifecycle policy applied (per retention policy)
- [ ] All managed clusters detached from ACM hub
- [ ] ManagedClusterSet `mas-world-2026` deleted
- [ ] All ACM policies for the event removed
- [ ] Event workloads removed from clusters (or clusters marked for deletion)
- [ ] All student accounts deleted from all clusters
- [ ] Student credentials removed from secret provider
- [ ] Showroom removed from all clusters
- [ ] Student login attempts fail on 3+ sampled clusters
- [ ] S3 access attempts fail with revoked credentials
- [ ] Facilitator login attempts fail

---

## 7. Phase 4: Within 1 Week

**Estimated time**: 3--4 hours
**Responsible**: Francis Anyaegbu (cost report, archive), Myles Vivian
(observability section of lessons learned), Ernie Steagall (presentation
section of lessons learned)

### 7.1 Generate Cost Report

Produce a cost report covering the full lifecycle of the workshop
environment, from initial cluster provisioning through teardown.

See `mas-world-2026-operations/cost-reporting/` for the cost report template.

**AWS compute costs**:

```bash
# Generate AWS Cost Explorer report for the event tag
aws ce get-cost-and-usage \
  --time-period Start=2026-08-01,End=2026-08-31 \
  --granularity DAILY \
  --metrics "BlendedCost" "UnblendedCost" "UsageQuantity" \
  --filter '{
    "Tags": {
      "Key": "event",
      "Values": ["mas-world-2026"]
    }
  }' \
  --group-by Type=DIMENSION,Key=SERVICE \
  --region PLACEHOLDER_AWS_REGION \
  > /tmp/post-event-aws-costs.json
```

**AWS S3 storage costs**:

```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-08-01,End=2026-08-31 \
  --granularity DAILY \
  --metrics "BlendedCost" \
  --filter '{
    "And": [
      {"Tags": {"Key": "event", "Values": ["mas-world-2026"]}},
      {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Simple Storage Service"]}}
    ]
  }' \
  --region PLACEHOLDER_AWS_REGION \
  > /tmp/post-event-s3-costs.json
```

**Cost report structure** (see `mas-world-2026-operations/cost-reporting/`):

```text
## Cost Report -- MAS World 2026

### Summary
| Category | Cost |
|----------|------|
| AWS EC2 (compute) | $ |
| AWS S3 (storage) | $ |
| AWS networking (data transfer, NAT, ELB) | $ |
| AWS other (Route53, Secrets Manager, IAM) | $ |
| IBM licensing (MAS, Manage) | $ |
| Red Hat subscriptions (OpenShift) | $ |
| Total | $ |

### Per-cluster average
| Metric | Value |
|--------|-------|
| Average compute cost per cluster | $ |
| Average storage cost per cluster | $ |
| Average total cost per cluster | $ |

### Timeline
| Phase | Duration | Cost |
|-------|----------|------|
| Development (N clusters) | | $ |
| Rehearsal (N clusters) | | $ |
| Event preparation (56 clusters) | | $ |
| Event day | | $ |
| Teardown | | $ |

### Recommendations for future events
[Cost optimization observations]
```

**Estimated time**: 45--60 minutes

### 7.2 Compile Lessons Learned

Gather input from all three facilitators and compile a lessons-learned
document. Use the template in Section 9 of this runbook.

Schedule a 30-minute debrief with Ernie Steagall, Francis Anyaegbu, and Myles
Vivian within 3 business days of the event.

Inputs to the debrief:

- Fleet status snapshots (Phase 1)
- Session diagnostics (Phase 1)
- Incident reports (Phase 1, Phase 2)
- Attendee feedback (if collected)
- Presenter observations
- Support staff observations
- Cost report (step 7.1)

**Estimated time**: 60--90 minutes (including debrief meeting)

### 7.3 Create Post-Event Report

Assemble the post-event report from the artifacts collected in prior phases.

```text
File: mas-world-2026-operations/reports/post-event-report.md

## Post-Event Report -- MAS World 2026

### Event summary
- Date: August 17, 2026
- Attendees: [actual count]
- Clusters used: [count]
- Spare clusters consumed: [count]
- Incidents: [count]

### Environment performance
- Clusters ready at event start: [count] / [total]
- Clusters replaced during event: [count]
- Mean validation time per cluster: [duration]
- Mean preparation time per cluster: [duration]

### Session results
[Per-module completion rates, if tracked]

### Incidents
[Summary from incident reports]

### Cost summary
[From step 7.1]

### Lessons learned
[From step 7.2]

### Recommendations
[For future events]
```

**Estimated time**: 30--45 minutes

### 7.4 Archive Configuration and Logs

Archive all configuration, logs, reports, and non-sensitive artifacts for
future reference.

**What to archive**:

- Configuration files (with credentials redacted)
- Fleet status snapshots
- Seat maps
- Diagnostics exports
- Incident reports
- Cost reports
- Lessons learned
- Post-event report
- Credential audit logs (no secret values)
- Showroom content (as released)
- Automation playbooks (as released)
- ACM policy definitions (as released)
- Validation and test results

**What NOT to archive**:

- Kubeconfigs
- Passwords or tokens
- AWS access keys or secret keys
- IBM entitlement keys
- MAS license files
- Pull secrets
- Private certificates or keys
- `.env` files
- Vault tokens
- Any file matching patterns in the project `.gitignore` credential section

Archive the safe artifacts:

```bash
# Create archive directory
ARCHIVE_DIR="mas-world-2026-archive-$(date +%Y%m%d)"
mkdir -p "/tmp/${ARCHIVE_DIR}"

# Copy configuration (credentials file excluded)
cp -r mas-world-2026-automation/config/ "/tmp/${ARCHIVE_DIR}/config/"
rm -f "/tmp/${ARCHIVE_DIR}/config/credentials.yaml"

# Copy reports and diagnostics
cp /tmp/post-event-fleet-status-*.json "/tmp/${ARCHIVE_DIR}/"
cp /tmp/post-event-seat-map-*.json "/tmp/${ARCHIVE_DIR}/"
cp /tmp/post-event-seat-map-*.csv "/tmp/${ARCHIVE_DIR}/"
cp /tmp/post-event-diagnostics-*.json "/tmp/${ARCHIVE_DIR}/"
cp /tmp/post-event-seat-report-*.json "/tmp/${ARCHIVE_DIR}/"
cp /tmp/post-event-aws-costs.json "/tmp/${ARCHIVE_DIR}/"
cp /tmp/post-event-s3-costs.json "/tmp/${ARCHIVE_DIR}/"
cp /tmp/post-event-credential-audit.json "/tmp/${ARCHIVE_DIR}/" 2>/dev/null || true

# Copy operations docs
cp -r mas-world-2026-operations/incident-templates/ "/tmp/${ARCHIVE_DIR}/incidents/"
cp -r mas-world-2026-operations/reports/ "/tmp/${ARCHIVE_DIR}/reports/" 2>/dev/null || true

# Copy project docs
cp -r docs/ "/tmp/${ARCHIVE_DIR}/docs/"

# Create the archive
tar czf "/tmp/${ARCHIVE_DIR}.tar.gz" -C /tmp "${ARCHIVE_DIR}"
echo "Archive created: /tmp/${ARCHIVE_DIR}.tar.gz"
```

Store the archive according to your organization's retention policy. See
Section 8 for retention guidance.

**Estimated time**: 20 minutes

### 7.5 Final Cleanup Verification

Run a comprehensive verification to confirm that all teardown operations
are complete and no residual event resources remain.

**Cluster verification** (sample 3--5 clusters):

```bash
for SEAT_NUM in 01 15 30 45 50; do
  echo "=== Verifying seat-${SEAT_NUM} ==="

  # Student namespace removed
  oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH \
    get namespace "student-${SEAT_NUM}" --no-headers 2>&1 \
    | grep -q "not found" && echo "Student namespace: REMOVED" || echo "Student namespace: STILL PRESENT"

  # Showroom removed
  oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH \
    get namespace showroom --no-headers 2>&1 \
    | grep -q "not found" && echo "Showroom namespace: REMOVED" || echo "Showroom namespace: STILL PRESENT"

  # Event labels removed (if clusters still exist)
  oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH \
    get nodes -l event=mas-world-2026 --no-headers 2>&1 \
    | grep -c "" | xargs -I{} echo "Nodes with event label: {}"

  # Student accounts absent
  oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH \
    get oauth -o jsonpath='{.items[0].spec.identityProviders[*].name}' 2>/dev/null \
    | grep -q "mas-world-htpasswd" && echo "HTPasswd IDP: STILL PRESENT" || echo "HTPasswd IDP: REMOVED"
done
```

**ACM hub verification**:

```bash
export KUBECONFIG=PLACEHOLDER_HUB_KUBECONFIG_PATH

# No event managed clusters
oc get managedclusters -l event=mas-world-2026 --no-headers 2>&1
# Expected: No resources found

# No event ManagedClusterSet
oc get managedclusterset mas-world-2026 --no-headers 2>&1
# Expected: not found

# No event policies
oc get policies -A -l event=mas-world-2026 --no-headers 2>&1
# Expected: No resources found
```

**AWS verification**:

```bash
# No active IAM access keys for event users
aws iam list-users --path-prefix /mas-world-2026/ --region PLACEHOLDER_AWS_REGION 2>/dev/null

# S3 buckets emptied (or deleted)
for SEAT_NUM in 01 15 30; do
  BUCKET="mas-world-2026-seat-${SEAT_NUM}-loki-PLACEHOLDER_SUFFIX"
  OBJECT_COUNT=$(aws s3 ls "s3://${BUCKET}" --recursive --region PLACEHOLDER_AWS_REGION 2>/dev/null | wc -l)
  echo "Bucket ${BUCKET}: ${OBJECT_COUNT} objects remaining"
done
```

**Secret provider verification**:

```bash
# Verify student secrets are deleted from the secret provider
# This is provider-specific; example for AWS Secrets Manager:
aws secretsmanager list-secrets \
  --filter Key=name,Values=mas-world/students \
  --region PLACEHOLDER_AWS_REGION 2>/dev/null \
  | grep -c "mas-world/students" | xargs -I{} echo "Student secrets remaining: {}"
# Expected: 0
```

**Estimated time**: 20 minutes

### Phase 4 Verification Checklist

- [ ] AWS cost report generated and reviewed
- [ ] S3 storage cost report generated
- [ ] Lessons learned debrief completed with all three facilitators
- [ ] Lessons learned document written (using template in Section 9)
- [ ] Post-event report assembled
- [ ] Configuration and logs archived (credentials excluded)
- [ ] Archive stored per retention policy
- [ ] Sample clusters verified clean (student namespaces, Showroom, accounts)
- [ ] ACM hub verified clean (no event clusters, policies, or sets)
- [ ] AWS IAM verified clean (no active event credentials)
- [ ] S3 buckets verified empty or deleted
- [ ] Secret provider verified clean (no student credentials remaining)
- [ ] Clusters handed to external provisioner for deletion (if applicable)

---

## 8. Data Retention Policy

This section provides guidance on retention periods. Adjust to match your
organization's compliance and record-keeping requirements.

| Data category | Minimum retention | Maximum retention | Storage location | Notes |
|---------------|-------------------|-------------------|------------------|-------|
| Fleet status snapshots | 90 days | 1 year | Organizational archive | Needed for future planning |
| Seat maps | 90 days | 1 year | Organizational archive | Anonymize after 90 days |
| Diagnostics | 30 days | 90 days | Organizational archive | Delete after post-mortem |
| Loki log exports | 7 days | 30 days | Temporary storage | Only if needed for incident investigation |
| S3 bucket contents | 0 days | 7 days | AWS S3 | Delete or expire via lifecycle policy |
| Incident reports | 1 year | 3 years | Organizational archive | Required for repeat-event planning |
| Cost reports | 1 year | 3 years | Organizational archive | Required for budgeting |
| Lessons learned | Permanent | Permanent | Organizational archive | Institutional knowledge |
| Post-event report | Permanent | Permanent | Organizational archive | Institutional knowledge |
| Credential audit logs | 90 days | 1 year | Organizational archive | No secret values |
| Configuration (redacted) | 1 year | 3 years | Organizational archive | Template for future events |
| Automation code | Permanent | Permanent | Git repository | Reusable for future events |
| Showroom content | Permanent | Permanent | Git repository | Reusable for future events |
| Student passwords | 0 days | 0 days | -- | Delete immediately after event |
| Kubeconfigs | 0 days | 0 days | -- | Delete immediately after event |
| AWS access keys | 0 days | 0 days | -- | Revoke and delete after event |
| IBM entitlement keys | Per IBM policy | Per IBM policy | Secret provider | Do not store in archive |

**Credentials must never be archived.** The archive process in step 7.4
explicitly excludes credential files. If credentials are accidentally included
in an archive, destroy the archive, rotate the affected credentials, and
create a new archive without credentials.

---

## 9. Lessons Learned Template

Use this template to structure the post-event lessons-learned document.
Schedule the debrief within 3 business days of the event.

```text
File: mas-world-2026-operations/reports/lessons-learned.md

# Lessons Learned -- MAS World 2026

**Date of event**: August 17, 2026
**Date of debrief**: [date]
**Participants**: Ernie Steagall, Francis Anyaegbu, Myles Vivian

---

## 1. Event Summary

- Planned attendees: 50
- Actual attendees: [count]
- Clusters provisioned: [count]
- Clusters ready at event start: [count]
- Spare clusters consumed: [count]
- Total incidents: [count]
- Critical incidents: [count]

---

## 2. What Went Well

### 2.1 Environment preparation
[What worked well in the cluster preparation process]

### 2.2 Content and exercises
[Which modules were most effective, best attendee engagement]

### 2.3 Operations and support
[Smooth operational aspects, effective support workflows]

### 2.4 Tooling and automation
[CLI tools, validation, solve/reset automation that worked as designed]

### 2.5 ACM demonstration
[Presenter demo effectiveness]

---

## 3. What Could Be Improved

### 3.1 Environment preparation
[Issues during cluster preparation, timing, reliability]

### 3.2 Content and exercises
[Modules that were too long, too short, confusing, or had errors]

### 3.3 Operations and support
[Support gaps, communication issues, process failures]

### 3.4 Tooling and automation
[CLI bugs, validation gaps, missing automation]

### 3.5 Timing and pacing
[Session pacing issues, modules that ran over or under]

---

## 4. Incidents and Root Causes

| Incident | Root cause | Impact | Resolution time | Prevention |
|----------|-----------|--------|-----------------|------------|
| | | | | |

---

## 5. Metrics

### 5.1 Preparation metrics
| Metric | Value |
|--------|-------|
| Mean cluster preparation time | |
| Median cluster preparation time | |
| Maximum cluster preparation time | |
| Preparation failure rate | |
| Mean retries per cluster | |

### 5.2 Event-day metrics
| Metric | Value |
|--------|-------|
| Clusters replaced during event | |
| Mean time to replace a cluster | |
| Student login success rate | |
| Exercise completion rate (per module) | |

### 5.3 Cost metrics
| Metric | Value |
|--------|-------|
| Total AWS cost | |
| Cost per attendee | |
| Cost per cluster | |
| S3 storage cost | |

---

## 6. Module-Specific Feedback

### 6.1 Navigation and Search (10 min)
- Attendee feedback:
- Facilitator observations:
- Timing accuracy:
- Validation effectiveness:

### 6.2 Advanced Cluster Management (10 min)
- Attendee feedback:
- Presenter observations:
- Demo reliability:
- Timing accuracy:

### 6.3 Updates (20 min)
- Attendee feedback:
- Facilitator observations:
- Timing accuracy:
- Update completion rate:

### 6.4 Observability and Logging (part of 40 min)
- Attendee feedback:
- Facilitator observations:
- Log query success rate:
- Historical log availability:

### 6.5 Identity (part of 40 min)
- Attendee feedback:
- Facilitator observations:
- Keycloak reliability:
- HCP limitations encountered:

---

## 7. Recommendations for Future Events

### 7.1 High priority
[Changes that would have prevented incidents or major issues]

### 7.2 Medium priority
[Improvements that would significantly improve the experience]

### 7.3 Low priority
[Nice-to-have improvements]

---

## 8. Reusable Assets

List assets from this event that can be reused for future events:

| Asset | Location | Reusability | Notes |
|-------|----------|-------------|-------|
| Automation playbooks | mas-world-2026-automation/ | High | Parameterized for any fleet size |
| Showroom content | mas-world-2026-showroom/ | Medium | Update versions and screenshots |
| ACM policies | mas-world-2026-acm/ | High | Label-driven, reusable |
| CLI tooling | masworld CLI | High | Configuration-driven |
| Cost reporting template | mas-world-2026-operations/cost-reporting/ | High | |
| Runbooks | mas-world-2026-operations/runbooks/ | High | Update dates and contacts |

---

## 9. Action Items

| ID | Action | Owner | Priority | Deadline | Status |
|----|--------|-------|----------|----------|--------|
| | | | | | |
```

---

## 10. Cross-References

| Document | Location | Relevance |
|----------|----------|-----------|
| Credential lifecycle design | `docs/credential-lifecycle.md` | Post-event cleanup phase (Section 3.4) |
| Event runbook (pre-event, event day) | `mas-world-2026-operations/runbooks/` | Preceding runbook phases |
| Incident templates | `mas-world-2026-operations/incident-templates/` | Phase 1 incident capture |
| Cost reporting template | `mas-world-2026-operations/cost-reporting/` | Phase 4 cost report |
| Repair procedures | `mas-world-2026-operations/repair-procedures/` | Troubleshooting during teardown |
| Seat assignment guide | `mas-world-2026-operations/seat-assignment/` | Final seat map export |
| Decommission playbook | `mas-world-2026-automation/playbooks/decommission-workshop.yml` | Phase 3 workload removal |
| Fleet validation playbook | `mas-world-2026-automation/playbooks/validate-fleet.yml` | Post-teardown verification |
| Credential rotation playbook | `mas-world-2026-automation/playbooks/rotate-credentials.yml` | Phase 1 credential disable |
| Configuration model | `docs/configuration-model.md` | Configuration file locations |
| Architecture decisions | `docs/decision-log.md` | S3 isolation model, Keycloak deployment model |
| Risk register | `docs/risk-register.md` | Risks related to teardown and data retention |
| Fleet dashboard | `mas-world-2026-operations/fleet-dashboard/` | Real-time fleet status during teardown |
| ACM policies | `mas-world-2026-automation/acm/` | Policy definitions removed in Phase 3 |
| Checklists | `mas-world-2026-operations/checklists/` | Pre-event and event-day checklists |

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-07-19 | Francis Anyaegbu | Initial draft |
