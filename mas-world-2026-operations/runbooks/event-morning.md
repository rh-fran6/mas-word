# Event Morning Runbook -- MAS World 2026

**Event:** MAS World 2026
**Date:** August 17, 2026
**Timezone:** America/Chicago (CDT, UTC-5)
**Session Start:** Determined by event schedule (referred to as T-0 below)
**Maximum Attendance:** 50
**Fleet:** 50 attendee clusters + 5 spare clusters + 1 facilitator cluster

**Facilitators:**

| Name | Role | Responsibility |
|---|---|---|
| Ernie Steagall (ONEOK) | Primary Presenter | Screen sharing, live demonstrations |
| Francis Anyaegbu (Red Hat) | Lab Owner | OpenShift environment, Showroom, attendee support |
| Myles Vivian (Cohesive) | Observability Lead | Observability content, attendee support |

**Related Runbooks:**

- `runbooks/pre-event.md` -- Full pre-event preparation (T-7 days through T-1 day)
- `runbooks/during-event.md` -- Live session monitoring and incident response
- `runbooks/after-event.md` -- Teardown, credential revocation, cleanup
- `repair-procedures/` -- Detailed per-component repair procedures
- `incident-templates/` -- Structured incident report templates
- `checklists/event-morning-checklist.md` -- Condensed checklist version of this runbook

**Prerequisites:**

- All clusters were prepared and validated during the pre-event window
- Credentials were rotated within the past 24 hours
- The event release is frozen and pinned to immutable tags
- All facilitators have reviewed this runbook

---

## Timeline Summary

| Time | Phase | Duration | Owner |
|---|---|---|---|
| T-4h | Facilitator assembly and workstation setup | 30 min | All |
| T-3h30m | Communications check | 15 min | All |
| T-3h | Full fleet revalidation | 30 min | Francis |
| T-2h30m | Failed cluster replacement | 30 min | Francis |
| T-2h | ACM compliance and drift staging | 30 min | Francis, Ernie |
| T-1h30m | Service confirmation | 30 min | All |
| T-1h | Student login validation and access cards | 30 min | Francis |
| T-30m | Presenter account and demo verification | 15 min | Ernie, Francis |
| T-15m | Change freeze and go/no-go decision | 15 min | All |
| T-0 | Session start | -- | Ernie |

---

## Phase 1: Facilitator Assembly and Workstation Setup (T-4h)

### Objective

All three facilitators are physically present, have functioning workstations, network
connectivity, and access to all required systems.

### 1.1 Facilitator check-in

All three facilitators must confirm presence in the workshop room or designated
staging area. If a facilitator is unreachable, escalate immediately.

**Escalation:** Contact the event coordinator. If a facilitator cannot attend,
activate the backup facilitator plan documented in `runbooks/pre-event.md`.

### 1.2 Workstation setup

Each facilitator workstation requires:

- Laptop with VPN or direct network access to cluster APIs
- Browser with tabs pre-loaded (see Section 1.3)
- Terminal with `masworld` CLI installed and configured
- Access to the `masworld` configuration directory
- SSH key or credential to reach jump hosts if applicable
- Power supply connected
- External display connected (presenter workstation only)

### 1.3 Verify CLI and configuration access

Run on each facilitator workstation:

```bash
masworld config validate --environment event
```

**Expected output:**

```
Configuration validation: PASSED
Environment: event
Fleet: 56 clusters (50 attendee, 5 spare, 1 facilitator)
Secret provider: connected
All credential references: resolvable
```

**Failure handling:**

If configuration validation fails:

```bash
masworld config render --environment event --redacted
```

Review the rendered configuration for missing or incorrect values. Common issues:

- Secret provider unreachable from conference network -- verify VPN or network path.
- Stale cached credentials -- clear the credential cache and retry.
- Configuration file not updated to event environment -- confirm the
  `MASWORLD_ENVIRONMENT=event` environment variable is set.

### 1.4 Verify network connectivity to cluster APIs

```bash
masworld fleet validate --check api-reachability --environment event
```

**Expected output:**

```
API reachability check:
  Attendee clusters: 50/50 reachable
  Spare clusters:     5/5 reachable
  Facilitator:        1/1 reachable
  Total:             56/56 reachable
```

**Failure handling:**

If any clusters are unreachable:

1. Confirm the facilitator workstation has the correct network route (VPN, proxy,
   or direct).
