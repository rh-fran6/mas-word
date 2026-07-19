# During-Event Procedures — MAS World 2026

**Status**: DRAFT
**Date**: 2026-07-19
**Event**: MAS World 2026 — August 17, 2026
**Timezone**: America/Chicago
**Cross-references**: [Pre-Event Checklist](../checklists/pre-event.md) | [Event Morning Runbook](event-morning.md) | [Post-Event Runbook](post-event.md) | [Repair Procedures](../repair-procedures/) | [Incident Templates](../incident-templates/)

---

## Quick Reference Card

Commands facilitators will use most during the live session. All commands
assume the `masworld` CLI is installed and configured, and that the
`--environment event` flag is used unless otherwise noted.

### Fleet Status

```bash
# Full fleet dashboard — run every 5 minutes during session
masworld report fleet-status --environment event

# Single cluster health
masworld cluster validate --cluster seat-XX --environment event

# Seat lookup by number
masworld seat show --seat XX --environment event
```

### Attendee Troubleshooting

```bash
# Validate a specific student can log in and reach all services
masworld student validate --seat XX --environment event

# Reset a single exercise module
masworld exercise reset --cluster seat-XX --module MODULE_NAME --environment event

# Modules: navigation, acm, updates, observability, identity
```

### Emergency Cluster Replacement

```bash
# Replace a failed seat with a spare (transactional)
masworld seat replace --seat XX --cluster spare-YY --environment event

# Verify the replacement
masworld cluster validate --cluster spare-YY --environment event
masworld student validate --seat XX --environment event
```

### Credential Rotation (Compromised Account)

```bash
# Rotate a single student password
masworld student rotate --seat XX --environment event

# Disable a student account immediately
masworld student disable --seat XX --environment event

# Regenerate access card after rotation
masworld student export-cards --seat XX --environment event --output /tmp/seat-XX-card.pdf
```

### ACM Drift Restoration

```bash
# Re-stage the safe drift condition on the facilitator cluster
masworld exercise reset --cluster facilitator-01 --module acm --environment event
```

### Exercise Solve (Unblock an Attendee)

```bash
# Run the solve automation for a stuck attendee
masworld exercise solve --cluster seat-XX --module MODULE_NAME --environment event
```

---

## 1. Facilitator Roles and Responsibilities

### 1.1 Ernie Steagall — Primary Presenter

- Drives the screen share and live demonstrations.
- Delivers introductory slides for each segment.
- Leads the ACM fleet management demonstration from the facilitator cluster.
- Leads the MAS updates demonstration.
- Controls session pacing. Announces segment transitions.
- Signals when attendees should begin and end each exercise.
- Does NOT troubleshoot individual attendee environments during live
  presentation segments.
- If a systemic issue is detected, pauses and communicates with the support
  facilitators before continuing.

### 1.2 Francis Anyaegbu — Lab Environment Owner

- Monitors the fleet dashboard continuously.
- Is the first responder for all OpenShift, Showroom, cluster, and
  infrastructure issues.
- Performs cluster replacements and spare swaps.
- Handles credential rotation and student account issues.
- Escalates platform issues to Red Hat or AWS support.
- Walks the room to assist attendees with console, terminal, and
  authentication problems.
- Coordinates with the presenter on timing if infrastructure issues cause
  delays.

### 1.3 Myles Vivian — Observability Lead

- Supports attendees during the observability and logging segment.
- Troubleshoots Loki query issues, log forwarding problems, and S3 access
  failures.
- Assists with identity segment troubleshooting.
- Walks the room to assist attendees during hands-on segments.
- Monitors for observability-specific fleet issues (LokiStack degraded,
  ClusterLogForwarder errors, S3 connectivity).

### 1.4 Shared Responsibilities

- All facilitators watch the session chat or communication channel.
- All facilitators can run `masworld` CLI commands from their workstations.
- All facilitators report incidents using the incident template in
  `../incident-templates/`.
- No facilitator modifies ACM hub policies, fleet configuration, or
  cluster-admin credentials during the session without agreement from at
  least one other facilitator.

---

## 2. Fleet Monitoring Procedures

### 2.1 Monitoring Frequency

| Period                            | Frequency        | Responsible       |
|-----------------------------------|------------------|-------------------|
| Session start (first 10 min)      | Every 2 minutes  | Francis Anyaegbu  |
| During presenter-led segments     | Every 5 minutes  | Francis Anyaegbu  |
| During hands-on exercises         | Every 3 minutes  | Francis Anyaegbu  |
| After cluster replacement         | Continuous until verified | Francis Anyaegbu |
| After credential rotation         | Immediate + 5 min recheck | Francis Anyaegbu |

### 2.2 Fleet Status Command

```bash
masworld report fleet-status --environment event
```

Expected healthy output:

```text
Fleet Status: MAS World 2026 — 2026-08-17
------------------------------------------
Total Clusters:    56
  Ready:           50
  Spare:            5
  Facilitator:      1
  Preparing:        0
  Warning:          0
  Failed:           0
  Quarantined:      0

Assigned Seats:    50 / 50
Unassigned Spare:   5
Last Validated:    2026-08-17T08:45:00-05:00
```

