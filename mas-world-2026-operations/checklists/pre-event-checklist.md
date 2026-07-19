# MAS World 2026 Pre-Event Checklist

Event: MAS World 2026
Date: August 17, 2026
Timezone: America/Chicago
Max Attendees: 50

This checklist covers milestones from T-30 days through T-1 day before the
event. Each section must be completed and signed off before advancing to the
next milestone. For detailed procedures, see the corresponding runbooks in
`../runbooks/`.

---

## T-30 Days: Infrastructure Readiness (July 18, 2026)

Cross-reference: `../runbooks/infrastructure-readiness.md`

### Configuration Validation

- [ ] Pull latest automation repository and verify branch is at the release tag
  ```bash
  cd mas-world-2026-automation
  git fetch --all --tags
  git checkout tags/v1.0.0-event
  ```

- [ ] Validate all configuration schemas pass
  ```bash
  masworld config validate --environment event
  ```
  Expected: `Configuration valid. 0 errors, 0 warnings.`

- [ ] Render effective configuration and review for correctness
  ```bash
  masworld config render --environment event --redact-secrets > /tmp/effective-config-review.yaml
  ```
  Expected: All secret values redacted as `***REDACTED***`. No real credentials visible.

- [ ] Verify event configuration matches planned fleet size
  ```bash
  masworld config render --environment event --section fleet
  ```
  Expected: `attendee_cluster_count: 50`, `spare_cluster_count: 5`, `facilitator_cluster_count: 1`

- [ ] Validate cluster inventory completeness
  ```bash
  masworld config validate --environment event --check inventory-counts
  ```
  Expected: 56 clusters defined (50 attendee + 5 spare + 1 facilitator), all enabled.

### Cluster Connectivity

- [ ] Verify API connectivity to all clusters in inventory
  ```bash
  masworld fleet validate --environment event --check api-reachability --parallel 10
  ```
  Expected: All 56 clusters report `API_REACHABLE`.

- [ ] Verify administrative credential retrieval for all clusters
  ```bash
  masworld fleet validate --environment event --check admin-auth --parallel 10
  ```
  Expected: All 56 clusters report `AUTH_VALID`.

- [ ] Run cluster preflight on all clusters
  ```bash
  masworld fleet validate --environment event --check preflight --parallel 5
  ```
  Expected: All clusters report `PASS` or `WARNING` (no `FAIL`).

- [ ] Review and archive preflight reports
  ```bash
  masworld report fleet-status --environment event --format json > reports/preflight-t30.json
  masworld report fleet-status --environment event --format markdown > reports/preflight-t30.md
  ```

### Version Pinning

- [ ] Confirm all component versions are pinned in `config/components.yaml`
  ```bash
  masworld config validate --environment event --check version-pinning
  ```
  Expected: `All component versions pinned. No floating tags or channels detected.`

- [ ] Confirm container images use digest references where supported
  ```bash
  masworld config validate --environment event --check image-pinning
  ```

### Secret Provider

- [ ] Verify secret provider connectivity
  ```bash
  masworld config validate --environment event --check secret-provider
  ```
  Expected: Secret provider reachable, all referenced secrets resolvable.

- [ ] Verify IBM entitlement key is stored and retrievable
  ```bash
  masworld config validate --environment event --check secret-ref \
    --ref "secret://mas-world/ibm/entitlement"
  ```
  Expected: `Secret reference valid. Value redacted.`

### T-30 Sign-Off

```
Infrastructure readiness confirmed by:

Facilitator: Francis Anyaegbu     Date: ____________  Signature: ____________
Facilitator: Ernie Steagall       Date: ____________  Signature: ____________
Facilitator: Myles Vivian         Date: ____________  Signature: ____________
```

---

## T-14 Days: Fleet Preparation (August 3, 2026)

Cross-reference: `../runbooks/fleet-preparation.md`

### Reference Cluster

- [ ] Prepare the facilitator cluster as the reference implementation
  ```bash
  masworld cluster prepare --cluster facilitator-01 --environment event --verbose
  ```
  Expected: All stages complete. Cluster status `READY`.

- [ ] Validate the reference cluster end to end
  ```bash
  masworld cluster validate --cluster facilitator-01 --environment event --full
  ```
  Expected: All checks `PASS` or `NOT_APPLICABLE`. Zero `FAIL`.

- [ ] Confirm MAS Core is ready on reference cluster
  ```bash
  masworld cluster validate --cluster facilitator-01 --check mas-core
  ```
  Expected: `mas_core: PASS`

- [ ] Confirm Maximo Manage is ready on reference cluster
  ```bash
  masworld cluster validate --cluster facilitator-01 --check maximo-manage
  ```
  Expected: `maximo_manage: PASS`

