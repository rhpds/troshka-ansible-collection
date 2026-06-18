#!/usr/bin/python
"""Create Troshka portal access tokens."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: portal_token
short_description: Create Troshka portal access token
description:
  - Generate a portal URL for browser-based project access.
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
  access_level:
    description: Access level for the portal
    type: str
    default: console
    choices: [console, readonly, full]
"""

RETURN = r"""
portal_url:
  description: Portal URL for browser access
  type: str
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            project_id=dict(type="str", required=True),
            access_level=dict(
                type="str", default="console", choices=["console", "readonly", "full"]
            ),
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
        resp = api.create_portal_token(p["project_id"], p["access_level"])
    except TroshkaAPIError as e:
        module.fail_json(msg=str(e))

    module.exit_json(
        changed=False,
        portal_url=resp.get("portal_url", ""),
    )


if __name__ == "__main__":
    main()
