# Diagnostic Command Reference

An organized reference of `oc` and related commands for troubleshooting
OpenShift clusters running MAS, logging, and identity workloads.

---

## Cluster health

```bash
# Overall cluster status
oc get clusterversion
oc get clusteroperators

# Degraded operators
oc get clusteroperators -o json | \
  jq -r '.items[] | select(.status.conditions[] | select(.type=="Degraded" and .status=="True")) | .metadata.name'

# Node status
oc get nodes
oc adm top nodes

# Node conditions (pressure, readiness)
oc get nodes -o json | \
  jq -r '.items[] | .metadata.name + ": " + ([.status.conditions[] | select(.status=="True") | .type] | join(", "))'

# Pending CSRs
oc get csr | grep Pending

# Cluster events (last hour)
oc get events -A --sort-by=.lastTimestamp | tail -50
```

## Operator status

```bash
# All installed operators
oc get csv -A

# Operator subscriptions
oc get subscription -A

# InstallPlans (pending approval)
oc get installplan -A | grep -v Complete

# CatalogSource health
oc get catalogsource -n openshift-marketplace
oc get pods -n openshift-marketplace

# Specific operator details
oc describe csv <csv-name> -n <namespace>
```

## Pod debugging

```bash
# Pods not in Running state
oc get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded

# Pod details and events
oc describe pod <pod-name> -n <namespace>

# Current container logs
oc logs <pod-name> -n <namespace> --tail=50

# Previous container logs (after crash)
oc logs <pod-name> -n <namespace> --previous --tail=50

# Logs from a specific container in a multi-container pod
oc logs <pod-name> -n <namespace> -c <container-name> --tail=50

# Follow logs in real time
oc logs <pod-name> -n <namespace> -f

# Resource usage for a pod
oc adm top pod <pod-name> -n <namespace>

# Execute a command in a running pod
oc exec <pod-name> -n <namespace> -- <command>

# Open a shell in a running pod
oc rsh <pod-name> -n <namespace>
```

## Storage

```bash
# PersistentVolumeClaims
oc get pvc -A

# Pending PVCs
oc get pvc -A | grep Pending

# PersistentVolumes
oc get pv

# StorageClasses
oc get storageclass

# Default StorageClass
oc get storageclass -o json | \
  jq -r '.items[] | select(.metadata.annotations["storageclass.kubernetes.io/is-default-class"]=="true") | .metadata.name'

# CSI drivers
oc get csidrivers

# PVC details (provisioning events)
oc describe pvc <pvc-name> -n <namespace>
```

## Routes and ingress

```bash
# All routes
oc get routes -A

# Route details (TLS, host)
oc get route <route-name> -n <namespace> -o yaml

# Test route accessibility
curl -sI https://<route-host> | head -5

# Ingress controller status
oc get ingresscontroller -n openshift-ingress-operator
oc get pods -n openshift-ingress

# Ingress controller logs
oc logs -n openshift-ingress -l ingresscontroller.operator.openshift.io/deployment-ingresscontroller=default --tail=20

# Check TLS certificate on a route
openssl s_client -connect <route-host>:443 -servername <route-host> </dev/null 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates
```

## Certificate checks

```bash
# Cluster certificates (cert-manager if installed)
oc get certificate -A
oc get certificaterequest -A
oc get issuer -A
oc get clusterissuer

# Ingress certificate secret
oc get secret -n openshift-ingress -l app=router

# Check certificate expiry on a specific secret
oc get secret <secret-name> -n <namespace> -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -dates

# API server certificate
openssl s_client -connect api.<cluster-domain>:6443 </dev/null 2>/dev/null | \
  openssl x509 -noout -dates
```

## RBAC debugging

```bash
# What can a user do?
oc auth can-i --list --as=<username>

# What can a user do in a specific namespace?
oc auth can-i --list --as=<username> -n <namespace>

# Can a user perform a specific action?
oc auth can-i get pods -n <namespace> --as=<username>

# ClusterRoleBindings for a user
oc get clusterrolebindings -o json | \
  jq -r '.items[] | select(.subjects[]? | .name=="<username>") | .metadata.name'

# RoleBindings in a namespace
oc get rolebindings -n <namespace>

# Describe a ClusterRole
oc describe clusterrole <role-name>

# Groups and their members
oc get groups
oc get group <group-name> -o yaml
```

## Logging stack

```bash
# Logging operator
oc get csv -n openshift-logging | grep -E "logging|loki"
oc get pods -n openshift-logging

# LokiStack status
oc get lokistack -n openshift-logging
oc describe lokistack logging-loki -n openshift-logging

# ClusterLogForwarder status
oc get clusterlogforwarder -n openshift-logging
oc describe clusterlogforwarder collector -n openshift-logging

# Collector (Vector) pod logs
oc logs -n openshift-logging -l app.kubernetes.io/component=collector --tail=30

# Loki component logs
oc logs -n openshift-logging -l app.kubernetes.io/component=ingester --tail=30
oc logs -n openshift-logging -l app.kubernetes.io/component=distributor --tail=30
oc logs -n openshift-logging -l app.kubernetes.io/component=query-frontend --tail=30

# S3 secret verification (keys only, not values)
oc get secret logging-loki-s3 -n openshift-logging -o jsonpath='{.data}' | jq 'keys'
```

## MAS (Maximo Application Suite)

```bash
# MAS namespaces
oc get namespaces | grep mas

# MAS Core status
oc get suite -A
oc describe suite <instance> -n mas-<instance>-core

# Maximo Manage status
oc get manageapp -A
oc get manageworkspace -A

# MAS pods
oc get pods -n mas-<instance>-core
oc get pods -n mas-<instance>-manage

# MAS routes
oc get routes -n mas-<instance>-core

# MAS operator logs
oc logs -n mas-<instance>-core -l app.kubernetes.io/name=ibm-mas-operator --tail=30
```

## ACM (Advanced Cluster Management)

```bash
# On the hub cluster:

# Managed clusters
oc get managedclusters

# Managed cluster sets
oc get managedclusterset

# Cluster labels
oc get managedcluster <name> -o jsonpath='{.metadata.labels}' | jq .

# Policies and compliance
oc get policy -A
oc get placementrule -A
oc get placementbinding -A

# Policy compliance status
oc get policy -A -o json | \
  jq -r '.items[] | .metadata.namespace + "/" + .metadata.name + ": " + (.status.compliant // "Unknown")'

# Klusterlet status (on managed cluster)
oc get pods -n open-cluster-management-agent
oc get pods -n open-cluster-management-agent-addon
```

## Network

```bash
# DNS resolution test (from a pod)
oc exec <pod-name> -n <namespace> -- nslookup <hostname>

# Service endpoints
oc get endpoints -n <namespace>

# NetworkPolicies
oc get networkpolicy -A

# Test connectivity to an external endpoint
oc exec <pod-name> -n <namespace> -- curl -s -o /dev/null -w "%{http_code}" https://<url>
```

## Resource utilization

```bash
# Cluster-wide resource usage
oc adm top nodes

# Namespace resource usage
oc adm top pods -n <namespace>

# Resource quotas
oc get resourcequota -A

# Limit ranges
oc get limitrange -A

# Detailed node resource allocation
oc describe node <node-name> | grep -A 20 "Allocated resources"
```
