import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins", "filter"))
from cluster_helpers import FilterModule


@pytest.fixture
def filter_module():
    return FilterModule()


def _make_creds(name, region="us-east-1", include_subnets=True):
    creds = {
        "aws_access_key_id": f"AKIA_{name}",
        "aws_secret_access_key": f"SECRET_{name}",
        "aws_region": region,
    }
    if include_subnets:
        creds["subnet_ids"] = f"subnet-{name}"
    return creds


class TestBuildClusterList:
    def test_single_facilitator(self, filter_module):
        categories = {
            "facilitator": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": True, "min_replicas": 2, "max_replicas": 4},
            },
        }
        creds = {"lab-facilitator-1": _make_creds("fac1")}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert len(result) == 1
        assert result[0]["name"] == "lab-facilitator-1"
        assert result[0]["category"] == "facilitator"
        assert result[0]["instance_type"] == "m5.xlarge"
        assert result[0]["initial_replicas"] == 2
        assert result[0]["autoscaling"]["enabled"] is True

    def test_full_topology(self, filter_module):
        categories = {
            "facilitator": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": True, "min_replicas": 2, "max_replicas": 4},
            },
            "hub": {
                "count": 1,
                "instance_type": "m5.2xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": True, "min_replicas": 2, "max_replicas": 6},
            },
            "seat": {
                "count": 3,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": True, "min_replicas": 2, "max_replicas": 4},
            },
        }
        creds = {
            "lab-facilitator-1": _make_creds("fac1"),
            "lab-hub-1": _make_creds("hub1"),
            "lab-seat-01": _make_creds("seat01"),
            "lab-seat-02": _make_creds("seat02", "us-west-2"),
            "lab-seat-03": _make_creds("seat03"),
        }
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert len(result) == 5
        names = [c["name"] for c in result]
        assert "lab-facilitator-1" in names
        assert "lab-hub-1" in names
        assert "lab-seat-01" in names
        assert "lab-seat-02" in names
        assert "lab-seat-03" in names

    def test_seat_zero_padding(self, filter_module):
        categories = {
            "seat": {
                "count": 12,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {f"lab-seat-{i:02d}": _make_creds(f"seat{i:02d}") for i in range(1, 13)}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert len(result) == 12
        assert result[0]["name"] == "lab-seat-01"
        assert result[8]["name"] == "lab-seat-09"
        assert result[9]["name"] == "lab-seat-10"
        assert result[11]["name"] == "lab-seat-12"

    def test_hub_not_zero_padded(self, filter_module):
        categories = {
            "hub": {
                "count": 3,
                "instance_type": "m5.2xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {f"lab-hub-{i}": _make_creds(f"hub{i}") for i in range(1, 4)}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert result[0]["name"] == "lab-hub-1"
        assert result[1]["name"] == "lab-hub-2"
        assert result[2]["name"] == "lab-hub-3"

    def test_missing_credentials_raises(self, filter_module):
        categories = {
            "hub": {
                "count": 1,
                "instance_type": "m5.2xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        with pytest.raises(ValueError, match="No credentials found for cluster 'lab-hub-1'"):
            filter_module.build_cluster_list(categories, "lab", {})

    def test_credentials_merged_correctly(self, filter_module):
        categories = {
            "facilitator": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 3,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"demo-facilitator-1": _make_creds("fac1", "eu-west-1")}
        result = filter_module.build_cluster_list(categories, "demo", creds)

        assert result[0]["aws_access_key_id"] == "AKIA_fac1"
        assert result[0]["aws_secret_access_key"] == "SECRET_fac1"
        assert result[0]["aws_region"] == "eu-west-1"
        assert result[0]["subnet_ids"] == "subnet-fac1"

    def test_custom_prefix(self, filter_module):
        categories = {
            "seat": {
                "count": 1,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"workshop-seat-01": _make_creds("s01")}
        result = filter_module.build_cluster_list(categories, "workshop", creds)

        assert result[0]["name"] == "workshop-seat-01"

    def test_default_initial_replicas(self, filter_module):
        categories = {
            "hub": {"count": 1, "instance_type": "m5.xlarge", "autoscaling": {"enabled": False}},
        }
        creds = {"lab-hub-1": _make_creds("hub1")}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert result[0]["initial_replicas"] == 2

    def test_filters_method_returns_dict(self, filter_module):
        filters = filter_module.filters()
        assert "build_cluster_list" in filters
        assert callable(filters["build_cluster_list"])

    def test_subnet_ids_from_infra_state(self, filter_module):
        categories = {
            "hub": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-hub-1": _make_creds("hub1", include_subnets=False)}
        infra_state = {
            "lab-hub-1": {
                "private_subnet_ids": "subnet-priv-a,subnet-priv-b",
                "public_subnet_ids": "subnet-pub-a,subnet-pub-b",
            },
        }
        result = filter_module.build_cluster_list(categories, "lab", creds, infra_state)

        assert result[0]["subnet_ids"] == "subnet-priv-a,subnet-priv-b,subnet-pub-a,subnet-pub-b"

    def test_subnet_ids_private_only_from_infra_state(self, filter_module):
        categories = {
            "hub": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-hub-1": _make_creds("hub1", include_subnets=False)}
        infra_state = {
            "lab-hub-1": {"private_subnet_ids": "subnet-priv-a,subnet-priv-b"},
        }
        result = filter_module.build_cluster_list(categories, "lab", creds, infra_state)

        assert result[0]["subnet_ids"] == "subnet-priv-a,subnet-priv-b"

    def test_credentials_subnet_ids_take_precedence(self, filter_module):
        categories = {
            "hub": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-hub-1": _make_creds("hub1")}
        infra_state = {
            "lab-hub-1": {"private_subnet_ids": "subnet-infra-a,subnet-infra-b"},
        }
        result = filter_module.build_cluster_list(categories, "lab", creds, infra_state)

        assert result[0]["subnet_ids"] == "subnet-hub1"

    def test_missing_subnet_ids_no_error_when_empty(self, filter_module):
        categories = {
            "hub": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-hub-1": _make_creds("hub1", include_subnets=False)}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert result[0]["subnet_ids"] == ""

    def test_backward_compat_three_args(self, filter_module):
        categories = {
            "seat": {
                "count": 1,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-seat-01": _make_creds("s01")}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert result[0]["subnet_ids"] == "subnet-s01"

    def test_empty_infra_state_uses_credentials(self, filter_module):
        categories = {
            "hub": {
                "count": 1,
                "instance_type": "m5.xlarge",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-hub-1": _make_creds("hub1")}
        result = filter_module.build_cluster_list(categories, "lab", creds, {})

        assert result[0]["subnet_ids"] == "subnet-hub1"

    def test_admin_password_passthrough(self, filter_module):
        categories = {
            "seat": {
                "count": 1,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {
            "lab-seat-01": {
                **_make_creds("s01"),
                "admin_password": "test-pw-123",
                "api_url": "https://api.example.com:6443",
            }
        }
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert result[0]["admin_password"] == "test-pw-123"
        assert result[0]["api_url"] == "https://api.example.com:6443"

    def test_admin_password_omitted_when_empty(self, filter_module):
        categories = {
            "seat": {
                "count": 1,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-seat-01": _make_creds("s01")}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert "admin_password" not in result[0]
        assert "api_url" not in result[0]

    def test_aws_account_id_passthrough(self, filter_module):
        categories = {
            "seat": {
                "count": 1,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {
            "lab-seat-01": {
                **_make_creds("s01"),
                "aws_account_id": "123456789012",
            }
        }
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert result[0]["aws_account_id"] == "123456789012"

    def test_aws_account_id_omitted_when_empty(self, filter_module):
        categories = {
            "seat": {
                "count": 1,
                "instance_type": "m5.large",
                "initial_replicas": 2,
                "autoscaling": {"enabled": False},
            },
        }
        creds = {"lab-seat-01": _make_creds("s01")}
        result = filter_module.build_cluster_list(categories, "lab", creds)

        assert "aws_account_id" not in result[0]


class TestToClusterList:
    def test_basic_conversion(self, filter_module):
        creds = {
            "lab-seat-01": {
                "aws_access_key_id": "AKIA_test",
                "purpose": "attendee",
                "seat_number": 1,
                "enabled": True,
            },
            "lab-facilitator-1": {
                "aws_access_key_id": "AKIA_fac",
                "purpose": "facilitator",
                "enabled": True,
            },
        }
        result = filter_module.to_cluster_list(creds)

        assert len(result) == 2
        assert result[0]["id"] == "lab-facilitator-1"
        assert result[1]["id"] == "lab-seat-01"

    def test_disabled_clusters_excluded(self, filter_module):
        creds = {
            "lab-seat-01": {"purpose": "attendee", "enabled": True},
            "lab-seat-02": {"purpose": "attendee", "enabled": False},
        }
        result = filter_module.to_cluster_list(creds)

        assert len(result) == 1
        assert result[0]["id"] == "lab-seat-01"

    def test_enabled_defaults_to_true(self, filter_module):
        creds = {
            "lab-seat-01": {"purpose": "attendee"},
        }
        result = filter_module.to_cluster_list(creds)

        assert len(result) == 1
        assert result[0]["id"] == "lab-seat-01"

    def test_empty_credentials(self, filter_module):
        result = filter_module.to_cluster_list({})
        assert result == []

    def test_filters_registered(self, filter_module):
        filters = filter_module.filters()
        assert "to_cluster_list" in filters
        assert callable(filters["to_cluster_list"])
