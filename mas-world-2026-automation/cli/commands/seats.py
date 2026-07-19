"""Seat assignment management commands."""

import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

import click
import yaml

from cli.config.loader import ConfigLoader


ASSIGNMENT_STATUSES = ("assigned", "unassigned", "quarantined")


def _load_assignments(config_dir: str) -> list[dict[str, Any]]:
    """Load the assignments file, returning an empty list if absent."""
    path = Path(config_dir) / "assignments.yaml"
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data or "assignments" not in data:
        return []
    return data["assignments"]


def _save_assignments(config_dir: str, assignments: list[dict[str, Any]]) -> None:
    """Write assignments back to the YAML file."""
    path = Path(config_dir) / "assignments.yaml"
    with open(path, "w") as f:
        yaml.dump(
            {"assignments": assignments},
            f,
            default_flow_style=False,
            sort_keys=False,
        )


def _resolve_username(profile_data: dict[str, Any], seat_number: int, padding: int) -> str:
    """Resolve the username from a credential profile template."""
    template = profile_data.get("username_template", "user{{ seat_number | pad(2) }}")
    padded = str(seat_number).zfill(padding)
    # Resolve the simple template pattern used in the config
    username = template.replace("{{ seat_number | pad(2) }}", padded)
    username = username.replace("{{ seat_number | pad(3) }}", str(seat_number).zfill(3))
    username = username.replace("{{ seat_number }}", str(seat_number))
    return username


@click.group("seat")
def seats_group() -> None:
    """Seat assignment and management."""


@seats_group.command("assign")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.option("--cluster", required=True, help="Cluster ID.")
@click.pass_context
def assign_seat(ctx: click.Context, seat: int, cluster: str) -> None:
    """Assign a seat to a cluster."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    # Load and validate configuration
    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    # Verify cluster exists in inventory
    cluster_cfg = None
    for c in config.clusters:
        if c.id == cluster:
            cluster_cfg = c
            break

    if cluster_cfg is None:
        click.secho(f"Cluster '{cluster}' not found in inventory.", fg="red", err=True)
        sys.exit(1)

    if not cluster_cfg.enabled:
        click.secho(f"Cluster '{cluster}' is disabled.", fg="red", err=True)
        sys.exit(1)

    if cluster_cfg.purpose.value not in ("attendee", "spare"):
        click.secho(
            f"Cluster '{cluster}' has purpose '{cluster_cfg.purpose.value}' "
            f"— only attendee and spare clusters can be assigned to seats.",
            fg="red",
            err=True,
        )
        sys.exit(1)

    # Load existing assignments
    assignments = _load_assignments(config_dir)

    # Check seat is not already assigned
    for a in assignments:
        if a["seat_number"] == seat and a.get("status") == "assigned":
            click.secho(
                f"Seat {seat} is already assigned to cluster '{a['cluster_id']}'. "
                f"Use 'replace' to change the assignment.",
                fg="red",
                err=True,
            )
            sys.exit(1)

    # Check cluster is not already assigned to a different seat
    for a in assignments:
        if a["cluster_id"] == cluster and a.get("status") == "assigned":
            click.secho(
                f"Cluster '{cluster}' is already assigned to seat {a['seat_number']}.",
                fg="red",
                err=True,
            )
            sys.exit(1)

    # Resolve username from credential profile
    profile_name = cluster_cfg.credentials.student_credential_profile
    profile = config.student_credential_profiles.get(profile_name)
    padding = config.fleet.assignment.seat_number_padding
    if profile:
        username = _resolve_username(profile.model_dump(), seat, padding)
    else:
        username = f"user{str(seat).zfill(padding)}"

    # Remove any previous unassigned entry for this seat
    assignments = [
        a for a in assignments
        if not (a["seat_number"] == seat and a.get("status") != "assigned")
    ]

    # Create assignment
    assignment = {
        "seat_number": seat,
        "cluster_id": cluster,
        "credential_profile": profile_name,
        "student_username": username,
        "status": "assigned",
    }

    assignments.append(assignment)
    _save_assignments(config_dir, assignments)

    click.secho(f"Seat {seat} assigned to cluster '{cluster}'.", fg="green")
    if verbose:
        click.echo(f"  Username: {username}")
        click.echo(f"  Profile:  {profile_name}")


@seats_group.command("replace")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.option("--cluster", required=True, help="Replacement cluster ID.")
@click.pass_context
def replace_seat(ctx: click.Context, seat: int, cluster: str) -> None:
    """Replace a seat's cluster with a spare."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    # Verify replacement cluster exists
    replacement_cfg = None
    for c in config.clusters:
        if c.id == cluster:
            replacement_cfg = c
            break

    if replacement_cfg is None:
        click.secho(f"Replacement cluster '{cluster}' not found in inventory.", fg="red", err=True)
        sys.exit(1)

    if not replacement_cfg.enabled:
        click.secho(f"Replacement cluster '{cluster}' is disabled.", fg="red", err=True)
        sys.exit(1)

    # Load existing assignments
    assignments = _load_assignments(config_dir)

    # Find current assignment for this seat
    current = None
    current_idx = None
    for idx, a in enumerate(assignments):
        if a["seat_number"] == seat and a.get("status") == "assigned":
            current = a
            current_idx = idx
            break

    if current is None:
        click.secho(f"Seat {seat} has no active assignment to replace.", fg="red", err=True)
        sys.exit(1)

    # Check replacement cluster is not already assigned
    for a in assignments:
        if a["cluster_id"] == cluster and a.get("status") == "assigned":
            click.secho(
                f"Replacement cluster '{cluster}' is already assigned to seat {a['seat_number']}.",
                fg="red",
                err=True,
            )
            sys.exit(1)

    old_cluster_id = current["cluster_id"]

    # Quarantine the old cluster
    current["status"] = "quarantined"

    # Resolve username for new assignment (preserve the same profile and username)
    profile_name = current.get("credential_profile", "attendee-default")
    username = current.get("student_username", f"user{str(seat).zfill(2)}")

    # Create new assignment entry
    new_assignment = {
        "seat_number": seat,
        "cluster_id": cluster,
        "credential_profile": profile_name,
        "student_username": username,
        "status": "assigned",
    }

    assignments.append(new_assignment)
    _save_assignments(config_dir, assignments)

    click.secho(
        f"Seat {seat} replaced: '{old_cluster_id}' (quarantined) -> '{cluster}'.",
        fg="green",
    )
    if verbose:
        click.echo(f"  Username: {username}")
        click.echo(f"  Profile:  {profile_name}")
        click.echo(f"  Old cluster '{old_cluster_id}' marked quarantined.")