### 2.3 Warning Indicators

Act immediately if any of the following appear:

| Indicator                        | Severity | Action                                        |
|----------------------------------|----------|-----------------------------------------------|
| Any cluster status `FAILED`      | Critical | Begin spare replacement (Section 5)           |
| Any cluster status `WARNING`     | High     | Investigate; prepare spare if degraded        |
| Spare count reaches 0            | High     | Alert all facilitators; no safety margin left  |
| Multiple clusters degraded       | Critical | Pause session; assess scope (Section 11)      |
| ACM hub unreachable              | Critical | ACM demo cannot proceed; skip or defer        |
| S3 connectivity failure (fleet)  | High     | Logging exercises will fail; assess scope      |

### 2.4 Per-Cluster Deep Check

When a specific seat reports trouble:

```bash
masworld cluster validate --cluster seat-XX --environment event --verbose
```

This runs all readiness checks and outputs per-component status:

```text
Cluster: seat-XX
  OpenShift API:             PASS
  OpenShift Console:         PASS
  MAS Core:                  PASS
  Maximo Manage:             PASS
  Database:                  PASS
  Logging Operator:          PASS
  LokiStack:                 PASS
  ClusterLogForwarder:       PASS
  S3 Object Storage:         PASS
  Identity Integration:      PASS
  Showroom:                  PASS
  Student Authentication:    PASS
  Student RBAC:              PASS
```

Time estimate: 30-60 seconds per cluster.

---

## 3. Common Attendee Issues and Solutions

### 3.1 Cannot Log In to OpenShift Console

**Symptoms**: Attendee sees "Login failed" or "Invalid credentials" on the
OpenShift console login page.

**Diagnosis**:

```bash
masworld student validate --seat XX --environment event
```

**Common Causes and Fixes**:

1. **Typo in username or password**: Verify the attendee is using the
   credentials from their access card. Usernames follow the pattern
   `userXX` (e.g., `user01`, `user12`). Confirm the attendee is selecting
   the `htpasswd` identity provider on the login page, not `kube:admin` or
   another provider.

2. **HTPasswd secret not synchronized**: The OAuth server may not have
   picked up the latest HTPasswd secret.

   ```bash
   masworld cluster validate --cluster seat-XX --environment event --check student_authentication
   ```

   If this reports `FAIL`, attempt repair:

   ```bash
   masworld cluster repair --cluster seat-XX --component student-accounts --environment event
   ```

   Time estimate: 1-2 minutes.

3. **OAuth pods not running**: Check if the OAuth server pods are healthy.

   ```bash
   masworld cluster validate --cluster seat-XX --environment event --check openshift_oauth
   ```

   If degraded, this likely requires a cluster replacement (Section 5).

4. **Account disabled or rotated**: If the account was previously disabled
   or rotated, re-enable it:

   ```bash
   masworld student create --seat XX --environment event
   masworld student validate --seat XX --environment event
   ```

**Escalation**: If none of the above resolves the issue within 3 minutes,
replace the cluster with a spare (Section 5).

### 3.2 Cannot Access Maximo

**Symptoms**: Attendee can log into OpenShift but the Maximo URL returns an
error, times out, or shows a blank page.

**Diagnosis**:

```bash
masworld cluster validate --cluster seat-XX --environment event --check mas_core,maximo_manage
```

**Common Causes and Fixes**:

1. **MAS route not resolving**: DNS propagation delay or ingress issue.
   Ask the attendee to try refreshing the page or clearing their browser
   cache. If the route itself is missing, attempt repair:

   ```bash
   masworld cluster repair --cluster seat-XX --component mas-routes --environment event
   ```

2. **MAS pods not ready**: MAS Core or Manage pods may be in a restart
   loop. Check the detailed status:

   ```bash
   masworld cluster validate --cluster seat-XX --environment event --check mas_core --verbose
   ```

   If pods are restarting, this is unlikely to self-heal during the session.
   Replace the cluster (Section 5).

3. **Database connectivity lost**: If the database check fails, the Manage
   application will not function. This requires cluster replacement.

4. **Certificate error in browser**: The attendee may need to accept a
   self-signed certificate. Instruct them to click through the browser
   warning. If certificates are expired, attempt repair:

   ```bash
   masworld cluster repair --cluster seat-XX --component certificates --environment event
   ```

**Escalation**: If MAS Core or Manage is down and repair does not resolve
within 3 minutes, replace the cluster (Section 5).

### 3.3 Showroom Not Loading

**Symptoms**: The Showroom URL from the access card returns a connection
error, timeout, or blank page.

**Diagnosis**:

```bash
masworld cluster validate --cluster seat-XX --environment event --check showroom
```

**Common Causes and Fixes**:

1. **Showroom pod not running**: The Showroom deployment may have been
   evicted or is pending.

   ```bash
   masworld cluster repair --cluster seat-XX --component showroom --environment event
   ```

   Time estimate: 1-2 minutes for the pod to restart.

2. **Incorrect URL on access card**: Verify the URL is correct:

   ```bash
   masworld seat show --seat XX --environment event
   ```

   Compare the `showroom_url` field with the attendee's access card.

