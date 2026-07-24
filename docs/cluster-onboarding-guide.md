# Cluster Onboarding Guide

Step-by-step instructions for onboarding live clusters into the MAS World
2026 automation framework.

## Prerequisites

- This repository cloned locally
- Python 3.11+ with `pyyaml`, `pydantic`, `click` installed
- `oc` CLI installed and functional
- Access credentials for each cluster (API URL + admin password or kubeconfig)
- AWS access key ID and secret for each cluster's AWS account (for S3/Loki)
- IBM entitlement key from <https://myibm.ibm.com/products-services/containerlibrary>
- IBM MAS license file from <https://www.ibm.com/software/passportadvantage/>
- OpenShift pull secret from <https://console.redhat.com/openshift/install/pull-secret>

## Step 1 — Set up the file secret provider

The file secret provider reads credentials from local YAML files that are
gitignored and never committed.

```bash
# Copy the example templates
cp secrets/masworld-secrets.yml.example secrets/masworld-secrets.yml
cp secrets/masworld-secrets.yml.example secrets/masworld-secrets.yml

# Restrict permissions — these files contain real credentials
chmod 600 secrets/masworld-secrets.yml secrets/cluster-credentials.yml
```

## Step 2 — Save credential files

Download and save these files into the `secrets/` directory:

```bash
# IBM entitlement key — paste the key from:
#   https://myibm.ibm.com/products-services/containerlibrary
echo "YOUR_IBM_ENTITLEMENT_KEY" > secrets/entitlement.dat
chmod 600 secrets/entitlement.dat

# IBM MAS license — save the license.dat file from Passport Advantage
#   https://www.ibm.com/software/passportadvantage/
cp /path/to/downloaded/license.dat secrets/license.dat
chmod 600 secrets/license.dat

# OpenShift pull secret — download JSON from:
#   https://console.redhat.com/openshift/install/pull-secret
cp /path/to/downloaded/pull-secret.json secrets/pullsecret.json
chmod 600 secrets/pullsecret.json
```

## Step 3 — Fill in shared secrets

Edit `secrets/shared.yaml`. The `file://` values reference the files you
saved in Step 2. Add your AWS credentials inline:

```yaml
# These reference the files saved in Step 2
ibm/entitlement-key: "file://entitlement.dat"
ibm/license: "file://license.dat"
registry/pull-secret: "file://pullsecret.json"

# Default AWS credentials (used when per-cluster keys are not set)
AWS_ACCESS_KEY_ID: "AKIA..."
AWS_ACCESS_KEY_SECRET: "wJalr..."
```

## Step 4 — Configure the secret provider

Edit `config/defaults.yaml` to switch from `env` to `file`:

```yaml
secrets:
  provider: file
  config:
    secrets_dir: secrets
```

## Step 5 — Add your first cluster to the inventory

Edit `secrets/cluster-credentials.yml` to add the cluster. All
per-cluster data (AWS credentials, account IDs, purpose, seat_number,
enabled, api_url, admin_password) lives in this single file under the
`cluster_credentials:` key.

Each entry key matches the generated cluster name pattern:
`{cluster_prefix}-{category}-{index}` (e.g., `lab-seat-01`).

```yaml
cluster_credentials:
  lab-seat-01:
    aws_access_key_id: "AKIA..."
    aws_secret_access_key: "wJalr..."
    aws_region: us-east-2
    enabled: true
    purpose: attendee
    seat_number: 1
    api_url: "https://api.lab-seat-01.example.com:6443"
    admin_password: "your-cluster-admin-password"
```

This file is encrypted with Ansible Vault. Event-level defaults
(admin_username, auth_method, student_credential_profile) are defined
in `config/defaults.yaml` and do not need to be repeated per cluster.

## Step 7 — Validate configuration

```bash
cd mas-world-2026-automation
PYTHONPATH=. python3 -m cli.main config validate
```

Expected output:

```
Configuration validation: PASS
  Event: mas-world-2026
  Clusters: 1 defined, 1 enabled
  Secret provider: file
```

