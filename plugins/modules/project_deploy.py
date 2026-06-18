#!/usr/bin/python
"""Trigger deployment on a Troshka project."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: project_deploy
short_description: Deploy a Troshka project
description:
  - Trigger deployment on an existing project, or deploy from a named pattern.
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
    description: Project ID to deploy
    type: str
  source:
    description: Deploy source type
    type: str
    choices: [project, pattern]
    default: project
  pattern_name:
    description: Pattern name (for source=pattern)
    type: str
  pattern_id:
    description: Pattern ID (for source=pattern, overrides name lookup)
    type: str
  name:
    description: Project name when deploying from pattern
    type: str
"""

RETURN = r"""
project_id:
  description: Project ID
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            project_id=dict(type="str"),
            source=dict(type="str", default="project", choices=["project", "pattern"]),
            pattern_name=dict(type="str"),
            pattern_id=dict(type="str"),
            name=dict(type="str"),
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

    result = {"changed": False}

    try:
        if p["source"] == "pattern":
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
                pattern_id, name=p.get("name") or p.get("pattern_name", "")
            )
            result["changed"] = True
            result["project_id"] = resp["id"]
        else:
            pid = p.get("project_id")
            if not pid:
                module.fail_json(msg="project_id required for source=project")
            api.trigger_deploy(pid)
            result["changed"] = True
            result["project_id"] = pid

    except TroshkaAPIError as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
