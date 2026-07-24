# MAS World 2026 Event Day Checklist

Event: MAS World 2026
Date: August 17, 2026
Timezone: America/Chicago
Total Session Duration: approximately 120 minutes

Facilitators:
- Ernie Steagall (ONEOK) -- Primary presenter
- Francis Anyaegbu (Red Hat) -- Lab environment owner, attendee support
- Myles Vivian (Cohesive) -- Observability content owner, attendee support

This checklist is used during the live session. It is organized by session
segment with monitoring checkpoints between segments. For detailed procedures,
see `../runbooks/event-day.md`.

Prerequisites: Complete `event-morning-checklist.md` and achieve GO decision.

---

## Pre-Session: Facilitator Roles Confirmation

- [ ] Confirm facilitator assignments for this session

  | Segment                | Presenter | Primary Support | Secondary Support |
  |------------------------|-----------|-----------------|-------------------|
  | Navigation and Search  | Ernie     | Francis         | Myles             |
  | ACM Fleet Management   | Ernie     | Francis         | Myles             |
  | Updates                | Ernie     | Francis         | Myles             |
  | Observability/Logging  | Myles     | Francis         | Ernie             |
  | Identity Provider      | Francis   | Myles           | Ernie             |

- [ ] Confirm monitoring dashboard is visible to Francis
  ```bash
  masworld report fleet-status --environment event --watch
  ```

- [ ] Confirm incident log is open and accessible to all facilitators

---

## Segment 1: Navigation and Search (10 minutes)

Cross-reference: `../runbooks/event-day.md#navigation-and-search`

### Segment Start

- [ ] **Handoff to Ernie:** Ernie begins introductory slides (1-2 minutes)
- [ ] **Francis:** Confirm attendees can access Showroom
  ```bash
  # Spot-check a few clusters if attendee issues are reported
  masworld cluster validate --cluster seat-01 --check showroom
  ```
- [ ] **Francis:** Monitor for attendee access issues during the first 2 minutes

### During Segment

- [ ] Attendees perform navigation exercise in their Showroom
- [ ] **Francis/Myles:** Assist attendees who cannot find their environment or log in

  If an attendee cannot log in:
  ```bash
  # Verify the student account on their assigned cluster
  masworld seat show --seat <SEAT_NUMBER>
  masworld student validate --cluster <CLUSTER_ID>
  ```

  If the cluster itself is unresponsive:
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check api-reachability
  # If FAIL, replace with spare:
  masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>
  masworld student export-cards --environment event --seat <SEAT_NUMBER> \
    --format pdf --output reports/access-cards/
  ```

### Validation

- [ ] Attendees run in-Showroom validation (button or command)
- [ ] **Francis:** If attendees report validation failures, check specific cluster
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check runtime-automation \
    --module navigation
  ```

### Solve (if needed)

- [ ] Run solve automation for attendees who are stuck
  ```bash
  masworld exercise reset --cluster <CLUSTER_ID> --module navigation --action solve
  ```

### Segment End

- [ ] **Francis:** Quick fleet status check between segments
  ```bash
  masworld report fleet-status --environment event --summary
  ```
  Record: Ready: ____ / 50   Failed: ____   Spares remaining: ____

---

## Monitoring Checkpoint 1 (between Navigation and ACM)

- [ ] **Francis:** Check fleet dashboard for any new failures
  ```bash
  masworld report fleet-status --environment event --status FAILED
  ```
  Expected: No output. If clusters listed, initiate replacement per `../runbooks/spare-replacement.md`.

- [ ] **Francis:** Confirm no degraded clusters
  ```bash
  masworld report fleet-status --environment event --status WARNING
  ```

- [ ] Resolve any open attendee issues before proceeding

---

## Segment 2: Advanced Cluster Management (10 minutes)

Cross-reference: `../runbooks/event-day.md#acm-fleet-management`

### Segment Start

- [ ] **Handoff to Ernie:** Ernie begins ACM introductory slides (1-2 minutes)
- [ ] **Francis:** Confirm ACM hub is accessible for Ernie's demo
  ```bash
  masworld cluster validate --cluster facilitator-01 --check acm-console
  ```
