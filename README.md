# AgnosticD Cloud Provider: Troshka

An Ansible collection that lets agnosticd-v2 deploy lab environments from pre-built Troshka patterns instead of provisioning from scratch.

## Why Troshka?

The current agnosticd model builds every lab environment from the ground up: provision cloud VMs, install an OS, deploy OpenShift, configure operators, set up the lab. This works, but it takes 45-90 minutes per environment and exercises a long chain of infrastructure that can fail at any step.

Troshka takes a different approach. A lab author builds the environment once — manually or via automation — and captures it as a **pattern** (a snapshot of the entire topology: VMs, disks, networks, configuration). When a student orders the lab, Troshka deploys that pattern in seconds by restoring the snapshot onto nested VMs. The cluster comes up pre-installed, pre-configured, and ready to use.

### What changes for lab authors

- **Build once, deploy many.** Create your lab environment however you like — manually through the Troshka UI, or via agnosticd in template mode. Once it works, capture it as a pattern. Every student gets an identical copy.

- **Faster iteration.** Testing a lab change means modifying the pattern and redeploying, not waiting for a full OCP install cycle. Pattern deploys take 1-2 minutes instead of 45-90.

- **Same agnosticv workflow.** Catalog items still live in agnosticv. You set `cloud_provider: troshka` and `troshka_pattern_name` instead of EC2 instance types. Babylon, AAP2, and the catalog experience are unchanged.

- **Workloads still work.** If your lab needs dynamic configuration at deploy time (per-student credentials, operator installs), you can deploy a base OCP pattern and overlay agnosticd workloads on top — same as today, just faster because the cluster is already running.

### What changes for students

- **No SSH access.** Students interact with their environment through a **web portal** (topology view with VNC console access) and **Showroom** (the existing lab guide UI). This is more secure and closer to how they'd interact with real infrastructure.

- **Faster startup.** Environments are ready in minutes, not an hour.

### What changes for operations

- **Fewer failure modes.** Pattern deployment doesn't depend on AMI availability, CloudFormation capacity, package repository health, or OCP installer versions. The pattern contains everything.

- **Simpler credentials.** Each Troshka instance manages its own cloud credentials internally. Agnosticv only needs a Troshka API key — no AWS access keys, no pull secrets for pattern-based deploys.

- **Full lifecycle.** Start, stop, status, and destroy work through the same agnosticd lifecycle hooks, driven by simple API calls instead of cloud provider orchestration.

### Three deployment modes

| Mode | agnosticv setting | Use case |
|------|------------------|----------|
| **Pattern** | `troshka_deploy_mode: pattern` | Production labs — deploy a pre-built golden image |
| **Pattern + Workloads** | `troshka_deploy_mode: pattern_workloads` | Labs that need dynamic post-deploy configuration |
| **Template** | `troshka_deploy_mode: template` | Build new patterns — deploy fresh OCP, configure, capture (dev only) |

## Collection Contents

### Roles

| Role | Purpose |
|------|---------|
| `deploy` | Deploy a pattern or template, poll until active, create portal token |
| `destroy` | Delete the Troshka project |
| `lifecycle` | Start / stop / status via the `ACTION` variable |
| `capture` | Capture a running project as a reusable pattern |
| `create_inventory` | Build Ansible inventory from topology AnsibleGroup tags |
| `portal_token` | Generate a student portal access token |

### Plugins

| Plugin | Purpose |
|--------|---------|
| `inventory/troshka` | Dynamic inventory plugin for SSH access to deployed VMs |
| `module_utils/troshka_api` | Shared HTTP client for the Troshka API |

## Quick Start

### agnosticv catalog item (mode 1 — pattern deploy)

```yaml
# troshka/my_ocp_lab/common.yaml
cloud_provider: troshka
troshka_deploy_mode: pattern
troshka_pattern_name: "OCP 4.16 Networking Lab"
troshka_portal_access_level: console

#include /includes/secrets/troshka-prod.yaml
```

### Test locally

```bash
# Deploy a pattern
./scripts/test-agnosticd-flow.sh --pattern-name "My Pattern"

# Lifecycle (use the GUID from deploy output)
./scripts/test-agnosticd-flow.sh --status --guid test-1234567890
./scripts/test-agnosticd-flow.sh --stop --guid test-1234567890
./scripts/test-agnosticd-flow.sh --start --guid test-1234567890
./scripts/test-agnosticd-flow.sh --destroy --guid test-1234567890
```

### Required variables

| Variable | Description |
|----------|-------------|
| `troshka_api_url` | Troshka API base URL |
| `troshka_api_key` | API key (`trk_...`) |
| `troshka_pattern_name` | Pattern name to deploy (or `troshka_pattern_id`) |
| `troshka_deploy_mode` | `pattern` (default), `pattern_workloads`, or `template` |

See `roles/deploy/defaults/main.yml` for all available options.
