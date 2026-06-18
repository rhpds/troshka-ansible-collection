#!/usr/bin/python
"""Troshka API module — single module for all Troshka API operations."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: troshka_api
short_description: Interact with the Troshka API
description:
  - Perform operations against the Troshka API including deploy, destroy,
    start, stop, capture patterns, check VM readiness, and more.
options:
  api_url:
    description: Troshka API base URL
    required: true
    type: str
  api_key:
    description: Troshka API key (trk_...)
    required: true
    type: str
    no_log: true
  action:
    description: The API action to perform
    required: true
    type: str
    choices:
      - deploy_pattern
      - deploy_template
      - trigger_deploy
      - get_project
      - delete_project
      - start_project
      - stop_project
      - deploy_progress
      - create_portal_token
      - capture_pattern
      - get_pattern
      - vm_ready
      - get_topology
  project_id:
    description: Project ID (required for most actions)
    type: str
  pattern_name:
    description: Pattern name for deploy_pattern
    type: str
  pattern_id:
    description: Pattern ID for deploy_pattern (overrides name lookup)
    type: str
  template_yaml:
    description: Template YAML dict for deploy_template
    type: dict
  project_name:
    description: Name for new project
    type: str
  common_password:
    description: Common password for the project
    type: str
    no_log: true
  ssh_pub_key:
    description: SSH public key to inject into bastion
    type: str
  auto_install_ocp:
    description: Whether to auto-install OCP via cloud-init
    type: bool
    default: true
  deploy_mode:
    description: Deploy mode (pattern, pattern_workloads, template)
    type: str
  portal_access_level:
    description: Portal access level
    type: str
    default: console
  capture_name:
    description: Name for captured pattern
    type: str
  capture_visibility:
    description: Pattern visibility
    type: str
    default: private
  vm_id:
    description: VM node ID for vm_ready
    type: str
  wait:
    description: Wait for operation to complete
    type: bool
    default: false
  wait_timeout:
    description: Wait timeout in seconds
    type: int
    default: 3600
  wait_interval:
    description: Wait poll interval in seconds
    type: int
    default: 15
"""

RETURN = """
result:
  description: API response data
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            action=dict(
                type="str",
                required=True,
                choices=[
                    "deploy_pattern",
                    "deploy_template",
                    "trigger_deploy",
                    "get_project",
                    "delete_project",
                    "start_project",
                    "stop_project",
                    "deploy_progress",
                    "create_portal_token",
                    "capture_pattern",
                    "get_pattern",
                    "vm_ready",
                    "get_topology",
                ],
            ),
            project_id=dict(type="str"),
            pattern_name=dict(type="str"),
            pattern_id=dict(type="str"),
            template_yaml=dict(type="dict"),
            project_name=dict(type="str"),
            common_password=dict(type="str", no_log=True),
            ssh_pub_key=dict(type="str"),
            auto_install_ocp=dict(type="bool", default=True),
            deploy_mode=dict(type="str"),
            portal_access_level=dict(type="str", default="console"),
            capture_name=dict(type="str"),
            capture_visibility=dict(type="str", default="private"),
            vm_id=dict(type="str"),
            wait=dict(type="bool", default=False),
            wait_timeout=dict(type="int", default=3600),
            wait_interval=dict(type="int", default=15),
        ),
        supports_check_mode=False,
    )

    from ansible_collections.agnosticd.cloud_provider_troshka.plugins.module_utils.troshka_api import (
        TroshkaAPI,
        TroshkaAPIError,
    )

    p = module.params
    try:
        api = TroshkaAPI(p["api_url"], p["api_key"])
    except TroshkaAPIError as e:
        module.fail_json(msg=f"Failed to create API client: {e}")

    action = p["action"]
    result = {"changed": False}

    try:
        if action == "deploy_pattern":
            pattern_id = p.get("pattern_id")
            if not pattern_id:
                name = p.get("pattern_name")
                if not name:
                    module.fail_json(msg="pattern_name or pattern_id required")
                patterns = api.list_patterns(name=name)
                if not patterns:
                    module.fail_json(msg=f"Pattern '{name}' not found")
                pattern_id = patterns[0]["id"]

            resp = api.deploy_pattern(
                pattern_id,
                name=p.get("project_name") or p.get("pattern_name", ""),
            )
            result["changed"] = True
            result["project_id"] = resp["id"]
            result["result"] = resp

        elif action == "deploy_template":
            tmpl = p.get("template_yaml")
            if not tmpl:
                module.fail_json(msg="template_yaml required")
            body = {
                "template_yaml": tmpl,
                "name": p.get("project_name", ""),
            }
            if p.get("common_password"):
                body["common_password"] = p["common_password"]
            if p.get("auto_install_ocp") is not None:
                body["auto_install_ocp"] = p["auto_install_ocp"]
            if p.get("ssh_pub_key"):
                body["ssh_pub_key"] = p["ssh_pub_key"]

            resp = api._request("POST", "/api/v1/projects/from-template", body)
            result["changed"] = True
            result["project_id"] = resp["id"]
            result["result"] = resp

        elif action == "trigger_deploy":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            api._request("POST", f"/api/v1/projects/{pid}/deploy", {})
            result["changed"] = True

        elif action == "get_project":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            result["result"] = api.get_project(pid)

        elif action == "get_topology":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            proj = api.get_project(pid)
            result["result"] = proj.get("topology", {})

        elif action == "delete_project":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            api.delete_project(pid)
            result["changed"] = True

        elif action == "start_project":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            api.start_project(pid)
            result["changed"] = True

        elif action == "stop_project":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            api.stop_project(pid)
            result["changed"] = True

        elif action == "deploy_progress":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            resp = api.get_deploy_progress(pid)
            result["result"] = resp

            if p.get("wait"):
                resp = api.wait_for_project_state(
                    pid,
                    target_states=["active", "error"],
                    timeout=p["wait_timeout"],
                    poll_interval=p["wait_interval"],
                )
                result["result"] = resp
                if resp.get("state") == "error":
                    module.fail_json(
                        msg=f"Deploy failed: {resp.get('deploy_error', 'unknown')}",
                        **result,
                    )

        elif action == "create_portal_token":
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required")
            resp = api.create_portal_token(pid, p.get("portal_access_level", "console"))
            result["result"] = resp

        elif action == "capture_pattern":
            pid = p.get("project_id")
            name = p.get("capture_name")
            if not pid or not name:
                module.fail_json(msg="project_id and capture_name required")
            resp = api.capture_pattern(
                name, pid, p.get("capture_visibility", "private")
            )
            result["changed"] = True
            result["pattern_id"] = resp["id"]
            result["result"] = resp

            if p.get("wait"):
                resp = api.wait_for_pattern_state(
                    resp["id"],
                    target_states=["available", "error"],
                    timeout=p["wait_timeout"],
                    poll_interval=p["wait_interval"],
                )
                result["result"] = resp
                if resp.get("state") == "error":
                    module.fail_json(msg="Pattern capture failed", **result)

        elif action == "get_pattern":
            pid = p.get("pattern_id")
            if not pid:
                module.fail_json(msg="pattern_id required")
            result["result"] = api.get_pattern(pid)

        elif action == "vm_ready":
            pid = p.get("project_id")
            vm_id = p.get("vm_id")
            if not pid or not vm_id:
                module.fail_json(msg="project_id and vm_id required")
            resp = api._request("GET", f"/api/v1/projects/{pid}/vms/{vm_id}/ready")
            result["ready"] = resp.get("ready", False)
            result["result"] = resp

    except TroshkaAPIError as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
