"""MAS World 2026 fleet management CLI."""

import sys

import click

from cli.commands.config import config_group
from cli.commands.cluster import cluster_group
from cli.commands.fleet import fleet_group
from cli.commands.seats import seats_group
from cli.commands.students import students_group
from cli.commands.exercises import exercises_group
from cli.commands.reports import reports_group


@click.group()
@click.option(
    "--env",
    type=click.Choice(["development", "rehearsal", "event"]),
    default="development",
    help="Target environment.",
)
@click.option(
    "--config-dir",
    type=click.Path(exists=True),
    default="config",
    help="Configuration directory.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def cli(ctx: click.Context, env: str, config_dir: str, verbose: bool) -> None:
    """MAS World 2026 — Fleet management CLI."""
    ctx.ensure_object(dict)
    ctx.obj["env"] = env
    ctx.obj["config_dir"] = config_dir
    ctx.obj["verbose"] = verbose


cli.add_command(config_group, "config")
cli.add_command(cluster_group, "cluster")
cli.add_command(fleet_group, "fleet")
cli.add_command(seats_group, "seat")
cli.add_command(students_group, "student")
cli.add_command(exercises_group, "exercise")
cli.add_command(reports_group, "report")


def main() -> None:
    cli(auto_envvar_prefix="MAS_WORLD")


if __name__ == "__main__":
    main()
