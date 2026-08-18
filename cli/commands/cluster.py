"""Single-cluster operations."""

import contextlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import click
import yaml

from cli.config.loader import ConfigLoader
from cli.secrets.provider import create_provider


def _find_project_root() -> Path:
    """Walk up from this file to find the automation project root."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "playbooks").is_dir() and (current / "ansible.cfg").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent


def _run_ansible(
    playbook: str,
    extra_vars: dict[str, str],
    verbose: bool = False,
    dry_run: bool = False,
    capture_output: bool = False,
) -> subprocess.CompletedProcess | int:
    """Run ansible-playbook with extra vars passed via a temp JSON file.

    Secrets never appear on the command line or in ``ps`` output.
    Returns the exit code (int) unless *capture_output* is True,
    in which case the full CompletedProcess is returned.
    """
    project_root = _find_project_root()
    playbook_path = project_root / "playbooks" / playbook

    if dry_run:
        safe = {
            k: (
                "***"
                if any(s in k.lower() for s in ("password", "secret", "key", "token", "license"))
                else v
            )
            for k, v in extra_vars.items()
        }
        click.echo("Dry-run mode — would execute:")
        click.echo(f"  ansible-playbook {playbook_path}")
        click.echo(f"  with vars: {json.dumps(safe, indent=2)}")
        return 0

    fd, vars_path = tempfile.mkstemp(suffix=".json", prefix="masworld-vars-")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(extra_vars, fh)
        os.chmod(vars_path, 0o600)

        cmd = [
            "ansible-playbook",
            str(playbook_path),
            "-c",
            "local",
            "-e",
            f"@{vars_path}",
        ]
        if verbose:
            cmd.append("-v")

        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=capture_output,
            text=True,
        )

        if capture_output:
            return result
        return result.returncode

    except FileNotFoundError:
        click.secho(
            "ansible-playbook not found. Ensure Ansible is installed and on PATH.",
            fg="red",
            err=True,
        )
        return 127
    finally:
        with contextlib.suppress(OSError):
            os.unlink(vars_path)


def _extract_base_domain(api_url: str) -> str:
    """Extract base domain from an OpenShift API URL."""
    parsed = urlparse(api_url)
    hostname = parsed.hostname or ""
    if hostname.startswith("api."):
        return hostname[4:]
    return hostname


def _resolve_secret(provider, ref: str, label: str) -> str | None:
    """Resolve a secret reference, returning None on failure."""
    if not ref or not ref.startswith("secret://"):
        return None
    try:
        return provider.get_secret(ref)
    except (KeyError, Exception) as exc:
        click.secho(f"  Warning: Could not resolve {label}: {exc}", fg="yellow", err=True)
        return None


def _load_cluster_credentials(credentials_key: str) -> dict[str, str]:
    """Load per-cluster credentials from secrets/cluster-credentials.yml."""
    project_root = _find_project_root()
    creds_path = project_root / "secrets" / "cluster-credentials.yml"
    if not creds_path.exists():
        return {}
    try:
        with open(creds_path) as fh:
            data = yaml.safe_load(fh) or {}
    except (OSError, yaml.YAMLError):
        return {}
    all_creds = data.get("cluster_credentials", {})
    return all_creds.get(credentials_key, {})


def _resolve_cluster_vars(
    config, raw_config: dict, cluster_cfg, verbose: bool = False
) -> dict[str, str]:
    """Resolve cluster config and secrets into Ansible extra-vars."""
    provider = create_provider(
        config.secrets.provider.value,
        config.secrets.config if isinstance(config.secrets.config, dict) else {},
    )

    vars_dict: dict[str, str] = {}

    vars_dict["masworld_event_id"] = config.event.id
    vars_dict["masworld_event_date"] = config.event.date
    vars_dict["masworld_event_timezone"] = config.event.timezone
    vars_dict["masworld_cluster_name"] = cluster_cfg.id
    vars_dict["masworld_cluster_id"] = cluster_cfg.id
    vars_dict["masworld_cluster_api_url"] = cluster_cfg.connection.api_url
    vars_dict["masworld_base_domain"] = _extract_base_domain(cluster_cfg.connection.api_url)
    vars_dict["masworld_cluster_purpose"] = cluster_cfg.purpose.value
    vars_dict["cluster_purpose"] = cluster_cfg.purpose.value

    if cluster_cfg.seat_number is not None:
        vars_dict["masworld_seat_number"] = str(cluster_cfg.seat_number)
        vars_dict["masworld_cluster_seat_number"] = str(cluster_cfg.seat_number)

    auth_method = cluster_cfg.connection.admin_auth_method.value
    admin_username = cluster_cfg.connection.admin_username

    cluster_creds = _load_cluster_credentials(cluster_cfg.id)

    if auth_method in ("password", "username-password"):
        password = cluster_creds.get("admin_password", "cluster-admin")
        if not password:
            secret_ref = cluster_cfg.connection.admin_secret_ref
            password = _resolve_secret(provider, secret_ref, "admin password")
        if password:
            vars_dict["masworld_admin_username"] = admin_username
            vars_dict["masworld_admin_password"] = password
    elif auth_method == "token":
        secret_ref = cluster_cfg.connection.admin_secret_ref
        token = _resolve_secret(provider, secret_ref, "API token")
        if token:
            vars_dict["masworld_api_token"] = token
    elif auth_method == "kubeconfig":
        secret_ref = cluster_cfg.connection.admin_secret_ref
        kubeconfig = _resolve_secret(provider, secret_ref, "kubeconfig")
        if kubeconfig:
            vars_dict["masworld_kubeconfig"] = kubeconfig

    if cluster_creds:
        aws_key = cluster_creds.get("aws_access_key_id", "")
        aws_secret = cluster_creds.get("aws_secret_access_key", "")
        if aws_key and aws_secret:
            vars_dict["masworld_loki_s3_access_key_id"] = aws_key
            vars_dict["masworld_loki_s3_access_key_secret"] = aws_secret

    ibm_cfg = raw_config.get("ibm", {})
    registry_cfg = raw_config.get("container_registry", {})

    ibm_ent_ref = ibm_cfg.get("entitlement_key_ref", "")
    ibm_lic_ref = ibm_cfg.get("license_ref", "")
    pull_secret_ref = registry_cfg.get("pull_secret_ref", "")

    ent_key = _resolve_secret(provider, ibm_ent_ref, "IBM entitlement key")
    if ent_key:
        vars_dict["masworld_ibm_entitlement_key"] = ent_key

    license_val = _resolve_secret(provider, ibm_lic_ref, "MAS license")
    if license_val:
        vars_dict["masworld_mas_license_file"] = license_val

    pull_secret = _resolve_secret(provider, pull_secret_ref, "pull secret")
    if pull_secret:
        vars_dict["masworld_pull_secret"] = pull_secret

    vars_dict["masworld_secrets_resolved"] = True

    vars_dict["masworld_mas_core_enabled"] = bool(config.components.mas.install_core)
    vars_dict["masworld_manage_enabled"] = bool(config.components.mas.install_manage)
    vars_dict["masworld_logging_enabled"] = bool(config.components.logging.enabled)
    vars_dict["masworld_loki_enabled"] = bool(config.components.loki.enabled)
    vars_dict["masworld_keycloak_enabled"] = bool(config.components.keycloak.enabled)
    vars_dict["masworld_mas_edge_enabled"] = bool(config.components.mas_edge.enabled)
    vars_dict["masworld_showroom_enabled"] = bool(config.components.showroom.enabled)
    vars_dict["masworld_acm_enabled"] = bool(config.components.acm_registration.enabled)

    preflight_cfg = raw_config.get("preflight", {})
    if preflight_cfg.get("min_workers") is not None:
        vars_dict["masworld_preflight_min_workers"] = str(preflight_cfg["min_workers"])
    if preflight_cfg.get("min_cpu") is not None:
        vars_dict["masworld_preflight_min_cpu"] = str(preflight_cfg["min_cpu"])
    if preflight_cfg.get("min_memory_gi") is not None:
        vars_dict["masworld_preflight_min_memory_gi"] = str(preflight_cfg["min_memory_gi"])

    if verbose:
        safe_keys = {
            k: (
                "***"
                if any(s in k.lower() for s in ("password", "secret", "key", "token", "license"))
                else v
            )
            for k, v in vars_dict.items()
        }
        for k, v in safe_keys.items():
            click.echo(f"  {k} = {v}")

    return vars_dict


@click.group("cluster")
def cluster_group() -> None:
    """Single-cluster preparation, validation, and repair."""


@cluster_group.command("prepare")
@click.argument("cluster_id")
@click.option("--dry-run", is_flag=True, help="Show what would be done.")
@click.pass_context
def prepare_cluster(ctx: click.Context, cluster_id: str, dry_run: bool) -> None:
    """Prepare a single cluster."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        raw_config = loader.load_raw()
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    cluster_cfg = None
    for c in config.clusters:
        if c.id == cluster_id:
            cluster_cfg = c
            break

    if cluster_cfg is None:
        click.secho(f"Cluster '{cluster_id}' not found in inventory.", fg="red", err=True)
        sys.exit(1)

    if not cluster_cfg.enabled:
        click.secho(f"Cluster '{cluster_id}' is disabled. Skipping.", fg="yellow", err=True)
        sys.exit(1)

    click.echo(f"Preparing cluster '{cluster_id}' (purpose: {cluster_cfg.purpose.value})...")

    if verbose:
        click.echo("Resolving cluster configuration and secrets...")

    extra_vars = _resolve_cluster_vars(config, raw_config, cluster_cfg, verbose=verbose)
    extra_vars["config_dir"] = config_dir
    extra_vars["env"] = env

    rc = _run_ansible("prepare-cluster.yml", extra_vars, verbose=verbose, dry_run=dry_run)

    if rc == 0:
        click.secho(f"Cluster '{cluster_id}' preparation completed.", fg="green")
    else:
        click.secho(
            f"Cluster '{cluster_id}' preparation failed (exit code {rc}).",
            fg="red",
            err=True,
        )
        sys.exit(1)