- [ ] Confirm logging stack is ready on reference cluster
  ```bash
  masworld cluster validate --cluster facilitator-01 --check logging
  ```
  Expected: `logging_operator: PASS`, `lokistack: PASS`, `cluster_log_forwarder: PASS`

- [ ] Confirm S3 object storage integration on reference cluster
  ```bash
  masworld cluster validate --cluster facilitator-01 --check s3-integration
  ```
  Expected: `s3_write_read: PASS`, `historical_log_query: PASS`

### Fleet Preparation -- Attendee Clusters

- [ ] Begin fleet preparation for all attendee clusters (batched)
  ```bash
  masworld fleet prepare --environment event --purpose attendee \
    --parallel 5 --timeout 240m --retry 3
  ```
  Expected: All 50 attendee clusters prepared. Status `READY` for each.

- [ ] Review fleet preparation summary
  ```bash
  masworld report fleet-status --environment event --purpose attendee
  ```
  Expected: 50/50 attendee clusters `READY`.

- [ ] Investigate and repair any failed attendee clusters
  ```bash
  masworld fleet validate --environment event --purpose attendee --status FAILED
  # For each failed cluster:
  masworld cluster repair --cluster <CLUSTER_ID> --environment event --verbose
  ```
  Expected: All clusters reach `READY` after repair.

### Fleet Preparation -- Spare Clusters

- [ ] Prepare all spare clusters
  ```bash
  masworld fleet prepare --environment event --purpose spare \
    --parallel 5 --timeout 240m --retry 3
  ```
  Expected: All 5 spare clusters prepared. Status `READY` for each.

- [ ] Validate all spare clusters
  ```bash
  masworld fleet validate --environment event --purpose spare
  ```
  Expected: 5/5 spare clusters `READY`.

### S3 Bucket Verification

- [ ] Verify S3 buckets exist for all clusters with correct policies
  ```bash
  masworld fleet validate --environment event --check s3-integration --parallel 10
  ```
  Expected: All clusters report `s3_write_read: PASS`.

- [ ] Verify S3 isolation between clusters (negative test)
  ```bash
  masworld fleet validate --environment event --check s3-isolation
  ```
  Expected: `S3 cross-cluster access denied. Isolation PASS.`

### Fleet Status Snapshot

- [ ] Generate and archive T-14 fleet status report
  ```bash
  masworld report fleet-status --environment event --format json > reports/fleet-status-t14.json
  masworld report fleet-status --environment event --format markdown > reports/fleet-status-t14.md
  ```

### T-14 Sign-Off

```
Fleet preparation confirmed by:

Facilitator: Francis Anyaegbu     Date: ____________  Signature: ____________
Facilitator: Ernie Steagall       Date: ____________  Signature: ____________
Facilitator: Myles Vivian         Date: ____________  Signature: ____________
```

---

## T-7 Days: Accounts, ACM, and Identity (August 10, 2026)

Cross-reference: `../runbooks/student-accounts.md`, `../runbooks/acm-registration.md`

### Student Account Creation

- [ ] Create student accounts on all attendee clusters
  ```bash
  masworld student create --environment event --purpose attendee --parallel 10
  ```
  Expected: 50 student accounts created, one per attendee cluster.

- [ ] Validate student authentication on all clusters
  ```bash
  masworld student validate --environment event --parallel 10
  ```
  Expected: All 50 student accounts authenticate successfully.

- [ ] Validate student RBAC isolation
  ```bash
  masworld student validate --environment event --check rbac-isolation --parallel 10
  ```
  Expected: All students confined to assigned namespace, no cluster-admin, no ACM access.

- [ ] Run negative access tests
  ```bash
  masworld student validate --environment event --check negative-access
  ```
  Expected: Cross-namespace access denied. Cluster-admin denied. ACM admin denied. Protected secrets inaccessible.

- [ ] Create facilitator accounts
  ```bash
  masworld student create --environment event --purpose facilitator
  ```
  Expected: Facilitator accounts created with appropriate elevated access.

### ACM Registration

- [ ] Register all clusters with the ACM hub
  ```bash
  masworld fleet validate --environment event --check acm-registration --parallel 10
  ```
  Expected: All 56 clusters registered as ManagedClusters.

- [ ] Verify ManagedClusterSet assignment
  ```bash
  masworld fleet validate --environment event --check acm-clusterset
  ```
  Expected: All clusters in the `mas-world-2026` ManagedClusterSet.

- [ ] Verify cluster labels are applied correctly
  ```bash
  masworld fleet validate --environment event --check acm-labels
  ```
  Expected: All clusters have correct `event`, `workload`, `environment`, `seat`, `purpose`, `readiness` labels.

### ACM Governance Policies

