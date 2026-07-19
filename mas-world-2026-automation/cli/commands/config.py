"""Configuration management commands."""

import json
import sys

import click

from cli.config.loader import ConfigLoader
from cli.config.validator import ConfigValidator


@click.group("config")
def config_group() -> None:
    """Configuration validation and inspection."""


@config_group.command("validate")
@click.option("--cluster", help="Validate only a specific cluster.")
@click.pass_context
def validate_config(ctx: click.Context, cluster: str | None) -> None:
    """Validate all configuration files against schemas."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    validator = ConfigValidator()
    errors = validator.validate(config, cluster_id=cluster)

    if errors:
        click.secho(f"Configuration validation failed with {len(errors)} error(s):", fg="red")
        for err in errors:
            severity = err.get("severity", "ERROR")
            color = "red" if severity == "ERROR" else "yellow"
            click.secho(f"  [{severity}] {err['message']}", fg=color)
            if err.get("path"):
                click.echo(f"         at: {err['path']}")
        sys.exit(1)

    click.secho("Configuration validation passed.", fg="green")


@config_group.command("render")
@click.option("--cluster", help="Render for a specific cluster.")
@click.option("--format", "fmt", type=click.Choice(["yaml", "json"]), default="yaml")
@click.pass_context
def render_effective_config(ctx: click.Context, cluster: str | None, fmt: str) -> None:
    """Render effective merged configuration with secrets redacted."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
        effective = loader.render_effective(config, cluster_id=cluster, redact_secrets=True)
    except Exception as e:
        click.secho(f"Failed to render configuration: {e}", fg="red", err=True)
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(effective, indent=2, default=str))
    else:
        import yaml

        click.echo(yaml.dump(effective, default_flow_style=False, sort_keys=False))


@config_group.command("diff")
@click.option("--from", "from_env", required=True, help="Source environment.")
@click.option("--to", "to_env", required=True, help="Target environment.")
@click.pass_context
def show_config_differences(ctx: click.Context, from_env: str, to_env: str) -> None:
    """Show configuration differences between environments."""
    config_dir = ctx.obj["config_dir"]

    try:
        loader_from = ConfigLoader(config_dir=config_dir, environment=from_env)
        loader_to = ConfigLoader(config_dir=config_dir, environment=to_env)
        config_from = loader_from.load()
        config_to = loader_to.load()
        diffs = ConfigLoader.diff(config_from, config_to)
    except Exception as e:
        click.secho(f"Failed to compare configurations: {e}", fg="red", err=True)
        sys.exit(1)

    if not diffs:
        click.echo(f"No differences between {from_env} and {to_env}.")
        return

    click.echo(f"Differences between {from_env} → {to_env}:")
    for d in diffs:
        click.echo(f"  {d['path']}: {d['from']} → {d['to']}")
