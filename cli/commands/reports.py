"""Reporting commands."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click
import yaml

from cli.config.loader import ConfigLoader


def _load_assignments(config_dir: str) -> list[dict[str, Any]]:
    """Load assignments from YAML file."""
    path = Path(config_dir) / "assignments.yaml"
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data or "assignments" not in data:
        return []
    return data["assignments"]


@click.group("report")
def reports_group() -> None:
    """Fleet and seat reporting."""


@reports_group.command("fleet-status")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
)
@click.pass_context
def fleet_status(ctx: click.Context, fmt: str) -> None:
    """Show fleet status dashboard."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    assignments = _load_assignments(config_dir)

    # Count clusters by purpose
    all_clusters = config.clusters
    enabled_clusters = [c for c in all_clusters if c.enabled]

    by_purpose: dict[str, int] = {}
    for c in enabled_clusters:
        purpose = c.purpose.value
        by_purpose[purpose] = by_purpose.get(purpose, 0) + 1

    disabled_count = len(all_clusters) - len(enabled_clusters)

    # Count assignments by status
    assigned_cluster_ids = set()
    quarantined_cluster_ids = set()
    assignment_counts: dict[str, int] = {}
    for a in assignments:
        status = a.get("status", "unknown")
        assignment_counts[status] = assignment_counts.get(status, 0) + 1
        if status == "assigned":
            assigned_cluster_ids.add(a["cluster_id"])
        elif status == "quarantined":
            quarantined_cluster_ids.add(a["cluster_id"])

    # Determine unassigned attendee/spare clusters
    assignable_cluster_ids = {
        c.id for c in enabled_clusters if c.purpose.value in ("attendee", "spare")
    }
    unassigned_count = len(assignable_cluster_ids - assigned_cluster_ids - quarantined_cluster_ids)

    # Spare cluster availability
    spare_clusters = [c for c in enabled_clusters if c.purpose.value == "spare"]
    spare_assigned = sum(1 for s in spare_clusters if s.id in assigned_cluster_ids)
    spare_available = len(spare_clusters) - spare_assigned

    generated_at = datetime.now(UTC).isoformat()

    dashboard = {
        "generated_at": generated_at,
        "environment": env,
        "total_clusters": len(all_clusters),
        "enabled_clusters": len(enabled_clusters),
        "disabled_clusters": disabled_count,
        "by_purpose": by_purpose,
        "assigned": assignment_counts.get("assigned", 0),
        "unassigned": unassigned_count,
        "quarantined": assignment_counts.get("quarantined", 0),
        "spare_total": len(spare_clusters),
        "spare_available": spare_available,
        "fleet_config": {
            "attendee_cluster_count": config.fleet.attendee_cluster_count,
            "spare_cluster_count": config.fleet.spare_cluster_count,
            "facilitator_cluster_count": config.fleet.facilitator_cluster_count,
        },
    }

    if fmt == "json":
        click.echo(json.dumps(dashboard, indent=2, default=str))

    elif fmt == "markdown":
        click.echo("## Fleet Status Dashboard")
        click.echo(f"\nGenerated: {generated_at}")
        click.echo(f"\nEnvironment: {env}")
        click.echo("")
        click.echo("| Metric | Value |")
        click.echo("|--------|-------|")
        click.echo(f"| Total clusters | {len(all_clusters)} |")
        click.echo(f"| Enabled | {len(enabled_clusters)} |")
        click.echo(f"| Disabled | {disabled_count} |")
        for purpose, count in sorted(by_purpose.items()):
            click.echo(f"| {purpose.title()} clusters | {count} |")
        click.echo(f"| Assigned | {assignment_counts.get('assigned', 0)} |")
        click.echo(f"| Unassigned | {unassigned_count} |")
        click.echo(f"| Quarantined | {assignment_counts.get('quarantined', 0)} |")
        click.echo(f"| Spare available | {spare_available} |")

    else:
        # Text dashboard
        click.echo(f"Fleet Status Dashboard — {env}")
        click.echo(f"Generated: {generated_at}")
        click.echo(f"{'=' * 45}")
        click.echo("")
        click.echo("  Cluster inventory:")
        click.echo(f"    Total:      {len(all_clusters)}")
        click.echo(f"    Enabled:    {len(enabled_clusters)}")
        click.echo(f"    Disabled:   {disabled_count}")
        click.echo("")
        click.echo("  By purpose:")
        for purpose, count in sorted(by_purpose.items()):
            click.echo(f"    {purpose.title():15s} {count}")
        click.echo("")
        click.echo("  Assignment status:")

        assigned_count = assignment_counts.get("assigned", 0)
        click.secho(
            f"    Assigned:     {assigned_count}", fg="green" if assigned_count > 0 else None
        )
        click.echo(f"    Unassigned:   {unassigned_count}")

        quarantined = assignment_counts.get("quarantined", 0)
        if quarantined > 0:
            click.secho(f"    Quarantined:  {quarantined}", fg="red")
        else:
            click.echo(f"    Quarantined:  {quarantined}")

        click.echo("")
        click.echo("  Spare clusters:")
        click.echo(f"    Total:      {len(spare_clusters)}")
        color = "green" if spare_available > 0 else "yellow"
        click.secho(f"    Available:  {spare_available}", fg=color)

        click.echo("")
        click.echo("  Expected counts (from config):")
        click.echo(f"    Attendee:    {config.fleet.attendee_cluster_count}")
        click.echo(f"    Spare:       {config.fleet.spare_cluster_count}")
        click.echo(f"    Facilitator: {config.fleet.facilitator_cluster_count}")


