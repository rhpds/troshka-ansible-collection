#!/usr/bin/python
"""Get Troshka pattern information."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: pattern_info
short_description: Get Troshka pattern details
description:
  - Get pattern state by ID, or list/search patterns by name.
  - Use with until/retries/delay to poll capture completion.
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
  pattern_id:
    description: Pattern ID to get details for
    type: str
  name:
    description: Search patterns by name
    type: str
"""

RETURN = r"""
state:
  description: Pattern state
  type: str
  returned: when pattern_id provided
pattern_id:
  description: Pattern ID
  type: str
  returned: always
patterns:
  description: List of matching patterns (when searching by name)
  type: list
  returned: when name provided
"""

from ansible.module_utils.basic import AnsibleModule  # noqa: E402


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(type="str", required=True),
            api_key=dict(type="str", required=True, no_log=True),
            pattern_id=dict(type="str"),
            name=dict(type="str"),
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

        if p.get("pattern_id"):
            pattern = api.get_pattern(p["pattern_id"])
            module.exit_json(
                changed=False,
                state=pattern.get("state", ""),
                pattern_id=p["pattern_id"],
                name=pattern.get("name", ""),
            )
        elif p.get("name"):
            patterns = api.list_patterns(name=p["name"])
            module.exit_json(changed=False, patterns=patterns)
        else:
            patterns = api.list_patterns()
            module.exit_json(changed=False, patterns=patterns)

    except TroshkaAPIError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