3. **Ingress or route issue**: If the route exists but is not responding,
   the cluster ingress controller may be degraded. Check overall cluster
   health before deciding on replacement.

4. **Network issue at the venue**: If multiple attendees report Showroom
   failures simultaneously, verify venue Wi-Fi and network. Try accessing a
   Showroom URL from a facilitator device to confirm.

**Workaround**: If Showroom is down but the cluster is otherwise healthy,
attendees can follow instructions directly from the presenter's shared
screen and use the OpenShift console tab directly via its URL.

### 3.4 Browser Terminal Not Connecting

**Symptoms**: The terminal tab in Showroom shows "Connecting..." indefinitely
or displays a WebSocket error.

**Diagnosis**:

```bash
masworld cluster validate --cluster seat-XX --environment event --check showroom --verbose
```

**Common Causes and Fixes**:

1. **Terminal pod not running**: The web terminal operator pod may need
   restarting.

   ```bash
   masworld cluster repair --cluster seat-XX --component web-terminal --environment event
   ```

2. **WebSocket blocked by venue network**: If multiple attendees experience
   this, the venue network may be blocking WebSocket connections. Test from
   a facilitator device on the same network.

   **Workaround**: Instruct the attendee to use the OpenShift console's
   built-in terminal (Terminal tab in the console) instead of the Showroom
   embedded terminal, or use `oc` CLI from their laptop if they have it
   installed.

3. **Session expired**: Ask the attendee to refresh the Showroom page and
   re-authenticate if prompted.

### 3.5 Exercise Validation Failing

**Symptoms**: The attendee has completed the exercise steps but the
validation check reports failure.

**Diagnosis**:

```bash
masworld exercise validate --cluster seat-XX --module MODULE_NAME --environment event --verbose
```

Replace `MODULE_NAME` with the relevant module: `navigation`, `acm`,
`updates`, `observability`, `identity`.

**Common Causes and Fixes**:

1. **Timing issue**: Some resources take time to reconcile. Ask the attendee
   to wait 30 seconds and retry validation.

2. **Incomplete steps**: Review the verbose validation output to determine
   which specific check failed. The output identifies the expected state and
   actual state. Guide the attendee to complete the missing step.

3. **Attendee worked in wrong namespace**: Confirm the attendee is operating
   in their assigned namespace (`student-XX`). A common mistake is working
   in the `default` namespace.

4. **Run the solve automation**: If the attendee is stuck and the session
   must move forward:

   ```bash
   masworld exercise solve --cluster seat-XX --module MODULE_NAME --environment event
   ```

   Then re-validate:

   ```bash
   masworld exercise validate --cluster seat-XX --module MODULE_NAME --environment event
   ```

### 3.6 Loki Query Returning No Results

**Symptoms**: During the observability exercise, the attendee runs a log
query and gets zero results or "no data found."

**Diagnosis**:

```bash
masworld cluster validate --cluster seat-XX --environment event --check lokistack,cluster_log_forwarder,s3_write_read,historical_log_query
```

**Common Causes and Fixes**:

1. **Sample workload not deployed or already cleaned up**: The log-generating
   workload may not have been created, or it may have been deleted before
   logs were ingested.

   ```bash
   masworld exercise reset --cluster seat-XX --module observability --environment event
   ```

   This re-deploys the sample workload with a new run ID. Instruct the
   attendee to wait 60-90 seconds for log ingestion before querying.

2. **Wrong query or time range**: Verify the attendee is using the correct
   LogQL query from the instructions and has selected a time range that
   covers the sample workload's execution. Common mistake: the time range
   picker is set to "Last 5 minutes" but the workload ran 10 minutes ago.
   Advise switching to "Last 30 minutes" or "Last 1 hour."

3. **ClusterLogForwarder misconfigured or errored**: If the CLF check
   fails, attempt repair:

   ```bash
   masworld cluster repair --cluster seat-XX --component log-forwarding --environment event
   ```

   Time estimate: 1-2 minutes for collector pods to restart and begin
   forwarding.

4. **LokiStack not ready**: If LokiStack is degraded, logs cannot be
   queried. Check:

   ```bash
   masworld cluster validate --cluster seat-XX --environment event --check lokistack --verbose
   ```

   If LokiStack is in a crash loop, this is unlikely to self-heal during
   the session. Consider cluster replacement (Section 5).

5. **S3 bucket inaccessible**: If the S3 write/read check fails, Loki
   cannot persist or retrieve logs.

   ```bash
   masworld cluster validate --cluster seat-XX --environment event --check s3_write_read --verbose
   ```

   If credentials are invalid, attempt rotation:

   ```bash
   masworld cluster repair --cluster seat-XX --component s3-credentials --environment event
   ```

   If the bucket itself is gone or the AWS region is unreachable, this
   requires AWS escalation (Section 8.4).

### 3.7 Identity Exercise Not Working

**Symptoms**: The attendee cannot complete the identity/Keycloak exercise
steps. Keycloak UI is inaccessible, OIDC login fails, or LDAP group sync
does not produce expected results.

