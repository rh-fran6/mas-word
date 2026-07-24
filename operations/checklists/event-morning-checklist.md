# MAS World 2026 Event Morning Checklist

Event: MAS World 2026
Date: August 17, 2026
Timezone: America/Chicago
Session Start: Refer to event schedule for exact time (T-0 below)

This checklist covers the four hours before session start (T-4h through T-0).
Every step must be completed in order. The go/no-go decision point is at T-30m.
For detailed procedures, see `../runbooks/event-morning.md`.

---

## T-4h: Infrastructure Revalidation

Cross-reference: `../runbooks/event-morning.md#infrastructure-revalidation`

- [ ] **[T-4h]** Confirm all facilitators are online and available
  ```
  Francis Anyaegbu:  [ ] Available
  Ernie Steagall:    [ ] Available
  Myles Vivian:      [ ] Available
  ```

- [ ] **[T-4h]** Pull latest pinned release tag on operations workstation
  ```bash
  cd mas-world-2026-automation
  git fetch --all --tags
  git checkout tags/v1.0.0-event
  git describe --tags --exact-match
  ```
  Expected: `v1.0.0-event`

- [ ] **[T-4h]** Validate configuration integrity
  ```bash
  masworld config validate --environment event
  ```
  Expected: `Configuration valid. 0 errors, 0 warnings.`

- [ ] **[T-4h]** Run full fleet validation on all clusters
  ```bash
  masworld fleet validate --environment event --full --parallel 10
  ```
  Expected: All 56 clusters `READY`.

- [ ] **[T-4h]** Record fleet status snapshot
  ```bash
  masworld report fleet-status --environment event --format json \
    > reports/fleet-status-morning.json
  masworld report fleet-status --environment event --format markdown \
    > reports/fleet-status-morning.md
  ```

- [ ] **[T-4h]** Review fleet status summary
  ```bash
  masworld report fleet-status --environment event --summary
  ```
  Expected output:
  ```
  Total:  56   Ready: 56   Failed: 0   Warning: 0
  Attendee: 50/50 READY    Spare: 5/5 READY    Facilitator: 1/1 READY
  Assigned: 50   Unassigned Spare: 5
  ```

---

## T-3h30m: Failed Cluster Replacement

Cross-reference: `../runbooks/spare-replacement.md`

- [ ] **[T-3h30m]** Identify any failed clusters from the morning validation
  ```bash
  masworld report fleet-status --environment event --status FAILED
  ```
  Expected: No output (no failed clusters). If clusters are listed, proceed with replacement.

- [ ] **[T-3h30m]** Replace each failed attendee cluster with a spare
  ```bash
  # Repeat for each failed cluster:
  masworld seat show --seat <SEAT_NUMBER>
  masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>
  masworld cluster validate --cluster <SPARE_CLUSTER_ID> --environment event --full
  ```
  Expected: Replacement cluster passes all checks. Seat reassigned. Failed cluster quarantined.

- [ ] **[T-3h30m]** Regenerate access cards for any replaced seats
  ```bash
  masworld student export-cards --environment event --seat <SEAT_NUMBER> \
    --format pdf --output reports/access-cards/
  ```

- [ ] **[T-3h30m]** Confirm remaining spare capacity
  ```bash
  masworld report fleet-status --environment event --purpose spare --status READY
  ```
  Expected: At least 1 spare cluster remains `READY` and `UNASSIGNED`.
  Record spare count: ____

---

## T-3h: Component Spot Checks

Cross-reference: `../runbooks/component-validation.md`

- [ ] **[T-3h]** Verify MAS routes are accessible on 3 sample clusters
  ```bash
  masworld cluster validate --cluster seat-01 --check mas-route
  masworld cluster validate --cluster seat-25 --check mas-route
  masworld cluster validate --cluster seat-50 --check mas-route
  ```
  Expected: MAS UI reachable on all three clusters.

- [ ] **[T-3h]** Verify Maximo Manage is operational on 3 sample clusters
  ```bash
  masworld cluster validate --cluster seat-01 --check maximo-manage
  masworld cluster validate --cluster seat-25 --check maximo-manage
  masworld cluster validate --cluster seat-50 --check maximo-manage
  ```
  Expected: `maximo_manage: PASS` on all three.

- [ ] **[T-3h]** Verify Showroom loads correctly on 3 sample clusters
  ```bash
  masworld cluster validate --cluster seat-01 --check showroom
  masworld cluster validate --cluster seat-25 --check showroom
  masworld cluster validate --cluster seat-50 --check showroom
  ```
  Expected: Showroom accessible, tabs configured, environment variables populated.

