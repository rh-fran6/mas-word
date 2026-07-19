"""Single-cluster operations."""

import json
import subprocess
import sys
from pathlib import Path

import click

from cli.config.loader import ConfigLoader


def _find_project_root() -> Path:
    """Walk up from this file to find the automation project root."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "playbooks").is_dir() and (current / "ansible.cfg").exists():
            return current
        current = current.parent
    # Fallback: assume two levels up from commands/
    return Path(__file__).resolve().parent.parent.parent


def _build_ansible_cmd(
    playbook: str,
    extra_vars: dict[str, str],
    verbose: bool = False,
) -> list[str]:
    """Build an ansible-playbook command with extra vars."""
    project_root = _find_project_root()
    playbook_path = project_root / "playbooks" / playbook

    cmd = ["ansible-playbook", str(playbook_path)]
    for key, value in extra_vars.items():
        cmd.extend(["-e", f"{key}={value}"])
    if verbose:
        cmd.append("-v")
    return cmd


def _run_ansible(
    playbook: str,
    extra_vars: dict[str, str],
    verbose: bool = False,
    dry_run: bool = False,
) -> int:
    """Run an ansible-playbook command. Returns the exit code."""
    cmd = _build_ansible_cmd(playbook, extra_vars, verbose)

    if dry_run:
        click.echo("Dry-run mode — would execute:")
        click.echo(f"  {' '.join(cmd)}")
        return 0

    if verbose:
        click.echo(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(_find_project_root()),
            capture_output=False,
            text=True,
        )
        return result.returncode
    except FileNotFoundError:
        click.secho(
            "ansible-playbook not found. Ensure Ansible is installed and on PATH.",
            fg="red",
            err=True,
        )
        return 127


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

    # Validate the cluster exists in config
    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
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

    extra_vars = {
        "cluster_id": cluster_id,
        "cluster_purpose": cluster_cfg.purpose.value,
        "config_dir": config_dir,
        "env": env,
    }
    if cluster_cfg.seat_number is not None:
        extra_vars["seat_number"] = str(cluster_cfg.seat_number)

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
    "--format", "fmt",
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

    extra_vars = {
        "cluster_id": cluster_id,
        "config_dir": config_dir,
        "env": env,
    }

    # Run the validation playbook and capture output
    cmd = _build_ansible_cmd("validate-cluster.yml", extra_vars, verbose)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(_find_project_root()),
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        click.secho(
            "ansible-playbook not found. Ensure Ansible is installed and on PATH.",
            fg="red",
            err=True,
        )
        sys.exit(1)

    # Check for a generated readiness report JSON
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
        # Text output
        status = validation_result.get("overall_status", "UNKNOWN")
        color = "green" if status == "PASS" else "red" if status == "FAIL" else "yellow"
        click.secho(f"Cluster '{cluster_id}': {status}", fg=color)
        checks = validation_result.get("checks", {})
        if checks:
            for check_name, check_result in checks.items():
                chk_color = (
                    "green" if check_result == "PASS"
                    else "red" if check_result == "FAIL"
                    else "cyan" if check_result == "NOT_APPLICABLE"
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

    extra_vars = {
        "cluster_id": cluster_id,
        "repair_components": repair_target,
        "config_dir": config_dir,
        "env": env,
    }

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
