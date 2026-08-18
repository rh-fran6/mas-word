#!/usr/bin/env python3
"""Post-install patches for ibm.mas_devops collection.

Applied automatically by `make setup` after `ansible-galaxy collection install`.
Patches are idempotent — safe to run multiple times on the same files.

Fixes:
  1. regex_search() returns string in until/assert conditionals
     (ansible-core >= 2.17 rejects non-boolean). Append 'is not none'.
  2. pause module breaks strategy:free parallel execution.
     Replace with ansible.builtin.wait_for + timeout.
  3. k8s lookup plugin runs on controller, ignoring per-host KUBECONFIG.
     Replace query('k8s', ...) with kubernetes.core.k8s_info module.
"""

import os
import re
import sys
from pathlib import Path


def patch_regex_search(collection_root):
    """Fix regex_search boolean conditional in suite_db2_setup_for_manage."""
    target = os.path.join(
        collection_root, "roles", "suite_db2_setup_for_manage", "tasks", "main.yml"
    )
    if not os.path.isfile(target):
        return 0

    text = Path(target).read_text()
    patched = re.sub(
        r"(regex_search\('DBstatus-Success', multiline=True\))(?! is not none)",
        r"\1 is not none",
        text,
    )
    if patched != text:
        Path(target).write_text(patched)
        print(f"  [1] regex_search fix applied: {os.path.relpath(target)}")
        return 1

    print("  [1] regex_search fix: already applied")
    return 0


def patch_pause_to_wait_for(collection_root):
    """Replace pause module with wait_for in strategy:free-incompatible files."""
    targets = [
        "roles/db2/tasks/delete_db2_operand_request.yml",
        "roles/db2/tasks/upgrade/run-db2-subscription-upgrade.yml",
        "roles/suite_db2_setup_for_manage/tasks/apply-db2-config-settings.yml",
    ]

    count = 0
    for rel_path in targets:
        target = os.path.join(collection_root, rel_path)
        if not os.path.isfile(target):
            continue

        text = Path(target).read_text()
        original = text

        def replace_pause_minutes(m):
            indent = m.group(1)
            minutes = int(m.group(2))
            return f"{indent}ansible.builtin.wait_for:\n{indent}  timeout: {minutes * 60}"

        text = re.sub(
            r"^(\s*)pause:\n\1  minutes:\s*(\d+)",
            replace_pause_minutes,
            text,
            flags=re.MULTILINE,
        )

        if text != original:
            Path(target).write_text(text)
            print(f"  [2] pause→wait_for applied: {os.path.relpath(target)}")
            count += 1

    if count == 0:
        print("  [2] pause→wait_for: already applied")

    return count


def patch_k8s_lookup_to_module(collection_root):
    """Replace k8s lookup plugin with k8s_info module in db2 dbconfig tasks.

    The k8s lookup plugin runs on the controller and ignores per-host
    KUBECONFIG, breaking strategy:free with multiple clusters.
    """
    targets = [
        "roles/suite_db2_setup_for_manage/tasks/db2_dbconfig.yml",
        "roles/suite_db2_setup_for_facilities/tasks/apply-db2-dbconfig.yml",
    ]

    old_block = (
        "- name: Verify if DB2 is already enforced\n"
        "  set_fact:\n"
        "    db2_cfg: \"{{  query('k8s', kind='ConfigMap', "
        "api_version='v1', resource_name=db2_config_name, "
        'namespace=db2_namespace) }}"'
    )
    new_block = (
        "- name: Verify if DB2 is already enforced\n"
        "  kubernetes.core.k8s_info:\n"
        "    kind: ConfigMap\n"
        "    api_version: v1\n"
        '    name: "{{ db2_config_name }}"\n'
        '    namespace: "{{ db2_namespace }}"\n'
        "  register: _db2_cfg_lookup\n"
        "\n"
        "- name: Set db2_cfg from lookup result\n"
        "  set_fact:\n"
        '    db2_cfg: "{{ _db2_cfg_lookup.resources }}"'
    )

    count = 0
    for rel_path in targets:
        target = os.path.join(collection_root, rel_path)
        if not os.path.isfile(target):
            continue

        text = Path(target).read_text()
        if old_block in text:
            text = text.replace(old_block, new_block)
            Path(target).write_text(text)
            print(f"  [3] k8s lookup→k8s_info applied: {os.path.relpath(target)}")
            count += 1

    if count == 0:
        print("  [3] k8s lookup→k8s_info: already applied")

    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: patch-collection.py <collection-root>", file=sys.stderr)
        sys.exit(1)

    collection_root = sys.argv[1]
    if not os.path.isdir(collection_root):
        print(f"ERROR: {collection_root} not found", file=sys.stderr)
        sys.exit(1)

    total = 0
    total += patch_regex_search(collection_root)
    total += patch_pause_to_wait_for(collection_root)
    total += patch_k8s_lookup_to_module(collection_root)

    if total > 0:
        print(f"Patch applied successfully ({total} file(s) modified).")
    else:
        print("All patches already applied.")


if __name__ == "__main__":
    main()