If validation fails, check:
- `admin_secret_ref` uses the `secret://` format
- The matching key exists in `secrets/cluster-credentials.yml`
- `secrets_dir` in `config/defaults.yaml` points to the right directory

## Step 8 — Test cluster connectivity

```bash
# Quick connectivity test using oc
oc login https://api.cluster-name.example.com:6443 \
  --username=kubeadmin \
  --password="$(PYTHONPATH=. python3 -c "
from cli.secrets.file_provider import FileSecretProvider
p = FileSecretProvider('secrets')
print(p.get_secret('secret://mas-world/clusters/test-01/admin-password'))
")" \
  --insecure-skip-tls-verify

# Verify cluster access
oc get nodes
oc get clusterversion
```

## Step 9 — Run cluster preflight (when implemented)

```bash
PYTHONPATH=. python3 -m cli.main cluster preflight --cluster test-01
```

## Enabling ACM integration (optional)

ACM integration is disabled by default. To enable it:

1. Add a hub cluster entry to `secrets/cluster-credentials.yml`:

```yaml
cluster_credentials:
  lab-hub-1:
    aws_access_key_id: "AKIA..."
    aws_secret_access_key: "wJalr..."
    aws_region: us-east-2
    enabled: true
    purpose: facilitator
    api_url: "https://api.lab-hub-1.example.com:6443"
    admin_password: "hub-admin-password"
```

3. Enable ACM in your environment config (e.g., `config/defaults.yaml`):

```yaml
components:
  acm_registration:
    enabled: true
    hub_cluster_id: "hub"
```

When ACM is disabled, the ACM registration role and ACM-related lab
activities are skipped automatically.

## Adding more clusters

Repeat Step 5 for each additional cluster. For a 50-seat fleet, add all
entries to `secrets/cluster-credentials.yml`:

1. Add all cluster entries with sequential `seat_number` values (1-50).
2. Add spare clusters with `purpose: spare` (no `seat_number`).
3. Add facilitator cluster(s) with `purpose: facilitator`.
5. Update `config/environments/event.yaml`:

```yaml
fleet:
  attendee_cluster_count: 50
  spare_cluster_count: 5
  facilitator_cluster_count: 1
  require_exact_cluster_counts: true
```

## Cluster naming conventions

| Purpose      | ID pattern         | Seat number |
|-------------|--------------------|-------------|
| Attendee    | `seat-01`..`seat-50` | 1..50       |
| Spare       | `spare-01`..`spare-05` | none      |
| Facilitator | `facilitator-01`   | none        |
| Hub (ACM)   | `hub`              | none        |
| Development | `test-01`          | 1           |

## Verifying the secrets file

Check that all referenced secrets resolve:

```bash
PYTHONPATH=. python3 -c "
from cli.secrets.file_provider import FileSecretProvider
p = FileSecretProvider('secrets')

# Check shared secrets
for ref in [
    'secret://mas-world/ibm/entitlement-key',
    'secret://mas-world/ibm/license',
    'secret://mas-world/registry/pull-secret',
    'secret://mas-world/AWS_ACCESS_KEY_ID',
    'secret://mas-world/AWS_ACCESS_KEY_SECRET',
]:
    status = 'FOUND' if p.exists(ref) else 'MISSING'
    print(f'  {ref}: {status}')

# Check per-cluster secrets (first cluster only)
for ref in [
    'secret://mas-world/clusters/test-01/admin-password',
    'secret://mas-world/clusters/test-01/AWS_ACCESS_KEY_ID',
    'secret://mas-world/clusters/test-01/AWS_ACCESS_KEY_SECRET',
]:
    status = 'FOUND' if p.exists(ref) else 'MISSING'
    print(f'  {ref}: {status}')
"
```

## Security reminders

- Never commit `secrets/*.yaml`, `secrets/*.dat`, or `secrets/*.json` — only `*.example` files are tracked
- Keep file permissions at `600` (`chmod 600 secrets/*`)
- Rotate credentials before the event (`masworld student rotate`)
- Revoke temporary AWS keys after the event
- Do not copy secrets files to shared drives or paste into chat