2. Confirm the conference venue network permits outbound HTTPS to cluster API
   endpoints on port 6443.
3. If the venue network blocks required ports, engage the event networking team
   immediately. This is a blocking issue.
4. Test from a mobile hotspot as a fallback to isolate venue network issues.

### 1.5 Verify presenter display and projection

Ernie must confirm:

- External display or projector is connected and mirroring or extending.
- Resolution is readable from the back of the room.
- Browser zoom level is set to at least 125% for visibility.
- Terminal font size is at least 16pt.

### 1.6 Communications check (T-3h30m)

Confirm the facilitator communication channel is operational:

- All three facilitators can send and receive messages on the agreed channel
  (Slack, Teams, or equivalent).
- Ernie can hear and respond to Francis and Myles during the session.
- A shared incident-tracking document or channel is open and bookmarked.

**Timing:** This phase must be complete by T-3h. If any facilitator workstation
is non-functional at T-3h, escalate to the event coordinator.

---

## Phase 2: Full Fleet Revalidation (T-3h)

### Objective

Confirm that all 56 clusters remain in a READY state after overnight. Detect any
clusters that have degraded since the last pre-event validation.

### 2.1 Run full fleet validation

```bash
masworld fleet validate \
  --environment event \
  --output json \
  --output-file /tmp/fleet-validation-t3h.json \
  --concurrency 10
```

**Expected duration:** 15-25 minutes for 56 clusters at concurrency 10.

**Expected output (summary):**

```
Fleet validation complete.
  READY:          56
  WARNING:         0
  FAILED:          0
  NOT_APPLICABLE:  0

All 56 clusters passed mandatory checks.
Report written to: /tmp/fleet-validation-t3h.json
```

### 2.2 Review the fleet status report

```bash
masworld report fleet-status --environment event
```

**Expected output:**

```
Fleet Status Report -- MAS World 2026
Generated: 2026-08-17T06:00:00-05:00

Total clusters:   56
Ready:            56
Preparing:         0
Warning:           0
Failed:            0
Assigned:          0
Unassigned:       50
Spare:             5
Facilitator:       1
Quarantined:       0
Last validated:   2026-08-17T06:00:00-05:00
```

### 2.3 Review individual cluster results

If any clusters show WARNING or FAILED:

```bash
masworld cluster validate --cluster <CLUSTER_ID> --verbose
```

Examine the per-check breakdown:

```
Cluster: seat-17
  openshift_api:            PASS
  openshift_console:        PASS
  mas_core:                 PASS
  maximo_manage:            PASS
  database:                 PASS
  logging_operator:         PASS
  lokistack:                PASS
  cluster_log_forwarder:    PASS
  s3_write_read:            PASS
  historical_log_query:     PASS
  identity:                 PASS
  showroom:                 PASS
  runtime_automation:       PASS
  student_authentication:   PASS
  student_rbac:             PASS
  mas_edge:                 NOT_APPLICABLE
  Overall:                  READY
```

### 2.4 Failure handling

**If 1-5 clusters are FAILED:**

Proceed to Phase 3 (spare replacement). This is the expected workflow.

**If more than 5 clusters are FAILED:**

This exceeds spare capacity. Escalate immediately:

1. Attempt automated repair on each failed cluster (see Phase 3 repair steps).
2. If repair does not restore enough clusters, assess whether the event can
   proceed with fewer seats.
3. Contact the event coordinator about reduced capacity.
4. Document the situation in the incident channel.

**If the facilitator cluster is FAILED:**

This blocks the ACM demonstration. Prioritize repair of the facilitator cluster
above spare replacement. If the facilitator cluster cannot be repaired, designate
one spare as the new facilitator cluster:

```bash
masworld cluster repair --cluster facilitator-01 --verbose
```

If repair fails:

```bash
# Reassign a spare as facilitator (requires manual inventory update)
# Document this in the incident channel before proceeding
masworld config render --environment event --redacted | grep spare
```

**Timing:** Fleet revalidation must be complete by T-2h30m. If it is still
running at T-2h30m, reduce concurrency and allow it to finish, but begin spare
replacement planning in parallel for any already-identified failures.

---

## Phase 3: Replace Failed Clusters with Spares (T-2h30m)

### Objective

Replace any attendee clusters that failed validation with spare clusters, ensuring
every assigned seat has a fully validated environment.

### 3.1 Identify failed attendee clusters

```bash
masworld report fleet-status --environment event --filter status=FAILED
```

