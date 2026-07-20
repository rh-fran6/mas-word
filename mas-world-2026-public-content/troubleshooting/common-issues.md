# Common Workshop Issues

This document lists frequently encountered issues during the MAS World
workshop with symptoms, diagnosis steps, and resolution.

---

## 1. Operator subscription pending

**Symptoms**: Operator shows `UpgradePending` or no CSV appears.

**Diagnosis**:
```bash
oc get subscription -A
oc get installplan -A
oc get catalogsource -n openshift-marketplace
oc get pods -n openshift-marketplace
```

**Resolution**:
- Check that the CatalogSource pods are running in `openshift-marketplace`.
- Verify network access to the operator registry.
- If an InstallPlan requires approval, approve it:
  ```bash
  oc patch installplan <name> -n <namespace> --type merge \
    -p '{"spec":{"approved":true}}'
  ```
- If the catalog is unhealthy, delete the catalog pod to force a refresh:
  ```bash
  oc delete pod -n openshift-marketplace -l olm.catalogSource=redhat-operators
  ```

---

## 2. LokiStack not ready

**Symptoms**: LokiStack CR shows `Pending` or `Degraded`. Loki pods are
in CrashLoopBackOff or not created.

**Diagnosis**:
```bash
oc get lokistack -n openshift-logging -o yaml
oc get pods -n openshift-logging -l app.kubernetes.io/instance=logging-loki
oc describe lokistack logging-loki -n openshift-logging
```

**Resolution**:
- Verify the S3 storage secret exists and contains valid credentials:
  ```bash
  oc get secret logging-loki-s3 -n openshift-logging
  ```
- Check that the S3 bucket exists and is accessible.
- Verify the StorageClass referenced in the LokiStack exists:
  ```bash
  oc get storageclass
  ```
- Check ingester pod logs for S3 connection errors:
  ```bash
  oc logs -n openshift-logging -l app.kubernetes.io/component=ingester --tail=50
  ```

---

## 3. S3 access denied

**Symptoms**: Loki ingester or compactor logs show `AccessDenied` or
`403 Forbidden` errors for S3 operations.

**Diagnosis**:
```bash
oc logs -n openshift-logging -l app.kubernetes.io/component=ingester --tail=30 | grep -i "access"
oc get secret logging-loki-s3 -n openshift-logging -o jsonpath='{.data}' | base64 -d
```

**Resolution**:
- Verify the IAM user/role has the required S3 permissions (PutObject,
  GetObject, DeleteObject, ListBucket).
- Check that the bucket name in the secret matches the actual bucket.
- Verify the AWS region is correct.
- Check the S3 bucket policy does not explicitly deny access.
- If using STS/IRSA, verify the trust policy and service account
  annotation.

---

## 4. OAuth login fails

**Symptoms**: Login page shows "Invalid credentials" or "Could not
identify identity provider."

**Diagnosis**:
```bash
oc get oauth cluster -o yaml
oc get pods -n openshift-authentication
oc logs -n openshift-authentication -l app=oauth-openshift --tail=30
oc get identity
```

**Resolution**:
- Verify the identity provider configuration in the OAuth CR.
- Check that the OAuth pods have restarted after configuration changes:
  ```bash
  oc get pods -n openshift-authentication -w
  ```
- If using Keycloak OIDC, verify:
  - Keycloak is running and accessible.
  - The client ID and secret match.
  - The redirect URI matches the cluster domain.
  - The issuer URL is reachable from the cluster.
- For htpasswd, verify the secret contains valid htpasswd data:
  ```bash
  oc get secret htpasswd-secret -n openshift-config -o jsonpath='{.data.htpasswd}' | base64 -d
  ```

---

## 5. MAS route not reachable

**Symptoms**: Browser shows "Application is not available" or a TLS error
when accessing the MAS URL.

**Diagnosis**:
```bash
oc get routes -n mas-<instance>-core
oc get pods -n mas-<instance>-core
oc get certificate -n mas-<instance>-core
```

**Resolution**:
- Check that MAS Core pods are running.
- Verify the route's TLS certificate is valid and not expired:
  ```bash
  oc get route -n mas-<instance>-core -o jsonpath='{.spec.host}'
  curl -vI https://<route-host> 2>&1 | grep -i "expire\|subject\|issuer"
  ```
- Check DNS resolution for the route hostname.
- If using custom certificates, verify the certificate chain is complete.
- Check the ingress controller logs:
  ```bash
  oc logs -n openshift-ingress -l ingresscontroller.operator.openshift.io/deployment-ingresscontroller=default --tail=20
  ```

---

## 6. Pod in CrashLoopBackOff

**Symptoms**: Pod repeatedly restarts. Status shows `CrashLoopBackOff`.

**Diagnosis**:
```bash
oc get pods -n <namespace>
oc describe pod <pod-name> -n <namespace>
oc logs <pod-name> -n <namespace> --previous
```