- [ ] **Francis:** Confirm drift is staged on facilitator cluster
  ```bash
  masworld fleet validate --environment event --check acm-compliance \
    --cluster facilitator-01
  ```
  Expected: Facilitator cluster shows noncompliant status.

### Presenter Demonstration (Ernie drives, attendees watch)

- [ ] Ernie shows fleet inventory in ACM console
- [ ] Ernie shows cluster labels and ManagedClusterSet
- [ ] Ernie demonstrates ACM Search across managed clusters
- [ ] Ernie shows governance policy `policy-mas-world-baseline`
- [ ] Ernie identifies the noncompliant facilitator cluster
- [ ] Ernie remediates the drift on the facilitator cluster
- [ ] **Francis:** Verify compliance is restored after remediation
  ```bash
  masworld fleet validate --environment event --check acm-compliance
  ```
  Expected: All clusters including facilitator are `Compliant`.

### Attendee Verification

- [ ] Attendees verify the propagated event marker on their own cluster (Showroom exercise)
- [ ] **Francis/Myles:** Assist attendees who cannot locate the marker

### Validation

- [ ] Attendees run ACM validation in Showroom
- [ ] **Francis:** Check specific clusters for attendees reporting issues
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check runtime-automation \
    --module acm
  ```

### Re-stage Drift (if another ACM demo is needed later)

- [ ] **Francis:** Re-stage drift if needed for a repeat demonstration
  ```bash
  masworld exercise reset --cluster facilitator-01 --module acm --action stage-drift
  ```

### Segment End

- [ ] **Francis:** Quick fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```
  Record: Ready: ____ / 50   Failed: ____   Spares remaining: ____

---

## Monitoring Checkpoint 2 (between ACM and Updates)

- [ ] **Francis:** Check for newly failed clusters
  ```bash
  masworld report fleet-status --environment event --status FAILED
  ```

- [ ] Replace any failed clusters
  ```bash
  # For each failed cluster:
  masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>
  ```

- [ ] Resolve any open attendee issues before proceeding

---

## Segment 3: Updates (20 minutes)

Cross-reference: `../runbooks/event-day.md#updates`

### Segment Start

- [ ] **Handoff to Ernie:** Ernie begins updates introductory slides (1-2 minutes)
- [ ] **Francis:** Confirm updates exercise is staged on all attendee clusters
  ```bash
  masworld fleet validate --environment event --check exercise-readiness \
    --module updates --parallel 10
  ```

### Presenter Demonstration

- [ ] Ernie demonstrates the update inspection workflow on facilitator cluster
- [ ] Ernie walks through update status history and lifecycle

### Attendee Exercise

- [ ] Attendees perform their bounded update exercise in Showroom
- [ ] **Francis/Myles:** Assist attendees encountering issues

  If an attendee's update exercise is stuck:
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check runtime-automation \
    --module updates
  ```

### Validation

- [ ] Attendees run updates validation in Showroom
- [ ] **Francis:** Assist with validation failures on specific clusters
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check runtime-automation \
    --module updates
  ```

### Solve (if needed)

- [ ] Run solve automation for stuck attendees
  ```bash
  masworld exercise reset --cluster <CLUSTER_ID> --module updates --action solve
  ```

### Reset (if needed for retry)

- [ ] Reset the updates exercise for an attendee who needs to start over
  ```bash
  masworld exercise reset --cluster <CLUSTER_ID> --module updates --action reset
  ```

### Segment End

- [ ] **Francis:** Quick fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```
  Record: Ready: ____ / 50   Failed: ____   Spares remaining: ____

---

## Monitoring Checkpoint 3 (between Updates and Observability)

- [ ] **Francis:** Check for newly failed clusters
  ```bash
  masworld report fleet-status --environment event --status FAILED
  ```

- [ ] Replace any failed clusters and regenerate access materials
  ```bash
  masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>
  masworld student export-cards --environment event --seat <SEAT_NUMBER> \
    --format pdf --output reports/access-cards/
  ```

- [ ] **Myles:** Confirm observability exercise prerequisites are intact
  ```bash
  masworld fleet validate --environment event --check exercise-readiness \
    --module observability --parallel 10
  ```

- [ ] **Handoff: Ernie transfers presenter role context to Myles for observability**
  ```
  Ernie confirms:  [ ] ACM demo complete, fleet stable
  Myles confirms:  [ ] Ready to lead observability segment
  Francis confirms: [ ] Fleet status nominal, support ready
  ```

---

## Segment 4: Observability and Logging (40 minutes)

Cross-reference: `../runbooks/event-day.md#observability-logging`

