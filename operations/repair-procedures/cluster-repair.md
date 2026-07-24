# Cluster Repair Procedures -- MAS World 2026

**Status**: DRAFT
**Date**: 2026-07-19
**Audience**: Facilitators (Francis Anyaegbu, Ernie Steagall, Myles Vivian)
**Cross-references**:
- Spare replacement: `mas-world-2026-operations/repair-procedures/spare-replacement.md`
- Event runbook: `mas-world-2026-operations/runbooks/`
- Credential lifecycle: `docs/credential-lifecycle.md`
- Architecture: `docs/architecture.md`

---

## Repair vs Replace Decision Flowchart

```text
Cluster failure detected
        |
        v
Is the cluster API reachable?
        |
   NO --+--> Is this during a live session?
        |           |
        |      YES -+--> REPLACE with spare immediately
        |           |    (target: <5 min to reassign)
        |      NO --+--> Attempt API recovery (5 min max)
        |                    |
        |               Recovered?
        |              YES --+--> Continue to component diagnosis
        |              NO ---+--> REPLACE with spare
        |
   YES -+--> Run automated repair
             |
             v
        masworld cluster repair --cluster <CLUSTER_ID>
             |
             v
        Did automated repair succeed?
             |
        YES -+--> Validate
             |        |
             |        v
             |   masworld cluster validate --cluster <CLUSTER_ID>
             |        |
             |   ALL PASS? --YES--> Return to service
             |        |
             |       NO --+--> Is this during a live session?
             |            |
             |       YES -+--> Has the attendee been waiting >10 min total?
             |            |         |
             |            |    YES -+--> REPLACE with spare
             |            |    NO --+--> One manual repair attempt (5 min)
             |            |                  |
             |            |             Resolved? --YES--> Validate and return
             |            |                  |
             |            |                 NO --+--> REPLACE with spare
             |            |
             |       NO --+--> Manual repair (up to 30 min)
             |                     |
             |                Resolved? --YES--> Validate and return
             |                     |
             |                    NO --+--> REPLACE with spare
             |
        NO --+--> Is this during a live session?
                  |
             YES -+--> REPLACE with spare immediately
             NO --+--> Manual repair (up to 30 min)
                           |
                      Resolved? --YES--> Validate and return
                           |
                          NO --+--> REPLACE with spare
```

**Key decision thresholds**:

| Scenario | Maximum repair time | Then |
|----------|-------------------|------|
| Live session, attendee blocked | 10 minutes total | Replace |
| Live session, attendee not blocked | 15 minutes total | Replace |
| Pre-event, spares available | 30 minutes | Replace |
| Pre-event, no spares available | 60 minutes | Escalate |
| Post-event | Best effort | Decommission |

---

## General Repair Workflow

All repair procedures follow this sequence:

1. Identify the failure (automated validation or attendee report).
2. Run automated diagnostics.
3. Attempt automated repair via the `masworld` CLI.
4. If automated repair fails, attempt manual fallback.
5. Validate after repair.
6. If validation fails, decide: retry manual repair or replace with spare.

**Automated repair command** (covers all known failure types):

```bash
masworld cluster repair --cluster <CLUSTER_ID>
```

**Targeted repair for a specific component**:

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component <COMPONENT>
```

Where `<COMPONENT>` is one of: `mas-core`, `maximo-manage`, `logging`,
`lokistack`, `s3`, `identity`, `student-auth`, `showroom`, `log-forwarding`.

**Validate after any repair**:

```bash
masworld cluster validate --cluster <CLUSTER_ID>
```

---

## 1. MAS Core Not Ready

### Symptoms

- Readiness check reports `mas_core: FAIL`.
- MAS operator pods in `CrashLoopBackOff`, `Error`, or `Pending` state.
- MAS Suite custom resource shows degraded conditions.
- MAS routes return 503 or are unreachable.
- Attendee reports "Maximo is not loading."

### Diagnostic Commands

```bash
# Check MAS operator pod status
oc get pods -n ibm-common-services --kubeconfig PLACEHOLDER_KUBECONFIG
oc get pods -n mas-<INSTANCE_ID>-core --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Suite custom resource status
oc get suite -n mas-<INSTANCE_ID>-core -o yaml --kubeconfig PLACEHOLDER_KUBECONFIG

# Check operator subscription and CSV
oc get sub -n ibm-common-services --kubeconfig PLACEHOLDER_KUBECONFIG
oc get csv -n ibm-common-services --kubeconfig PLACEHOLDER_KUBECONFIG

# Check MAS routes
oc get routes -n mas-<INSTANCE_ID>-core --kubeconfig PLACEHOLDER_KUBECONFIG

# Check events for errors
oc get events -n mas-<INSTANCE_ID>-core --sort-by='.lastTimestamp' \
  --kubeconfig PLACEHOLDER_KUBECONFIG | tail -30

# Check operator logs
oc logs deployment/ibm-mas-operator -n mas-<INSTANCE_ID>-core \
  --tail=100 --kubeconfig PLACEHOLDER_KUBECONFIG

# Check certificate readiness
oc get certificate -A --kubeconfig PLACEHOLDER_KUBECONFIG

