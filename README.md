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
| `troshka_showroom_content_repo` | Optional git URL to override baked showroom content on pattern deploy |
| `troshka_showroom_content_ref` | Optional git tag/branch/commit for showroom Antora build |
| `troshka_showroom_build_content` | Optional bool; when repo/ref overrides are set, Troshka defaults this to true |

### Showroom content on pattern deploy

Patterns capture baked showroom HTML (`build_content: false`). To ship a newer workshop doc tag without re-capturing the pattern, pass showroom overrides (maps to `POST /patterns/{id}/deploy` `showroom`):

```yaml
troshka_showroom_content_ref: "{{ showroom_content_ref | default('v0.0.2') }}"
# troshka_showroom_content_repo: "https://github.com/org/other-repo.git"
```

Or call `troshka.cloud.project_deploy` directly:

```yaml
- troshka.cloud.project_deploy:
    api_url: "{{ troshka_api_url }}"
    api_key: "{{ troshka_api_key }}"
    source: pattern
    pattern_name: "Network Automation Workshop"
    name: "{{ guid }}"
    showroom:
      content_ref: "v0.0.2"
```

### Deploy modes

| Mode | Setting | Use case |
|------|---------|----------|
| Pattern | `troshka_deploy_mode: pattern` | Deploy a pre-built golden image |
| Pattern + Workloads | `troshka_deploy_mode: pattern_workloads` | Deploy base image, then run agnosticd workloads |
| Template | `troshka_deploy_mode: template` | Build new patterns from OCP templates (dev only) |

See `roles/deploy/defaults/main.yml` for all available options.

### agnosticd-v2 today

`agnosticd-v2` still includes `agnosticd.cloud_provider_troshka.deploy` by default (`infrastructure_deployment.yml`). That role now supports the same `troshka_showroom_*` variables (update your installed collection from this repo or reinstall after publish). Longer term, switch the include to `troshka.cloud.deploy` once this collection ships the role.
