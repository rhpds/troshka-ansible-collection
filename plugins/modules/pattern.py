#!/usr/bin/python
"""Manage Troshka patterns — capture or delete."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: pattern
short_description: Manage Troshka patterns
description:
  - Capture a pattern from a project or delete an existing pattern.
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
    choices: [present, absent]
    default: present
  name:
    description: Pattern name (for capture)
    type: str
  source_project_id:
    description: Project to capture from (for state=present)
    type: str
  visibility:
    description: Pattern visibility
    type: str
    default: private
    choices: [private, public]
  pattern_id:
    description: Pattern ID (for state=absent)
    type: str
"""

RETURN = r"""
pattern_id:
  description: Pattern ID
  type: str
  returned: when state=present
state:
  description: Pattern state
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            state=dict(type="str", default="present", choices=["present", "absent"]),
            name=dict(type="str"),
            source_project_id=dict(type="str"),
            visibility=dict(
                type="str", default="private", choices=["private", "public"]
            ),
            pattern_id=dict(type="str"),
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
        if p["state"] == "present":
            if not p.get("name") or not p.get("source_project_id"):
                module.fail_json(msg="name and source_project_id required for capture")
            resp = api.capture_pattern(
                p["name"], p["source_project_id"], p["visibility"]
            )
            result["changed"] = True
            result["pattern_id"] = resp["id"]
            result["state"] = resp.get("state", "capturing")
        else:
            pid = p.get("pattern_id")
            if not pid:
                module.fail_json(msg="pattern_id required for state=absent")
            api._request("DELETE", f"/api/v1/patterns/{pid}")
            result["changed"] = True
            result["state"] = "absent"

    except TroshkaAPIError as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