**Expected output (example with failures):**

```
Failed clusters:
  seat-23   FAILED   mas_core: CRD not ready (timeout)
  seat-41   FAILED   s3_write_read: AccessDenied
```

### 3.2 Attempt automated repair before using spares

For each failed cluster, attempt repair first:

```bash
masworld cluster repair --cluster seat-23 --verbose
```

**Expected duration:** 5-15 minutes per cluster depending on the failure.

After repair, revalidate:

```bash
masworld cluster validate --cluster seat-23 --verbose
```

If the cluster now passes, no spare replacement is needed. Move to the next failed
cluster.

### 3.3 Replace with a spare cluster

If repair fails, replace the attendee cluster with a spare:

```bash
masworld seat replace \
  --seat 23 \
  --cluster spare-01 \
  --environment event \
  --verbose
```

**Expected output:**

```
Seat replacement initiated:
  Seat:              23
  Old cluster:       seat-23
  New cluster:       spare-01

  [1/7] Disabling credentials on seat-23 ...    DONE
  [2/7] Creating student account on spare-01 ... DONE
  [3/7] Updating Showroom endpoints ...          DONE
  [4/7] Updating Maximo endpoints ...            DONE
  [5/7] Updating assignment inventory ...        DONE
  [6/7] Validating replacement cluster ...       DONE
  [7/7] Quarantining old cluster seat-23 ...     DONE

Seat 23 successfully reassigned to spare-01.
Cluster seat-23 quarantined.
Remaining spares: 4
```

**Critical:** The replacement operation is transactional. If any step fails, the
seat remains assigned to the original cluster and no partial state is left behind.
Review the error output and retry or escalate.

### 3.4 Validate after replacement

```bash
masworld cluster validate --cluster spare-01 --verbose
```

Confirm the replacement cluster passes all mandatory checks.

### 3.5 Record spare usage

After all replacements, verify remaining spare capacity:

```bash
masworld report fleet-status --environment event --filter purpose=spare
```

**Expected output:**

```
Spare clusters:
  spare-02   READY    available
  spare-03   READY    available
  spare-04   READY    available
  spare-05   READY    available

Spares available: 4/5
Spares used:      1/5 (spare-01 -> seat 23)
```

**Failure handling:**

If all 5 spares are consumed and additional clusters fail, the event must proceed
with reduced capacity. Notify the event coordinator immediately. Do not assign
failed or unvalidated clusters to attendees under any circumstances.

**Timing:** Spare replacement must be complete by T-2h. Each replacement takes
approximately 5-10 minutes.

---

## Phase 4: ACM Compliance and Drift Staging (T-2h)

### Objective

Confirm that all clusters are compliant with the ACM governance baseline, then
stage the deliberate safe drift on the facilitator cluster for the live demo.

### 4.1 Verify ACM hub connectivity

```bash
masworld cluster validate --cluster hub --check acm-api --verbose
```

**Expected output:**

```
ACM hub: hub-cluster
  API reachable:     PASS
  ManagedClusterSet: mas-world-2026   PASS
  Managed clusters:  56/56 registered PASS
  Cluster labels:    consistent       PASS
```

### 4.2 Verify full fleet compliance

```bash
masworld fleet validate --check acm-compliance --environment event
```

**Expected output:**

```
ACM Governance Compliance:
  policy-mas-world-baseline:
    verify-mas-namespace:           56/56 compliant
    verify-logging-operator:        56/56 compliant
    verify-lokistack:               56/56 compliant
    verify-cluster-log-forwarder:   56/56 compliant
    verify-mas-edge:                56/56 compliant (or NOT_APPLICABLE)
    enforce-event-marker:           56/56 compliant

  Overall fleet compliance: 100%
```

**Failure handling:**

If any attendee or spare cluster is non-compliant:

1. Identify the non-compliant policy and cluster:

   ```bash
   masworld fleet validate --check acm-compliance --environment event --verbose
   ```

2. If the non-compliance is on a resource managed by automation, attempt repair:

   ```bash
   masworld cluster repair --cluster <CLUSTER_ID> --component acm --verbose
   ```

3. If repair does not resolve compliance, investigate manually. Non-compliance on
   the event-marker ConfigMap suggests the cluster was not properly prepared.

### 4.3 Stage safe drift on the facilitator cluster

The ACM demo requires exactly one cluster to be deliberately non-compliant so Ernie
can demonstrate policy detection and remediation. The drift must be harmless and
must only affect the facilitator cluster.

