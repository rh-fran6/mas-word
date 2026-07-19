"""Student account lifecycle commands."""

import json
import secrets
import string
import subprocess
import sys
from pathlib import Path
from typing import Any

import click
import yaml

from cli.config.loader import ConfigLoader
from cli.config.schema import ClusterConfig, MASWorldConfig, PasswordMode
from cli.secrets.provider import create_provider


def _find_project_root() -> Path:
    """Walk up from this file to find the automation project root."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "playbooks").is_dir() and (current / "ansible.cfg").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent


def _run_ansible(
    playbook: str,
    extra_vars: dict[str, str],
    verbose: bool = False,
) -> int:
    """Run an ansible-playbook command. Returns the exit code."""
    project_root = _find_project_root()
    playbook_path = project_root / "playbooks" / playbook

    cmd = ["ansible-playbook", str(playbook_path)]
    for key, value in extra_vars.items():
        cmd.extend(["-e", f"{key}={value}"])
    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=False,
            text=True,
        )
        return result.returncode
    except FileNotFoundError:
        click.secho(
            "ansible-playbook not found. Ensure Ansible is installed and on PATH.",
            fg="red",
            err=True,
        )
        return 127


def _generate_password(length: int = 18) -> str:
    """Generate a cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits
    # Ensure at least one digit and one uppercase and one lowercase
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and any(c.isdigit() for c in password)
        ):
            return password


def _resolve_template(template: str, seat_number: int, padding: int) -> str:
    """Resolve a template string with seat_number substitution."""
    padded = str(seat_number).zfill(padding)
    result = template.replace("{{ seat_number | pad(2) }}", padded)
    result = result.replace("{{ seat_number | pad(3) }}", str(seat_number).zfill(3))
    result = result.replace("{{ seat_number }}", str(seat_number))
    return result


def _select_clusters(
    config: MASWorldConfig,
    cluster_id: str | None,
    seat: int | None,
) -> list[ClusterConfig]:
    """Filter clusters based on --cluster and --seat options."""
    clusters = [c for c in config.clusters if c.enabled]

    if cluster_id:
        clusters = [c for c in clusters if c.id == cluster_id]
        if not clusters:
            click.secho(f"Cluster '{cluster_id}' not found or disabled.", fg="red", err=True)
            sys.exit(1)

    if seat is not None:
        clusters = [c for c in clusters if c.seat_number == seat]
        if not clusters:
            click.secho(f"No cluster found for seat {seat}.", fg="red", err=True)
            sys.exit(1)

    return clusters


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


@click.group("student")
def students_group() -> None:
    """Student account management."""


