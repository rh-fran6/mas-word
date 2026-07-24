class FilterModule:
    def filters(self):
        return {
            "build_cluster_list": self.build_cluster_list,
            "to_cluster_list": self.to_cluster_list,
        }

    @staticmethod
    def build_cluster_list(
        cluster_categories, cluster_prefix, cluster_credentials, infra_state=None
    ):
        """Merge topology definition with per-cluster credentials into a flat list."""
        if infra_state is None:
            infra_state = {}

        clusters = []
        for category in sorted(cluster_categories.keys()):
            config = cluster_categories[category]
            count = config["count"]
            for i in range(1, count + 1):
                index_str = f"{i:02d}" if category == "seat" else str(i)
                name = f"{cluster_prefix}-{category}-{index_str}"

                if name not in cluster_credentials:
                    raise ValueError(
                        f"No credentials found for cluster '{name}' in "
                        f"cluster_credentials. Check secrets/cluster-credentials.yml."
                    )

                creds = cluster_credentials[name]

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

                if creds.get("admin_password"):
                    entry["admin_password"] = creds["admin_password"]
                if creds.get("api_url"):
                    entry["api_url"] = creds["api_url"]
                if creds.get("aws_account_id"):
                    entry["aws_account_id"] = creds["aws_account_id"]

                clusters.append(entry)
        return clusters

    @staticmethod
    def to_cluster_list(cluster_credentials):
        """Transform cluster_credentials dict into a list for Phase 2 fleet playbooks."""
        result = []
        for name, entry in sorted(cluster_credentials.items()):
            if not entry.get("enabled", True):
                continue
            item = dict(entry)
            item["id"] = name
            result.append(item)
        return result