```bash
masworld exercise reset \
  --cluster facilitator-01 \
  --module acm \
  --stage drift \
  --verbose
```

**Expected output:**

```
ACM drift staging on facilitator-01:
  Removing ConfigMap mas-world-event-marker from namespace mas-world-system ... DONE
  Drift staged successfully.

  Expected ACM state:
    facilitator-01: NonCompliant on enforce-event-marker
    All other clusters: Compliant
```

### 4.4 Verify drift is visible in ACM

Ernie should verify from the ACM console:

1. Open the ACM hub console in a browser.
2. Navigate to Governance > Policies > policy-mas-world-baseline.
3. Confirm that facilitator-01 shows as NonCompliant.
4. Confirm that all other clusters show as Compliant.

Alternatively, verify from CLI:

```bash
masworld fleet validate --check acm-compliance --environment event --verbose \
  | grep -A2 "facilitator-01"
```

**Expected output:**

```
  facilitator-01:
    enforce-event-marker: NonCompliant  (staged drift -- expected)
    All other policies:   Compliant
```

### 4.5 Verify remediation action is prepared

Confirm that remediating the drift will work by checking that the enforce action
is configured:

```bash
masworld cluster validate --cluster facilitator-01 --check acm-remediation-ready
```

**Expected output:**

```
ACM remediation readiness:
  Policy: enforce-event-marker
  Remediation action: enforce
  Template: ConfigMap mas-world-event-marker
  Expected result: ConfigMap recreated, cluster returns to Compliant
  Status: READY
```

**Do not run the actual remediation now.** Ernie will trigger it live during the
session.

**Failure handling:**

If drift staging fails, check that the facilitator cluster is registered with ACM
and that the policy targets it correctly. If the policy cannot detect the drift,
repair the ACM policy configuration:

```bash
masworld cluster repair --cluster facilitator-01 --component acm --verbose
```

Then re-stage the drift.

**Timing:** ACM compliance verification and drift staging must be complete by T-1h30m.

---

## Phase 5: Service Confirmation (T-1h30m)

### Objective

Confirm that all critical services are accessible and responding correctly across
the entire fleet: MAS routes, Logging/Loki, Identity/Keycloak, and Showroom.

### 5.1 MAS route validation

```bash
masworld fleet validate --check mas-routes --environment event --concurrency 10
```

**Expected output:**

```
MAS route validation:
  MAS Core UI:      56/56 responding (HTTP 200/302)
  Maximo Manage UI:  56/56 responding (HTTP 200/302)

  All MAS routes healthy.
```

**Failure handling:**

If any MAS route is not responding:

```bash
masworld cluster validate --cluster <CLUSTER_ID> --check mas-routes --verbose
```

Common causes:

- Certificate expiry -- check route certificate validity dates.
- Pod not running -- check MAS pods in the MAS namespace.
- Ingress controller degraded -- check the cluster's ingress operator status.

Attempt repair:

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component mas --verbose
```

### 5.2 Logging and Loki validation

```bash
masworld fleet validate --check logging --environment event --concurrency 10
```

**Expected output:**

```
Logging validation:
  Logging Operator:        56/56 healthy
  LokiStack:               56/56 ready
  ClusterLogForwarder:     56/56 active
  S3 write test:           56/56 passed
  S3 read test:            56/56 passed
  Historical log query:    56/56 passed

  All logging services healthy.
```

**Failure handling:**

S3 access failures are the most common logging issue. For each failed cluster:

```bash
masworld cluster validate --cluster <CLUSTER_ID> --check logging --verbose
```

Check:

- S3 bucket exists and is accessible.
- IAM credentials or workload identity are valid and not expired.
- The Kubernetes Secret containing S3 credentials is present in the correct
  namespace.
- LokiStack pods are running and not in CrashLoopBackOff.

Attempt repair:

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component logging --verbose
```

**Myles** should personally verify Loki query functionality on at least 3 clusters
by running a sample query from the logging console.

### 5.3 Identity and Keycloak validation

```bash
masworld fleet validate --check identity --environment event --concurrency 10
```

**Expected output:**

```
Identity validation:
  Keycloak deployment:     healthy
  OAuth integration:       56/56 configured
  OIDC endpoints:          56/56 responding
  LDAP group-sync config:  56/56 present

  All identity services healthy.
```

**Failure handling:**

