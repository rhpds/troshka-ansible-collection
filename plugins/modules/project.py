#!/usr/bin/python
"""Manage Troshka projects — create, delete, start, stop."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: project
short_description: Manage Troshka projects
description:
  - Create projects from template YAML, delete, start, or stop projects.
options:
  api_url:
    description: Troshka API base URL
    required: true
    type: str
  api_key:
    description: Troshka API key
    required: true
    type: str
    no_log: true
  state:
    description: Desired state
    type: str
    choices: [present, absent, started, stopped]
    default: present
  project_id:
    description: Project ID (required for absent/started/stopped)
    type: str
  name:
    description: Project name (for creation)
    type: str
  template_yaml:
    description: Template YAML dict for creating from template
    type: dict
  common_password:
    description: Common password for BMC and cloud-user
    type: str
    no_log: true
  ssh_pub_key:
    description: SSH public key to inject into bastion
    type: str
  auto_install_ocp:
    description: Whether to auto-install OCP via cloud-init
    type: bool
    default: true
"""

RETURN = r"""
project_id:
  description: Project ID
  type: str
  returned: when state=present
state:
  description: Project state
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            state=dict(
                type="str",
                default="present",
                choices=["present", "absent", "started", "stopped"],
            ),
            project_id=dict(type="str"),
            name=dict(type="str"),
            template_yaml=dict(type="dict"),
            common_password=dict(type="str", no_log=True),
            ssh_pub_key=dict(type="str"),
            auto_install_ocp=dict(type="bool", default=True),
            guid=dict(type="str"),
        ),
        supports_check_mode=False,
    )

    from ansible_collections.troshka.cloud.plugins.module_utils.troshka_api import (
        TroshkaAPI,
        TroshkaAPIError,
    )

    p = module.params
    try:
        api = TroshkaAPI(p["api_url"], p["api_key"])
    except TroshkaAPIError as e:
        module.fail_json(msg=str(e))

    state = p["state"]
    result = {"changed": False}

    try:
        if state == "present":
            tmpl = p.get("template_yaml")
            if not tmpl:
                module.fail_json(msg="template_yaml required for state=present")
            resp = api.create_from_template(
                tmpl,
                name=p.get("name", ""),
                common_password=p.get("common_password"),
                ssh_pub_key=p.get("ssh_pub_key"),
                auto_install_ocp=p.get("auto_install_ocp"),
            )
            result["changed"] = True
            result["project_id"] = resp["id"]
            result["name"] = resp.get("name", "")
            result["state"] = "draft"

            if p.get("guid"):
                api._request(
                    "PATCH",
                    f"/api/v1/projects/{resp['id']}",
                    {"guid": p["guid"]},
                )

        elif state == "absent":
            if not p.get("project_id"):
                module.fail_json(msg="project_id required for state=absent")
            api.delete_project(p["project_id"])
            result["changed"] = True
            result["state"] = "absent"

        elif state == "started":
            if not p.get("project_id"):
                module.fail_json(msg="project_id required for state=started")
            api.start_project(p["project_id"])
            result["changed"] = True
            result["state"] = "starting"

        elif state == "stopped":
            if not p.get("project_id"):
                module.fail_json(msg="project_id required for state=stopped")
            api.stop_project(p["project_id"])
            result["changed"] = True
            result["state"] = "stopping"

    except TroshkaAPIError as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
