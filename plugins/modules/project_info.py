#!/usr/bin/python
"""Get Troshka project information."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: project_info
short_description: Get Troshka project details
description:
  - Retrieve project state, topology, OCP status, and deploy progress.
  - Use with until/retries/delay for polling deploy or OCP readiness.
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
  project_id:
    description: Project ID
    required: true
    type: str
"""

RETURN = r"""
state:
  description: Project state (draft, deploying, active, stopped, error)
  type: str
  returned: always
name:
  description: Project name
  type: str
  returned: always
ocp_status:
  description: OCP install status
  type: str
  returned: when available
topology:
  description: Full project topology JSONB (design-time)
  type: dict
  returned: always
deployed_topology:
  description: Deployed topology JSONB with runtime data (domainUuid, etc.)
  type: dict
  returned: when available
deploy_error:
  description: Deploy error message
  type: str
  returned: when state=error
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            project_id=dict(type="str"),
            guid=dict(type="str"),
        ),
        supports_check_mode=True,
    )

    from ansible_collections.troshka.cloud.plugins.module_utils.troshka_api import (
        TroshkaAPI,
        TroshkaAPIError,
    )

    p = module.params
    try:
        api = TroshkaAPI(p["api_url"], p["api_key"])

        if p.get("project_id"):
            proj = api.get_project(p["project_id"])
        elif p.get("guid"):
            from urllib.parse import urlencode

            projects = api._request(
                "GET", f"/api/v1/projects/?{urlencode({'guid': p['guid']})}"
            )
            if not projects:
                module.exit_json(changed=False, found=False, state="", project_id="")
                return
            proj = projects[0]
        else:
            module.fail_json(msg="project_id or guid required")
            return
    except TroshkaAPIError as e:
        module.fail_json(msg=str(e))

    module.exit_json(
        changed=False,
        found=True,
        state=proj.get("state", ""),
        name=proj.get("name", ""),
        ocp_status=proj.get("ocp_status", ""),
        topology=proj.get("topology", {}),
        deployed_topology=proj.get("deployed_topology", {}),
        deploy_error=proj.get("deploy_error", ""),
        project_id=proj.get("id", p.get("project_id", "")),
    )


if __name__ == "__main__":
    main()