If Keycloak is degraded:

```bash
masworld cluster validate --cluster <CLUSTER_ID> --check identity --verbose
```

If the Keycloak deployment itself is down, this affects the identity module but
does not block the earlier modules. Prioritize repair but do not delay the overall
timeline if repair takes longer than 15 minutes. The identity module can be
adjusted during the session if necessary.

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component identity --verbose
```

### 5.4 Showroom validation

```bash
masworld fleet validate --check showroom --environment event --concurrency 10
```

**Expected output:**

```
Showroom validation:
  Showroom deployed:       56/56
  Showroom UI responding:  56/56 (HTTP 200)
  Terminal accessible:     56/56
  Environment variables:   56/56 correctly injected

  All Showroom instances healthy.
```

**Failure handling:**

If Showroom is not responding on a cluster:

```bash
masworld cluster validate --cluster <CLUSTER_ID> --check showroom --verbose
```

Showroom failures on individual clusters can be resolved by redeploying:

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component showroom --verbose
```

If Showroom is down on many clusters simultaneously, suspect a shared dependency
(container registry, Git hosting) and check those services first.

### 5.5 Cross-service summary

After all service checks, generate a consolidated status:

```bash
masworld report fleet-status --environment event --detailed
```

Review the output and confirm all services are green before proceeding.

**Timing:** Service confirmation must be complete by T-1h.

---

## Phase 6: Student Login Validation and Access Cards (T-1h)

### Objective

Validate that every student account can authenticate and access its assigned
resources. Generate the final access cards for distribution.

### 6.1 Validate student accounts

```bash
masworld student validate \
  --environment event \
  --concurrency 10 \
  --verbose
```

**Expected duration:** 10-15 minutes for 50 accounts.

**Expected output:**

```
Student account validation:
  Authentication:          50/50 passed
  Console access:          50/50 passed
  Namespace access:        50/50 passed
  Showroom access:         50/50 passed
  Maximo access:           50/50 passed
  Cross-namespace blocked: 50/50 passed (isolation confirmed)
  ACM access blocked:      50/50 passed (isolation confirmed)
  Cluster-admin blocked:   50/50 passed (isolation confirmed)

  All student accounts validated.
```

**Failure handling:**

If student authentication fails on any cluster:

```bash
masworld student validate --seat <SEAT_NUMBER> --verbose
```

Common causes:

- htpasswd Secret not synced -- recreate the student account:

  ```bash
  masworld student create --seat <SEAT_NUMBER> --environment event --force
  ```

- OAuth server not restarted after credential change -- the repair will handle
  this, but it may take 2-3 minutes for the OAuth pods to roll.

If student isolation checks fail (a student can access another namespace or has
cluster-admin), this is a **critical security issue**. Do not assign that cluster
until the RBAC is corrected:

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component student-rbac --verbose
```

Revalidate after repair. If isolation still fails, quarantine the cluster and
replace with a spare.

### 6.2 Generate final seat assignment map

```bash
masworld seat export-map \
  --environment event \
  --output-file /tmp/seat-map-final.json
```

**Expected output:**

```
Seat map exported:
  Total seats:    50
  Assigned:       50
  Unassigned:      0
  Output: /tmp/seat-map-final.json
```

### 6.3 Generate access cards

```bash
masworld student export-cards \
  --environment event \
  --format pdf \
  --output-dir /tmp/access-cards/ \
  --include-qr
```

**Expected output:**

```
Access cards generated:
  Cards created:  50
  Format:         PDF with QR codes
  Output directory: /tmp/access-cards/

  Files:
    /tmp/access-cards/seat-01-access-card.pdf
    /tmp/access-cards/seat-02-access-card.pdf
    ...
    /tmp/access-cards/seat-50-access-card.pdf
    /tmp/access-cards/all-access-cards-combined.pdf
    /tmp/access-cards/facilitator-seat-map.pdf