### Segment Start

- [ ] **Handoff to Myles:** Myles begins observability introductory slides (1-2 minutes)
- [ ] **Francis:** Confirm logging stack is healthy across the fleet
  ```bash
  masworld fleet validate --environment event --check logging --parallel 10
  ```

### 10-Minute Checkpoint (within segment)

- [ ] **Francis:** Periodic fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```

### Attendee Exercise: Deploy Sample Logging Workload

- [ ] Attendees deploy the sample workload that emits identifiable log messages
- [ ] **Myles/Francis:** Assist attendees who cannot deploy the workload

  If the logging workload does not start:
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check runtime-automation \
    --module observability
  ```

### Attendee Exercise: Query Logs in Loki

- [ ] Attendees query their logs through the logging interface
- [ ] **Myles:** Assist attendees who cannot find their logs

  If Loki is not returning results for a cluster:
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check lokistack
  masworld cluster validate --cluster <CLUSTER_ID> --check cluster-log-forwarder
  masworld cluster validate --cluster <CLUSTER_ID> --check s3-integration
  ```

### Attendee Exercise: Historical Log Query

- [ ] Attendees delete the sample workload and query historical logs
- [ ] **Myles:** Confirm historical logs are still queryable after deletion
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check historical-log-query
  ```

### 20-Minute Checkpoint (within segment)

- [ ] **Francis:** Periodic fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```

### Validation

- [ ] Attendees run observability validation in Showroom
- [ ] **Myles/Francis:** Assist with validation failures
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check runtime-automation \
    --module observability
  ```

### Solve (if needed)

- [ ] Run solve automation for stuck attendees
  ```bash
  masworld exercise reset --cluster <CLUSTER_ID> --module observability --action solve
  ```

### Reset (if needed for retry)

- [ ] Reset the observability exercise for an attendee
  ```bash
  masworld exercise reset --cluster <CLUSTER_ID> --module observability --action reset
  ```

### Segment End

- [ ] **Francis:** Quick fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```
  Record: Ready: ____ / 50   Failed: ____   Spares remaining: ____

---

## Monitoring Checkpoint 4 (between Observability and Identity)

- [ ] **Francis:** Check for newly failed clusters
  ```bash
  masworld report fleet-status --environment event --status FAILED
  ```

- [ ] Replace any failed clusters
  ```bash
  masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>
  masworld student export-cards --environment event --seat <SEAT_NUMBER> \
    --format pdf --output reports/access-cards/
  ```

- [ ] **Handoff: Myles transfers presenter role context to Francis for identity**
  ```
  Myles confirms:   [ ] Observability segment complete, no outstanding issues
  Francis confirms:  [ ] Ready to lead identity segment
  Ernie confirms:    [ ] Available for secondary support
  ```

---

## Segment 5: Identity Provider Integration (40 minutes)

Cross-reference: `../runbooks/event-day.md#identity-provider`

### Segment Start

- [ ] **Handoff to Francis:** Francis begins identity introductory slides (1-2 minutes)
- [ ] **Myles:** Take over fleet monitoring role
  ```bash
  masworld report fleet-status --environment event --watch
  ```

### 10-Minute Checkpoint (within segment)

- [ ] **Myles:** Periodic fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```

### Attendee Exercise: Inspect Keycloak/OIDC Configuration

- [ ] Attendees inspect the preconfigured identity resources
- [ ] **Myles/Ernie:** Assist attendees who cannot access the identity inspection steps

  If identity resources are not visible on a cluster:
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check identity
  ```

### Attendee Exercise: Test Authentication Flow

- [ ] Attendees test the authentication workflow
- [ ] **Myles/Ernie:** Assist attendees encountering authentication errors

### Attendee Exercise: LDAP Group Sync

- [ ] Attendees inspect or run the bounded group-sync demonstration
- [ ] **Myles/Ernie:** Assist attendees with group-sync issues

### 20-Minute Checkpoint (within segment)

