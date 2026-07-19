"""Custom Jinja2/Ansible filters for MAS World automation."""

from __future__ import annotations

import re


def pad(value: int | str, width: int = 2) -> str:
    """Zero-pad a number to a fixed width."""
    return str(value).zfill(width)


def redact(value: str) -> str:
    """Redact a value for logging purposes."""
    if not isinstance(value, str) or len(value) < 4:
        return "**REDACTED**"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def s3_bucket_name(cluster_id: str, prefix: str = "mas-world-2026") -> str:
    """Generate a valid S3 bucket name for a cluster."""
    sanitized = re.sub(r"[^a-z0-9-]", "-", cluster_id.lower())
    return f"{prefix}-{sanitized}-loki"


def seat_username(seat_number: int, template: str = "user{seat:02d}") -> str:
    """Generate a student username from a seat number."""
    return template.format(seat=seat_number)


class FilterModule:
    """Ansible filter plugin."""

    def filters(self) -> dict:
        return {
            "pad": pad,
            "redact": redact,
            "s3_bucket_name": s3_bucket_name,
            "seat_username": seat_username,
        }