- [ ] Deploy baseline governance policies
  ```bash
  masworld fleet validate --environment event --check acm-policies
  ```
  Expected: `policy-mas-world-baseline` and sub-policies deployed. All attendee clusters compliant.

- [ ] Pre-stage harmless drift on facilitator cluster for ACM demo
  ```bash
  masworld exercise reset --cluster facilitator-01 --module acm --action stage-drift
  ```
  Expected: Facilitator cluster shows one noncompliant policy. Attendee clusters unaffected.

- [ ] Verify ACM demo drift is contained to facilitator cluster only
  ```bash
  masworld fleet validate --environment event --check acm-compliance --purpose attendee
  ```
  Expected: All 50 attendee clusters `Compliant`. Facilitator cluster shows expected drift.

### Identity Integration

- [ ] Verify identity (Keycloak/OIDC) configuration on all clusters
  ```bash
  masworld fleet validate --environment event --check identity --parallel 10
  ```
  Expected: All clusters report `identity: PASS`.

### T-7 Sign-Off

```
Accounts and ACM confirmed by:

Facilitator: Francis Anyaegbu     Date: ____________  Signature: ____________
Facilitator: Ernie Steagall       Date: ____________  Signature: ____________
Facilitator: Myles Vivian         Date: ____________  Signature: ____________
```

---

## T-3 Days: Rehearsal (August 14, 2026)

Cross-reference: `../runbooks/rehearsal.md`

### Full Rehearsal Execution

- [ ] Revalidate entire fleet before rehearsal
  ```bash
  masworld fleet validate --environment event --full --parallel 10
  ```
  Expected: All 56 clusters `READY`.

- [ ] Conduct facilitator rehearsal of all five lab segments
  ```
  Segment 1: Navigation and Search       (10 min) -- Francis leads
  Segment 2: Advanced Cluster Management  (10 min) -- Ernie presents
  Segment 3: Updates                      (20 min) -- Ernie presents
  Segment 4: Observability and Logging    (40 min) -- Myles leads
  Segment 5: Identity Provider            (40 min) -- Francis leads
  ```

- [ ] Test Showroom loads correctly on at least 3 attendee clusters
  ```bash
  masworld cluster validate --cluster seat-01 --check showroom
  masworld cluster validate --cluster seat-25 --check showroom
  masworld cluster validate --cluster seat-50 --check showroom
  ```
  Expected: Showroom accessible and parameterized correctly on all tested clusters.

- [ ] Test exercise validation on rehearsal clusters
  ```bash
  masworld cluster validate --cluster seat-01 --check runtime-automation
  ```

- [ ] Test exercise solve automation
  ```bash
  masworld exercise reset --cluster seat-01 --module navigation --action solve
  masworld exercise reset --cluster seat-01 --module observability --action solve
  masworld exercise reset --cluster seat-01 --module identity --action solve
  ```
  Expected: Solve automation completes successfully for each module.

- [ ] Test exercise reset automation
  ```bash
  masworld exercise reset --cluster seat-01 --module navigation --action reset
  masworld exercise reset --cluster seat-01 --module observability --action reset
  masworld exercise reset --cluster seat-01 --module identity --action reset
  ```
  Expected: Exercises return to pre-exercise state.

- [ ] Test spare cluster replacement
  ```bash
  masworld seat assign --seat 1 --cluster seat-01
  masworld seat replace --seat 1 --cluster spare-01
  masworld seat show --seat 1
  ```
  Expected: Seat 1 reassigned to spare-01. Old cluster quarantined. New cluster validated.

  ```bash
  # Revert the test replacement
  masworld seat replace --seat 1 --cluster seat-01
  masworld seat unassign --seat 1
  ```

- [ ] Test ACM drift remediation demo end to end
  ```bash
  # Verify drift is staged
  masworld exercise reset --cluster facilitator-01 --module acm --action stage-drift
  # Presenter remediates during rehearsal
  # Verify compliance restored
  masworld fleet validate --environment event --check acm-compliance
  ```
  Expected: All clusters compliant after remediation.

- [ ] Test historical log query (observability exercise)
  ```bash
  masworld cluster validate --cluster seat-01 --check historical-log-query
  ```
  Expected: Historical logs queryable from Loki after sample workload deletion.

- [ ] Record rehearsal issues in `docs/rehearsal-findings.md`

### T-3 Sign-Off

```
Rehearsal completed by:

Facilitator: Francis Anyaegbu     Date: ____________  Signature: ____________
Facilitator: Ernie Steagall       Date: ____________  Signature: ____________
Facilitator: Myles Vivian         Date: ____________  Signature: ____________

Rehearsal result:  [ ] PASS  [ ] PASS WITH ISSUES  [ ] FAIL -- RESCHEDULE
```

---

## T-1 Day: Final Preparation (August 16, 2026)