**Diagnosis**:

```bash
masworld cluster validate --cluster seat-XX --environment event --check identity
masworld exercise validate --cluster seat-XX --module identity --environment event --verbose
```

**Common Causes and Fixes**:

1. **Keycloak pod not running or route inaccessible**: Attempt repair:

   ```bash
   masworld cluster repair --cluster seat-XX --component keycloak --environment event
   ```

   Time estimate: 1-3 minutes for Keycloak to restart.

2. **Preconfigured OIDC client missing or misconfigured**: The identity
   exercise depends on pre-staged Keycloak configuration. If this is
   missing, reset the exercise:

   ```bash
   masworld exercise reset --cluster seat-XX --module identity --environment event
   ```

3. **OAuth server not updated with IDP configuration**: If the OpenShift
   OAuth server does not list the expected identity provider, repair:

   ```bash
   masworld cluster repair --cluster seat-XX --component identity-oauth --environment event
   ```

4. **LDAP group sync not producing expected groups**: The LDAP server or
   sync configuration may be incorrect. Run the solve to apply the expected
   final state:

   ```bash
   masworld exercise solve --cluster seat-XX --module identity --environment event
   ```

5. **HCP OAuth limitations**: If the cluster is a Hosted Control Plane
   (HCP) cluster, certain OAuth customizations are not supported. The
   Showroom content documents these limitations. If an attendee encounters
   HCP-specific behavior, direct them to the "Platform Considerations"
   callout box in the identity module.

**Workaround**: If Keycloak is unrecoverable, the attendee can observe the
presenter's demonstration and inspect the pre-staged resources (read-only)
using `oc get` commands documented in the identity module's fallback
section.

---

## 4. Exercise Reset Procedures

Each module has a reset playbook that restores the exercise to its initial
state. Resets are idempotent and safe to run multiple times.

### 4.1 Navigation and Search

```bash
masworld exercise reset --cluster seat-XX --module navigation --environment event
```

- Removes any resources the attendee created in their namespace during the
  navigation exercise.
- Restores the sample resources used for search exercises.
- Time estimate: 15-30 seconds.

### 4.2 ACM Fleet Management

The ACM module is primarily presenter-led. Attendees verify a propagated
marker on their own cluster. To reset the attendee-side verification:

```bash
masworld exercise reset --cluster seat-XX --module acm --environment event
```

- Removes the event marker ConfigMap from the attendee cluster so the
  attendee can observe it being re-propagated.
- Time estimate: 10-15 seconds.

To re-stage the drift condition on the facilitator cluster for the live
demo, see Section 6.

### 4.3 Updates

```bash
masworld exercise reset --cluster seat-XX --module updates --environment event
```

- Reverts the attendee's update exercise to the pre-staged initial state.
- Restores the operator or component to its pre-update version or
  configuration.
- Does NOT trigger a full MAS reinstallation.
- Time estimate: 1-2 minutes.

IMPORTANT: Only reset the updates module if the attendee has not progressed
past the point of no return documented in the module. If the attendee has
completed the update, the reset will revert it, which takes additional time.
Confirm with the attendee before resetting.

### 4.4 Observability and Logging

```bash
masworld exercise reset --cluster seat-XX --module observability --environment event
```

- Deletes and re-creates the sample log-generating workload with a new run
  ID and seat ID.
- Does NOT delete existing logs from Loki/S3.
- Does NOT reinstall or reconfigure the Logging Operator, LokiStack, or
  ClusterLogForwarder.
- The attendee must wait 60-90 seconds after reset for new logs to appear.
- Time estimate: 30-60 seconds for the reset command; 60-90 seconds for log
  ingestion.

### 4.5 Identity

```bash
masworld exercise reset --cluster seat-XX --module identity --environment event
```

- Restores the Keycloak client configuration to its pre-exercise state.
- Removes any OAuth provider changes the attendee may have applied.
- Restores the LDAP group sync configuration.
- Time estimate: 1-2 minutes (Keycloak reconciliation).

### 4.6 Bulk Reset (All Modules for One Cluster)

If a cluster needs a full exercise reset across all modules:

```bash
masworld exercise reset --cluster seat-XX --module all --environment event
```

Time estimate: 3-5 minutes.

---

## 5. Mid-Session Cluster Replacement (Spare Swap)

Use this procedure when a cluster is unrecoverably failed and must be
replaced by a spare during the live session.

### 5.1 Prerequisites

- At least one spare cluster is available and in `READY` status.
- The spare has been validated during the event morning checks.
- The failed cluster's seat number is known.

### 5.2 Procedure

Time estimate for the entire procedure: 3-5 minutes.

**Step 1**: Identify the failed seat and an available spare.

```bash
masworld seat show --seat XX --environment event
masworld report fleet-status --environment event | grep -E "Spare|spare"
```

**Step 2**: Perform the replacement. This is a transactional operation. It
will:
- Disable the student credential on the old cluster.
- Create or activate the student credential on the spare cluster.
- Update Showroom endpoint data.
- Update the seat assignment inventory.
- Validate the replacement cluster.
- Mark the old cluster as quarantined.

