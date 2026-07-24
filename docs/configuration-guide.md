# Configuration Guide

## Step 1: Set Up the ROSA Token

1. Visit [console.redhat.com/openshift/token/rosa](https://console.redhat.com/openshift/token/rosa)
2. Copy your offline access token
3. Create the token file:

```bash
cp secrets/rosa-token.yml.example secrets/rosa-token.yml
```

4. Paste your token into `secrets/rosa-token.yml`:

```yaml
rosa_token: "eyJhbGciOiJSUzI1NiIs..."
```

## Step 2: Define Your Cluster Topology

Edit `group_vars/all/cluster_topology.yml`:

```yaml
cluster_prefix: "lab"    # All clusters will be named lab-{category}-{index}

cluster_categories:
  facilitator:
    count: 1              # Always 1
    instance_type: "m5.xlarge"
    initial_replicas: 2
    autoscaling:
      enabled: true
      min_replicas: 2
      max_replicas: 4
      machinepool_name: "autoscale-workers"

  hub:
    count: 1
    instance_type: "m5.2xlarge"
    initial_replicas: 2
    autoscaling:
      enabled: true
      min_replicas: 2
      max_replicas: 6
      machinepool_name: "autoscale-workers"

  seat:
    count: 10             # Number of participant clusters
    instance_type: "m5.large"
    initial_replicas: 2
    autoscaling:
      enabled: true
      min_replicas: 2
      max_replicas: 4
      machinepool_name: "autoscale-workers"
```

## Step 3: Configure Per-Cluster AWS Credentials

Each cluster needs its own AWS account credentials. The credential key must match the generated cluster name.

Naming rules:
- Facilitator: `{prefix}-facilitator-1`
- Hub: `{prefix}-hub-1`, `{prefix}-hub-2`, etc.
- Seats: `{prefix}-seat-01`, `{prefix}-seat-02`, etc. (zero-padded)

```bash
cp secrets/cluster-credentials.yml.example secrets/cluster-credentials.yml
```

Edit `secrets/cluster-credentials.yml`:

```yaml
cluster_credentials:
  lab-facilitator-1:
    aws_access_key_id: "AKIA..."
    aws_secret_access_key: "..."
    # aws_region: "us-east-2"      # Optional - defaults to us-east-2
    # subnet_ids: "subnet-abc,..."  # Optional when using 'make setup-infra'

  lab-hub-1:
    aws_access_key_id: "AKIA..."
    aws_secret_access_key: "..."

  lab-seat-01:
    aws_access_key_id: "AKIA..."
    aws_secret_access_key: "..."
    # ... one entry per seat
```

> **Note:** When using `make setup-infra` (Step 4), you only need to provide `aws_access_key_id` and `aws_secret_access_key` for each account. The `subnet_ids` field is optional and will be auto-discovered from the infrastructure state file (`group_vars/all/infra_state.yml`) during cluster provisioning. You may still set `subnet_ids` manually to override auto-discovery.

### Region Configuration

The default region for all accounts is **us-east-2** (Ohio).

- **Global override:** Set `aws_default_region` in `group_vars/all/aws_infra_defaults.yml` to change the default for all accounts.
- **Per-account override:** Set `aws_region` in a specific account's entry in `secrets/cluster-credentials.yml` to override the region for that account only.

Per-account settings take precedence over the global default.

### Finding Subnet IDs (Manual Setup Only)

If you are **not** using `make setup-infra` and need to provide subnet IDs manually:

```bash
# In each AWS account:
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-XXXX" \
  --query 'Subnets[].SubnetId' --output text
```

Use private subnets with NAT gateway access for HCP clusters.

## Step 4: Set Up AWS Infrastructure

Run `make setup-infra` to automatically create all required AWS networking infrastructure across every account defined in `secrets/cluster-credentials.yml`:

```bash
make setup-infra
```

This command performs the following for each AWS account:

- Creates a VPC with public and private subnets
- Provisions NAT gateways and Internet gateways (IGWs)
- Runs `rosa init` to initialize the ROSA environment
- Runs `rosa create account-roles --hosted-cp` to create the required IAM account roles for Hosted Control Plane clusters

Infrastructure state (including subnet IDs) is saved to `group_vars/all/infra_state.yml`. During cluster provisioning, `subnet_ids` are automatically resolved from this state file, so you do not need to look them up or enter them manually.

> **This is a one-time setup per workshop.** You only need to run `make setup-infra` once. Subsequent `make provision` runs will read from the saved infrastructure state.

## Step 5: Adjust ROSA Defaults (Optional)

Edit `group_vars/all/rosa_defaults.yml` to change:
- `rosa_version`: OpenShift version (e.g., `"4.17"`)
- `rosa_channel_group`: `stable`, `candidate`, or `fast`
- Timeout and retry settings for async operations

## Step 6: Encrypt Secrets (Recommended)

```bash
make encrypt-secrets
# You'll be prompted to set a vault password

# Run playbooks with:
make provision VAULT_ARGS="--ask-vault-pass"
```

## Adding or Removing Clusters

To change the number of seat clusters:

1. Update `seat.count` in `group_vars/all/cluster_topology.yml`
2. Add or remove corresponding entries in `secrets/cluster-credentials.yml`
3. Run `make validate` to verify
4. Run `make provision` (ROSA handles existing clusters gracefully)
