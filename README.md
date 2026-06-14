# AgnosticD Cloud Provider: Troshka

Ansible collection for deploying Troshka patterns and templates via agnosticd-v2.

## Roles

- **deploy** — Deploy a pattern or template to a Troshka project
- **destroy** — Delete a Troshka project
- **lifecycle** — Start/stop/status operations
- **capture** — Capture a project as a reusable pattern
- **create_inventory** — Build Ansible inventory from topology tags
- **portal_token** — Create a student portal access token

## Plugins

- **inventory/troshka** — Dynamic inventory plugin for SSH access to deployed VMs