```bash
masworld seat replace --seat XX --cluster spare-YY --environment event
```

If the command fails partway through, the seat assignment remains pointed
at the original cluster. The operation can be retried safely.

**Step 3**: Verify the replacement.

```bash
masworld cluster validate --cluster spare-YY --environment event
masworld student validate --seat XX --environment event
```

Both commands must report all checks as `PASS`.

**Step 4**: Generate a new access card for the attendee.

```bash
masworld student export-cards --seat XX --environment event --output /tmp/seat-XX-card.pdf
```

**Step 5**: Deliver the new access card to the attendee. Inform them that
their URLs and possibly their password have changed. Walk them through
logging in to the new environment.

**Step 6**: Confirm the old cluster is quarantined and excluded from future
assignment.

```bash
masworld seat show --seat XX --environment event
masworld report fleet-status --environment event
```

The old cluster should appear with status `Quarantined`. The spare count
will have decreased by one.

### 5.3 If No Spares Are Available

If the spare pool is exhausted:

1. Alert all facilitators immediately.
2. Attempt repair on the failed cluster:

   ```bash
   masworld cluster repair --cluster seat-XX --environment event
   masworld cluster validate --cluster seat-XX --environment event
   ```

3. If repair fails, the attendee cannot continue with a dedicated
   environment. Options:
   - Pair the attendee with an adjacent seat (both follow the same screen).
   - The attendee follows along with the presenter's shared screen only.
4. Record the incident for the post-event report.

---

## 6. Restoring ACM Drift After the Demo Section

The ACM fleet management demonstration uses a deliberately noncompliant
facilitator cluster to show policy detection and remediation. After the
demo, the drift condition must be re-staged so it is available if the demo
needs to be repeated or referenced later.

### 6.1 When to Restore Drift

- Immediately after the ACM demo segment concludes and the presenter
  transitions to the next section.
- If the presenter requests a repeat of the drift demo.

### 6.2 Procedure

**Step 1**: Verify the facilitator cluster is compliant (post-remediation
state from the demo):

```bash
masworld cluster validate --cluster facilitator-01 --environment event --check acm_compliance
```

**Step 2**: Re-stage the safe drift condition:

```bash
masworld exercise reset --cluster facilitator-01 --module acm --environment event
```

This command:
- Removes or modifies the harmless event ConfigMap on the facilitator
  cluster to create the noncompliant state.
- Does NOT modify any MAS, Loki, OAuth, ingress, or certificate resources.
- Does NOT affect any attendee cluster.

**Step 3**: Verify the drift is detected by ACM:

```bash
masworld cluster validate --cluster facilitator-01 --environment event --check acm_drift_staged
```

Expected output: the facilitator cluster shows as noncompliant for the
targeted policy, and all attendee clusters remain compliant.

Time estimate: 1-2 minutes for the drift to be detected by ACM governance.

### 6.3 Safety Constraints

- Drift is ONLY staged on `facilitator-01`. Never stage drift on an
  attendee cluster.
- The drifted resource is a dedicated event ConfigMap. Critical services
  (MAS, Loki, OAuth, ingress, ACM connectivity) are never deliberately
  broken.
- If drift staging fails, do not attempt manual modification of ACM
  policies. Record the issue and skip re-staging.

---

## 7. Handling Compromised Credentials

Use this procedure if a student password is believed to be compromised
(shared publicly, visible on a screen, written on a whiteboard, etc.) or if
an attendee reports unauthorized activity in their namespace.

### 7.1 Immediate Rotation

**Step 1**: Rotate the credential immediately:

```bash
masworld student rotate --seat XX --environment event
```

This command:
- Generates a new cryptographically secure password.
- Updates the HTPasswd secret on the cluster.
- Stores the new password in the configured secret provider.
- Forces the OAuth server to pick up the change.

Time estimate: 30-60 seconds.

**Step 2**: Validate the new credential works:

```bash
masworld student validate --seat XX --environment event
```

**Step 3**: Generate a new access card:

```bash
masworld student export-cards --seat XX --environment event --output /tmp/seat-XX-card.pdf
```

**Step 4**: Deliver the new access card to the attendee privately. Inform
them their old password no longer works.

### 7.2 If Unauthorized Activity Is Suspected

If there is evidence that the compromised credential was used to access the
environment:

**Step 1**: Disable the account immediately, then investigate:

```bash
masworld student disable --seat XX --environment event
```

**Step 2**: Check for unauthorized resources in the attendee namespace. Use
the facilitator's cluster-admin access (not the student credential):

```bash
# From a facilitator workstation with appropriate access
oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH get all -n student-XX
oc --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH get events -n student-XX --sort-by='.lastTimestamp'
```

**Step 3**: If the namespace is clean, re-enable the account with a new
password:

```bash
masworld student create --seat XX --environment event
masworld student validate --seat XX --environment event
```

**Step 4**: If the namespace contains unauthorized resources, reset the
exercises and re-create the account:

```bash
masworld exercise reset --cluster seat-XX --module all --environment event
masworld student create --seat XX --environment event
```