```

### 6.4 Verify access card content

Spot-check at least 3 access cards (first, middle, last):

```bash
masworld seat show --seat 1 --environment event
masworld seat show --seat 25 --environment event
masworld seat show --seat 50 --environment event
```

**Expected output (example for seat 1):**

```
Seat:             1
Cluster:          seat-01
Username:         user01
Password:         [REDACTED -- see access card]
Showroom URL:     https://showroom.apps.seat-01.PLACEHOLDER_DOMAIN
Console URL:      https://console-openshift-console.apps.seat-01.PLACEHOLDER_DOMAIN
Maximo URL:       https://maxinst.mas-seat-01.apps.seat-01.PLACEHOLDER_DOMAIN
Status:           ASSIGNED
Cluster status:   READY
Last validated:   2026-08-17T07:00:00-05:00
```

Verify that:

- Each access card shows a unique seat number.
- URLs correspond to the correct cluster.
- No access card contains credentials for a different seat.
- No access card contains facilitator, admin, or AWS credentials.

### 6.5 Prepare access card distribution

- Print the combined PDF if physical cards are needed.
- Prepare digital distribution if cards will be shared electronically.
- Keep the facilitator seat map accessible to all three facilitators.
- Do not distribute access cards to attendees until T-0.

**Timing:** Student validation and access card generation must be complete by T-30m.

---

## Phase 7: Presenter Account and Demo Verification (T-30m)

### Objective

Ernie verifies that the presenter account, ACM demonstration flow, and exercise
reset mechanism all work correctly.

### 7.1 Test presenter account

Ernie logs in to the facilitator cluster with the presenter credentials:

```bash
masworld student validate --seat facilitator --verbose
```

Verify:

- Presenter can access the OpenShift console.
- Presenter can access Maximo.
- Presenter can access the ACM hub console.
- Presenter can access the Loki/logging console.
- Presenter has the required permissions for the demo (scoped admin, not
  cluster-admin unless required).

### 7.2 Dry-run the ACM demonstration flow

Ernie walks through the ACM demo mentally or with abbreviated steps:

1. Open ACM hub console. Verify the fleet is visible.
2. Verify cluster labels are displayed correctly.
3. Run a search query across managed clusters. Confirm results.
4. Navigate to Governance. Verify the baseline policy is visible.
5. Confirm facilitator-01 shows as NonCompliant.
6. **Do not remediate yet.** Confirm the remediation button/action is available.

If Ernie identifies any issue with the ACM console or demo flow, Francis
investigates and repairs immediately.

### 7.3 Verify exercise reset works

Test the reset mechanism for each module on the facilitator cluster:

```bash
masworld exercise reset --cluster facilitator-01 --module navigation --verbose
masworld exercise reset --cluster facilitator-01 --module updates --verbose
masworld exercise reset --cluster facilitator-01 --module observability --verbose
masworld exercise reset --cluster facilitator-01 --module identity --verbose
```

**Expected output (per module):**

```
Exercise reset: navigation on facilitator-01
  Resetting exercise state ...     DONE
  Restaging sample data ...        DONE
  Validating reset state ...       DONE
  Exercise ready for attendee use.
```

**Failure handling:**

If any exercise reset fails, attempt repair:

```bash
masworld cluster repair --cluster facilitator-01 --component <MODULE> --verbose
```

If reset cannot be restored for a specific module, the facilitator team must decide
whether to proceed without that module's reset capability. Document the limitation.

### 7.4 Re-stage ACM drift after reset testing

If the ACM-related reset or testing cleared the staged drift, re-stage it:

```bash
masworld exercise reset \
  --cluster facilitator-01 \
  --module acm \
  --stage drift \
  --verbose
