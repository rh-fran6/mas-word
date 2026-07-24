# AWS Account Prerequisites

Most infrastructure required for ROSA HCP cluster provisioning is now created automatically by `make setup-infra`. This document covers the manual prerequisites that must be in place **before** running any automation.

## What Is Automated

The `make setup-infra` command handles the following for each AWS account, so you no longer need to create them manually:

- **VPC creation** -- a dedicated VPC is provisioned per account
- **Subnet creation** -- 3 private and 3 public subnets spread across availability zones
- **NAT Gateway creation** -- provides outbound internet access from private subnets
- **Internet Gateway creation** -- provides inbound connectivity for public subnets
- **Route table configuration** -- private subnets route through the NAT Gateway; public subnets route through the Internet Gateway
- **ROSA enrollment** -- runs `rosa init` to register the account for ROSA
- **ROSA account roles** -- runs `rosa create account-roles --hosted-cp` to create the IAM roles required by ROSA HCP

Because these steps are automated, you only need to ensure the manual prerequisites below are satisfied.

## Manual Prerequisites

### IAM Permissions

The AWS credentials used for each account must have sufficient permissions for the automation and for ROSA to operate. The required permissions cover:

- VPC, subnet, NAT Gateway, Internet Gateway, and route table management
- IAM role and policy creation (operator roles, OIDC provider, account roles)
- EC2 instance, security group, and load balancer management
- EBS volume management
- Route53 hosted zone management (if using custom domains)

The simplest approach is to attach `AdministratorAccess` to the IAM user. For production environments with least-privilege requirements, refer to the [ROSA required AWS permissions](https://docs.openshift.com/rosa/rosa_planning/rosa-sts-aws-prereqs.html).

### AWS Service Quotas

Verify that each AWS account has sufficient service quotas before running the automation.

#### EC2 Instance Quota

Check the On-Demand Standard instance vCPU limit:

```bash
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A  # Running On-Demand Standard instances
```

For a fleet of 10 seats with `m5.large` (2 vCPUs each, minimum 2 replicas):
- Minimum: 4 vCPUs per account
- With autoscaling max 4 replicas: 8 vCPUs per account

#### VPC Quota

The automation creates one VPC per account. Verify the VPC limit can accommodate it:

```bash
aws service-quotas get-service-quota \
  --service-code vpc \
  --quota-code L-F678F1CE  # VPCs per Region
```

#### Elastic IP Quota

Each NAT Gateway requires one Elastic IP address. Verify the quota:

```bash
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-0263D0A3  # Elastic IPs
```

## Region Configuration

The default region used by the automation is **us-east-2**. To use a different region, set the `AWS_DEFAULT_REGION` environment variable before running `make setup-infra`:

```bash
export AWS_DEFAULT_REGION="eu-west-1"
make setup-infra
```

You can also set the region per account in your credentials file. See the credentials documentation for details on per-account configuration.

## Collecting Information for the Credentials File

For each AWS account, gather:

1. **AWS Access Key ID and Secret** -- create an IAM user or use temporary credentials
2. **Region** (optional) -- defaults to us-east-2 if not specified

Subnet IDs and VPC IDs are no longer required in the credentials file. The automation creates and tracks these resources automatically.
