"""
Troshka connection plugin for Ansible.

Executes commands and transfers files on VMs inside Troshka nested
environments via the Troshka API, without requiring direct SSH access
from the Ansible controller.

Usage in inventory::

    bastion:
      ansible_connection: troshka.cloud.troshka
      troshka_api_url: https://troshka.example.com
      troshka_api_key: trk_...
      troshka_project_id: <project-uuid>
      troshka_vm_id: <vm-node-id>
      ansible_user: cloud-user
"""

from __future__ import annotations

import os
import shlex

from ansible.errors import AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()

DOCUMENTATION = """
    name: troshka
    short_description: Execute commands and transfer files via Troshka API
    description:
        - Run commands on VMs inside Troshka nested environments
        - Transfer files using the Troshka file push/pull API
        - No direct SSH from the controller is required
    author: Troshka Team
    options:
        troshka_api_url:
            description: Troshka API base URL
            type: str
            required: true
            vars:
                - name: troshka_api_url
            env:
                - name: TROSHKA_API_URL
        troshka_api_key:
            description: Troshka API key (trk_...)
            type: str
            required: true
            vars:
                - name: troshka_api_key
            env:
                - name: TROSHKA_API_KEY
        troshka_project_id:
            description: Troshka project ID
            type: str
            required: true
            vars:
                - name: troshka_project_id
        troshka_vm_id:
            description: Troshka VM node ID
            type: str
            required: true
            vars:
                - name: troshka_vm_id
        troshka_timeout:
            description: Command execution timeout in seconds
            type: int
            default: 600
            vars:
                - name: troshka_timeout
        private_key_file:
            description: Path to SSH private key file
            type: str
            vars:
                - name: ansible_ssh_private_key_file
                - name: ansible_private_key_file
        remote_password:
            description: SSH password (fallback if no key)
            type: str
            no_log: true
            vars:
                - name: ansible_password
                - name: ansible_ssh_pass
"""


class Connection(ConnectionBase):
    """Troshka API-based connection plugin."""

    transport = "troshka.cloud.troshka"
    has_pipelining = False
    has_tty = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super().__init__(play_context, new_stdin, *args, **kwargs)
        self._api = None

    def _get_api(self):
        if self._api is not None:
            return self._api

        from ansible_collections.troshka.cloud.plugins.module_utils.troshka_api import (
            TroshkaAPI,
            TroshkaAPIError,
        )

        api_url = self.get_option("troshka_api_url")
        api_key = self.get_option("troshka_api_key")

        if not api_url or not api_key:
            raise AnsibleConnectionFailure(
                "troshka_api_url and troshka_api_key are required"
            )

        try:
            self._api = TroshkaAPI(api_url, api_key)
        except TroshkaAPIError as e:
            raise AnsibleConnectionFailure(f"Failed to create Troshka API client: {e}")

        return self._api

    def _connect(self):
        self._get_api()
        self._connected = True
        return self

    def close(self):
        self._connected = False

    def exec_command(self, cmd, in_data=None, sudoable=True):
        super().exec_command(cmd, in_data=in_data, sudoable=sudoable)

        from ansible_collections.troshka.cloud.plugins.module_utils.troshka_api import (
            TroshkaAPIError,
        )

        api = self._get_api()
        project_id = self.get_option("troshka_project_id")
        vm_id = self.get_option("troshka_vm_id")
        username = self._play_context.remote_user or "cloud-user"
        password = (
            self.get_option("remote_password") or self._play_context.password or ""
        )
        timeout = self.get_option("troshka_timeout")

        # Read SSH private key
        private_key = ""
        key_path = (
            self.get_option("private_key_file") or self._play_context.private_key_file
        )
        if key_path:
            try:
                with open(os.path.expanduser(key_path)) as f:
                    private_key = f.read()
                display.vvv(
                    "TROSHKA: using SSH key auth", host=self._play_context.remote_addr
                )
            except (OSError, IOError):
                display.warning(f"Could not read SSH key: {key_path}")

        if sudoable and self._play_context.become:
            become_cmd = self._play_context.become_method or "sudo"
            become_user = self._play_context.become_user or "root"
            if self._play_context.become_pass:
                cmd = f"echo {shlex.quote(self._play_context.become_pass)} | {become_cmd} -S -u {become_user} {cmd}"
            else:
                cmd = f"{become_cmd} -u {become_user} {cmd}"

        log_cmd = (
            cmd
            if not self._play_context.become_pass
            else cmd.split("|", 1)[-1].strip()
            if "|" in cmd
            else cmd
        )
        display.vvv(f"TROSHKA EXEC: {log_cmd}", host=self._play_context.remote_addr)

        try:
            result = api.exec_command(
                project_id,
                vm_id,
                cmd,
                username=username,
                password=password,
                private_key=private_key,
                timeout=timeout,
            )
        except TroshkaAPIError as e:
            raise AnsibleConnectionFailure(
                f"Troshka exec failed (timeout={timeout}s): {e}"
            )

        if result is None:
            raise AnsibleConnectionFailure(
                f"Troshka exec returned empty response (timeout={timeout}s, cmd truncated={log_cmd[:80]})"
            )

        stdout = (result.get("output") or "").encode()
        stderr = (result.get("error") or "").encode()
        exit_code = result.get("exit_code", 0)

        if result.get("timed_out"):
            display.warning(
                f"TROSHKA: command timed out after {timeout}s: {log_cmd[:80]}"
            )

        return exit_code, stdout, stderr

    def put_file(self, in_path, out_path):
        super().put_file(in_path, out_path)

        from ansible_collections.troshka.cloud.plugins.module_utils.troshka_api import (
            TroshkaAPIError,
        )

        if not os.path.exists(in_path):
            raise AnsibleFileNotFound(f"Input path not found: {in_path}")

        api = self._get_api()
        project_id = self.get_option("troshka_project_id")
        vm_id = self.get_option("troshka_vm_id")
        username = self._play_context.remote_user or "cloud-user"
        password = self._play_context.password or ""

        display.vvv(
            f"TROSHKA PUT: {in_path} -> {out_path}",
            host=self._play_context.remote_addr,
        )

        try:
            api.upload_file(
                project_id,
                vm_id,
                in_path,
                out_path,
                username=username,
                password=password,
            )
        except TroshkaAPIError as e:
            raise AnsibleConnectionFailure(f"Troshka file upload failed: {e}")

    def fetch_file(self, in_path, out_path):
        super().fetch_file(in_path, out_path)

        from ansible_collections.troshka.cloud.plugins.module_utils.troshka_api import (
            TroshkaAPIError,
        )

        api = self._get_api()
        project_id = self.get_option("troshka_project_id")
        vm_id = self.get_option("troshka_vm_id")
        username = self._play_context.remote_user or "cloud-user"
        password = self._play_context.password or ""

        display.vvv(
            f"TROSHKA FETCH: {in_path} -> {out_path}",
            host=self._play_context.remote_addr,
        )

        try:
            api.download_file(
                project_id,
                vm_id,
                in_path,
                out_path,
                username=username,
                password=password,
            )
        except TroshkaAPIError as e:
            raise AnsibleConnectionFailure(f"Troshka file download failed: {e}")