@cluster_group.command("validate")
@click.argument("cluster_id")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
)
@click.pass_context
def validate_cluster(ctx: click.Context, cluster_id: str, fmt: str) -> None:
    """Run readiness checks on a single cluster."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        raw_config = loader.load_raw()
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    cluster_cfg = None
    for c in config.clusters:
        if c.id == cluster_id:
            cluster_cfg = c
            break

    if cluster_cfg is None:
        click.secho(f"Cluster '{cluster_id}' not found in inventory.", fg="red", err=True)
        sys.exit(1)

    click.echo(f"Validating cluster '{cluster_id}'...")

    extra_vars = _resolve_cluster_vars(config, raw_config, cluster_cfg, verbose=verbose)
    extra_vars["config_dir"] = config_dir
    extra_vars["env"] = env

    rv = _run_ansible("validate-cluster.yml", extra_vars, verbose=verbose, capture_output=True)

    if isinstance(rv, int):
        sys.exit(rv)

    result = rv
    project_root = _find_project_root()
    report_path = project_root / "reports" / f"readiness-{cluster_id}.json"

    validation_result = {
        "cluster_id": cluster_id,
        "overall_status": "PASS" if result.returncode == 0 else "FAIL",
        "ansible_exit_code": result.returncode,
    }

    if report_path.exists():
        try:
            with open(report_path) as f:
                validation_result = json.loads(f.read())
        except (json.JSONDecodeError, OSError):
            pass

    if fmt == "json":
        click.echo(json.dumps(validation_result, indent=2, default=str))
    elif fmt == "markdown":
        click.echo(f"## Validation: {cluster_id}")
        click.echo("")
        status = validation_result.get("overall_status", "UNKNOWN")
        click.echo(f"**Overall status:** {status}")
        click.echo("")
        checks = validation_result.get("checks", {})
        if checks:
            click.echo("| Check | Result |")
            click.echo("|-------|--------|")
            for check_name, check_result in checks.items():
                click.echo(f"| {check_name} | {check_result} |")
        click.echo("")
    else:
        status = validation_result.get("overall_status", "UNKNOWN")
        color = "green" if status == "PASS" else "red" if status == "FAIL" else "yellow"
        click.secho(f"Cluster '{cluster_id}': {status}", fg=color)
        checks = validation_result.get("checks", {})
        if checks:
            for check_name, check_result in checks.items():
                chk_color = (
                    "green"
                    if check_result == "PASS"
                    else "red"
                    if check_result == "FAIL"
                    else "cyan"
                    if check_result == "NOT_APPLICABLE"
                    else "yellow"
                )
                click.secho(f"  {check_name}: {check_result}", fg=chk_color)

    if verbose and result.stdout:
        click.echo("\n--- Ansible output ---")
        click.echo(result.stdout)

    if result.returncode != 0:
        if verbose and result.stderr:
            click.echo(result.stderr, err=True)
        sys.exit(1)


@cluster_group.command("repair")
@click.argument("cluster_id")
@click.option("--component", help="Repair only a specific component.")
@click.pass_context
def repair_cluster(ctx: click.Context, cluster_id: str, component: str | None) -> None:
    """Repair a failed cluster."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        raw_config = loader.load_raw()
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    cluster_cfg = None
    for c in config.clusters:
        if c.id == cluster_id:
            cluster_cfg = c
            break

    if cluster_cfg is None:
        click.secho(f"Cluster '{cluster_id}' not found in inventory.", fg="red", err=True)
        sys.exit(1)

    repair_target = component if component else "all"
    click.echo(f"Repairing cluster '{cluster_id}' (component: {repair_target})...")

    extra_vars = _resolve_cluster_vars(config, raw_config, cluster_cfg, verbose=verbose)
    extra_vars["config_dir"] = config_dir
    extra_vars["env"] = env
    extra_vars["repair_components"] = repair_target

    rc = _run_ansible("repair-cluster.yml", extra_vars, verbose=verbose)

    if rc == 0:
        click.secho(f"Cluster '{cluster_id}' repair completed.", fg="green")
    else:
        click.secho(
            f"Cluster '{cluster_id}' repair failed (exit code {rc}).",
            fg="red",
            err=True,
        )
        sys.exit(1)
