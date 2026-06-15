# Troshka Ansible Collection

## Overview

`agnosticd.cloud_provider_troshka` — AgnosticD V2 cloud provider collection for Troshka nested VM environments.

Namespace: `agnosticd`, Collection: `cloud_provider_troshka`, Requires Ansible >= 2.16.0.

## Structure

- **`plugins/module_utils/troshka_api.py`** — Shared API client (`TroshkaAPI` class), stdlib-only (`urllib.request`), no pip dependencies
- **`plugins/inventory/troshka.py`** — Dynamic inventory plugin, groups VMs by `AnsibleGroup` tags, auto-configures ProxyJump through bastion
- **`roles/`** — AgnosticD lifecycle roles: `deploy`, `destroy`, `capture`, `lifecycle`, `create_inventory`, `portal_token`

## API Client

`TroshkaAPI(api_url, api_key)` — all keys start with `trk_`. Methods: `list_patterns`, `deploy_pattern`, `deploy_template`, `get_project`, `delete_project`, `start_project`, `stop_project`, `get_deploy_progress`, `create_portal_token`, `capture_pattern`, `wait_for_project_state`, `wait_for_pattern_state`.

## Inventory Plugin

Inventory files must be named `*.troshka.yml`. Required options: `api_url`, `api_key`, `project_id`. The plugin finds the bastion VM (AnsibleGroup containing "bastions"), gets its external IP, and sets ProxyJump for all non-bastion hosts.

## Key Conventions

- **No pip dependencies** — everything uses stdlib (`urllib.request`, `json`, `time`)
- **API keys** — always prefixed `trk_`, validated in client constructor
- **Topology-driven** — all VM metadata (IPs, groups, credentials) comes from `project.topology` JSONB
- **Bastion required** — inventory plugin expects exactly one VM with `bastions` in AnsibleGroup tags
- **Main Troshka repo** — `~/troshka/` has the backend API and troshkad agent code

## Related

The Troshka backend exec API (`POST /projects/{project_id}/vms/{vm_id}/exec`) runs commands on VMs via SSH (preferred) or serial console (fallback). This is the transport for the connection plugin.