```

Verify drift is visible in ACM (repeat the check from Phase 4.4).

**Timing:** Demo verification must be complete by T-15m.

---

## Phase 8: Change Freeze and Go/No-Go Decision (T-15m)

### Objective

Freeze all changes to the environment. Conduct a structured go/no-go decision
among all three facilitators.

### 8.1 Freeze changes

From T-15m onward, no configuration changes, repairs, replacements, or credential
rotations are permitted unless they are required to resolve a blocking issue
identified in the go/no-go decision.

Announce the freeze in the facilitator channel:

> CHANGE FREEZE IN EFFECT. No modifications to any cluster, configuration, or
> credential without explicit agreement from all three facilitators.

### 8.2 Final fleet status

```bash
masworld report fleet-status --environment event --detailed
```

Record the output. This is the final state-of-the-world before the session.

### 8.3 Go/No-Go decision matrix

All three facilitators review the matrix below. Each criterion is evaluated as
GO (met) or NO-GO (not met, with impact assessment).

| # | Criterion | Required | Check Command | Status |
|---|---|---|---|---|
| 1 | All facilitators present and workstations functional | Yes | Visual confirmation | __ |
| 2 | Network connectivity to all cluster APIs | Yes | `masworld fleet validate --check api-reachability` | __ |
| 3 | At least 45 attendee clusters READY | Yes | `masworld report fleet-status` | __ |
| 4 | All assigned seats have validated clusters | Yes | `masworld seat export-map` | __ |
| 5 | At least 1 spare cluster available | Recommended | `masworld report fleet-status --filter purpose=spare` | __ |
| 6 | MAS Core responding on all assigned clusters | Yes | `masworld fleet validate --check mas-routes` | __ |
| 7 | Maximo Manage responding on all assigned clusters | Yes | `masworld fleet validate --check mas-routes` | __ |
| 8 | Logging/Loki operational on all assigned clusters | Yes | `masworld fleet validate --check logging` | __ |
| 9 | Identity/Keycloak operational on all assigned clusters | Recommended | `masworld fleet validate --check identity` | __ |
| 10 | Showroom responding on all assigned clusters | Yes | `masworld fleet validate --check showroom` | __ |
| 11 | Student authentication validated on all assigned clusters | Yes | `masworld student validate` | __ |
| 12 | Student isolation validated (RBAC, cross-namespace) | Yes | `masworld student validate` (includes isolation checks) | __ |
| 13 | ACM hub operational and fleet registered | Yes | `masworld fleet validate --check acm-compliance` | __ |
| 14 | ACM drift staged on facilitator cluster | Yes | `masworld fleet validate --check acm-compliance --verbose` | __ |
| 15 | Presenter account functional | Yes | `masworld student validate --seat facilitator` | __ |
| 16 | Exercise reset mechanism functional | Recommended | Manual dry-run by Ernie | __ |
| 17 | Access cards generated and ready for distribution | Yes | Files in `/tmp/access-cards/` | __ |
| 18 | Facilitator communication channel operational | Yes | Visual confirmation | __ |
| 19 | Projector/display functional | Yes | Visual confirmation | __ |
| 20 | Conference Wi-Fi tested for attendee browser access | Recommended | Manual browser test | __ |

### 8.4 Decision rules

**GO:** All "Yes" criteria are met.

**CONDITIONAL GO:** All "Yes" criteria are met, but one or more "Recommended"
criteria are not. Document the missing items and confirm that all facilitators
accept the risk. Announce the limitation and any workaround to attendees if it
affects their experience.

**NO-GO:** One or more "Yes" criteria are not met.

If NO-GO:

1. Identify the specific blocking criteria.
2. Estimate time to resolve.
3. If resolution is possible within the remaining time, attempt it and re-evaluate.
4. If resolution is not possible, escalate to the event coordinator to discuss
   session delay, reduced scope, or cancellation.
5. Document the decision and rationale.

### 8.5 Record the decision

All three facilitators verbally confirm GO, CONDITIONAL GO, or NO-GO.

Record in the facilitator channel:

> GO/NO-GO DECISION at [timestamp]: [GO / CONDITIONAL GO / NO-GO]
> Facilitators: Ernie [GO/NO-GO], Francis [GO/NO-GO], Myles [GO/NO-GO]
> Conditions: [none / list any conditions or limitations]

**Timing:** The go/no-go decision must be final by T-5m.

---

## Phase 9: Session Start Procedures (T-0)

### Objective

Transition smoothly from preparation to live session delivery.

### 9.1 Pre-start (T-5m to T-0)

- Ernie has the opening slide deck loaded and visible on the projector.
- Francis has the fleet dashboard open on a secondary display or laptop.
- Myles has the incident channel and logging console open.
- Access cards are staged for distribution (physical or digital).
- Room lights, microphone, and A/V are confirmed.

### 9.2 Session start (T-0)

1. **Ernie** begins the opening presentation.
2. **Francis** distributes access cards to attendees as they arrive or at the
   designated distribution point.
3. **Myles** monitors the facilitator channel for early issues.

### 9.3 Attendee onboarding

As attendees receive access cards and begin logging in:

- Francis and Myles circulate to assist with initial login issues.
- Common first-login issues:
  - Attendee cannot reach the Showroom URL -- verify the attendee's device is on
    the conference Wi-Fi and the URL is entered correctly.
  - Authentication failure -- verify the seat number matches the access card. If
    credentials are invalid, regenerate for that specific seat:

    ```bash
    masworld student create --seat <SEAT_NUMBER> --environment event --force
    ```

  - Browser certificate warning -- instruct the attendee to accept the self-signed
    certificate or use the documented browser exception procedure.

### 9.4 Transition to during-event monitoring

Once all attendees are logged in and the first module begins, transition to the
during-event monitoring procedures documented in `runbooks/during-event.md`.

---

## Escalation Path

For all phases, use this escalation order:

| Level | Contact | When |
|---|---|---|
| 1 | Facilitator team (Ernie, Francis, Myles) | Any issue during morning preparation |
| 2 | Event coordinator | Facilitator unavailability, room/A/V issues, NO-GO decision |
| 3 | Red Hat platform team | OpenShift cluster infrastructure issues not resolvable by repair automation |
| 4 | IBM support | MAS-specific issues not resolvable by repair automation |
| 5 | AWS support | S3, IAM, or networking issues at the cloud-provider level |

Contact details for levels 2-5 should be documented in `runbooks/escalation-contacts.md`
with phone numbers and support case procedures. Do not store contact details in this
runbook if they are sensitive.

---

## Rollback Procedures

### Rolling back a failed spare replacement

If a spare replacement leaves a seat in an inconsistent state:

```bash
masworld seat replace \
  --seat <SEAT_NUMBER> \
  --cluster <ORIGINAL_CLUSTER_ID> \
  --environment event \
  --force \
  --verbose