@seats_group.command("unassign")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.pass_context
def unassign_seat(ctx: click.Context, seat: int) -> None:
    """Unassign a seat."""
    config_dir = ctx.obj["config_dir"]

    assignments = _load_assignments(config_dir)

    found = False
    for a in assignments:
        if a["seat_number"] == seat and a.get("status") == "assigned":
            a["status"] = "unassigned"
            found = True

    if not found:
        click.secho(f"Seat {seat} has no active assignment.", fg="yellow", err=True)
        sys.exit(1)

    _save_assignments(config_dir, assignments)
    click.secho(f"Seat {seat} unassigned.", fg="green")


@seats_group.command("show")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.pass_context
def show_seat(ctx: click.Context, seat: int) -> None:
    """Show details for a seat assignment."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]

    assignments = _load_assignments(config_dir)

    # Find all entries for this seat (may include quarantined history)
    seat_entries = [a for a in assignments if a["seat_number"] == seat]
    if not seat_entries:
        click.secho(f"No assignment found for seat {seat}.", fg="yellow", err=True)
        sys.exit(1)

    # Show the active assignment first
    active = [a for a in seat_entries if a.get("status") == "assigned"]
    inactive = [a for a in seat_entries if a.get("status") != "assigned"]

    # Try to load config for endpoint information
    endpoints = {}
    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
        for entry in active:
            for c in config.clusters:
                if c.id == entry["cluster_id"]:
                    endpoints = {
                        "console_url": c.endpoints.console_url,
                        "mas_url": c.endpoints.mas_url,
                        "showroom_url": c.endpoints.showroom_url,
                        "logging_url": c.endpoints.logging_url,
                    }
                    break
    except Exception:
        pass

    click.echo(f"Seat {seat} details:")
    click.echo(f"{'=' * 40}")

    if active:
        entry = active[0]
        click.secho("  Status:   assigned", fg="green")
        click.echo(f"  Cluster:  {entry['cluster_id']}")
        click.echo(f"  Username: {entry.get('student_username', 'N/A')}")
        click.echo(f"  Profile:  {entry.get('credential_profile', 'N/A')}")
        if endpoints:
            click.echo("  Endpoints:")
            for name, url in endpoints.items():
                display = url if url else "not configured"
                click.echo(f"    {name}: {display}")
    else:
        click.secho("  Status:   no active assignment", fg="yellow")

    if inactive:
        click.echo(f"\n  History ({len(inactive)} previous):")
        for entry in inactive:
            click.echo(
                f"    Cluster: {entry['cluster_id']} "
                f"[{entry.get('status', 'unknown')}]"
            )


@seats_group.command("export-map")
@click.option(
    "--format", "fmt",
    type=click.Choice(["json", "csv", "markdown"]),
    default="json",
)
@click.pass_context
def export_seat_map(ctx: click.Context, fmt: str) -> None:
    """Export the full seat assignment map."""
    config_dir = ctx.obj["config_dir"]

    assignments = _load_assignments(config_dir)

    if not assignments:
        click.secho("No assignments found.", fg="yellow", err=True)
        sys.exit(1)

    # Filter to active assignments for export, sorted by seat number
    active = sorted(
        [a for a in assignments if a.get("status") == "assigned"],
        key=lambda a: a["seat_number"],
    )

    if fmt == "json":
        click.echo(json.dumps(active, indent=2, default=str))

    elif fmt == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["seat_number", "cluster_id", "student_username", "credential_profile", "status"],
        )
        writer.writeheader()
        for a in active:
            writer.writerow({
                "seat_number": a["seat_number"],
                "cluster_id": a["cluster_id"],
                "student_username": a.get("student_username", ""),
                "credential_profile": a.get("credential_profile", ""),
                "status": a.get("status", ""),
            })
        click.echo(output.getvalue().rstrip())

    elif fmt == "markdown":
        click.echo("| Seat | Cluster | Username | Profile | Status |")
        click.echo("|------|---------|----------|---------|--------|")
        for a in active:
            click.echo(
                f"| {a['seat_number']} "
                f"| {a['cluster_id']} "
                f"| {a.get('student_username', '')} "
                f"| {a.get('credential_profile', '')} "
                f"| {a.get('status', '')} |"
            )