- [ ] **[T-3h]** Verify S3 object storage connectivity on 3 sample clusters
  ```bash
  masworld cluster validate --cluster seat-01 --check s3-integration
  masworld cluster validate --cluster seat-25 --check s3-integration
  masworld cluster validate --cluster seat-50 --check s3-integration
  ```
  Expected: `s3_write_read: PASS` on all three.

- [ ] **[T-3h]** Verify student login on 3 sample clusters
  ```bash
  masworld student validate --cluster seat-01
  masworld student validate --cluster seat-25
  masworld student validate --cluster seat-50
  ```
  Expected: Student authentication succeeds, namespace accessible, RBAC correct.

---

## T-2h: ACM and Demo Preparation

Cross-reference: `../runbooks/acm-demo-preparation.md`

- [ ] **[T-2h]** Verify all clusters registered and visible in ACM
  ```bash
  masworld fleet validate --environment event --check acm-registration
  ```
  Expected: All 56 clusters registered as ManagedClusters.

- [ ] **[T-2h]** Verify ACM baseline policy compliance on attendee clusters
  ```bash
  masworld fleet validate --environment event --check acm-compliance --purpose attendee
  ```
  Expected: All 50 attendee clusters `Compliant`.

- [ ] **[T-2h]** Re-stage ACM drift on facilitator cluster
  ```bash
  masworld exercise reset --cluster facilitator-01 --module acm --action stage-drift
  ```
  Expected: Facilitator cluster shows exactly one noncompliant policy.

- [ ] **[T-2h]** Verify ACM drift is isolated to facilitator cluster only
  ```bash
  masworld fleet validate --environment event --check acm-compliance --purpose attendee
  masworld fleet validate --environment event --check acm-compliance --purpose spare
  ```
  Expected: All attendee and spare clusters remain `Compliant`.

- [ ] **[T-2h]** Test ACM remediation on facilitator cluster (dry run)
  ```bash
  masworld exercise reset --cluster facilitator-01 --module acm --action solve
  masworld fleet validate --environment event --check acm-compliance
  ```
  Expected: All clusters including facilitator now `Compliant`.

- [ ] **[T-2h]** Re-stage drift again after dry run (ready for live demo)
  ```bash
  masworld exercise reset --cluster facilitator-01 --module acm --action stage-drift
  ```
  Expected: Facilitator cluster noncompliant. Attendee clusters compliant.

---

## T-1h30m: Exercise Readiness

Cross-reference: `../runbooks/exercise-readiness.md`

- [ ] **[T-1h30m]** Verify observability sample workload is staged on all clusters
  ```bash
  masworld fleet validate --environment event --check exercise-readiness \
    --module observability --parallel 10
  ```
  Expected: Observability exercise prerequisites present on all attendee clusters.

- [ ] **[T-1h30m]** Verify identity exercise resources are staged on all clusters
  ```bash
  masworld fleet validate --environment event --check exercise-readiness \
    --module identity --parallel 10
  ```
  Expected: Identity exercise prerequisites present on all attendee clusters.

- [ ] **[T-1h30m]** Verify updates exercise is staged on all clusters
  ```bash
  masworld fleet validate --environment event --check exercise-readiness \
    --module updates --parallel 10
  ```
  Expected: Updates exercise prerequisites present on all attendee clusters.

- [ ] **[T-1h30m]** Test one full solve/reset cycle on facilitator cluster
  ```bash
  masworld exercise reset --cluster facilitator-01 --module observability --action solve
  masworld exercise reset --cluster facilitator-01 --module observability --action reset
  masworld exercise reset --cluster facilitator-01 --module identity --action solve
  masworld exercise reset --cluster facilitator-01 --module identity --action reset
  ```
  Expected: Solve and reset complete without errors.

---

## T-1h: Presenter Preparation

Cross-reference: `../runbooks/presenter-preparation.md`

- [ ] **[T-1h]** Confirm Ernie can access the facilitator cluster OpenShift console
  ```bash
  masworld cluster validate --cluster facilitator-01 --check console-access
  ```

- [ ] **[T-1h]** Confirm Ernie can access MAS on the facilitator cluster
  ```bash
  masworld cluster validate --cluster facilitator-01 --check mas-route
  ```

- [ ] **[T-1h]** Confirm Ernie can access the ACM hub console
  ```bash
  masworld cluster validate --cluster facilitator-01 --check acm-console
  ```

- [ ] **[T-1h]** Confirm Francis has support access to representative clusters
  ```bash
  masworld student validate --cluster seat-01 --user facilitator
  masworld student validate --cluster seat-50 --user facilitator
  ```

- [ ] **[T-1h]** Confirm Myles has support access to representative clusters
  ```bash
  masworld student validate --cluster seat-01 --user facilitator
  ```

---

## T-45m: Final Seat Map and Materials

Cross-reference: `../runbooks/seat-assignment.md`