@students_group.command("create")
@click.option("--cluster", help="Target a specific cluster.")
@click.option("--seat", type=int, help="Target a specific seat.")
@click.pass_context
def create_student_accounts(ctx: click.Context, cluster: str | None, seat: int | None) -> None:
    """Create student accounts on target clusters."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    clusters = _select_clusters(config, cluster, seat)

    if not clusters:
        click.secho("No target clusters found.", fg="yellow", err=True)
        sys.exit(1)

    # Create secret provider for storing generated passwords
    provider = create_provider(
        config.secrets.provider.value,
        config.secrets.config,
    )

    padding = config.fleet.assignment.seat_number_padding
    created_count = 0
    failed_count = 0

    for c in clusters:
        profile_name = c.credentials.student_credential_profile
        profile = config.student_credential_profiles.get(profile_name)

        if profile is None:
            click.secho(
                f"  Cluster '{c.id}': credential profile '{profile_name}' not found. Skipping.",
                fg="red",
                err=True,
            )
            failed_count += 1
            continue

        seat_num = c.seat_number
        if seat_num is None:
            click.secho(
                f"  Cluster '{c.id}': no seat number assigned. Skipping student creation.",
                fg="yellow",
                err=True,
            )
            continue

        username = _resolve_template(profile.username_template, seat_num, padding)
        click.echo(f"Creating student account '{username}' on cluster '{c.id}'...")

        # Handle password based on mode
        password_ref = None
        if profile.password.mode == PasswordMode.GENERATED:
            password = _generate_password(profile.password.length)
            if profile.password.secret_ref_template:
                ref = _resolve_template(
                    profile.password.secret_ref_template, seat_num, padding,
                )
                try:
                    provider.set_secret(ref, password)
                    password_ref = ref
                    if verbose:
                        click.echo(f"  Password stored at: {ref}")
                except Exception as e:
                    click.secho(
                        f"  Failed to store password for '{username}': {e}",
                        fg="red",
                        err=True,
                    )
                    failed_count += 1
                    continue

        elif profile.password.mode == PasswordMode.SECRET_REF:
            if profile.password.secret_ref_template:
                password_ref = _resolve_template(
                    profile.password.secret_ref_template, seat_num, padding,
                )
            else:
                click.secho(
                    f"  Cluster '{c.id}': SECRET_REF mode but no ref template. Skipping.",
                    fg="red",
                    err=True,
                )
                failed_count += 1
                continue

        elif profile.password.mode == PasswordMode.DISABLED:
            if verbose:
                click.echo(f"  Password disabled for '{username}' (external IDP).")

        # Run the student creation playbook
        extra_vars: dict[str, str] = {
            "cluster_id": c.id,
            "seat_number": str(seat_num),
            "student_username": username,
            "credential_profile": profile_name,
            "config_dir": config_dir,
            "env": env,
        }

        rc = _run_ansible("prepare-cluster.yml", extra_vars, verbose=verbose)

        if rc == 0:
            click.secho(f"  Student '{username}' created on '{c.id}'.", fg="green")
            created_count += 1
        else:
            click.secho(
                f"  Failed to create student '{username}' on '{c.id}' (exit code {rc}).",
                fg="red",
                err=True,
            )
            failed_count += 1

    click.echo(f"\nStudent accounts: {created_count} created, {failed_count} failed.")
    if failed_count > 0:
        sys.exit(1)


@students_group.command("rotate")
@click.option("--cluster", help="Target a specific cluster.")
@click.option("--seat", type=int, help="Target a specific seat.")
@click.pass_context
def rotate_student_credentials(
    ctx: click.Context, cluster: str | None, seat: int | None,
) -> None:
    """Rotate student credentials."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    clusters = _select_clusters(config, cluster, seat)

    if not clusters:
        click.secho("No target clusters found.", fg="yellow", err=True)
        sys.exit(1)

    provider = create_provider(
        config.secrets.provider.value,
        config.secrets.config,
    )

    padding = config.fleet.assignment.seat_number_padding
    rotated_count = 0
    failed_count = 0

    for c in clusters:
        profile_name = c.credentials.student_credential_profile
        profile = config.student_credential_profiles.get(profile_name)

        if profile is None:
            click.secho(
                f"  Cluster '{c.id}': profile '{profile_name}' not found.",
                fg="red",
                err=True,
            )
            failed_count += 1
            continue

        seat_num = c.seat_number
        if seat_num is None:
            continue

        if profile.password.mode != PasswordMode.GENERATED:
            if verbose:
                click.echo(
                    f"  Cluster '{c.id}': password mode is '{profile.password.mode.value}', "
                    f"rotation not applicable."
                )
            continue

        username = _resolve_template(profile.username_template, seat_num, padding)
        click.echo(f"Rotating credentials for '{username}' on '{c.id}'...")

        # Generate new password
        new_password = _generate_password(profile.password.length)

        # Store in secret provider
        if profile.password.secret_ref_template:
            ref = _resolve_template(
                profile.password.secret_ref_template, seat_num, padding,
            )
            try:
                provider.set_secret(ref, new_password)
            except Exception as e:
                click.secho(
                    f"  Failed to store rotated password: {e}",
                    fg="red",
                    err=True,
                )
                failed_count += 1
                continue

        # Run rotation playbook
        extra_vars = {
            "cluster_id": c.id,
            "seat_number": str(seat_num),
            "config_dir": config_dir,
            "env": env,
        }

        rc = _run_ansible("rotate-credentials.yml", extra_vars, verbose=verbose)

        if rc == 0:
            click.secho(f"  Credentials rotated for '{username}'.", fg="green")
            rotated_count += 1
        else:
            click.secho(
                f"  Rotation failed for '{username}' (exit code {rc}).",
                fg="red",
                err=True,
            )
            failed_count += 1

    click.echo(f"\nCredential rotation: {rotated_count} rotated, {failed_count} failed.")
    if failed_count > 0:
        sys.exit(1)


