"""Exercise management commands."""

import subprocess
import sys
from pathlib import Path

import click

from cli.config.loader import ConfigLoader


# Map module names to their runtime-automation directory names
MODULE_DIR_MAP = {
    "navigation": "navigation",
    "acm": "acm",
    "updates": "updates",
    "observability": "observability",
    "identity": "identity",
}


def _find_project_root() -> Path:
    """Walk up from this file to find the automation project root."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "playbooks").is_dir() and (current / "ansible.cfg").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent


@click.group("exercise")
def exercises_group() -> None:
    """Exercise reset and management."""


@exercises_group.command("reset")
@click.argument("cluster_id")
@click.option(
    "--module",
    required=True,
    type=click.Choice(["navigation", "acm", "updates", "observability", "identity"]),
    help="Module to reset.",
)
@click.pass_context
def reset_exercise(ctx: click.Context, cluster_id: str, module: str) -> None:
    """Reset an exercise to its initial state on a cluster."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    # Validate the cluster exists
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
        click.secho(f"Cluster '{cluster_id}' is disabled.", fg="yellow", err=True)
        sys.exit(1)

    # Locate the reset playbook
    project_root = _find_project_root()
    module_dir = MODULE_DIR_MAP.get(module, module)

    # Check the showroom runtime-automation directory first
    reset_playbook = project_root / "showroom" / "runtime-automation" / module_dir / "reset.yml"

    if not reset_playbook.exists():
        # Fall back to the main playbooks/reset-exercises.yml with module variable
        reset_playbook = project_root / "playbooks" / "reset-exercises.yml"
        if not reset_playbook.exists():
            click.secho(
                f"No reset playbook found for module '{module}'.\n"
                f"  Checked: showroom/runtime-automation/{module_dir}/reset.yml\n"
                f"  Checked: playbooks/reset-exercises.yml",
                fg="red",
                err=True,
            )
            sys.exit(1)
        use_module_var = True
    else:
        use_module_var = False

    click.echo(f"Resetting '{module}' exercise on cluster '{cluster_id}'...")

    cmd = ["ansible-playbook", str(reset_playbook)]
    cmd.extend(["-e", f"cluster_id={cluster_id}"])
    cmd.extend(["-e", f"config_dir={config_dir}"])
    cmd.extend(["-e", f"env={env}"])

    if use_module_var:
        cmd.extend(["-e", f"module={module}"])

    if cluster_cfg.seat_number is not None:
        cmd.extend(["-e", f"seat_number={cluster_cfg.seat_number}"])

    if verbose:
        cmd.append("-v")
        click.echo(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=False,
            text=True,
        )
    except FileNotFoundError:
        click.secho(
            "ansible-playbook not found. Ensure Ansible is installed and on PATH.",
            fg="red",
            err=True,
        )
        sys.exit(1)

    if result.returncode == 0:
        click.secho(
            f"Exercise '{module}' reset on cluster '{cluster_id}'.",
            fg="green",
        )
    else:
        click.secho(
            f"Exercise reset failed for '{module}' on '{cluster_id}' "
            f"(exit code {result.returncode}).",
            fg="red",
            err=True,
        )
        sys.exit(1)
