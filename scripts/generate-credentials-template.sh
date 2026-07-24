#!/usr/bin/env bash
set -euo pipefail

# Generates a cluster-credentials.yml template from cluster topology parameters.
# Usage: ./scripts/generate-credentials-template.sh [prefix] [facilitator_count] [hub_count] [seat_count] [region]

PREFIX="${1:-lab}"
FACILITATOR_COUNT="${2:-1}"
HUB_COUNT="${3:-1}"
SEAT_COUNT="${4:-5}"
REGION="${5:-us-east-2}"

OUTPUT="secrets/cluster-credentials.yml"

echo "Generating credentials template for:"
echo "  Prefix: $PREFIX"
echo "  Facilitator clusters: $FACILITATOR_COUNT"
echo "  Hub clusters: $HUB_COUNT"
echo "  Seat clusters: $SEAT_COUNT"
echo "  Default region: $REGION"
echo "  Output: $OUTPUT"
echo

cat > "$OUTPUT" << HEADER
---
# Per-cluster AWS credentials.
# subnet_ids is optional if using 'make setup-infra' to create VPCs automatically.
cluster_credentials:
HEADER

for i in $(seq 1 "$FACILITATOR_COUNT"); do
  cat >> "$OUTPUT" << EOF
  ${PREFIX}-facilitator-${i}:
    aws_access_key_id: "REPLACE_ME"
    aws_secret_access_key: "REPLACE_ME"
    aws_region: "${REGION}"
    # subnet_ids: "subnet-REPLACE_ME,subnet-REPLACE_ME"  # Optional: created by 'make setup-infra'

EOF
done

for i in $(seq 1 "$HUB_COUNT"); do
  cat >> "$OUTPUT" << EOF
  ${PREFIX}-hub-${i}:
    aws_access_key_id: "REPLACE_ME"
    aws_secret_access_key: "REPLACE_ME"
    aws_region: "${REGION}"
    # subnet_ids: "subnet-REPLACE_ME,subnet-REPLACE_ME"

EOF
done

for i in $(seq 1 "$SEAT_COUNT"); do
  INDEX=$(printf "%02d" "$i")
  cat >> "$OUTPUT" << EOF
  ${PREFIX}-seat-${INDEX}:
    aws_access_key_id: "REPLACE_ME"
    aws_secret_access_key: "REPLACE_ME"
    aws_region: "${REGION}"
    # subnet_ids: "subnet-REPLACE_ME,subnet-REPLACE_ME"

EOF
done

echo "Generated $OUTPUT with $((FACILITATOR_COUNT + HUB_COUNT + SEAT_COUNT)) cluster entries."
echo "Edit the file to replace REPLACE_ME placeholders with actual AWS credentials."
echo "Run 'make setup-infra' to create VPCs and subnets automatically."