```

The `--force` flag allows reassignment even if the original cluster is quarantined.
After rollback, revalidate:

```bash
masworld cluster validate --cluster <ORIGINAL_CLUSTER_ID> --verbose
```

### Rolling back ACM drift staging

If drift staging causes unexpected policy violations on attendee clusters:

```bash
masworld exercise reset \
  --cluster facilitator-01 \
  --module acm \
  --stage compliant \
  --verbose
```

This restores the facilitator cluster to full compliance. Investigate why drift
affected other clusters before re-staging.

### Rolling back student credential changes

If student credentials were accidentally rotated or invalidated:

```bash
masworld student create \
  --environment event \
  --force \
  --verbose
```

This recreates all student accounts with new credentials. Access cards must be
regenerated afterward:

```bash
masworld student export-cards \
  --environment event \
  --format pdf \
  --output-dir /tmp/access-cards/ \
  --include-qr
```

---

## Timing Recovery

If any phase runs over its allocated time:

| Situation | Action |
|---|---|
| Phase 2 (fleet validation) runs long | Reduce concurrency. Begin Phase 3 planning for known failures. |
| Phase 3 (spare replacement) runs long | Skip repair attempts, go directly to spare replacement. |
| Phase 4 (ACM compliance) runs long | Defer drift staging to T-30m window; Ernie stages it. |
| Phase 5 (service confirmation) runs long | Run service checks in parallel with Phase 6. |
| Phase 6 (student validation) runs long | Reduce concurrency. Spot-check rather than full validation if under T-20m. |
| Phase 7 (demo verification) runs long | Ernie performs abbreviated check; Francis handles remaining items. |
| All phases consume available time | Conduct go/no-go with available information. Document gaps. |

The absolute deadline for the go/no-go decision is T-5m. If preparation is still
in progress at T-5m, conduct the go/no-go based on the information available and
continue resolving non-blocking issues after session start.

---

## Quick Reference: Critical Commands

```bash
# Configuration
masworld config validate --environment event
masworld config render --environment event --redacted

# Fleet operations
masworld fleet validate --environment event --concurrency 10
masworld report fleet-status --environment event
masworld report fleet-status --environment event --detailed
masworld report fleet-status --environment event --filter status=FAILED

# Individual cluster
masworld cluster validate --cluster <ID> --verbose
masworld cluster repair --cluster <ID> --verbose
masworld cluster repair --cluster <ID> --component <COMPONENT> --verbose

# Seat management
masworld seat replace --seat <N> --cluster <ID> --environment event --verbose
masworld seat show --seat <N> --environment event
masworld seat export-map --environment event --output-file /tmp/seat-map-final.json

# Student accounts
masworld student validate --environment event --concurrency 10
masworld student validate --seat <N> --verbose
masworld student create --seat <N> --environment event --force
masworld student export-cards --environment event --format pdf --output-dir /tmp/access-cards/ --include-qr

# Exercise management
masworld exercise reset --cluster <ID> --module <MODULE> --verbose
masworld exercise reset --cluster facilitator-01 --module acm --stage drift --verbose

# ACM
masworld fleet validate --check acm-compliance --environment event
masworld fleet validate --check acm-compliance --environment event --verbose
```