# Check persistent volume claims
oc get pvc -n mas-<INSTANCE_ID>-core --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| Operator pod `CrashLoopBackOff` | OOM, missing dependency, catalog issue |
| CSV in `Pending` or `Failed` | Subscription channel mismatch, missing catalog source |
| Suite CR conditions show `MongoDBNotReady` | MongoDB prerequisite not ready |
| Suite CR conditions show `CertificateNotReady` | cert-manager not functioning |
| Routes exist but return 503 | Backend pods not ready |
| PVC in `Pending` | StorageClass or capacity issue |
| ImagePullBackOff on operator pods | IBM registry credential issue |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component mas-core
```

The automated repair attempts, in order:
1. Verify IBM catalog source is present and healthy.
2. Verify IBM entitlement pull secret is configured.
3. Restart degraded operator pods.
4. Wait for operator CSV to reach `Succeeded`.
5. Verify prerequisite CRs (MongoDB, cert-manager).
6. Wait for Suite CR conditions to stabilize (up to 15 minutes).
7. Verify MAS routes are responding.

### Manual Fallback

If automated repair fails:

```bash
# 1. Check and restore IBM catalog source
oc get catalogsource -n openshift-marketplace --kubeconfig PLACEHOLDER_KUBECONFIG
oc get catalogsource ibm-operator-catalog -n openshift-marketplace -o yaml \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 2. Check IBM entitlement pull secret
oc get secret ibm-entitlement-key -n ibm-common-services \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 3. Delete and allow operator pod to be recreated
oc delete pod -l app=ibm-mas -n mas-<INSTANCE_ID>-core \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 4. If CSV is stuck, delete and allow subscription to recreate
oc delete csv <CSV_NAME> -n ibm-common-services --kubeconfig PLACEHOLDER_KUBECONFIG

# 5. Wait and recheck (allow up to 10 minutes)
oc wait --for=condition=Ready suite/<INSTANCE_ID> \
  -n mas-<INSTANCE_ID>-core --timeout=600s --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks mas_core
```

Expected output: `mas_core: PASS`

### Estimated Time to Repair

- Automated repair: 10-20 minutes (operator reconciliation is slow).
- Manual repair: 15-30 minutes.
- If prerequisite (MongoDB, cert-manager) is the root cause: 20-45 minutes.

### Repair vs Replace Decision

- **During live session**: If MAS Core is not ready within 10 minutes of
  detection, replace with spare. Attendees cannot proceed with any MAS
  exercises without it.
- **Pre-event**: Allow up to 45 minutes for automated + manual repair.
  Prerequisite repairs (MongoDB, cert-manager) take significant time to
  reconcile.

---

## 2. Maximo Manage Degraded

### Symptoms

- Readiness check reports `maximo_manage: FAIL`.
- Manage workspace CR shows degraded or non-Ready conditions.
- Manage pods are not running or are crashlooping.
- Maximo UI loads but returns errors or is blank.
- Database connectivity errors in Manage pod logs.
- Manage activation shows `ActivationFailed`.

### Diagnostic Commands

```bash
# Check Manage workspace CR
oc get manageworkspace -n mas-<INSTANCE_ID>-manage -o yaml \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Manage pods
oc get pods -n mas-<INSTANCE_ID>-manage --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Manage server bundle pods specifically
oc get pods -n mas-<INSTANCE_ID>-manage -l app=manage-maxinst \
  --kubeconfig PLACEHOLDER_KUBECONFIG
oc get pods -n mas-<INSTANCE_ID>-manage -l app=manage-all \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check database connectivity from a Manage pod
oc logs deployment/<MANAGE_DEPLOYMENT> -n mas-<INSTANCE_ID>-manage \
  --tail=50 --kubeconfig PLACEHOLDER_KUBECONFIG | grep -i "database\|jdbc\|sql\|connect"

# Check Manage route
oc get route -n mas-<INSTANCE_ID>-manage --kubeconfig PLACEHOLDER_KUBECONFIG

# Check events
oc get events -n mas-<INSTANCE_ID>-manage --sort-by='.lastTimestamp' \
  --kubeconfig PLACEHOLDER_KUBECONFIG | tail -30

# Check PVCs
oc get pvc -n mas-<INSTANCE_ID>-manage --kubeconfig PLACEHOLDER_KUBECONFIG

# Check JdbcCfg
oc get jdbccfg -n mas-<INSTANCE_ID>-core -o yaml --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| ManageWorkspace `ActivationFailed` | Database schema deployment failed |
| Pods `CrashLoopBackOff` with JDBC errors | Database unreachable or credentials invalid |
| ManageWorkspace `DeploymentFailed` | Image pull failure or resource constraint |
| Manage route 503 | Backend pods not started |
| JdbcCfg not Ready | Database connection configuration issue |
| PVC Pending | Storage provisioning issue |
| maxinst pod failed | Initial database setup (first deployment) failed |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component maximo-manage
```

The automated repair attempts:
1. Verify JdbcCfg CR is Ready (database connectivity).
2. Verify database credentials secret exists.
3. Restart failed Manage pods.
4. Wait for ManageWorkspace to reconcile (up to 20 minutes).
5. Verify Manage route returns HTTP 200.

### Manual Fallback

```bash
# 1. Verify database credentials secret
oc get secret <JDBC_SECRET_NAME> -n mas-<INSTANCE_ID>-core \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 2. Test database connectivity from within the cluster
oc run db-test --rm -it --restart=Never \
  --image=registry.access.redhat.com/ubi9/ubi-minimal:latest \
  -n mas-<INSTANCE_ID>-manage --kubeconfig PLACEHOLDER_KUBECONFIG \
  -- bash -c "curl -v telnet://PLACEHOLDER_DB_HOST:PLACEHOLDER_DB_PORT"

# 3. If database credentials are stale, re-apply from secret provider
# (coordinate with credential lifecycle -- see docs/credential-lifecycle.md)

# 4. Restart Manage deployment
oc rollout restart deployment -n mas-<INSTANCE_ID>-manage \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 5. Watch for recovery
oc get manageworkspace -n mas-<INSTANCE_ID>-manage -w \
  --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks maximo_manage,database
```

Expected output: `maximo_manage: PASS`, `database: PASS`

### Estimated Time to Repair

- Database credential issue: 5-10 minutes.
- Pod restart with healthy database: 5-15 minutes.
- Manage activation failure (maxinst re-run): 30-60 minutes.
- Full Manage redeployment: not recommended during event.

### Repair vs Replace Decision

- **During live session**: If Manage is not accessible within 10 minutes,
  replace. Manage activation failures can take 30+ minutes to resolve.
- **Pre-event**: Allow up to 30 minutes for pod-level issues. If activation
  itself failed, consider re-running the prepare playbook for the Manage
  component (up to 60 minutes). If that fails, replace.

---

## 3. Logging Stack Failure

### Symptoms

- Readiness check reports `logging_operator: FAIL`.
- Logging operator pods not running.
- Collector (Vector) pods not running or crashlooping.
- No log data appearing in Loki.
- Attendee cannot complete observability exercise.

### Diagnostic Commands

```bash
# Check Logging operator
oc get pods -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG
oc get csv -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG

# Check collector pods
oc get ds -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG
oc get pods -n openshift-logging -l component=collector \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check collector logs for errors
oc logs ds/collector -n openshift-logging --tail=50 \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check ClusterLogging CR
oc get clusterlogging -n openshift-logging -o yaml \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check subscription
oc get sub cluster-logging -n openshift-logging -o yaml \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check events
oc get events -n openshift-logging --sort-by='.lastTimestamp' \
  --kubeconfig PLACEHOLDER_KUBECONFIG | tail -20
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| Operator pod not running | Subscription or CSV issue |
| Collector DaemonSet 0/N ready | Node scheduling or image pull issue |
| Collector pods `CrashLoopBackOff` | Configuration error or LokiStack endpoint unreachable |
| CSV `Pending` | Catalog source issue, dependency not met |
| No ClusterLogging CR present | Initial deployment incomplete |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component logging
```

The automated repair attempts:
1. Verify Logging operator subscription exists and is healthy.
2. Verify CSV status.
3. Restart degraded operator pods if needed.
4. Verify ClusterLogging CR exists.
5. Verify collector DaemonSet is scheduling on all nodes.
6. Wait for collector pods to reach Ready state.

### Manual Fallback

```bash
# 1. If CSV is stuck, delete and let subscription recreate
oc delete csv <LOGGING_CSV_NAME> -n openshift-logging \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 2. If collector pods are crashlooping, check for config issues
oc describe ds/collector -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG

# 3. If collector cannot reach Loki, check service endpoint
oc get svc -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG | grep loki

# 4. Restart collector pods
oc delete pods -l component=collector -n openshift-logging \
  --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks logging_operator
```

Expected output: `logging_operator: PASS`

### Estimated Time to Repair

- Collector pod restart: 2-5 minutes.
- Operator CSV recovery: 5-10 minutes.
- Full redeployment of Logging stack: 10-20 minutes.

### Repair vs Replace Decision

- **During live session**: Logging is needed for the observability module. If
  the attendee has not reached that module yet, allow up to 15 minutes for
  repair. If they are currently on the observability module and blocked, replace
  after 10 minutes.
- **Pre-event**: Allow up to 20 minutes. Re-run the logging role from the
  prepare playbook if needed.

---

## 4. LokiStack Not Ready

### Symptoms

- Readiness check reports `lokistack: FAIL`.
- LokiStack pods in `Pending`, `CrashLoopBackOff`, or `Error` state.
- LokiStack CR conditions show errors.
- Log queries return no results or errors.
- Ingestion failures visible in collector logs.

### Diagnostic Commands

```bash
# Check Loki operator
oc get pods -n openshift-operators-redhat -l app.kubernetes.io/name=loki-operator \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check LokiStack CR
oc get lokistack -n openshift-logging -o yaml --kubeconfig PLACEHOLDER_KUBECONFIG

# Check LokiStack pods
oc get pods -n openshift-logging -l app.kubernetes.io/managed-by=lokistack-controller \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check for pending PVCs
oc get pvc -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Loki ingester and compactor status
oc logs -l app.kubernetes.io/component=ingester -n openshift-logging \
  --tail=30 --kubeconfig PLACEHOLDER_KUBECONFIG

# Check S3 connectivity from Loki pods
oc logs -l app.kubernetes.io/component=compactor -n openshift-logging \
  --tail=30 --kubeconfig PLACEHOLDER_KUBECONFIG | grep -i "s3\|storage\|error"

# Check object storage secret
oc get secret logging-loki-s3 -n openshift-logging \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check events
oc get events -n openshift-logging --sort-by='.lastTimestamp' \
  --kubeconfig PLACEHOLDER_KUBECONFIG | tail -20
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| Pods `Pending` | PVC not provisioned or insufficient resources |
| Pods `CrashLoopBackOff` with S3 errors | S3 credential or bucket issue |
| LokiStack `Degraded` condition | Partial component failure |
| Ingester pod OOM killed | Insufficient memory limits for workload |
| Compactor failing | S3 connectivity or permission issue |
| PVC `Pending` | StorageClass issue or no available capacity |
| Object storage secret missing | S3 credential not injected |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component lokistack
```

The automated repair attempts:
1. Verify Loki operator is running.
2. Verify object storage secret exists and has required keys.
3. Verify S3 bucket exists and is accessible (see S3 repair in section 5).
4. Restart failed LokiStack pods.
5. Wait for LokiStack CR to report Ready (up to 10 minutes).
6. Run a test log query to confirm ingestion is working.

### Manual Fallback

```bash
# 1. Check if object storage secret is present and correct
oc get secret logging-loki-s3 -n openshift-logging -o jsonpath='{.data}' \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 2. If secret is missing, re-run the S3 credential provisioning
masworld cluster repair --cluster <CLUSTER_ID> --component s3

# 3. If pods are in Pending due to PVCs, check StorageClass
oc get sc --kubeconfig PLACEHOLDER_KUBECONFIG
oc get pvc -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG

# 4. Delete stuck pods to trigger reschedule
oc delete pods -l app.kubernetes.io/managed-by=lokistack-controller \
  -n openshift-logging --field-selector=status.phase!=Running \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 5. If LokiStack is fundamentally broken, delete and re-create
# WARNING: This loses buffered data. Use only pre-event.
oc delete lokistack logging-loki -n openshift-logging \
  --kubeconfig PLACEHOLDER_KUBECONFIG