@students_group.command("disable")
@click.option("--cluster", help="Target a specific cluster.")
@click.option("--seat", type=int, help="Target a specific seat.")
@click.pass_context
def disable_student_accounts(
    ctx: click.Context, cluster: str | None, seat: int | None,
) -> None:
    """Disable student accounts."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    clusters = _select_clusters(config, cluster, seat)

    if not clusters:
        click.secho("No target clusters found.", fg="yellow", err=True)
        sys.exit(1)

    disabled_count = 0
    failed_count = 0

    for c in clusters:
        click.echo(f"Disabling student accounts on cluster '{c.id}'...")

        extra_vars = {
            "cluster_id": c.id,
            "student_action": "disable",
            "config_dir": config_dir,
            "env": env,
        }
        if c.seat_number is not None:
            extra_vars["seat_number"] = str(c.seat_number)

        rc = _run_ansible("prepare-cluster.yml", extra_vars, verbose=verbose)

        if rc == 0:
            click.secho(f"  Student accounts disabled on '{c.id}'.", fg="green")
            disabled_count += 1
        else:
            click.secho(
                f"  Failed to disable accounts on '{c.id}' (exit code {rc}).",
                fg="red",
                err=True,
            )
            failed_count += 1

    click.echo(f"\nStudent accounts: {disabled_count} disabled, {failed_count} failed.")
    if failed_count > 0:
        sys.exit(1)


@students_group.command("delete")
@click.option("--cluster", help="Target a specific cluster.")
@click.option("--seat", type=int, help="Target a specific seat.")
@click.pass_context
def delete_student_accounts(
    ctx: click.Context, cluster: str | None, seat: int | None,
) -> None:
    """Delete student accounts."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    clusters = _select_clusters(config, cluster, seat)

    if not clusters:
        click.secho("No target clusters found.", fg="yellow", err=True)
        sys.exit(1)

    deleted_count = 0
    failed_count = 0

    for c in clusters:
        click.echo(f"Deleting student accounts on cluster '{c.id}'...")

        extra_vars = {
            "cluster_id": c.id,
            "student_action": "delete",
            "config_dir": config_dir,
            "env": env,
        }
        if c.seat_number is not None:
            extra_vars["seat_number"] = str(c.seat_number)

        rc = _run_ansible("prepare-cluster.yml", extra_vars, verbose=verbose)

        if rc == 0:
            click.secho(f"  Student accounts deleted on '{c.id}'.", fg="green")
            deleted_count += 1
        else:
            click.secho(
                f"  Failed to delete accounts on '{c.id}' (exit code {rc}).",
                fg="red",
                err=True,
            )
            failed_count += 1

    click.echo(f"\nStudent accounts: {deleted_count} deleted, {failed_count} failed.")
    if failed_count > 0:
        sys.exit(1)


