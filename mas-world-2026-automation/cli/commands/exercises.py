"""Exercise management commands."""

import sys

import click


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
    click.echo(f"Reset {module} exercise on {cluster_id}: not yet implemented.")
    sys.exit(2)
