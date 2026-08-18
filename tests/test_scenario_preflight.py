"""Tests for deployment scenario infrastructure."""

import os

import pytest
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
        assert "facilitator" in content
        assert "selectattr" in content
        assert "length == 1" in content

    def test_cluster_ready_checks_efs_existence(self):
        """Cluster-ready preflight must check AWS for existing EFS filesystems."""
        with open(os.path.join(self.ROLE_DIR, "tasks", "cluster-ready.yml")) as f:
            content = f.read()
        assert "describe-file-systems" in content
        assert "_preflight_efs_ids" in content
        assert "EFS Filesystem Check" in content

    def test_cluster_ready_efs_check_excludes_hub(self):
        """EFS preflight check should only run for non-hub clusters."""
        with open(os.path.join(self.ROLE_DIR, "tasks", "cluster-ready.yml")) as f:
            content = f.read()
        assert "rejectattr('category', 'equalto', 'hub')" in content


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


class TestParallelClusterReadyPlaybook:
    """Verify deploy-cluster-ready.yml parallel playbook structure."""

    PLAYBOOK_DIR = os.path.join(os.path.dirname(__file__), "..", "playbooks")
    PLAYBOOK_PATH = os.path.join(PLAYBOOK_DIR, "deploy-cluster-ready.yml")

    def test_parallel_playbook_exists(self):
        assert os.path.isfile(self.PLAYBOOK_PATH)

    def test_has_three_plays(self):
        with open(self.PLAYBOOK_PATH) as f:
            data = list(yaml.safe_load_all(f))[0]
        assert len(data) == 3, "deploy-cluster-ready.yml should have exactly 3 plays"

    def test_play2_uses_strategy_free(self):
        with open(self.PLAYBOOK_PATH) as f:
            data = list(yaml.safe_load_all(f))[0]
        assert data[1].get("strategy") == "free"

    def test_play1_registers_cluster_fleet(self):
        with open(self.PLAYBOOK_PATH) as f:
            content = f.read()
        assert "cluster_fleet" in content
        assert "add_host" in content

    def test_play1_sets_python_interpreter(self):
        with open(self.PLAYBOOK_PATH) as f:
            content = f.read()
        assert "ansible_python_interpreter" in content
        assert "ansible_playbook_python" in content

    def test_play2_includes_per_cluster_tasks(self):
        with open(self.PLAYBOOK_PATH) as f:
            content = f.read()
        assert "_wait-machinepool-nodes.yml" in content
        assert "_prepare-single-cluster.yml" in content
        assert "_validate-single-cluster.yml" in content

    def test_kubeconfig_isolation_in_prepare(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_prepare-single-cluster.yml")) as f:
            content = f.read()
        assert "KUBECONFIG" in content
        assert "kubeconfig-{{ cluster.id }}" in content

    def test_acm_registration_excludes_hub(self):
        with open(os.path.join(self.PLAYBOOK_DIR, "_prepare-single-cluster.yml")) as f:
            content = f.read()
        assert "masworld_cluster_purpose" in content
        assert "!= 'hub'" in content

    def test_efs_provisioned_per_cluster_in_parallel(self):
        """EFS provisioned per-cluster via aws_efs in parallel phase."""
        with open(os.path.join(self.PLAYBOOK_DIR, "_prepare-single-cluster.yml")) as f:
            prepare_content = f.read()
        assert "name: aws_efs" in prepare_content
        assert "_cluster_efs_ids" in prepare_content
        with open(self.PLAYBOOK_PATH) as f:
            playbook_content = f.read()
        assert "include_role" not in playbook_content or "name: aws_efs" not in playbook_content

    def test_aws_credentials_passed_to_dynamic_hosts(self):
        """Dynamic hosts need AWS credentials for EFS CSI driver role."""
        with open(self.PLAYBOOK_PATH) as f:
            content = f.read()
        assert "masworld_aws_access_key_id" in content
        assert "masworld_aws_secret_access_key" in content

    def test_no_pause_module_in_pipeline_ibm_roles(self):
        """Vendored IBM roles must not use pause (breaks strategy:free)."""
        collections_base = os.path.join(
            os.path.dirname(__file__),
            "..",
            "collections",
            "ansible_collections",
            "ibm",
            "mas_devops",
            "roles",
        )
        pipeline_roles = [
            "cert_manager",
            "db2",
            "dro",
            "ibm_catalogs",
            "mongodb",
            "sls",
            "suite_app_configure",
            "suite_app_install",
            "suite_config",
            "suite_db2_setup_for_manage",
            "suite_install",
        ]
        for role in pipeline_roles:
            tasks_dir = os.path.join(collections_base, role, "tasks")
            if not os.path.isdir(tasks_dir):
                continue
            for root, _dirs, files in os.walk(tasks_dir):
                for fname in files:
                    if not fname.endswith(".yml") and not fname.endswith(".yaml"):
                        continue
                    if fname.startswith("delete_") or fname.startswith("upgrade_"):
                        continue
                    rel_parts = os.path.relpath(root, tasks_dir).split(os.sep)
                    if any(p in ("delete", "upgrade") for p in rel_parts):
                        continue
                    fpath = os.path.join(root, fname)
                    with open(fpath) as f:
                        content = f.read()
                    data = yaml.safe_load(content)
                    if not isinstance(data, list):
                        continue
                    for task in data:
                        if not isinstance(task, dict):
                            continue
                        for key in ("pause", "ansible.builtin.pause"):
                            if key in task:
                                params = task[key]
                                if not isinstance(params, dict) or not (
                                    params.get("minutes") or params.get("seconds")
                                ):
                                    raise AssertionError(
                                        f"pause found in {fpath} — "
                                        "use wait_for for strategy:free"
                                    )


class TestAcmHubConfiguration:
    """Verify ACM hub role defaults and subscription configuration."""

    ROLE_DIR = os.path.join(os.path.dirname(__file__), "..", "roles", "acm_hub")

    def test_acm_operator_source_is_redhat_operators(self):
        with open(os.path.join(self.ROLE_DIR, "defaults", "main.yml")) as f:
            data = yaml.safe_load(f)
        assert data["masworld_acm_operator_source"] == "redhat-operators"

    def test_acm_channel_matches_components(self):
        with open(os.path.join(self.ROLE_DIR, "defaults", "main.yml")) as f:
            defaults = yaml.safe_load(f)
        with open(os.path.join(os.path.dirname(__file__), "..", "config", "components.yaml")) as f:
            components = yaml.safe_load(f)
        expected_channel = f"release-{components['components']['acm']['version']}"
        assert defaults["masworld_acm_operator_channel"] == expected_channel

    def test_acm_task_resolves_channel_from_components(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "masworld_components.components.acm.version" in content

    def test_acm_task_has_subscription_diagnostics(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "Diagnose ACM Subscription state" in content
        assert "InstallPlan" in content

    def test_acm_waits_for_csv_not_deployment_label(self):
        """Operator readiness must check CSV phase, not a guessed deployment label."""
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "ClusterServiceVersion" in content
        assert "status.phase" in content
        assert "'Succeeded'" in content
        assert "app=multiclusterhub-operator" not in content


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
        assert "masworld_logging_enabled: false" in content
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


class TestDb2SecurityAndDiagnostics:
    """Verify Db2 SCC creation and failure diagnostics in maximo_manage role."""

    ROLE_DIR = os.path.join(os.path.dirname(__file__), "..", "roles", "maximo_manage")
    COLLECTIONS_DB2 = os.path.join(
        os.path.dirname(__file__),
        "..",
        "collections",
        "ansible_collections",
        "ibm",
        "mas_devops",
        "roles",
        "db2",
    )

    def test_scc_template_exists(self):
        assert os.path.isfile(os.path.join(self.ROLE_DIR, "templates", "db2u-scc.yml.j2"))

    def test_scc_template_has_required_capabilities(self):
        with open(os.path.join(self.ROLE_DIR, "templates", "db2u-scc.yml.j2")) as f:
            content = f.read()
        for cap in ["SYS_RESOURCE", "IPC_OWNER", "SYS_NICE"]:
            assert cap in content, f"SCC must include {cap} capability"
        assert "allowPrivilegedContainer: true" in content

    def test_scc_created_before_db2_install(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        scc_pos = content.find("db2u-scc")
        db2_pos = content.find("ibm.mas_devops.db2")
        assert scc_pos < db2_pos, "SCC must be created before db2 role runs"

    def test_namespace_labeled_for_privileged_pods(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "pod-security.kubernetes.io/enforce: privileged" in content

    def test_rescue_captures_db2_status(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "Db2uCluster" in content
        assert "_db2_rescue_status" in content
        assert "_db2_rescue_pods" in content
        assert "_db2_rescue_pvcs" in content

    def test_rescue_shows_common_causes(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "COMMON CAUSES ON ROSA HCP" in content
        assert "oc get scc db2u-scc" in content

    @pytest.mark.skipif(
        not os.path.isdir(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "collections",
                "ansible_collections",
                "ibm",
                "mas_devops",
                "roles",
                "db2",
            )
        ),
        reason="IBM collection not installed",
    )
    def test_db2_role_exists_in_collection(self):
        """IBM collection db2 role must exist after install."""
        assert os.path.isfile(os.path.join(self.COLLECTIONS_DB2, "tasks", "main.yml"))

    @pytest.mark.skipif(
        not os.path.isdir(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "collections",
                "ansible_collections",
                "ibm",
                "mas_devops",
                "roles",
                "suite_db2_setup_for_manage",
            )
        ),
        reason="IBM collection not installed",
    )
    def test_k8s_lookup_replaced_with_module(self):
        """k8s lookup plugin must be replaced with k8s_info module after patching."""
        dbconfig_files = [
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "collections",
                "ansible_collections",
                "ibm",
                "mas_devops",
                "roles",
                "suite_db2_setup_for_manage",
                "tasks",
                "db2_dbconfig.yml",
            ),
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "collections",
                "ansible_collections",
                "ibm",
                "mas_devops",
                "roles",
                "suite_db2_setup_for_facilities",
                "tasks",
                "apply-db2-dbconfig.yml",
            ),
        ]
        for path in dbconfig_files:
            if not os.path.isfile(path):
                continue
            with open(path) as f:
                content = f.read()
            assert "query('k8s'" not in content, f"k8s lookup still present in {path}"
            assert "kubernetes.core.k8s_info" in content, f"k8s_info module missing in {path}"

    def test_scc_grants_service_accounts(self):
        with open(os.path.join(self.ROLE_DIR, "templates", "db2u-scc.yml.j2")) as f:
            content = f.read()
        assert "db2u-operator" in content
        assert "db2u" in content
        assert "default" in content

    def test_stale_db2_cleanup_before_install(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        cleanup_pos = content.find("Clean up stale Db2 deployment")
        db2_pos = content.find("ibm.mas_devops.db2")
        assert cleanup_pos > 0, "Stale Db2 cleanup task must exist"
        assert cleanup_pos < db2_pos, "Stale cleanup must run before db2 role"

    def test_stale_db2_checks_both_cr_types(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "Db2uCluster" in content
        assert "Db2uInstance" in content

    def test_stale_db2_cleanup_deletes_pvcs(self):
        with open(os.path.join(self.ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "c-db2u-manage-meta" in content
        assert "c-db2u-manage-backup" in content


class TestEfsStorageClassUidGid:
    """Verify EFS StorageClass includes UID/GID for Db2 compatibility."""

    EFS_ROLE_DIR = os.path.join(os.path.dirname(__file__), "..", "roles", "efs_csi_driver")

    def test_defaults_include_uid_gid(self):
        with open(os.path.join(self.EFS_ROLE_DIR, "defaults", "main.yml")) as f:
            data = yaml.safe_load(f)
        assert data["masworld_efs_uid"] == "0"
        assert data["masworld_efs_gid"] == "0"

    def test_storageclass_includes_uid_gid_parameters(self):
        with open(os.path.join(self.EFS_ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "uid:" in content
        assert "gid:" in content
        assert "masworld_efs_uid" in content
        assert "masworld_efs_gid" in content

    def test_storageclass_replace_on_uid_mismatch(self):
        with open(os.path.join(self.EFS_ROLE_DIR, "tasks", "main.yml")) as f:
            content = f.read()
        assert "Replace efs StorageClass if parameters are stale" in content
        assert "state: absent" in content


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