# Then re-run the lokistack role:
# masworld cluster repair --cluster <CLUSTER_ID> --component lokistack
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks lokistack,historical_log_query
```

Expected output: `lokistack: PASS`, `historical_log_query: PASS`

### Estimated Time to Repair

- Pod restart with healthy S3: 3-5 minutes.
- S3 credential fix + LokiStack restart: 5-10 minutes.
- PVC or StorageClass issue: 10-20 minutes.
- Full LokiStack delete/recreate: 15-25 minutes.

### Repair vs Replace Decision

- **During live session**: If the attendee is on the observability module and
  LokiStack is not recoverable in 10 minutes, replace. If they have not
  reached that module, allow 15 minutes.
- **Pre-event**: Allow up to 25 minutes. If the LokiStack needs full
  recreation, re-run the prepare playbook for logging components.

---

## 5. S3 Connectivity Failure

### Symptoms

- Readiness check reports `s3_write_read: FAIL`.
- LokiStack pods logging S3 access denied or connection errors.
- Compactor or ingester pods failing with storage backend errors.
- Attendees cannot see historical logs (data not persisted).

### Diagnostic Commands

```bash
# Check object storage secret in the cluster
oc get secret logging-loki-s3 -n openshift-logging -o yaml \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Verify the secret has required keys (do NOT print values)
oc get secret logging-loki-s3 -n openshift-logging \
  -o jsonpath='{range .data}{@}{"\n"}{end}' \
  --kubeconfig PLACEHOLDER_KUBECONFIG | wc -l

# Check Loki compactor logs for S3 errors
oc logs -l app.kubernetes.io/component=compactor -n openshift-logging \
  --tail=50 --kubeconfig PLACEHOLDER_KUBECONFIG 2>&1 | grep -i "s3\|access\|denied\|bucket\|error"

# Check Loki ingester logs for S3 errors
oc logs -l app.kubernetes.io/component=ingester -n openshift-logging \
  --tail=50 --kubeconfig PLACEHOLDER_KUBECONFIG 2>&1 | grep -i "s3\|access\|denied\|bucket\|error"

# Verify bucket exists (from workstation with AWS CLI)
aws s3api head-bucket --bucket PLACEHOLDER_BUCKET_NAME \
  --region PLACEHOLDER_AWS_REGION 2>&1

# Check bucket policy
aws s3api get-bucket-policy --bucket PLACEHOLDER_BUCKET_NAME \
  --region PLACEHOLDER_AWS_REGION 2>&1

# Verify IAM credentials are valid (from workstation with AWS CLI)
aws sts get-caller-identity --region PLACEHOLDER_AWS_REGION 2>&1
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| `AccessDenied` in Loki logs | IAM credentials expired, revoked, or wrong policy |
| `NoSuchBucket` in Loki logs | Bucket deleted or name mismatch |
| `RequestTimeTooSkewed` | Clock drift on nodes |
| Connection timeout | Network or VPC endpoint issue |
| Secret missing or empty | S3 credentials not provisioned for this cluster |
| `InvalidAccessKeyId` | IAM key was rotated but cluster secret not updated |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component s3
```

The automated repair attempts:
1. Verify bucket exists; create if missing.
2. Verify public access block is enabled.
3. Verify encryption is configured.
4. Verify IAM credentials are valid.
5. Regenerate IAM credentials if invalid.
6. Update the Kubernetes secret with current credentials.
7. Restart LokiStack pods to pick up new credentials.
8. Perform a write/read test against the bucket.

### Manual Fallback

```bash
# 1. Recreate the bucket if missing
aws s3api create-bucket --bucket PLACEHOLDER_BUCKET_NAME \
  --region PLACEHOLDER_AWS_REGION \
  --create-bucket-configuration LocationConstraint=PLACEHOLDER_AWS_REGION

aws s3api put-public-access-block --bucket PLACEHOLDER_BUCKET_NAME \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# 2. Create or rotate IAM credentials
# (Use the credential lifecycle process in docs/credential-lifecycle.md)

# 3. Update the Kubernetes secret
oc create secret generic logging-loki-s3 \
  -n openshift-logging \
  --from-literal=access_key_id=PLACEHOLDER_ACCESS_KEY \
  --from-literal=access_key_secret=PLACEHOLDER_SECRET_KEY \
  --from-literal=bucketnames=PLACEHOLDER_BUCKET_NAME \
  --from-literal=endpoint=https://s3.PLACEHOLDER_AWS_REGION.amazonaws.com \
  --from-literal=region=PLACEHOLDER_AWS_REGION \
  --dry-run=client -o yaml --kubeconfig PLACEHOLDER_KUBECONFIG | \
  oc apply -f - --kubeconfig PLACEHOLDER_KUBECONFIG

# 4. Restart LokiStack to use new credentials
oc delete pods -l app.kubernetes.io/managed-by=lokistack-controller \
  -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks s3_write_read,lokistack
```

Expected output: `s3_write_read: PASS`, `lokistack: PASS`

### Estimated Time to Repair

- Credential refresh + pod restart: 5-10 minutes.
- Bucket recreation + credential provision: 10-15 minutes.
- Network or VPC endpoint issue: 15-30 minutes (may require escalation).

### Repair vs Replace Decision

- **During live session**: S3 issues block the observability module only. If
  the attendee has not reached that module, allow 15 minutes. If they are on
  the observability module, replace after 10 minutes.
- **Pre-event**: Allow up to 20 minutes. Re-run the full S3 + LokiStack
  provisioning if needed.

---

## 6. Identity/Keycloak Failure

### Symptoms

- Readiness check reports `identity: FAIL`.
- Keycloak pod not running, crashlooping, or unresponsive.
- Keycloak route returns 503 or certificate error.
- Keycloak realm missing or misconfigured.
- OIDC authentication test fails.
- LDAP group sync produces errors.

### Diagnostic Commands

```bash
# Check Keycloak pods
oc get pods -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Keycloak statefulset or deployment
oc get statefulset -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG
oc describe statefulset keycloak -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Keycloak logs
oc logs statefulset/keycloak -n keycloak --tail=50 \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Keycloak route and certificate
oc get route -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG
oc get certificate -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Keycloak PVC
oc get pvc -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG

# Test Keycloak endpoint
KEYCLOAK_URL=$(oc get route keycloak -n keycloak \
  -o jsonpath='{.spec.host}' --kubeconfig PLACEHOLDER_KUBECONFIG)
curl -sk "https://${KEYCLOAK_URL}/health/ready"

# Check events
oc get events -n keycloak --sort-by='.lastTimestamp' \
  --kubeconfig PLACEHOLDER_KUBECONFIG | tail -20
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| Pod `CrashLoopBackOff` | Database issue, bad config, OOM |
| Pod `Pending` | PVC not bound or resource constraint |
| Route returns certificate error | Certificate not issued or expired |
| Realm not found | Initial realm import failed |
| LDAP connection error | LDAP server unreachable or credentials wrong |
| OIDC client misconfigured | Client secret mismatch or redirect URI wrong |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component identity
```

The automated repair attempts:
1. Verify Keycloak pod is running.
2. Restart if crashlooping.
3. Verify route and certificate are valid.
4. Verify realm exists.
5. Re-import realm configuration if missing.
6. Verify OIDC client configuration.
7. Test authentication flow.

### Manual Fallback

```bash
# 1. Restart Keycloak
oc rollout restart statefulset/keycloak -n keycloak \
  --kubeconfig PLACEHOLDER_KUBECONFIG
oc rollout status statefulset/keycloak -n keycloak --timeout=120s \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 2. If PVC issue, check StorageClass and capacity
oc get pvc -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG
oc get sc --kubeconfig PLACEHOLDER_KUBECONFIG

# 3. If certificate expired or missing
oc get certificate -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG
# Check cert-manager is functioning
oc get pods -n cert-manager --kubeconfig PLACEHOLDER_KUBECONFIG
# Delete certificate to trigger reissuance
oc delete certificate keycloak-tls -n keycloak --kubeconfig PLACEHOLDER_KUBECONFIG

# 4. If realm import failed, re-run the identity role
masworld cluster repair --cluster <CLUSTER_ID> --component identity
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks identity
```

Expected output: `identity: PASS`

### Estimated Time to Repair

- Pod restart: 2-5 minutes.
- Certificate reissuance: 3-10 minutes.
- Realm re-import: 5-10 minutes.
- Full redeployment: 10-20 minutes.

### Repair vs Replace Decision

- **During live session**: Identity is needed for the identity module only. If
  the attendee has not reached that module, allow 15 minutes. If they are
  blocked on identity exercises, replace after 10 minutes.
- **Pre-event**: Allow up to 20 minutes.

---

## 7. Student Authentication Failure

### Symptoms

- Readiness check reports `student_authentication: FAIL` or `student_rbac: FAIL`.
- Attendee cannot log in to OpenShift console.
- `oc login` with student credentials fails.
- OAuth server returns errors.
- HTPasswd identity provider not configured.

### Diagnostic Commands

```bash
# Check OAuth configuration
oc get oauth cluster -o yaml --kubeconfig PLACEHOLDER_KUBECONFIG

# Check htpasswd secret exists
oc get secret htpasswd-secret -n openshift-config \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check OAuth server pods
oc get pods -n openshift-authentication --kubeconfig PLACEHOLDER_KUBECONFIG

# Check OAuth server logs
oc logs deployment/oauth-openshift -n openshift-authentication \
  --tail=30 --kubeconfig PLACEHOLDER_KUBECONFIG

# Test student login (from workstation)
# WARNING: Password is retrieved from secret provider, not hard-coded
oc login PLACEHOLDER_API_URL --username=PLACEHOLDER_USERNAME \
  --password=PLACEHOLDER_PASSWORD --insecure-skip-tls-verify

# Check RoleBindings for the student
oc get rolebinding -n student-PLACEHOLDER_SEAT_NUMBER \
  --kubeconfig PLACEHOLDER_KUBECONFIG
oc get clusterrolebinding | grep PLACEHOLDER_USERNAME

# Check if student namespace exists
oc get namespace student-PLACEHOLDER_SEAT_NUMBER \
  --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| HTPasswd secret missing | Student account creation did not run |
| OAuth pods not ready | OAuth server deployment issue (can affect all users) |
| Login fails with "invalid credentials" | Password mismatch between htpasswd and secret provider |
| Login succeeds but namespace access denied | RoleBinding missing or wrong |
| Student namespace missing | Namespace creation step failed |
| OAuth CR missing htpasswd provider | OAuth configuration not applied |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component student-auth
```

The automated repair attempts:
1. Verify OAuth configuration includes htpasswd provider.
2. Verify htpasswd secret exists with correct user entries.
3. Re-sync htpasswd from secret provider if passwords mismatched.
4. Verify student namespace exists.
5. Verify RoleBindings for the student.
6. Restart OAuth server if configuration was changed.
7. Wait for OAuth pods to stabilize.
8. Test student login.

### Manual Fallback

```bash
# 1. Recreate student accounts for this cluster
masworld student create --cluster <CLUSTER_ID>

# 2. If only one student needs repair
masworld student create --cluster <CLUSTER_ID> --seat <SEAT_NUMBER>

# 3. If OAuth server is unstable, restart it
oc rollout restart deployment/oauth-openshift -n openshift-authentication \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 4. Wait for OAuth to stabilize (critical -- affects ALL logins)
oc rollout status deployment/oauth-openshift -n openshift-authentication \
  --timeout=120s --kubeconfig PLACEHOLDER_KUBECONFIG

# 5. Validate login
masworld student validate --cluster <CLUSTER_ID> --seat <SEAT_NUMBER>
```

**WARNING**: Restarting the OAuth server temporarily disrupts ALL
authentication on the cluster, including any active attendee sessions. During a
live session, coordinate with the attendee before restarting OAuth.

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks student_authentication,student_rbac
```

Expected output: `student_authentication: PASS`, `student_rbac: PASS`

### Estimated Time to Repair

