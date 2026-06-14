# AgnosticD Cloud Provider: Troshka

Ansible collection for deploying Troshka patterns and templates via agnosticd-v2.

## Roles

| Role | Purpose |
|------|---------|
| `deploy` | Deploy a pattern or template, poll until active, create portal token |
| `destroy` | Delete the Troshka project |
| `lifecycle` | Start / stop / status via the `ACTION` variable |
| `capture` | Capture a running project as a reusable pattern |
| `create_inventory` | Build Ansible inventory from topology AnsibleGroup tags |
| `portal_token` | Generate a student portal access token |

## Plugins

| Plugin | Purpose |
|--------|---------|
| `inventory/troshka` | Dynamic inventory plugin for SSH access to deployed VMs |
| `module_utils/troshka_api` | Shared HTTP client for the Troshka API |

## Usage

### agnosticv catalog item

```yaml
cloud_provider: troshka
troshka_deploy_mode: pattern
troshka_pattern_name: "OCP 4.16 Networking Lab"
troshka_portal_access_level: console

#include /includes/secrets/troshka-prod.yaml
```

### Required variables

| Variable | Description |
|----------|-------------|
| `troshka_api_url` | Troshka API base URL |
| `troshka_api_key` | API key (`trk_...`) |
| `troshka_pattern_name` | Pattern name to deploy (or `troshka_pattern_id`) |
| `troshka_deploy_mode` | `pattern` (default), `pattern_workloads`, or `template` |

### Deploy modes

| Mode | Setting | Use case |
|------|---------|----------|
| Pattern | `troshka_deploy_mode: pattern` | Deploy a pre-built golden image |
| Pattern + Workloads | `troshka_deploy_mode: pattern_workloads` | Deploy base image, then run agnosticd workloads |
| Template | `troshka_deploy_mode: template` | Build new patterns from OCP templates (dev only) |

See `roles/deploy/defaults/main.yml` for all available options.
