"""Tests for deployment scenario infrastructure."""

import os

import yaml


class TestScenarioPreflightRole:
    """Verify scenario_preflight role structure and configuration."""

    ROLE_DIR = os.path.join(os.path.dirname(__file__), "..", "roles", "scenario_preflight")

    def test_main_dispatcher_exists(self):
        assert os.path.isfile(os.path.join(self.ROLE_DIR, "tasks", "main.yml"))

    def test_greenfield_tasks_exist(self):
        assert os.path.isfile(os.path.join(self.ROLE_DIR, "tasks", "greenfield.yml"))

    def test_aws_ready_tasks_exist(self):
        assert os.path.isfile(os.path.join(self.ROLE_DIR, "tasks", "aws-ready.yml"))

    def test_cluster_ready_tasks_exist(self):
        assert os.path.isfile(os.path.join(self.ROLE_DIR, "tasks", "cluster-ready.yml"))

    def test_vars_define_valid_scenarios(self):
        with open(os.path.join(self.ROLE_DIR, "vars", "main.yml")) as f:
            data = yaml.safe_load(f)
        scenarios = data["scenario_valid_scenarios"]
        assert "greenfield" in scenarios
        assert "aws-ready" in scenarios
        assert "cluster-ready" in scenarios
        assert len(scenarios) == 3

    def test_defaults_define_machinepool_params(self):
        with open(os.path.join(self.ROLE_DIR, "defaults", "main.yml")) as f:
            data = yaml.safe_load(f)
        assert data["workshop_machinepool_name"] == "workshop-pool"
        assert data["workshop_machinepool_min_replicas"] == 1
        assert data["workshop_machinepool_max_replicas"] == 3

    def test_shared_phase2_validation_exists(self):
        assert os.path.isfile(os.path.join(self.ROLE_DIR, "tasks", "_validate-phase2-fields.yml"))

    def test_shared_phase2_validation_checks_purpose(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "_validate-phase2-fields.yml")) as f:
            content = f.read()
        assert "facilitator" in content
        assert "hub" in content
        assert "attendee" in content
        assert "spare" in content
        assert "seat_number" in content


class TestScenarioPreflightValidation:
    """Verify scenario-specific validation coverage."""

    ROLE_DIR = os.path.join(os.path.dirname(__file__), "..", "roles", "scenario_preflight")

    def test_greenfield_includes_phase2_validation(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "greenfield.yml")) as f:
            content = f.read()
        assert "_validate-phase2-fields.yml" in content

    def test_aws_ready_includes_phase2_validation(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "aws-ready.yml")) as f:
            content = f.read()
        assert "_validate-phase2-fields.yml" in content

    def test_aws_ready_validates_initial_replicas(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "aws-ready.yml")) as f:
            content = f.read()
        assert "initial_replicas" in content

    def test_cluster_ready_includes_phase2_validation(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "cluster-ready.yml")) as f:
            content = f.read()
        assert "_validate-phase2-fields.yml" in content

    def test_cluster_ready_validates_api_url(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "cluster-ready.yml")) as f:
            content = f.read()
        assert "api_url" in content
        assert "admin_password" in content

    def test_cluster_ready_validates_facilitator_count(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "cluster-ready.yml")) as f:
            content = f.read()
        assert "facilitator.count" in content


class TestWorkshopMachinepoolAction:
    """Verify workshop_machinepool is registered as a valid rosa_cluster action."""

    def test_action_in_valid_actions(self):
        vars_path = os.path.join(
            os.path.dirname(__file__), "..", "roles", "rosa_cluster", "vars", "main.yml"
        )
        with open(vars_path) as f:
            data = yaml.safe_load(f)
        assert "workshop_machinepool" in data["rosa_valid_actions"]

    def test_workshop_machinepool_tasks_exist(self):
        tasks_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "roles",
            "rosa_cluster",
            "tasks",
            "workshop_machinepool.yml",
        )
        assert os.path.isfile(tasks_path)