- HTPasswd re-sync: 2-5 minutes.
- OAuth server restart: 2-3 minutes (plus brief authentication outage).
- Full student account recreation: 3-5 minutes.

### Repair vs Replace Decision

- **During live session**: Student auth failure blocks the attendee completely.
  If not resolved in 5 minutes via automated repair, replace. Do not restart
  OAuth during a live session unless absolutely necessary.
- **Pre-event**: Allow up to 10 minutes. Recreating accounts is fast and safe.

---

## 8. Showroom Not Loading

### Symptoms

- Readiness check reports `showroom: FAIL`.
- Attendee cannot access the workshop instructions.
- Showroom URL returns 503, 404, or connection refused.
- Showroom loads but shows incorrect variables (placeholders instead of values).
- Terminal tab does not connect.

### Diagnostic Commands

```bash
# Check Showroom deployment
oc get pods -n showroom --kubeconfig PLACEHOLDER_KUBECONFIG
oc get deployment -n showroom --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Showroom route
oc get route -n showroom --kubeconfig PLACEHOLDER_KUBECONFIG
SHOWROOM_URL=$(oc get route showroom -n showroom \
  -o jsonpath='{.spec.host}' --kubeconfig PLACEHOLDER_KUBECONFIG)
curl -sk "https://${SHOWROOM_URL}" | head -20

# Check Showroom ConfigMap (contains injected variables)
oc get configmap showroom-config -n showroom -o yaml \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check Showroom logs
oc logs deployment/showroom -n showroom --tail=50 \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check terminal/wetty pods
oc get pods -n showroom -l app=wetty --kubeconfig PLACEHOLDER_KUBECONFIG

# Check events
oc get events -n showroom --sort-by='.lastTimestamp' \
  --kubeconfig PLACEHOLDER_KUBECONFIG | tail -20

# Check if the namespace exists
oc get namespace showroom --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| Showroom pod not running | Deployment issue, image pull failure |
| Route exists but 503 | Pod not ready or service selector mismatch |
| Page loads with PLACEHOLDER values | ConfigMap not injected or stale |
| Terminal tab fails to connect | Wetty pod not running or network policy |
| 404 on all pages | Content not mounted or Antora build failed |
| Namespace missing | Showroom deployment never ran |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component showroom
```

The automated repair attempts:
1. Verify Showroom namespace exists.
2. Verify Showroom deployment and pods are running.
3. Verify ConfigMap contains correct per-seat variables.
4. Re-inject variables if stale or missing.
5. Restart Showroom pods if ConfigMap was updated.
6. Verify route is accessible.
7. Verify terminal connectivity.

### Manual Fallback

```bash
# 1. If namespace or deployment is missing, re-run Showroom deployment
masworld cluster repair --cluster <CLUSTER_ID> --component showroom

# 2. If ConfigMap has wrong values, update it
# Re-run Showroom variable injection for this seat
masworld cluster repair --cluster <CLUSTER_ID> --component showroom

# 3. Restart Showroom pods
oc rollout restart deployment/showroom -n showroom \
  --kubeconfig PLACEHOLDER_KUBECONFIG
oc rollout status deployment/showroom -n showroom --timeout=60s \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 4. If the image cannot be pulled, check registry access
oc get pods -n showroom -o jsonpath='{.items[*].status.containerStatuses[*].state}' \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 5. If terminal is broken, restart wetty
oc rollout restart deployment/wetty -n showroom \
  --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks showroom,runtime_automation
```

Expected output: `showroom: PASS`, `runtime_automation: PASS`

### Estimated Time to Repair

- Pod restart: 1-3 minutes.
- ConfigMap re-injection + restart: 2-5 minutes.
- Full Showroom redeployment: 5-10 minutes.

### Repair vs Replace Decision

- **During live session**: Showroom failure blocks the attendee from reading
  instructions. This is critical. If not resolved in 5 minutes, replace. The
  attendee has no way to follow the workshop without it.
- **Pre-event**: Allow up to 10 minutes. Full redeployment is straightforward.

---

## 9. ClusterLogForwarder Misconfigured

### Symptoms

- Readiness check reports `cluster_log_forwarder: FAIL`.
- ClusterLogForwarder CR shows error conditions.
- Logs are collected but not forwarded to LokiStack.
- Partial log types missing (e.g., audit logs not appearing).
- Collector pods running but pipeline metrics show zero throughput.

### Diagnostic Commands

```bash
# Check ClusterLogForwarder CR
oc get clusterlogforwarder -n openshift-logging -o yaml \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check CLF conditions
oc get clusterlogforwarder instance -n openshift-logging \
  -o jsonpath='{.status.conditions}' --kubeconfig PLACEHOLDER_KUBECONFIG | python3 -m json.tool

# Check collector logs for pipeline errors
oc logs ds/collector -n openshift-logging --tail=50 \
  --kubeconfig PLACEHOLDER_KUBECONFIG 2>&1 | grep -i "error\|pipeline\|forward\|drop"

# Check if CLF references a valid output
oc get clusterlogforwarder instance -n openshift-logging \
  -o jsonpath='{.spec.outputs}' --kubeconfig PLACEHOLDER_KUBECONFIG

# Verify LokiStack service is reachable from collector
oc get svc -n openshift-logging --kubeconfig PLACEHOLDER_KUBECONFIG | grep loki
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| CLF status `Degraded` | Invalid pipeline or output reference |
| Missing log types in output | Input selector not configured for that type |
| Collector dropping logs | LokiStack output backpressure or misconfigured endpoint |
| CLF CR missing | Initial deployment incomplete |
| Output references wrong service name | LokiStack name mismatch |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID> --component log-forwarding
```

The automated repair attempts:
1. Verify ClusterLogForwarder CR exists.
2. Verify outputs reference the correct LokiStack endpoint.
3. Verify inputs include application, infrastructure, and audit.
4. Verify pipelines connect inputs to outputs.
5. Re-apply the CLF CR if misconfigured.
6. Restart collector pods after CLF update.
7. Verify log flow by checking ingestion metrics.