**Resolution**:
- Check the previous container logs for the crash reason.
- Common causes:
  - Missing configuration (ConfigMap or Secret not mounted).
  - Database connection failure.
  - Insufficient memory (OOMKilled -- check `oc describe pod` for
    `Last State: OOMKilled`).
  - Image pull failure (wrong image tag or registry credentials).
- For OOMKilled, increase the memory limit in the pod spec or CR.
- For missing config, verify all referenced ConfigMaps and Secrets exist.

---

## 7. PVC pending

**Symptoms**: PersistentVolumeClaim stays in `Pending` state. Pods that
depend on it cannot start.

**Diagnosis**:
```bash
oc get pvc -n <namespace>
oc describe pvc <pvc-name> -n <namespace>
oc get storageclass
oc get pv
```

**Resolution**:
- Check the PVC events for provisioning errors.
- Verify the requested StorageClass exists and has a provisioner.
- Check that the storage provisioner pods are running:
  ```bash
  oc get pods -n openshift-cluster-csi-drivers
  ```
- For AWS EBS, verify the CSI driver is healthy and the node has IAM
  permissions to create volumes.
- Check if the volume binding mode is `WaitForFirstConsumer` -- the PV
  will not be created until a pod is scheduled.

---

## 8. Certificate expired or not trusted

**Symptoms**: TLS errors in browser, `x509: certificate has expired` in
pod logs, or `unknown authority` errors.

**Diagnosis**:
```bash
# Check ingress certificate
oc get secret -n openshift-ingress
openssl s_client -connect <route-host>:443 -servername <route-host> </dev/null 2>/dev/null | openssl x509 -noout -dates

# Check MAS certificates
oc get certificate -A
```

**Resolution**:
- If the default ingress certificate expired, renew it via the ingress
  controller or cert-manager.
- If a custom CA is not trusted, add it to the cluster's trusted CA
  bundle:
  ```bash
  oc create configmap custom-ca -n openshift-config \
    --from-file=ca-bundle.crt=YOUR_CA_FILE
  oc patch proxy/cluster --type=merge \
    -p '{"spec":{"trustedCA":{"name":"custom-ca"}}}'
  ```
- For MAS certificates, check the Certificate CRs and their issuers.
- Restart affected pods after certificate renewal.

---

## 9. Keycloak realm import stuck

**Symptoms**: KeycloakRealmImport CR shows `Processing` indefinitely or
the realm does not appear in the Keycloak admin console.

**Diagnosis**:
```bash
oc get keycloakrealmimport -n keycloak
oc describe keycloakrealmimport <name> -n keycloak
oc logs -n keycloak -l app=keycloak --tail=50
```

**Resolution**:
- Check Keycloak pod logs for import errors (duplicate clients, invalid
  configuration).
- Verify the Keycloak CR is in Ready state before importing realms.
- If the realm already exists, the import may conflict. Delete and
  recreate, or use the Keycloak admin console to apply changes manually.
- Check that the KeycloakRealmImport references the correct
  `keycloakCRName`.

---

## 10. ClusterLogForwarder not collecting logs

**Symptoms**: No logs appear in Loki. Collector pods are running but
queries return empty results.

**Diagnosis**:
```bash
oc get clusterlogforwarder -n openshift-logging -o yaml
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector
oc logs -n openshift-logging -l app.kubernetes.io/component=collector --tail=30
```

**Resolution**:
- Verify the collector ServiceAccount exists and has the required
  ClusterRoles bound:
  ```bash
  oc get clusterrolebinding | grep collector
  ```
- Check the ClusterLogForwarder status conditions for errors.
- Verify the LokiStack output target name and namespace are correct.
- Ensure the collector pods have been restarted after CLF changes.
- Test with a known log-generating pod (see `logging/sample-log-generator.yaml`).

---

## 11. ACM managed cluster import failed

**Symptoms**: ManagedCluster shows `Unknown` or `Unavailable` condition
on the ACM hub.

**Diagnosis**:
```bash
# On the hub
oc get managedcluster <cluster-name> -o yaml
oc get managedclusteraddons -n <cluster-name>

# On the managed cluster
oc get pods -n open-cluster-management-agent
oc logs -n open-cluster-management-agent -l app=klusterlet --tail=30
```

**Resolution**:
- Verify network connectivity between the hub and managed cluster.
- Check that the klusterlet agent pods are running on the managed cluster.
- Re-import the cluster if the bootstrap secret has expired.
- Check firewall rules allow the managed cluster to reach the hub API.

---

## 12. Insufficient cluster resources

**Symptoms**: Pods stay in `Pending` state. Events show
`Insufficient cpu` or `Insufficient memory`.

**Diagnosis**:
```bash
oc describe node <node-name> | grep -A 5 "Allocated resources"
oc get pods -A --field-selector=status.phase=Pending
oc adm top nodes
```

**Resolution**:
- Identify which workloads are consuming the most resources.
- Scale down non-essential workloads.
- If possible, add worker nodes to the cluster.
- Review resource requests and limits for over-provisioned pods.
- Check if resource quotas are blocking scheduling:
  ```bash
  oc get resourcequota -A
  ```
