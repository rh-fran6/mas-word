"""Single-cluster operations."""

import sys

import click


@click.group("cluster")
def cluster_group() -> None:
    """Single-cluster preparation, validation, and repair."""


@cluster_group.command("prepare")
@click.argument("cluster_id")
@click.option("--dry-run", is_flag=True, help="Show what would be done.")
@click.pass_context
def prepare_cluster(ctx: click.Context, cluster_id: str, dry_run: bool) -> None:
    """Prepare a single cluster."""
    click.echo(f"Cluster preparation for {cluster_id}: not yet implemented.")
    sys.exit(2)


@cluster_group.command("validate")
@click.argument("cluster_id")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "markdown"]), default="text")
@click.pass_context
def validate_cluster(ctx: click.Context, cluster_id: str, fmt: str) -> None:
    """Run readiness checks on a single cluster."""
    click.echo(f"Cluster validation for {cluster_id}: not yet implemented.")
    sys.exit(2)


@cluster_group.command("repair")
@click.argument("cluster_id")
@click.option("--component", help="Repair only a specific component.")
@click.pass_context
def repair_cluster(ctx: click.Context, cluster_id: str, component: str | None) -> None:
    """Repair a failed cluster."""
    click.echo(f"Cluster repair for {cluster_id}: not yet implemented.")
    sys.exit(2)