### Manual Fallback

```bash
# 1. Delete and re-create the ClusterLogForwarder
oc delete clusterlogforwarder instance -n openshift-logging \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Re-apply from the known-good configuration
masworld cluster repair --cluster <CLUSTER_ID> --component log-forwarding

# 2. Restart collector pods to pick up new CLF
oc delete pods -l component=collector -n openshift-logging \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 3. Wait and verify log ingestion
# Generate a test log entry and query for it in Loki
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID> --checks cluster_log_forwarder,historical_log_query
```

Expected output: `cluster_log_forwarder: PASS`, `historical_log_query: PASS`

### Estimated Time to Repair

- CLF re-apply + collector restart: 3-5 minutes.
- Full pipeline verification including log query: 5-10 minutes.

### Repair vs Replace Decision

- **During live session**: CLF issues only affect the observability module. If
  the attendee is not on that module, allow 10 minutes. If they are blocked,
  replace after 10 minutes.
- **Pre-event**: Allow up to 15 minutes. This is a fast repair in most cases.

---

## 10. OpenShift API Unreachable

### Symptoms

- Readiness check reports `openshift: FAIL`.
- All `oc` commands fail with connection refused or timeout.
- OpenShift console is unreachable.
- All cluster workloads are inaccessible.

### Diagnostic Commands

```bash
# Test API reachability
curl -sk https://PLACEHOLDER_API_URL:6443/healthz

# DNS resolution
dig PLACEHOLDER_API_HOSTNAME

# Network path
traceroute PLACEHOLDER_API_HOSTNAME

# Check from AWS Console or CLI whether instances are running
aws ec2 describe-instances --region PLACEHOLDER_AWS_REGION \
  --filters "Name=tag:kubernetes.io/cluster/PLACEHOLDER_CLUSTER_ID,Values=owned" \
  --query "Reservations[].Instances[].{ID:InstanceId,State:State.Name,Type:InstanceType}" \
  --output table

# Check load balancer health (API server LB)
aws elbv2 describe-target-health \
  --target-group-arn PLACEHOLDER_TARGET_GROUP_ARN \
  --region PLACEHOLDER_AWS_REGION
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| DNS not resolving | DNS zone issue, Route53 problem |
| Connection refused | API server pods not running, LB misconfigured |
| Connection timeout | Security group, NACL, or routing issue |
| EC2 instances stopped | Instance terminated or stopped |
| Certificate error | API server certificate expired |
| Partial connectivity | Control plane node failure (one of several) |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID>
```

The automated repair has limited capability when the API is unreachable. It
will:
1. Test DNS resolution.
2. Test network connectivity on port 6443.
3. Report diagnostic findings.
4. If connectivity is restored, proceed with standard repair.

**Most API unreachable issues require infrastructure-level intervention.**

### Manual Fallback

```bash
# 1. Verify DNS
dig +short PLACEHOLDER_API_HOSTNAME

# 2. If DNS is fine, check if API is responding on the resolved IP
curl -sk --connect-timeout 10 https://PLACEHOLDER_API_IP:6443/healthz

# 3. If instances are stopped, start them (requires AWS access)
aws ec2 start-instances --instance-ids PLACEHOLDER_INSTANCE_ID \
  --region PLACEHOLDER_AWS_REGION

# 4. If control plane nodes are unhealthy, this is a platform issue.
# Escalate to the cluster provisioning team or Red Hat support.
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID>
```

All checks must pass for the cluster to return to service.

### Estimated Time to Repair

- DNS propagation fix: 5-15 minutes.
- EC2 instance restart: 5-10 minutes.
- Control plane recovery: 15-60 minutes (may require escalation).
- Full cluster rebuild: not feasible during event.

### Repair vs Replace Decision

- **During live session**: If the API is unreachable, replace immediately. Do
  not wait. The attendee is completely blocked and infrastructure-level
  repairs are unpredictable.
- **Pre-event**: Allow up to 30 minutes for infrastructure-level
  troubleshooting. If the cluster is provisioned by an external team, escalate
  immediately and use a spare for the seat in the meantime.

---

## 11. Node Pressure or Resource Exhaustion

### Symptoms

- Readiness check reports warnings or failures related to node health.
- Pods in `Pending` state across multiple namespaces.
- Pods being evicted or OOM killed.
- Node status shows `MemoryPressure`, `DiskPressure`, or `PIDPressure`.
- Degraded `ClusterOperators`.
- Slow API responses.

### Diagnostic Commands

```bash
# Check node status
oc get nodes --kubeconfig PLACEHOLDER_KUBECONFIG
oc describe nodes --kubeconfig PLACEHOLDER_KUBECONFIG | \
  grep -A5 "Conditions:" | grep -E "MemoryPressure|DiskPressure|PIDPressure|Ready"

# Check resource allocation
oc adm top nodes --kubeconfig PLACEHOLDER_KUBECONFIG
oc adm top pods -A --sort-by=memory --kubeconfig PLACEHOLDER_KUBECONFIG | head -20

# Check for pending pods
oc get pods -A --field-selector=status.phase=Pending \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# Check for evicted pods
oc get pods -A --field-selector=status.phase=Failed \
  --kubeconfig PLACEHOLDER_KUBECONFIG | grep Evicted

# Check node resource requests vs capacity
oc describe nodes --kubeconfig PLACEHOLDER_KUBECONFIG | \
  grep -A20 "Allocated resources"

# Check for degraded ClusterOperators
oc get clusteroperators --kubeconfig PLACEHOLDER_KUBECONFIG | \
  grep -v "True.*False.*False"

# Check disk usage on nodes (if SSH available)
# Otherwise check machine health from AWS
aws ec2 describe-instance-status --instance-ids PLACEHOLDER_INSTANCE_ID \
  --region PLACEHOLDER_AWS_REGION
```

### Root Cause Identification