@reports_group.command("seat-report")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
)
@click.pass_context
def seat_report(ctx: click.Context, fmt: str) -> None:
    """Generate comprehensive seat assignment report."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    assignments = _load_assignments(config_dir)

    # Build cluster endpoint lookup
    cluster_map = {c.id: c for c in config.clusters}

    generated_at = datetime.now(UTC).isoformat()

    # Separate active from historical
    active_assignments = [a for a in assignments if a.get("status") == "assigned"]
    active_assignments.sort(key=lambda a: a["seat_number"])

    quarantined = [a for a in assignments if a.get("status") == "quarantined"]
    unassigned = [a for a in assignments if a.get("status") == "unassigned"]

    report_data: list[dict[str, Any]] = []
    for a in active_assignments:
        cluster_id = a["cluster_id"]
        cluster_cfg = cluster_map.get(cluster_id)
        entry: dict[str, Any] = {
            "seat_number": a["seat_number"],
            "cluster_id": cluster_id,
            "username": a.get("student_username", "N/A"),
            "profile": a.get("credential_profile", "N/A"),
            "status": a.get("status", "unknown"),
        }
        if cluster_cfg:
            entry["console_url"] = cluster_cfg.endpoints.console_url or "N/A"
            entry["mas_url"] = cluster_cfg.endpoints.mas_url or "N/A"
            entry["showroom_url"] = cluster_cfg.endpoints.showroom_url or "N/A"
        report_data.append(entry)

    report = {
        "generated_at": generated_at,
        "environment": env,
        "total_active": len(active_assignments),
        "total_quarantined": len(quarantined),
        "total_unassigned": len(unassigned),
        "seats": report_data,
    }

    if fmt == "json":
        click.echo(json.dumps(report, indent=2, default=str))

    elif fmt == "markdown":
        click.echo("## Seat Assignment Report")
        click.echo(f"\nGenerated: {generated_at}")
        click.echo(f"\nEnvironment: {env}")
        click.echo(
            f"\nActive: {len(active_assignments)} | "
            f"Quarantined: {len(quarantined)} | "
            f"Unassigned: {len(unassigned)}"
        )
        click.echo("")

        if report_data:
            click.echo("| Seat | Cluster | Username | Profile | Status |")
            click.echo("|------|---------|----------|---------|--------|")
            for entry in report_data:
                click.echo(
                    f"| {entry['seat_number']} "
                    f"| {entry['cluster_id']} "
                    f"| {entry['username']} "
                    f"| {entry['profile']} "
                    f"| {entry['status']} |"
                )
        else:
            click.echo("No active seat assignments.")

        if quarantined:
            click.echo("\n### Quarantined Clusters")
            click.echo("")
            click.echo("| Seat | Cluster | Status |")
            click.echo("|------|---------|--------|")
            for q in quarantined:
                click.echo(f"| {q['seat_number']} | {q['cluster_id']} | quarantined |")

    else:
        # Text output
        click.echo(f"Seat Assignment Report — {env}")
        click.echo(f"Generated: {generated_at}")
        click.echo(f"{'=' * 60}")
        click.echo(
            f"\nActive: {len(active_assignments)}  "
            f"Quarantined: {len(quarantined)}  "
            f"Unassigned: {len(unassigned)}"
        )

        if report_data:
            click.echo(
                f"\n{'Seat':<6} {'Cluster':<16} {'Username':<12} {'Profile':<18} {'Status':<12}"
            )
            click.echo(f"{'-' * 6} {'-' * 16} {'-' * 12} {'-' * 18} {'-' * 12}")
            for entry in report_data:
                color = "green" if entry["status"] == "assigned" else "yellow"
                click.secho(
                    f"{entry['seat_number']:<6} "
                    f"{entry['cluster_id']:<16} "
                    f"{entry['username']:<12} "
                    f"{entry['profile']:<18} "
                    f"{entry['status']:<12}",
                    fg=color,
                )
        else:
            click.echo("\nNo active seat assignments.")

        if quarantined:
            click.echo("\nQuarantined clusters:")
            for q in quarantined:
                click.secho(
                    f"  Seat {q['seat_number']}: {q['cluster_id']}",
                    fg="red",
                )
