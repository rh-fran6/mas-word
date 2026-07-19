"""Seat assignment management commands."""

import sys

import click


@click.group("seat")
def seats_group() -> None:
    """Seat assignment and management."""


@seats_group.command("assign")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.option("--cluster", required=True, help="Cluster ID.")
@click.pass_context
def assign_seat(ctx: click.Context, seat: int, cluster: str) -> None:
    """Assign a seat to a cluster."""
    click.echo(f"Assigning seat {seat} to cluster {cluster}: not yet implemented.")
    sys.exit(2)


@seats_group.command("replace")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.option("--cluster", required=True, help="Replacement cluster ID.")
@click.pass_context
def replace_seat(ctx: click.Context, seat: int, cluster: str) -> None:
    """Replace a seat's cluster with a spare."""
    click.echo(f"Replacing seat {seat} with cluster {cluster}: not yet implemented.")
    sys.exit(2)


@seats_group.command("unassign")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.pass_context
def unassign_seat(ctx: click.Context, seat: int) -> None:
    """Unassign a seat."""
    click.echo(f"Unassigning seat {seat}: not yet implemented.")
    sys.exit(2)


@seats_group.command("show")
@click.option("--seat", required=True, type=int, help="Seat number.")
@click.pass_context
def show_seat(ctx: click.Context, seat: int) -> None:
    """Show details for a seat assignment."""
    click.echo(f"Show seat {seat}: not yet implemented.")
    sys.exit(2)


@seats_group.command("export-map")
@click.option("--format", "fmt", type=click.Choice(["json", "csv", "markdown"]), default="json")
@click.pass_context
def export_seat_map(ctx: click.Context, fmt: str) -> None:
    """Export the full seat assignment map."""
    click.echo("Export seat map: not yet implemented.")
    sys.exit(2)