class TestDeployPlaybook:
    """Verify deploy.yml playbook and scenario includes exist."""

    PLAYBOOK_DIR = os.path.join(os.path.dirname(__file__), "..", "playbooks")

    def test_deploy_playbook_exists(self):
        assert os.path.isfile(os.path.join(self.PLAYBOOK_DIR, "deploy.yml"))

    def test_greenfield_include_exists(self):
        assert os.path.isfile(os.path.join(self.PLAYBOOK_DIR, "_deploy-greenfield.yml"))

    def test_aws_ready_include_exists(self):
        assert os.path.isfile(os.path.join(self.PLAYBOOK_DIR, "_deploy-aws-ready.yml"))

    def test_cluster_ready_include_exists(self):
        assert os.path.isfile(os.path.join(self.PLAYBOOK_DIR, "_deploy-cluster-ready.yml"))

    def test_deploy_playbook_requires_scenario(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "deploy.yml")) as f:
            data = yaml.safe_load(f)
        play = data[0] if isinstance(data, list) else data
        pre_tasks = play.get("pre_tasks", [])
        assert any(
            "deployment_scenario" in str(t.get("ansible.builtin.assert", {}).get("that", ""))
            for t in pre_tasks
        ), "deploy.yml should validate deployment_scenario in pre_tasks"