Cross-reference: `../runbooks/final-preparation.md`

### Credential Rotation

- [ ] Rotate all student credentials
  ```bash
  masworld student rotate --environment event --parallel 10
  ```
  Expected: All 50 student passwords regenerated and stored in secret provider.

- [ ] Validate all rotated credentials
  ```bash
  masworld student validate --environment event --parallel 10
  ```
  Expected: All 50 students authenticate with new credentials.

### Final Fleet Validation

- [ ] Run full fleet validation
  ```bash
  masworld fleet validate --environment event --full --parallel 10
  ```
  Expected: All 56 clusters `READY`. Zero `FAIL`.

- [ ] Repair any clusters showing warnings or failures
  ```bash
  # For any cluster not READY:
  masworld cluster repair --cluster <CLUSTER_ID> --environment event --verbose
  masworld cluster validate --cluster <CLUSTER_ID> --environment event --full
  ```

### Seat Assignment

- [ ] Assign all attendee seats
  ```bash
  masworld seat assign --environment event --auto-assign --purpose attendee
  ```
  Expected: Seats 1 through 50 assigned to attendee clusters.

- [ ] Verify seat assignments
  ```bash
  masworld seat export-map --environment event --format json > reports/seat-map-final.json
  masworld seat export-map --environment event --format markdown > reports/seat-map-final.md
  ```

- [ ] Verify spare clusters remain unassigned and available
  ```bash
  masworld report fleet-status --environment event --purpose spare
  ```
  Expected: 5 spare clusters `READY`, `UNASSIGNED`.

### Attendee Materials

- [ ] Generate attendee access cards
  ```bash
  masworld student export-cards --environment event --format pdf \
    --output reports/access-cards/
  ```
  Expected: 50 individual access cards generated, each containing only that attendee's credentials.

- [ ] Generate facilitator seat inventory
  ```bash
  masworld report seat-report --environment event --format markdown \
    > reports/facilitator-seat-inventory.md
  ```

- [ ] Generate printable fallback assignment sheet
  ```bash
  masworld student export-cards --environment event --format csv \
    --output reports/fallback-assignments.csv
  ```

- [ ] Spot-check 3 access cards for correctness
  ```
  Verify card for seat 1:   correct Showroom URL, console URL, MAS URL, username, password
  Verify card for seat 25:  correct Showroom URL, console URL, MAS URL, username, password
  Verify card for seat 50:  correct Showroom URL, console URL, MAS URL, username, password
  ```

### ACM Demo Re-staging

- [ ] Re-stage ACM drift on facilitator cluster (fresh for event)
  ```bash
  masworld exercise reset --cluster facilitator-01 --module acm --action stage-drift
  ```
  Expected: Facilitator cluster shows expected noncompliant policy.

- [ ] Verify all attendee clusters remain compliant
  ```bash
  masworld fleet validate --environment event --check acm-compliance --purpose attendee
  ```
  Expected: All 50 attendee clusters `Compliant`.

### Final Reports

- [ ] Generate final fleet status report
  ```bash
  masworld report fleet-status --environment event --format json > reports/fleet-status-final.json
  masworld report fleet-status --environment event --format markdown > reports/fleet-status-final.md
  ```

- [ ] Archive all reports for event-day reference
  ```bash
  cp -r reports/ reports-archive-$(date +%Y%m%d)/
  ```

### Version Freeze

- [ ] Confirm automation repository is at the pinned release tag
  ```bash
  cd mas-world-2026-automation
  git describe --tags --exact-match
  ```
  Expected: Output matches the event release tag (e.g., `v1.0.0-event`).

- [ ] Confirm no uncommitted changes in automation
  ```bash
  git status --porcelain
  ```
  Expected: Clean working directory. No output.

### T-1 Sign-Off

```
Final preparation confirmed by:

Facilitator: Francis Anyaegbu     Date: ____________  Signature: ____________
Facilitator: Ernie Steagall       Date: ____________  Signature: ____________
Facilitator: Myles Vivian         Date: ____________  Signature: ____________

Fleet status:     [ ] ALL READY  [ ] READY WITH SPARES USED  [ ] NOT READY
Event go/no-go:   [ ] GO         [ ] NO-GO -- escalate to all facilitators
```

---

## Appendix: Quick Reference

| Milestone | Date            | Primary Owner | Approvers       |
|-----------|-----------------|---------------|-----------------|
| T-30      | July 18, 2026   | Francis       | Ernie, Myles    |
| T-14      | August 3, 2026  | Francis       | Ernie, Myles    |
| T-7       | August 10, 2026 | Francis       | Ernie, Myles    |
| T-3       | August 14, 2026 | Francis       | Ernie, Myles    |
| T-1       | August 16, 2026 | Francis       | Ernie, Myles    |
