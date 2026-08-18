class FilterModule:
    def filters(self):
        return {
            "build_cluster_list": self.build_cluster_list,
            "to_cluster_list": self.to_cluster_list,
            "seat_range": self.seat_range,
        }

    @staticmethod
    def _parse_category(name, prefix, known_categories):
        """Extract category from a credential key like 'lab-seat-01' -> 'seat'."""
        if not name.startswith(prefix + "-"):
            raise ValueError(
                f"Cluster '{name}' does not start with prefix '{prefix}-'. "
                f"Check cluster_prefix and secrets/cluster-credentials.yml."
            )
        suffix = name[len(prefix) + 1 :]
        for cat in sorted(known_categories, key=len, reverse=True):
            if suffix.startswith(cat + "-"):
                return cat
        raise ValueError(
            f"Cluster '{name}' does not match any category in cluster_categories "
            f"({', '.join(sorted(known_categories))}). "
            f"Expected key pattern: {prefix}-<category>-<index>"
        )

    @staticmethod
    def build_cluster_list(
        cluster_categories, cluster_prefix, cluster_credentials, infra_state=None
    ):
        """Merge per-category defaults with per-cluster credentials into a flat list.

        Clusters are enumerated from cluster_credentials keys (the source of truth),
        not from topology counts. Each key is matched to a category in
        cluster_categories to apply sizing defaults.
        """
        if infra_state is None:
            infra_state = {}

        clusters = []
        for name in sorted(cluster_credentials.keys()):
            creds = cluster_credentials[name]

            if not creds.get("enabled", True):
                continue

            category = FilterModule._parse_category(name, cluster_prefix, cluster_categories.keys())
            config = cluster_categories[category]

            subnet_ids = creds.get("subnet_ids", "")
            if not subnet_ids and name in infra_state:
                private = infra_state[name].get("private_subnet_ids", "")
                public = infra_state[name].get("public_subnet_ids", "")
                parts = [s for s in [private, public] if s]
                subnet_ids = ",".join(parts)

            entry = {
                "name": name,
                "category": category,
                "instance_type": config["instance_type"],
                "initial_replicas": config.get("initial_replicas", 2),
                "autoscaling": config.get("autoscaling", {"enabled": False}),
                "aws_access_key_id": creds["aws_access_key_id"],
                "aws_secret_access_key": creds["aws_secret_access_key"],
                "aws_region": creds["aws_region"],
                "subnet_ids": subnet_ids,
            }

            for field in (
                "admin_password",
                "api_url",
                "aws_account_id",
                "bastion_host",
                "bastion_username",
                "bastion_password",
                "purpose",
                "seat_number",
            ):
                if creds.get(field):
                    entry[field] = creds[field]

            clusters.append(entry)
        return clusters

    @staticmethod
    def seat_range(clusters, seat_start=None, seat_end=None):
        """Filter a cluster list to attendee/seat clusters within a seat number range.

        When both seat_start and seat_end are None, returns the full list unchanged.
        When a range is specified, only includes clusters whose purpose is
        'attendee' or category is 'seat' with seat_number in [seat_start, seat_end].
        """
        if seat_start is None and seat_end is None:
            return clusters

        result = []
        for cluster in clusters:
            purpose = cluster.get("purpose", cluster.get("category", ""))
            if purpose not in ("attendee", "seat"):
                continue
            seat = cluster.get("seat_number")
            if seat is None or str(seat).strip() == "":
                continue
            seat = int(seat)
            if seat_start is not None and seat < int(seat_start):
                continue
            if seat_end is not None and seat > int(seat_end):
                continue
            result.append(cluster)
        return result

    @staticmethod
    def to_cluster_list(cluster_credentials):
        """Transform cluster_credentials dict into a list for Phase 2 fleet playbooks."""
        result = []
        for name, entry in sorted(cluster_credentials.items()):
            if not entry.get("enabled", True):
                continue
            item = dict(entry)
            item["id"] = name
            if not item.get("admin_password"):
                item["admin_password"] = "cluster-admin"  # pragma: allowlist secret
            result.append(item)
        return result