- [ ] **Myles:** Periodic fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```

### Validation

- [ ] Attendees run identity validation in Showroom
- [ ] **Francis/Myles:** Assist with validation failures
  ```bash
  masworld cluster validate --cluster <CLUSTER_ID> --check runtime-automation \
    --module identity
  ```

### Solve (if needed)

- [ ] Run solve automation for stuck attendees
  ```bash
  masworld exercise reset --cluster <CLUSTER_ID> --module identity --action solve
  ```

### Reset (if needed for retry)

- [ ] Reset the identity exercise for an attendee
  ```bash
  masworld exercise reset --cluster <CLUSTER_ID> --module identity --action reset
  ```

### Segment End

- [ ] **Myles:** Final fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```
  Record: Ready: ____ / 50   Failed: ____   Spares remaining: ____

---

## Post-Session Immediate Actions

Cross-reference: `../runbooks/post-session.md`

### Within 15 Minutes of Session End

- [ ] **Francis:** Generate final fleet status report
  ```bash
  masworld report fleet-status --environment event --format json \
    > reports/fleet-status-post-session.json
  masworld report fleet-status --environment event --format markdown \
    > reports/fleet-status-post-session.md
  ```

- [ ] **Francis:** Generate final seat report
  ```bash
  masworld report seat-report --environment event --format json \
    > reports/seat-report-post-session.json
  ```

- [ ] **Francis:** Record session metrics
  ```
  Session results:
  Attendees present:           ____
  Clusters used:               ____
  Spare replacements made:     ____
  Solve automations triggered: ____
  Incidents logged:            ____
  ```

- [ ] **Francis:** Export incident log for post-event review

### Within 1 Hour of Session End

- [ ] **Francis:** Disable all student accounts
  ```bash
  masworld student disable --environment event --parallel 10
  ```
  Expected: All 50 student accounts disabled. Authentication denied.

- [ ] **Francis:** Verify student accounts are disabled
  ```bash
  masworld student validate --environment event --expect-disabled --parallel 10
  ```
  Expected: All students fail authentication (expected after disable).

- [ ] **Francis:** Revoke any temporary cloud credentials created for the session
  ```bash
  masworld student rotate --environment event --action revoke --parallel 10
  ```

### Within 4 Hours of Session End

- [ ] **Francis:** Begin post-event credential revocation
  See `../runbooks/post-event-teardown.md` for the full teardown procedure.

- [ ] **All facilitators:** Debrief and record lessons learned
  ```
  Location: _______________________________________________
  Attendees: Francis, Ernie, Myles
  ```

---

## Quick Reference: Common Event-Day Commands

### Check a specific seat

```bash
masworld seat show --seat <SEAT_NUMBER>
```

### Validate a specific cluster

```bash
masworld cluster validate --cluster <CLUSTER_ID> --environment event --full
```

### Replace a failed cluster with a spare

```bash
masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>
masworld student export-cards --environment event --seat <SEAT_NUMBER> \
  --format pdf --output reports/access-cards/
```

### Solve an exercise for an attendee

```bash
masworld exercise reset --cluster <CLUSTER_ID> --module <MODULE> --action solve
```
Where `<MODULE>` is one of: `navigation`, `acm`, `updates`, `observability`, `identity`

### Reset an exercise for an attendee

```bash
masworld exercise reset --cluster <CLUSTER_ID> --module <MODULE> --action reset
```

### Check fleet status

```bash
masworld report fleet-status --environment event --summary
```

### Show all failed clusters

```bash
masworld report fleet-status --environment event --status FAILED
```

### Show remaining spares

```bash
masworld report fleet-status --environment event --purpose spare --status READY
```

---

## Incident Escalation Matrix

| Issue                          | First Responder | Escalation       |
|--------------------------------|-----------------|------------------|
| Attendee cannot log in         | Francis         | Ernie            |
| Cluster unresponsive           | Francis         | Red Hat support   |
| MAS not loading                | Francis         | IBM support       |
| Loki not returning logs        | Myles           | Francis           |
| S3 access failure              | Francis         | AWS support       |
| ACM hub unreachable            | Francis         | Red Hat support   |
| Showroom not loading           | Francis         | RHDP support      |
| All spares exhausted           | Francis         | All facilitators  |
| Network/Wi-Fi issues           | All             | Venue support     |

For detailed escalation procedures, see `../runbooks/escalation.md`.