- [ ] **[T-45m]** Export final seat map
  ```bash
  masworld seat export-map --environment event --format json > reports/seat-map-event-day.json
  masworld seat export-map --environment event --format markdown > reports/seat-map-event-day.md
  ```

- [ ] **[T-45m]** Verify all 50 seats are assigned
  ```bash
  masworld report seat-report --environment event --summary
  ```
  Expected: `Assigned: 50/50. Unassigned spare: N.`

- [ ] **[T-45m]** Verify access cards are available (printed or digital)
  ```
  Physical cards printed:    [ ] Yes  [ ] No (digital fallback ready)
  Digital cards accessible:  [ ] Yes
  Fallback CSV available:    [ ] Yes
  ```

- [ ] **[T-45m]** Confirm access card distribution plan
  ```
  Distribution method: [ ] At-seat  [ ] Registration desk  [ ] Digital link
  ```

---

## T-30m: Go/No-Go Decision

Cross-reference: `../runbooks/go-no-go.md`

- [ ] **[T-30m]** Run final fleet status check
  ```bash
  masworld report fleet-status --environment event --summary
  ```

- [ ] **[T-30m]** Review go/no-go criteria

  ```
  GO CRITERIA (all must be checked):
  - [ ] All 50 attendee clusters READY
  - [ ] At least 1 spare cluster READY and UNASSIGNED
  - [ ] All 50 student accounts authenticate
  - [ ] Showroom accessible on all 50 clusters
  - [ ] MAS accessible on all 50 clusters
  - [ ] Logging stack operational on all 50 clusters
  - [ ] ACM hub operational with all clusters registered
  - [ ] ACM drift staged on facilitator cluster only
  - [ ] All facilitators have confirmed access
  - [ ] Access cards ready for distribution
  - [ ] Conference Wi-Fi tested from presentation area
  ```

- [ ] **[T-30m]** Record go/no-go decision

  ```
  Decision:  [ ] GO   [ ] NO-GO

  If NO-GO, reason: ___________________________________________________
  Mitigation plan:  ___________________________________________________

  Decided by:
  Francis Anyaegbu:  [ ] GO  [ ] NO-GO   Signature: ____________
  Ernie Steagall:    [ ] GO  [ ] NO-GO   Signature: ____________
  Myles Vivian:      [ ] GO  [ ] NO-GO   Signature: ____________
  ```

---

## T-15m: Final Preparations

- [ ] **[T-15m]** Open fleet monitoring dashboard
  ```bash
  masworld report fleet-status --environment event --watch
  ```

- [ ] **[T-15m]** Confirm communication channel open between all facilitators
  ```
  Primary channel:   [ ] Confirmed (e.g., Slack, Teams, Signal)
  Backup channel:    [ ] Confirmed
  ```

- [ ] **[T-15m]** Confirm escalation contacts are reachable
  ```
  IBM support contact:       [ ] Confirmed
  Red Hat support contact:   [ ] Confirmed
  AWS support contact:       [ ] Confirmed
  ```

- [ ] **[T-15m]** Stage facilitator workstations
  ```
  Francis: Terminal open, masworld CLI ready, monitoring dashboard visible
  Myles:   Terminal open, masworld CLI ready, Loki/logging dashboard visible
  Ernie:   Presenter screen ready, ACM console open, MAS open
  ```

---

## T-5m: Pre-Session Final Checks

- [ ] **[T-5m]** Confirm Ernie's presenter screen is sharing correctly
- [ ] **[T-5m]** Confirm facilitator cluster Showroom is displayed
- [ ] **[T-5m]** Silence or redirect non-critical notifications
- [ ] **[T-5m]** Start incident log for the session
  ```
  Incident log location: _______________________________________________
  ```

---

## T-0: Session Begins

- [ ] **[T-0]** Confirm attendees are receiving access cards
- [ ] **[T-0]** Monitor fleet dashboard for any cluster status changes
  ```bash
  masworld report fleet-status --environment event --watch
  ```
- [ ] **[T-0]** Transition to event-day checklist: `event-day-checklist.md`

---

## Emergency Procedures Quick Reference

If a cluster fails during morning preparation:

```bash
# 1. Identify the failed cluster and affected seat
masworld seat show --seat <SEAT_NUMBER>

# 2. Replace with a spare
masworld seat replace --seat <SEAT_NUMBER> --cluster <SPARE_CLUSTER_ID>

# 3. Validate the replacement
masworld cluster validate --cluster <SPARE_CLUSTER_ID> --environment event --full

# 4. Regenerate access card
masworld student export-cards --environment event --seat <SEAT_NUMBER> \
  --format pdf --output reports/access-cards/

# 5. Confirm spare inventory
masworld report fleet-status --environment event --purpose spare --status READY
```

If the go/no-go decision is NO-GO, see `../runbooks/no-go-procedures.md`.