| Observation | Likely cause |
|------------|-------------|
| MemoryPressure on nodes | Too many workloads or memory leak |
| DiskPressure | Log volume, image cache, or PV full |
| Pods Pending with "Insufficient cpu/memory" | Resource requests exceed capacity |
| Multiple pods Evicted | Node under pressure, kubelet evicting pods |
| Single node NotReady | Node failure (hardware, network, kubelet) |
| ClusterOperators Degraded | Cascade from node pressure |

### Automated Repair

```bash
masworld cluster repair --cluster <CLUSTER_ID>
```

The automated repair attempts:
1. Identify pods consuming excessive resources.
2. Clean up completed and evicted pods.
3. Restart pods that are crashlooping and consuming resources.
4. Verify node conditions return to normal.
5. Verify pending pods are scheduled.

### Manual Fallback

```bash
# 1. Clean up evicted and completed pods
oc delete pods -A --field-selector=status.phase=Failed \
  --kubeconfig PLACEHOLDER_KUBECONFIG

# 2. Identify largest resource consumers
oc adm top pods -A --sort-by=cpu --kubeconfig PLACEHOLDER_KUBECONFIG | head -10
oc adm top pods -A --sort-by=memory --kubeconfig PLACEHOLDER_KUBECONFIG | head -10

# 3. If a non-critical pod is consuming excessive resources, restart it
oc delete pod <POD_NAME> -n <NAMESPACE> --kubeconfig PLACEHOLDER_KUBECONFIG

# 4. If a node is NotReady, cordon and investigate
oc adm cordon <NODE_NAME> --kubeconfig PLACEHOLDER_KUBECONFIG
oc describe node <NODE_NAME> --kubeconfig PLACEHOLDER_KUBECONFIG

# 5. If disk pressure, clean up images
oc adm prune images --confirm --kubeconfig PLACEHOLDER_KUBECONFIG

# 6. If the node cannot recover, it may need to be replaced at the
#    infrastructure level (requires cluster provisioning team)

# 7. After node stabilizes, uncordon
oc adm uncordon <NODE_NAME> --kubeconfig PLACEHOLDER_KUBECONFIG
```

### Validation After Repair

```bash
masworld cluster validate --cluster <CLUSTER_ID>
```

Pay special attention to node conditions and pod scheduling.

### Estimated Time to Repair

- Pod cleanup: 2-5 minutes.
- Node recovery from pressure: 5-15 minutes.
- Node replacement: 15-30 minutes (infrastructure-level).
- If multiple nodes are affected: consider replacing the cluster.

### Repair vs Replace Decision

- **During live session**: If a single node is under pressure and workloads
  are affected, attempt cleanup (5 minutes). If the cluster is fundamentally
  under-resourced or multiple nodes are failing, replace immediately.
- **Pre-event**: Investigate root cause thoroughly (up to 30 minutes). Node
  pressure often indicates a sizing issue that will recur. If the cluster
  is consistently under-resourced, flag it for replacement or resizing by the
  provisioning team.

---

## Appendix A: Complete Repair Command Reference

| Command | Description |
|---------|-------------|
| `masworld cluster repair --cluster <ID>` | Run all applicable repairs |
| `masworld cluster repair --cluster <ID> --component mas-core` | Repair MAS Core |
| `masworld cluster repair --cluster <ID> --component maximo-manage` | Repair Maximo Manage |
| `masworld cluster repair --cluster <ID> --component logging` | Repair Logging Operator and collector |
| `masworld cluster repair --cluster <ID> --component lokistack` | Repair LokiStack |
| `masworld cluster repair --cluster <ID> --component s3` | Repair S3 connectivity |
| `masworld cluster repair --cluster <ID> --component identity` | Repair Keycloak/identity |
| `masworld cluster repair --cluster <ID> --component student-auth` | Repair student authentication |
| `masworld cluster repair --cluster <ID> --component showroom` | Repair Showroom |
| `masworld cluster repair --cluster <ID> --component log-forwarding` | Repair ClusterLogForwarder |
| `masworld cluster validate --cluster <ID>` | Run all validation checks |
| `masworld cluster validate --cluster <ID> --checks <CHECK>[,<CHECK>]` | Run specific checks |
| `masworld report fleet-status` | Show fleet-wide health |

### Validation Check Names

```text
openshift
mas_core
maximo_manage
database
logging_operator
lokistack
cluster_log_forwarder
s3_write_read
historical_log_query
identity
showroom
runtime_automation
student_authentication
student_rbac
mas_edge
```

---

## Appendix B: Escalation Contacts

| Issue domain | Primary contact | Escalation |
|-------------|----------------|------------|
| OpenShift cluster infrastructure | Cluster provisioning team | Red Hat Support |
| MAS installation/activation | Francis Anyaegbu | IBM Support |
| Logging and observability | Myles Vivian | Red Hat Support |
| AWS (S3, IAM, EC2) | Francis Anyaegbu | AWS Support |
| ACM hub | Francis Anyaegbu | Red Hat Support |
| Showroom | Francis Anyaegbu | RHDP team |
| Workshop content | Ernie Steagall | Francis Anyaegbu |

---

## Appendix C: Timing Summary

| Failure type | Automated repair | Manual repair | Replace threshold (live) |
|-------------|-----------------|---------------|-------------------------|
| MAS Core | 10-20 min | 15-30 min | 10 min |
| Maximo Manage | 5-20 min | 10-60 min | 10 min |
| Logging Operator | 2-10 min | 5-20 min | 10-15 min |
| LokiStack | 3-10 min | 10-25 min | 10-15 min |
| S3 connectivity | 5-10 min | 10-15 min | 10-15 min |
| Identity/Keycloak | 2-10 min | 5-20 min | 10-15 min |
| Student auth | 2-5 min | 3-10 min | 5 min |
| Showroom | 1-5 min | 2-10 min | 5 min |
| ClusterLogForwarder | 3-5 min | 5-10 min | 10 min |
| API unreachable | N/A | 5-60 min | Immediate |
| Node pressure | 2-15 min | 5-30 min | 5 min |