@students_group.command("validate")
@click.option("--cluster", help="Target a specific cluster.")
@click.option("--seat", type=int, help="Target a specific seat.")
@click.pass_context
def validate_student_access(
    ctx: click.Context, cluster: str | None, seat: int | None,
) -> None:
    """Validate student login and access controls."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    clusters = _select_clusters(config, cluster, seat)

    if not clusters:
        click.secho("No target clusters found.", fg="yellow", err=True)
        sys.exit(1)

    padding = config.fleet.assignment.seat_number_padding
    passed_count = 0
    failed_count = 0

    for c in clusters:
        profile_name = c.credentials.student_credential_profile
        profile = config.student_credential_profiles.get(profile_name)

        seat_num = c.seat_number
        if seat_num is None:
            continue

        if profile:
            username = _resolve_template(profile.username_template, seat_num, padding)
        else:
            username = f"user{str(seat_num).zfill(padding)}"

        click.echo(f"Validating student '{username}' on cluster '{c.id}'...")

        extra_vars = {
            "cluster_id": c.id,
            "seat_number": str(seat_num),
            "student_username": username,
            "config_dir": config_dir,
            "env": env,
        }

        rc = _run_ansible("validate-cluster.yml", extra_vars, verbose=verbose)

        if rc == 0:
            click.secho(f"  Student '{username}' validation passed.", fg="green")
            passed_count += 1
        else:
            click.secho(
                f"  Student '{username}' validation failed (exit code {rc}).",
                fg="red",
                err=True,
            )
            failed_count += 1

    click.echo(f"\nStudent validation: {passed_count} passed, {failed_count} failed.")
    if failed_count > 0:
        sys.exit(1)


@students_group.command("export-cards")
@click.option(
    "--format", "fmt",
    type=click.Choice(["html", "pdf", "json"]),
    default="html",
)
@click.option("--seat", type=int, help="Generate for a specific seat.")
@click.pass_context
def export_access_cards(ctx: click.Context, fmt: str, seat: int | None) -> None:
    """Generate attendee access cards."""
    config_dir = ctx.obj["config_dir"]
    env = ctx.obj["env"]
    verbose = ctx.obj["verbose"]

    try:
        loader = ConfigLoader(config_dir=config_dir, environment=env)
        config = loader.load()
    except Exception as e:
        click.secho(f"Failed to load configuration: {e}", fg="red", err=True)
        sys.exit(1)

    assignments = _load_assignments(config_dir)

    if not assignments:
        click.secho("No assignments found. Run seat assignments first.", fg="yellow", err=True)
        sys.exit(1)

    # Filter to active assignments
    active = [a for a in assignments if a.get("status") == "assigned"]
    if seat is not None:
        active = [a for a in active if a["seat_number"] == seat]

    if not active:
        target = f"seat {seat}" if seat is not None else "any seat"
        click.secho(f"No active assignments found for {target}.", fg="yellow", err=True)
        sys.exit(1)

    active.sort(key=lambda a: a["seat_number"])

    # Build cluster lookup for endpoints
    cluster_map: dict[str, ClusterConfig] = {}
    for c in config.clusters:
        cluster_map[c.id] = c

    # Attempt to get passwords from secret provider
    provider = None
    try:
        provider = create_provider(
            config.secrets.provider.value,
            config.secrets.config,
        )
    except Exception:
        if verbose:
            click.echo("  Secret provider unavailable; passwords will show as references.")

    padding = config.fleet.assignment.seat_number_padding

    cards: list[dict[str, Any]] = []
    for a in active:
        seat_num = a["seat_number"]
        cluster_id = a["cluster_id"]
        username = a.get("student_username", f"user{str(seat_num).zfill(padding)}")
        profile_name = a.get("credential_profile", "attendee-default")

        # Get endpoints from cluster config
        cluster_cfg = cluster_map.get(cluster_id)
        endpoints = {}
        if cluster_cfg:
            endpoints = {
                "console_url": cluster_cfg.endpoints.console_url or "See facilitator",
                "mas_url": cluster_cfg.endpoints.mas_url or "See facilitator",
                "showroom_url": cluster_cfg.endpoints.showroom_url or "See facilitator",
            }

        # Retrieve password (never include cluster-admin creds)
        password_display = "See facilitator"
        profile = config.student_credential_profiles.get(profile_name)
        if profile and provider and profile.password.secret_ref_template:
            ref = _resolve_template(
                profile.password.secret_ref_template, seat_num, padding,
            )
            try:
                password_display = provider.get_secret(ref)
            except (KeyError, Exception):
                password_display = f"Retrieve from: {ref}"

        card = {
            "seat_number": seat_num,
            "username": username,
            "password": password_display,
            **endpoints,
            "support": "Raise your hand or ask a facilitator for help.",
        }
        cards.append(card)

    if fmt == "json":
        click.echo(json.dumps(cards, indent=2, default=str))

    elif fmt == "html":
        click.echo("<!DOCTYPE html>")
        click.echo('<html lang="en"><head>')
        click.echo('<meta charset="UTF-8">')
        click.echo("<title>MAS World 2026 - Access Cards</title>")
        click.echo("<style>")
        click.echo("  body { font-family: sans-serif; margin: 20px; }")
        click.echo("  .card { border: 2px solid #333; padding: 20px; margin: 15px 0;"
                    " max-width: 500px; page-break-inside: avoid; }")
        click.echo("  .card h2 { margin-top: 0; color: #c00; }")
        click.echo("  .card dt { font-weight: bold; margin-top: 8px; }")
        click.echo("  .card dd { margin-left: 0; margin-bottom: 4px; }")
        click.echo("  @media print { .card { break-inside: avoid; } }")
        click.echo("</style>")
        click.echo("</head><body>")
        click.echo("<h1>MAS World 2026 - Attendee Access Cards</h1>")

        for card in cards:
            click.echo('<div class="card">')
            click.echo(f'  <h2>Seat {card["seat_number"]}</h2>')
            click.echo("  <dl>")
            click.echo(f'    <dt>Username</dt><dd>{card["username"]}</dd>')
            click.echo(f'    <dt>Password</dt><dd>{card["password"]}</dd>')
            for key in ("showroom_url", "console_url", "mas_url"):
                if key in card:
                    label = key.replace("_", " ").title()
                    click.echo(f"    <dt>{label}</dt><dd>{card[key]}</dd>")
            click.echo(f'    <dt>Support</dt><dd>{card["support"]}</dd>')
            click.echo("  </dl>")
            click.echo("</div>")

        click.echo("</body></html>")

    elif fmt == "pdf":
        click.secho(
            "PDF export requires additional dependencies. Use --format html "
            "and print to PDF from a browser.",
            fg="yellow",
            err=True,
        )
        # Fall back to JSON output
        click.echo(json.dumps(cards, indent=2, default=str))

    if verbose:
        click.echo(f"\nGenerated {len(cards)} access card(s).", err=True)
