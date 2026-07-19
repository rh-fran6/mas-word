"""Reporting commands."""

import sys

import click


@click.group("report")
def reports_group() -> None:
    """Fleet and seat reporting."""


@reports_group.command("fleet-status")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "markdown"]), default="text")
@click.pass_context
def fleet_status(ctx: click.Context, fmt: str) -> None:
    """Show fleet status dashboard."""
    click.echo("Fleet status: not yet implemented.")
    sys.exit(2)


@reports_group.command("seat-report")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "markdown"]), default="text")
@click.pass_context
def seat_report(ctx: click.Context, fmt: str) -> None:
    """Generate comprehensive seat assignment report."""
    click.echo("Seat report: not yet implemented.")
    sys.exit(2)
