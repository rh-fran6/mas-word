"""Fleet-level orchestration commands."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from cli.config.loader import ConfigLoader
from cli.config.schema import ClusterConfig


def _find_project_root() -> Path:
    """Walk up from this file to find the automation project root."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "playbooks").is_dir() and (current / "ansible.cfg").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent


def _prepare_single_cluster(
    cluster: ClusterConfig,
    config_dir: str,
    env: str,
    verbose: bool,
    project_root: Path,
) -> dict[str, Any]:
    """Prepare one cluster via ansible-playbook. Returns a result dict."""
    playbook_path = project_root / "playbooks" / "prepare-cluster.yml"

    extra_vars = {
        "cluster_id": cluster.id,
        "cluster_purpose": cluster.purpose.value,
        "config_dir": config_dir,
        "env": env,
    }
    if cluster.seat_number is not None:
        extra_vars["seat_number"] = str(cluster.seat_number)

    cmd = ["ansible-playbook", str(playbook_path)]
    for key, value in extra_vars.items():
        cmd.extend(["-e", f"{key}={value}"])
    if verbose:
        cmd.append("-v")

    start_time = datetime.now(timezone.utc)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=14400,  # 4-hour hard timeout
        )
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        return {
            "cluster_id": cluster.id,
            "purpose": cluster.purpose.value,
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode,
            "duration_seconds": round(duration, 1),
            "error": result.stderr.strip()[-500:] if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        return {
            "cluster_id": cluster.id,
            "purpose": cluster.purpose.value,
            "status": "TIMEOUT",
            "exit_code": -1,
            "duration_seconds": round(duration, 1),
            "error": "Cluster preparation timed out",
        }
    except FileNotFoundError:
        return {
            "cluster_id": cluster.id,
            "purpose": cluster.purpose.value,
            "status": "FAILED",
            "exit_code": 127,
            "duration_seconds": 0,
            "error": "ansible-playbook not found on PATH",
        }


@click.group("fleet")
def fleet_group() -> None:
    """Fleet preparation and validation."""


@fleet_group.command("prepare")
@click.option("--max-concurrent", type=int, help="Maximum parallel cluster operations.")
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing.")
@click.pass_context
def prepare_fleet(ctx: click.Context, max_concurrent: int | None, dry_run: bool) -> None:
    """Prepare all clusters in the fleet."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    enabled_clusters = [c for c in config.clusters if c.enabled]

    if not enabled_clusters:
        click.secho("No enabled clusters found in inventory.", fg="yellow", err=True)
        sys.exit(1)

    concurrency = max_concurrent or config.fleet.preparation.max_concurrent_clusters

    click.echo(f"Fleet preparation — {env} environment")
    click.echo(f"  Clusters:    {len(enabled_clusters)}")
    click.echo(f"  Concurrency: {concurrency}")
    click.echo(f"  Clusters:    {', '.join(c.id for c in enabled_clusters)}")

    if dry_run:
        click.echo("\nDry-run mode — no changes will be made.")
        click.echo("\nWould prepare the following clusters:")
        for c in enabled_clusters:
            click.echo(
                f"  {c.id} (purpose: {c.purpose.value}, "
                f"seat: {c.seat_number if c.seat_number is not None else 'N/A'})"
            )
        sys.exit(0)

    click.echo(f"\nStarting fleet preparation...")
    project_root = _find_project_root()

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                _prepare_single_cluster,
                cluster,
                config_dir,
                env,
                verbose,
                project_root,
            ): cluster
            for cluster in enabled_clusters
        }

        for future in as_completed(futures):
            cluster = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "cluster_id": cluster.id,
                    "purpose": cluster.purpose.value,
                    "status": "FAILED",
                    "exit_code": -1,
                    "duration_seconds": 0,
                    "error": str(exc),
                }
            results.append(result)

            # Print progress
            status = result["status"]
            color = "green" if status == "SUCCESS" else "red"
            click.secho(
                f"  [{len(results)}/{len(enabled_clusters)}] "
                f"{result['cluster_id']}: {status} "
                f"({result['duration_seconds']}s)",
                fg=color,
            )

    # Summary
    succeeded = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] != "SUCCESS")

    click.echo(f"\nFleet preparation complete.")
    click.secho(f"  Succeeded: {succeeded}", fg="green")
    if failed > 0:
        click.secho(f"  Failed:    {failed}", fg="red")
        click.echo("\nFailed clusters:")
        for r in results:
            if r["status"] != "SUCCESS":
                click.secho(f"  {r['cluster_id']}: {r['status']}", fg="red")
                if r.get("error"):
                    click.echo(f"    {r['error'][:200]}")
        sys.exit(1)


@fleet_group.command("validate")
@click.option(
    "--format", "fmt",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
)
@click.pass_context
def validate_fleet(ctx: click.Context, fmt: str) -> None:
    """Run readiness checks across the entire fleet."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    enabled_clusters = [c for c in config.clusters if c.enabled]

    if not enabled_clusters:
        click.secho("No enabled clusters found in inventory.", fg="yellow", err=True)
        sys.exit(1)

    click.echo(f"Validating fleet — {len(enabled_clusters)} clusters...")

    project_root = _find_project_root()
    playbook_path = project_root / "playbooks" / "validate-fleet.yml"

    cmd = [
        "ansible-playbook", str(playbook_path),
        "-e", f"config_dir={config_dir}",
        "-e", f"env={env}",
    ]
    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
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

    # Attempt to load per-cluster readiness reports
    reports_dir = project_root / "reports"
    fleet_results: list[dict[str, Any]] = []

    for cluster in enabled_clusters:
        report_path = reports_dir / f"readiness-{cluster.id}.json"
        if report_path.exists():
            try:
                with open(report_path) as f:
                    fleet_results.append(json.loads(f.read()))
            except (json.JSONDecodeError, OSError):
                fleet_results.append({
                    "cluster_id": cluster.id,
                    "overall_status": "UNKNOWN",
                })
        else:
            fleet_results.append({
                "cluster_id": cluster.id,
                "overall_status": "PASS" if result.returncode == 0 else "UNKNOWN",
            })

    # Compute summary
    status_counts: dict[str, int] = {}
    for r in fleet_results:
        status = r.get("overall_status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

    validated_at = datetime.now(timezone.utc).isoformat()

    fleet_summary = {
        "validated_at": validated_at,
        "total_clusters": len(fleet_results),
        "status_counts": status_counts,
        "clusters": fleet_results,
    }

    if fmt == "json":
        click.echo(json.dumps(fleet_summary, indent=2, default=str))

    elif fmt == "markdown":
        click.echo("## Fleet Validation Report")
        click.echo(f"\nValidated at: {validated_at}")
        click.echo(f"\nTotal clusters: {len(fleet_results)}")
        click.echo("")
        click.echo("| Status | Count |")
        click.echo("|--------|-------|")
        for status, count in sorted(status_counts.items()):
            click.echo(f"| {status} | {count} |")
        click.echo("")
        click.echo("| Cluster | Status |")
        click.echo("|---------|--------|")
        for r in fleet_results:
            click.echo(f"| {r['cluster_id']} | {r.get('overall_status', 'UNKNOWN')} |")

    else:
        # Text output
        click.echo(f"\nFleet validation at {validated_at}")
        click.echo(f"{'=' * 50}")
        for status, count in sorted(status_counts.items()):
            color = (
                "green" if status == "PASS" or status == "READY"
                else "red" if status == "FAIL" or status == "FAILED"
                else "yellow"
            )
            click.secho(f"  {status}: {count}", fg=color)

        click.echo(f"\nPer-cluster results:")
        for r in fleet_results:
            status = r.get("overall_status", "UNKNOWN")
            color = (
                "green" if status in ("PASS", "READY")
                else "red" if status in ("FAIL", "FAILED")
                else "yellow"
            )
            click.secho(f"  {r['cluster_id']}: {status}", fg=color)

    if verbose and result.stdout:
        click.echo("\n--- Ansible output ---")
        click.echo(result.stdout)

    if result.returncode != 0:
        sys.exit(1)