**Step 5**: Record the incident using the template in
`../incident-templates/`.

### 7.3 Bulk Credential Compromise

If multiple credentials are compromised (e.g., the seat map was displayed
publicly):

```bash
# Rotate all student credentials
masworld student rotate --all --environment event

# Regenerate all access cards
masworld student export-cards --all --environment event --output /tmp/access-cards/

# Export updated seat map for facilitators
masworld seat export-map --environment event --output /tmp/seat-map-rotated.json
```

Time estimate: 2-5 minutes for full fleet rotation. Access cards must be
redistributed to all attendees. Announce the rotation and ask attendees to
use their new credentials.

---

## 8. Escalation Procedures

### 8.1 When to Escalate

Escalate when:

- A problem affects 3 or more attendee clusters simultaneously.
- A single cluster cannot be repaired or replaced within 5 minutes.
- The ACM hub is unreachable or degraded.
- AWS services (S3, IAM, Secrets Manager) are experiencing failures.
- IBM registry (cp.icr.io) is unreachable.
- MAS or Manage enters a state that cannot be recovered by the repair
  automation.
- A security incident is suspected (unauthorized access beyond a single
  compromised password).
- The venue network is causing widespread connectivity failures.
- All spare clusters are exhausted and additional clusters are failing.

### 8.2 Internal Escalation (Facilitator Team)

| Role                | Escalation Scope                              |
|---------------------|-----------------------------------------------|
| Lab Environment Owner (Francis) | OpenShift, ACM, Showroom, fleet, credentials |
| Observability Lead (Myles) | Logging, Loki, S3, identity, Keycloak          |
| Primary Presenter (Ernie) | Session timing, content decisions, attendee comms |

Communication channel: Use the pre-arranged facilitator communication
channel (configured during pre-event setup). Do not rely solely on verbal
communication across the room.

### 8.3 Red Hat Support

**When**: OpenShift platform issues, ACM hub degradation, Operator
failures, cluster-level problems not resolved by repair automation.

**How**:

1. Open a case at https://access.redhat.com/support/cases/ with severity
   based on impact:
   - Severity 1: Multiple clusters down, event blocked.
   - Severity 2: Single cluster issue, workaround available (spare swap).
2. Provide:
   - Cluster ID and version.
   - `masworld cluster validate` output (ensure no secrets are included).
   - Description of the failure and steps taken.
   - Must-gather output if time permits:
     ```bash
     oc adm must-gather --kubeconfig=PLACEHOLDER_KUBECONFIG_PATH --dest-dir=/tmp/must-gather-seat-XX
     ```
3. Reference the event context: "MAS World 2026 conference workshop,
   live session in progress, 50 attendees affected."
4. The Lab Environment Owner is the primary contact for Red Hat support.

### 8.4 AWS Support

**When**: S3 bucket access failures, IAM credential issues, Secrets Manager
unavailability, regional service degradation.

**How**:

1. Check the AWS Service Health Dashboard for the configured region.
2. If no known outage, open a support case through the AWS console or CLI:
   ```bash
   # Check S3 bucket accessibility
   aws s3 ls s3://PLACEHOLDER_BUCKET_NAME --region PLACEHOLDER_AWS_REGION
   ```
3. Provide:
   - AWS account ID (from configuration, not hard-coded here).
   - Region.
   - Bucket name(s) affected.
   - Error messages from the `masworld` CLI output.
4. The Lab Environment Owner is the primary contact for AWS support.

### 8.5 IBM Support

**When**: MAS or Manage enters an unrecoverable state, IBM registry
(cp.icr.io) is unreachable, licensing issues.

**How**:

1. Open a case at https://www.ibm.com/mysupport with the MAS product
   selected.
2. Provide:
   - MAS version.
   - OpenShift version.
   - MAS custom resource status.
   - Pod logs for failing MAS components (ensure no secrets are included).
3. Reference the event context.
4. IBM support cases are unlikely to resolve during the live session. For
   MAS failures, the primary mitigation is cluster replacement with a spare.

### 8.6 Escalation Log

Record all escalations in the facilitator communication channel and in the
incident template. After the event, consolidate into the post-event report.

---

## 9. Communication Protocol Between Facilitators

### 9.1 Communication Channel

All facilitators must have the pre-arranged communication channel open on a
secondary device (phone, tablet, or second laptop screen) throughout the
session. This channel is used for:

- Fleet status alerts.
- Attendee issue reports.
- Timing coordination.
- Escalation notifications.
- Spare cluster availability warnings.

### 9.2 Message Conventions

Use clear, concise messages with these prefixes:

| Prefix           | Meaning                                              |
|------------------|------------------------------------------------------|
| `FLEET:`         | Fleet-wide status update or alert                    |
| `SEAT XX:`       | Issue with a specific seat                           |
| `REPLACE:`       | Spare swap initiated or completed                    |
| `TIMING:`        | Session pacing concern or schedule adjustment         |
| `ESCALATION:`    | External support case opened                         |
| `RESOLVED:`      | Previously reported issue resolved                   |
| `ACM:`           | ACM demo drift staging or compliance update          |

Examples:

```text
SEAT 17: Cannot access Maximo. Attempting repair.
SEAT 17: Repair failed. Replacing with spare-03.
REPLACE: Seat 17 now on spare-03. Validated. New card delivered.
FLEET: All clusters READY. Spare count: 4.
TIMING: Observability segment running 3 min long. Suggest shortening identity intro.
```

### 9.3 When to Notify the Presenter

Notify the presenter (through the communication channel, not by
interrupting the presentation) when:

- A fleet-wide issue may require pausing the session.
- The spare pool is exhausted.
- A segment must be skipped or shortened due to technical issues.
- An escalation has been opened that affects the session content.
- More than 3 attendees are blocked on the same issue (may indicate a
  systemic problem or unclear instructions).

Do NOT notify the presenter for:

- Individual seat issues being handled by support facilitators.
- Routine spare swaps.
- Exercise resets.

---

## 10. Session Timing and Pacing Guidance

### 10.1 Session Schedule

| Start    | Duration | Segment                          | Lead   |
|----------|----------|----------------------------------|--------|
| T+00:00  | 10 min   | Navigation and Search            | Ernie  |
| T+10:00  | 10 min   | ACM Fleet Management             | Ernie  |
| T+20:00  | 20 min   | Updates                          | Ernie  |
| T+40:00  | 40 min   | Observability and Identity       | Ernie  |
|          |          | (combined segment)               |        |

Total session time: approximately 80 minutes.

### 10.2 Segment Structure (Repeated for Each Section)

1. **Introductory slide** (1-2 min): Presenter explains what and why.
2. **Presenter demonstration** (where applicable): Presenter shows the
   operation on the facilitator cluster or shared screen.
3. **Attendee exercise** (bounded time): Attendees follow steps in
   Showroom. A timer or clear end signal is given by the presenter.
4. **Validation** (1-2 min): Attendees run validation. Facilitators
   verify fleet-wide.
5. **Transition** (30 sec): Brief summary, transition to next segment.

### 10.3 Pacing Rules

- The presenter controls segment timing. Support facilitators do not
  extend segments without the presenter's agreement.
- If more than 25% of attendees (13 or more) are not finished when the
  exercise timer expires, the presenter may grant a 2-minute extension
  once per segment.
- If an attendee is stuck, support facilitators run the solve automation
  rather than spending more than 2-3 minutes on manual troubleshooting:

  ```bash
  masworld exercise solve --cluster seat-XX --module MODULE_NAME --environment event
  ```

- If a technical issue causes a segment to run long, the presenter and
  support facilitators agree (via the communication channel) which
  subsequent segment to shorten or which content to mark as "take-home."

### 10.4 Time Buffer Allocation

Build a 5-10 minute buffer into the overall session. If the session runs
ahead of schedule, the extra time can be used for:

- Extended Q&A.
- Additional exploration of Maximo.
- Deeper dive into production architecture considerations.
- Attendee-driven questions about their own environments.

If the session runs behind, use the buffer to absorb the delay. If the
buffer is exhausted, prioritize completing the observability and identity
segments, as they have the most hands-on content.

### 10.5 Segment-Specific Timing Notes

**Navigation and Search (10 min)**:
- Simplest segment. Should not overrun.
- If it finishes early, the presenter can add a brief Q&A before moving to
  ACM.

**ACM Fleet Management (10 min)**:
- Primarily presenter-led. Timing is controlled by the presenter.
- The drift/remediation demo must be rehearsed to complete within the
  allocated time. If remediation takes longer than expected, the presenter
  can narrate the expected outcome and move on.
- Attendee verification of the propagated marker should take less than
  2 minutes.

**Updates (20 min)**:
- The update exercise is designed to complete within the allocated window.
  If a full MAS update is not feasible, the pre-staged approach is used.
- If the update exercise takes longer than expected on some clusters,
  run the solve automation for stragglers.

**Observability and Identity (40 min combined)**:
- Approximately 20 minutes for observability, 20 minutes for identity.
  The exact split is flexible.
- Observability depends on log ingestion timing. Build in 60-90 seconds of
  wait time after deploying the sample workload before attendees query.
- Identity exercises depend on Keycloak responsiveness. If Keycloak is slow,
  allow additional time.

---

## 11. Emergency Procedures (Complete Environment Failure)

### 11.1 Definition of Complete Environment Failure

A complete environment failure is defined as any situation where 10 or more
attendee clusters (20% of the fleet) are simultaneously unreachable,
failed, or unusable, OR where a shared dependency (ACM hub, AWS region,
IBM registry, venue network) is down and affecting all attendees.

### 11.2 Immediate Actions

**Step 1**: The Lab Environment Owner announces the issue to all
facilitators on the communication channel:

```text
FLEET: EMERGENCY — [description of failure]. [X] clusters affected. Assessing scope.
```

**Step 2**: The presenter pauses the hands-on exercise and transitions to
a discussion or Q&A slide while the issue is assessed.

**Step 3**: Diagnose the scope:

```bash
masworld report fleet-status --environment event
```

Classify the failure:

| Scope                                    | Category       |
|------------------------------------------|----------------|
| Single cluster                           | Not an emergency. Use spare swap. |
| 2-9 clusters                             | Elevated. Swap spares; investigate root cause. |
| 10+ clusters simultaneously              | Emergency. Pause session. |
| ACM hub down                             | ACM demo cannot proceed; other exercises may continue. |
| AWS region degraded                      | Logging exercises cannot proceed; other exercises may continue. |
| Venue network down                       | All access lost. Wait for network restoration. |
| IBM registry unreachable                 | No immediate impact if MAS is already installed. |

**Step 4**: Based on the category, follow the appropriate path below.

### 11.3 Partial Fleet Failure (10+ Clusters, Shared Dependencies Intact)

1. Identify affected clusters:

   ```bash
   masworld report fleet-status --environment event --filter status=FAILED,WARNING
   ```

2. Attempt bulk repair:

   ```bash
   masworld cluster repair --filter status=FAILED --environment event --max-concurrent 5
   ```

3. Replace clusters that cannot be repaired, starting with the highest seat
   numbers (those attendees are farthest from the presenter and most likely
   to need individual support):

   ```bash
   masworld seat replace --seat XX --cluster spare-YY --environment event
   ```

4. If spares are exhausted, pair affected attendees with nearby working
   seats.

5. Resume the session once 80% or more of seats are functional.

### 11.4 Shared Dependency Failure

**ACM Hub Down**:
- Skip the ACM demo segment. The presenter describes the concepts with
  slides.
- All other exercises can continue on individual clusters.
- Notify attendees that the ACM segment will be provided as a recorded
  demo or follow-up material.

**AWS S3/IAM Outage**:
- The observability exercise (Loki queries) will fail.
- All other exercises can continue.
- The presenter demonstrates logging concepts with slides or a pre-recorded
  demo.
- If S3 recovers during the session, re-attempt the observability exercise.

**Venue Network Failure**:
- No attendee can access any cluster.
- The presenter continues with slides and pre-recorded demonstrations.
- All facilitators monitor for network restoration.
- When network is restored:
  1. Revalidate fleet.
  2. Reset exercises that were in progress.
  3. Resume hands-on exercises from the current segment.

**Full Infrastructure Failure (All Clusters Unreachable)**:
- The presenter continues with slides and pre-recorded demonstrations for
  all remaining segments.
- If recovery occurs before the session ends, resume with abbreviated
  exercises.
- Provide attendees with access information to continue the lab after the
  session (if clusters are restored).

### 11.5 Recovery Validation After Emergency

After any emergency recovery, before resuming hands-on exercises:

```bash
# Full fleet validation
masworld fleet validate --environment event

# Verify all student accounts
masworld student validate --all --environment event

# Generate updated fleet report
masworld report fleet-status --environment event
```

Only resume hands-on exercises when the fleet status shows at least 80% of
seats in `READY` status.

### 11.6 Post-Emergency Communication

After the emergency is resolved:

1. The presenter briefly acknowledges the interruption and thanks attendees
   for their patience.
2. The presenter clearly states which exercise the session is resuming from.
3. Facilitators proactively check on attendees who had cluster replacements
   during the emergency.
4. All facilitators record the incident details for the post-event report
   using the template in `../incident-templates/`.

---

## Appendix A: Module Name Reference

For use with `masworld exercise` subcommands:

| Module Name      | Session Segment                   |
|------------------|-----------------------------------|
| `navigation`     | Navigation and Search             |
| `acm`            | ACM Fleet Management              |
| `updates`        | Updates                           |
| `observability`  | Observability and Logging         |
| `identity`       | Identity Provider Integration     |

## Appendix B: Cluster Naming Convention

| Pattern            | Purpose                          |
|--------------------|----------------------------------|
| `seat-XX`          | Attendee cluster (XX = 01-50)    |
| `spare-YY`         | Spare cluster (YY = 01-05)       |
| `facilitator-ZZ`   | Facilitator cluster (ZZ = 01)    |

## Appendix C: Key File Locations

| Resource                    | Path                                           |
|-----------------------------|------------------------------------------------|
| Fleet configuration         | `config/event.yaml`                            |
| Cluster inventory            | `config/clusters.yaml`                         |
| Credential references        | `config/credentials.yaml`                      |
| Component configuration      | `config/components.yaml`                       |
| Incident templates           | `../incident-templates/`                       |
| Pre-event checklist          | `../checklists/pre-event.md`                   |
| Event morning runbook        | `event-morning.md`                             |
| Post-event runbook           | `post-event.md`                                |
| Repair procedures            | `../repair-procedures/`                        |

## Appendix D: Status Codes

| Status         | Meaning                                           |
|----------------|---------------------------------------------------|
| `READY`        | All mandatory checks passed                       |
| `WARNING`      | Non-critical checks failed; cluster is usable     |
| `FAILED`       | Mandatory checks failed; cluster is not assignable|
| `PREPARING`    | Cluster preparation is in progress                |
| `QUARANTINED`  | Cluster has been replaced and excluded            |
| `NOT_APPLICABLE` | Check does not apply (component disabled)       |
