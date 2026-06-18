#!/usr/bin/python
"""Check Troshka VM readiness."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: vm_info
short_description: Check if a Troshka VM is reachable
description:
  - Check if a VM is reachable via the Troshka exec API.
  - Use with until/retries/delay to wait for a VM to boot.
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
  vm_id:
    description: VM node ID
    required: true
    type: str
"""

RETURN = r"""
ready:
  description: Whether the VM is reachable
  type: bool
  returned: always
reason:
  description: Reason if not ready
  type: str
  returned: when not ready
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            project_id=dict(type="str", required=True),
            vm_id=dict(type="str", required=True),
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
        resp = api.vm_ready(p["project_id"], p["vm_id"])
    except TroshkaAPIError as e:
        module.exit_json(changed=False, ready=False, reason=str(e))

    module.exit_json(
        changed=False,
        ready=resp.get("ready", False),
        reason=resp.get("reason", ""),
        vm_id=p["vm_id"],
    )


if __name__ == "__main__":
    main()