class TestClusterProfileResolution:
    """Verify purpose-based component gating via _resolve-cluster-profile.yml."""

    PLAYBOOK_DIR = os.path.join(os.path.dirname(__file__), "..", "playbooks")

    def test_resolve_cluster_profile_exists(self):
        assert os.path.isfile(os.path.join(self.PLAYBOOK_DIR, "_resolve-cluster-profile.yml"))

    def test_profile_defines_hub_overrides(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_resolve-cluster-profile.yml")) as f:
            content = f.read()
        assert "masworld_acm_enabled: true" in content
        assert "masworld_mas_core_enabled: false" in content
        assert "masworld_manage_enabled: false" in content
        assert "masworld_logging_enabled: false" in content
        assert "_resolved_purpose == 'hub'" in content

    def test_profile_defines_full_stack(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_resolve-cluster-profile.yml")) as f:
            content = f.read()
        assert "masworld_mas_core_enabled: true" in content
        assert "masworld_manage_enabled: true" in content
        assert "masworld_logging_enabled: true" in content
        assert "_resolved_purpose != 'hub'" in content

    def test_fleet_inner_loop_resolves_profile(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_prepare-single-cluster.yml")) as f:
            content = f.read()
        assert "_resolve-cluster-profile.yml" in content

    def test_fleet_inner_loop_has_when_conditions(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_prepare-single-cluster.yml")) as f:
            content = f.read()
        assert "masworld_mas_prerequisites_enabled" in content
        assert "masworld_mas_core_enabled" in content
        assert "masworld_manage_enabled" in content
        assert "masworld_logging_enabled" in content
        assert "masworld_acm_enabled" in content

    def test_fleet_inner_loop_includes_mas_edge(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_prepare-single-cluster.yml")) as f:
            content = f.read()
        assert "mas_edge" in content
        assert "masworld_mas_edge_enabled" in content

    def test_prepare_cluster_resolves_profile(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "prepare-cluster.yml")) as f:
            content = f.read()
        assert "_resolve-cluster-profile.yml" in content

    def test_validate_inner_loop_resolves_profile(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_validate-single-cluster.yml")) as f:
            content = f.read()
        assert "_resolve-cluster-profile.yml" in content

    def test_decommission_is_purpose_aware(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "decommission-workshop.yml")) as f:
            content = f.read()
        assert "masworld_cluster_purpose != 'hub'" in content
        assert "cluster_purpose | default('attendee')" in content

    def test_repair_is_purpose_aware(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "repair-cluster.yml")) as f:
            content = f.read()
        assert "masworld_cluster_purpose != 'hub'" in content
        assert "cluster_purpose | default('attendee')" in content

    def test_readiness_checks_differ_by_purpose(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_resolve-cluster-profile.yml")) as f:
            data = yaml.safe_load_all(f)
            list(data)
        profile_text = open(os.path.join(self.PLAYBOOK_DIR, "_resolve-cluster-profile.yml")).read()
        assert "masworld_readiness_checks" in profile_text


class TestLabReadiness:
    """Verify lab readiness test infrastructure."""

    SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
    PLAYBOOK_DIR = os.path.join(os.path.dirname(__file__), "..", "playbooks")

    def test_lab_readiness_script_exists(self):
        assert os.path.isfile(os.path.join(self.SCRIPTS_DIR, "lab-readiness-test.sh"))

    def test_lab_readiness_script_executable(self):
        path = os.path.join(self.SCRIPTS_DIR, "lab-readiness-test.sh")
        assert os.access(path, os.X_OK)

    def test_lab_readiness_script_covers_all_exercises(self):
        with open(os.path.join(self.SCRIPTS_DIR, "lab-readiness-test.sh")) as f:
            content = f.read()
        for ex in [
            "Exercise 1",
            "Exercise 2",
            "Exercise 3",
            "Exercise 4",
            "Exercise 5",
            "Exercise 6",
        ]:
            assert ex in content, f"Script should cover {ex}"

    def test_lab_readiness_script_has_debug_commands(self):
        with open(os.path.join(self.SCRIPTS_DIR, "lab-readiness-test.sh")) as f:
            content = f.read()
        assert "Debug:" in content, "Script should include debug commands on failure"

    def test_lab_readiness_script_has_fleet_mode(self):
        with open(os.path.join(self.SCRIPTS_DIR, "lab-readiness-test.sh")) as f:
            content = f.read()
        assert "--fleet" in content

    def test_lab_readiness_script_checks_htpasswd(self):
        with open(os.path.join(self.SCRIPTS_DIR, "lab-readiness-test.sh")) as f:
            content = f.read()
        assert "masworld-htpasswd-secret" in content

    def test_lab_readiness_script_checks_ldap(self):
        with open(os.path.join(self.SCRIPTS_DIR, "lab-readiness-test.sh")) as f:
            content = f.read()
        assert "ldapsearch" in content
        assert "alice.engineer" in content

    def test_lab_readiness_playbook_exists(self):
        assert os.path.isfile(os.path.join(self.PLAYBOOK_DIR, "lab-readiness.yml"))

    def test_lab_readiness_playbook_has_oauth(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "lab-readiness.yml")) as f:
            content = f.read()
        assert "oauth-authorization-server" in content

    def test_lab_readiness_playbook_covers_exercises(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "lab-readiness.yml")) as f:
            content = f.read()
        for component in [
            "Suite",
            "ManageWorkspace",
            "LokiStack",
            "ClusterLogForwarder",
            "Keycloak",
        ]:
            assert component in content, f"Playbook should check {component}"

    def test_htpasswd_secret_name_consistent(self):
        """The runtime readiness script must use the same secret name as student_accounts role."""
        defaults_path = os.path.join(
            os.path.dirname(__file__), "..", "roles", "student_accounts", "defaults", "main.yml"
        )
        runtime_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "showroom",
            "runtime-automation",
            "readiness",
            "validate.yml",
        )
        with open(defaults_path) as f:
            defaults_content = f.read()
        with open(runtime_path) as f:
            runtime_content = f.read()
        assert "masworld-htpasswd-secret" in defaults_content
        assert "masworld-htpasswd-secret" in runtime_content
        assert "name: htpasswd-secret" not in runtime_content


class TestRosaDefaults:
    """Verify workshop machinepool defaults in rosa_defaults."""

    def test_workshop_machinepool_defaults(self):
        defaults_path = os.path.join(
            os.path.dirname(__file__), "..", "group_vars", "all", "rosa_defaults.yml"
        )
        with open(defaults_path) as f:
            data = yaml.safe_load(f)
        assert data["workshop_machinepool_name"] == "workshop-pool"
        assert data["workshop_machinepool_min_replicas"] == 1
        assert data["workshop_machinepool_max_replicas"] == 3
