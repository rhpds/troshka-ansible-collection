"""
Troshka API client for Ansible collection.

This module provides a shared API client class that uses only urllib.request
(no external dependencies) to communicate with the Troshka API.
"""

import json
import os
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse


class TroshkaAPIError(Exception):
    """Exception raised for Troshka API errors."""

    pass


class TroshkaAPI:
    """
    Client for the Troshka API.

    Args:
        api_url: Base URL for the Troshka API (e.g., "https://troshka.example.com")
        api_key: API key starting with "trk_"
    """

    def __init__(self, api_url, api_key):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

        if not api_key.startswith("trk_"):
            raise TroshkaAPIError("API key must start with 'trk_'")

    def _request(self, method, path, body=None):
        """
        Make an HTTP request to the Troshka API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            path: API path starting with / (e.g., "/api/v1/patterns/")
            body: Optional dict to send as JSON body

        Returns:
            Parsed JSON response

        Raises:
            TroshkaAPIError: On HTTP errors or invalid responses
        """
        url = self.api_url + path
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as response:
                response_text = response.read().decode("utf-8")
                if response_text:
                    return json.loads(response_text)
                return None
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
                error_data = json.loads(error_body)
                error_msg = error_data.get("detail", error_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                error_msg = error_body if error_body else str(e)

            raise TroshkaAPIError(
                f"HTTP {e.code} {e.reason} for {method} {path}: {error_msg}"
            )
        except urllib.error.URLError as e:
            raise TroshkaAPIError(f"Failed to connect to {url}: {e.reason}")
        except json.JSONDecodeError as e:
            raise TroshkaAPIError(f"Invalid JSON response from {path}: {e}")

    def list_patterns(self, name=None):
        """
        List patterns, optionally filtered by name.

        Args:
            name: Optional pattern name filter

        Returns:
            List of pattern dicts
        """
        path = "/api/v1/patterns/"
        if name:
            path += f"?name={urllib.parse.quote(name)}"
        return self._request("GET", path)

    def deploy_pattern(
        self,
        pattern_id,
        name=None,
        inject_vars=None,
        auto_deploy=True,
        auto_start=True,
        guid=None,
    ):
        """
        Deploy a pattern to create a new project.

        Args:
            pattern_id: ID of the pattern to deploy
            name: Optional project name (auto-generated if not provided)
            inject_vars: Optional dict of variables to inject into topology
            auto_deploy: Whether to auto-deploy (default: True)
            auto_start: Whether to auto-start VMs (default: True)
            guid: Optional GUID for the project

        Returns:
            Project dict with keys: id, name, state, topology
        """
        body = {"auto_deploy": auto_deploy, "auto_start": auto_start}
        if name:
            body["name"] = name
        if inject_vars:
            body["inject_vars"] = inject_vars
        if guid:
            body["guid"] = guid

        return self._request("POST", f"/api/v1/patterns/{pattern_id}/deploy", body)

    def deploy_template(
        self,
        template,
        version,
        name,
        overrides=None,
        auto_deploy=False,
        auto_start=True,
    ):
        """
        Deploy a topology template.

        Args:
            template: Template name (e.g., "ocp-ipi")
            version: Template version (e.g., "4.15")
            name: Project name
            overrides: Optional dict of template overrides
            auto_deploy: Whether to auto-deploy (default: False)
            auto_start: Whether to auto-start VMs (default: True)

        Returns:
            Project dict with keys: id, name, state, topology
        """
        body = {
            "template": template,
            "version": version,
            "name": name,
            "auto_deploy": auto_deploy,
            "auto_start": auto_start,
        }
        if overrides:
            body["overrides"] = overrides

        return self._request("POST", "/api/v1/deploy-template", body)

    def get_project(self, project_id):
        """
        Get project details.

        Args:
            project_id: Project ID

        Returns:
            Project dict
        """
        return self._request("GET", f"/api/v1/projects/{project_id}")

    def delete_project(self, project_id):
        """
        Delete a project.

        Args:
            project_id: Project ID

        Returns:
            Response dict
        """
        return self._request("DELETE", f"/api/v1/projects/{project_id}")

    def start_project(self, project_id):
        """
        Start all VMs in a project.

        Args:
            project_id: Project ID

        Returns:
            Response dict
        """
        return self._request("POST", f"/api/v1/projects/{project_id}/start")

    def stop_project(self, project_id):
        """
        Stop all VMs in a project.

        Args:
            project_id: Project ID

        Returns:
            Response dict
        """
        return self._request("POST", f"/api/v1/projects/{project_id}/stop")

    def get_deploy_progress(self, project_id):
        """
        Get deployment progress for a project.

        Args:
            project_id: Project ID

        Returns:
            Progress dict with keys: phase, message, detail, etc.
        """
        return self._request("GET", f"/api/v1/projects/{project_id}/deploy-progress")

    def create_portal_token(self, project_id, access_level="console"):
        """
        Create a portal access token for a project.

        Args:
            project_id: Project ID
            access_level: Access level ("console" or "full")

        Returns:
            Dict with keys: token, access_level, portal_url
        """
        body = {"access_level": access_level}
        return self._request(
            "POST", f"/api/v1/projects/{project_id}/portal-token", body
        )

    def capture_pattern(self, name, source_project_id, visibility="private"):
        """
        Capture a pattern from an existing project.

        Args:
            name: Pattern name
            source_project_id: Source project ID to capture from
            visibility: Pattern visibility ("private" or "public")

        Returns:
            Pattern dict with state="capturing"
        """
        body = {
            "name": name,
            "source_project_id": source_project_id,
            "visibility": visibility,
        }
        return self._request("POST", "/api/v1/patterns/", body)

    def get_pattern(self, pattern_id):
        """
        Get pattern details.

        Args:
            pattern_id: Pattern ID

        Returns:
            Pattern dict
        """
        return self._request("GET", f"/api/v1/patterns/{pattern_id}")

    def wait_for_project_state(
        self, project_id, target_states, timeout=600, poll_interval=10
    ):
        """
        Poll project until it reaches one of the target states.

        Args:
            project_id: Project ID
            target_states: List of acceptable states (e.g., ["active", "error"])
            timeout: Max seconds to wait (default: 600)
            poll_interval: Seconds between polls (default: 10)

        Returns:
            Project dict

        Raises:
            TroshkaAPIError: On timeout
        """
        start_time = time.time()

        while True:
            project = self.get_project(project_id) or {}
            current_state = project.get("state")

            if current_state in target_states:
                return project

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TroshkaAPIError(
                    f"Timeout waiting for project {project_id} to reach states {target_states}. "
                    f"Current state: {current_state} after {int(elapsed)}s"
                )

            time.sleep(poll_interval)

    def wait_for_pattern_state(
        self, pattern_id, target_states, timeout=1800, poll_interval=15
    ):
        """
        Poll pattern until it reaches one of the target states.

        Args:
            pattern_id: Pattern ID
            target_states: List of acceptable states (e.g., ["available", "error"])
            timeout: Max seconds to wait (default: 1800)
            poll_interval: Seconds between polls (default: 15)

        Returns:
            Pattern dict

        Raises:
            TroshkaAPIError: On timeout
        """
        start_time = time.time()

        while True:
            pattern = self.get_pattern(pattern_id) or {}
            current_state = pattern.get("state")

            if current_state in target_states:
                return pattern

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TroshkaAPIError(
                    f"Timeout waiting for pattern {pattern_id} to reach states {target_states}. "
                    f"Current state: {current_state} after {int(elapsed)}s"
                )

            time.sleep(poll_interval)

    def exec_command(
        self,
        project_id,
        vm_id,
        command,
        username="cloud-user",
        password="",
        timeout=30,
        use_ssh=True,
    ):
        """Execute a command on a VM.

        Returns:
            Dict with keys: output, error, exit_code
        """
        body = {
            "command": command,
            "username": username,
            "timeout": timeout,
            "use_ssh": use_ssh,
        }
        if password:
            body["password"] = password
        return self._request(
            "POST", f"/api/v1/projects/{project_id}/vms/{vm_id}/exec", body
        )

    def upload_file(
        self,
        project_id,
        vm_id,
        local_path,
        remote_path,
        username="cloud-user",
        password="",
        mode="0644",
    ):
        """Upload a file to a VM via multipart upload.

        Returns:
            Dict with keys: size, remote_path
        """
        with open(local_path, "rb") as f:
            file_data = f.read()

        boundary = uuid.uuid4().hex
        filename = os.path.basename(local_path)

        qs = urllib.parse.urlencode(
            {
                "remote_path": remote_path,
                "mode": mode,
                "username": username,
                **({"password": password} if password else {}),
            }
        )
        url = f"{self.api_url}/api/v1/projects/{project_id}/vms/{vm_id}/files?{qs}"

        body_parts = []
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode()
        )
        body_parts.append(b"Content-Type: application/octet-stream")
        body_parts.append(b"")
        body_parts.append(file_data)
        body_parts.append(f"--{boundary}--".encode())
        body = b"\r\n".join(body_parts)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="PUT")

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            try:
                error_msg = json.loads(error_body).get("detail", error_body)
            except (json.JSONDecodeError, ValueError):
                error_msg = error_body
            raise TroshkaAPIError(f"File upload failed (HTTP {e.code}): {error_msg}")
        except urllib.error.URLError as e:
            raise TroshkaAPIError(f"Failed to connect for file upload: {e.reason}")

    def download_file(
        self,
        project_id,
        vm_id,
        remote_path,
        local_path,
        username="cloud-user",
        password="",
    ):
        """Download a file from a VM to a local path.

        Returns:
            Dict with keys: size, local_path
        """
        qs = urllib.parse.urlencode(
            {
                "remote_path": remote_path,
                "username": username,
                **({"password": password} if password else {}),
            }
        )
        url = f"{self.api_url}/api/v1/projects/{project_id}/vms/{vm_id}/files?{qs}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/octet-stream",
        }

        req = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req) as response:
                data = response.read()
                with open(local_path, "wb") as f:
                    f.write(data)
                return {"size": len(data), "local_path": local_path}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            try:
                error_msg = json.loads(error_body).get("detail", error_body)
            except (json.JSONDecodeError, ValueError):
                error_msg = error_body
            raise TroshkaAPIError(f"File download failed (HTTP {e.code}): {error_msg}")
        except urllib.error.URLError as e:
            raise TroshkaAPIError(f"Failed to connect for file download: {e.reason}")
