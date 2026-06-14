"""
Troshka dynamic inventory plugin for Ansible.

Builds inventory from a Troshka project's topology, grouping hosts by AnsibleGroup tags.
"""

from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError
from ansible_collections.agnosticd.cloud_provider_troshka.plugins.module_utils.troshka_api import (
    TroshkaAPI,
    TroshkaAPIError
)


DOCUMENTATION = """
    name: troshka
    plugin_type: inventory
    short_description: Troshka dynamic inventory
    description:
        - Builds inventory from a Troshka project's topology
        - Groups hosts by AnsibleGroup tags on VM nodes
        - Automatically configures ProxyJump through bastion host
    options:
        api_url:
            description: Troshka API base URL
            required: true
            type: str
        api_key:
            description: Troshka API key (trk_...)
            required: true
            type: str
        project_id:
            description: Troshka project ID
            required: true
            type: str
"""


class InventoryModule(BaseInventoryPlugin):
    """Troshka dynamic inventory plugin."""

    NAME = 'agnosticd.cloud_provider_troshka.troshka'

    def verify_file(self, path):
        """
        Verify that the inventory file is valid for this plugin.
        Accept .troshka.yml or .troshka.yaml files.
        """
        if super(InventoryModule, self).verify_file(path):
            return path.endswith(('.troshka.yml', '.troshka.yaml'))
        return False

    def parse(self, inventory, loader, path, cache=True):
        """Parse the inventory file and populate the inventory."""
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        # Read configuration from inventory file
        self._read_config_data(path)

        try:
            api_url = self.get_option('api_url')
            api_key = self.get_option('api_key')
            project_id = self.get_option('project_id')
        except Exception as e:
            raise AnsibleError(f"Missing required configuration: {e}")

        # Create API client
        try:
            api = TroshkaAPI(api_url, api_key)
        except TroshkaAPIError as e:
            raise AnsibleError(f"Failed to create Troshka API client: {e}")

        # Fetch project
        try:
            project = api.get_project(project_id)
        except TroshkaAPIError as e:
            raise AnsibleError(f"Failed to fetch project {project_id}: {e}")

        if not project:
            raise AnsibleError(f"Project {project_id} not found")

        topology = project.get('topology', {})
        if not topology:
            raise AnsibleError(f"Project {project_id} has no topology")

        nodes = topology.get('nodes', [])
        external_ips = topology.get('externalIps', [])

        # Find bastion VM and its external IP
        bastion_node = None
        bastion_external_ip = None

        for node in nodes:
            if node.get('type') != 'vmNode':
                continue

            data = node.get('data', {})
            tags = data.get('tags', {})
            ansible_groups = tags.get('AnsibleGroup', '')

            # Check if this VM is in the bastions group
            if 'bastions' in [g.strip() for g in ansible_groups.split(',') if g.strip()]:
                bastion_node = node
                bastion_vm_id = node.get('id')

                # Look for external IP in externalIps array
                for eip in external_ips:
                    if eip.get('vmId') == bastion_vm_id:
                        bastion_external_ip = eip.get('ip')
                        break

                # If not in externalIps, check portForwards in node data
                if not bastion_external_ip:
                    port_forwards = data.get('portForwards', [])
                    for pf in port_forwards:
                        if pf.get('externalIp'):
                            bastion_external_ip = pf['externalIp']
                            break

                break

        if not bastion_node:
            raise AnsibleError("No bastion host found in topology (no VM with 'bastions' in AnsibleGroup)")

        if not bastion_external_ip:
            raise AnsibleError(f"Bastion VM {bastion_node.get('id')} has no external IP")

        bastion_hostname = bastion_node.get('data', {}).get('name', 'bastion')

        # Process all VM nodes
        for node in nodes:
            if node.get('type') != 'vmNode':
                continue

            data = node.get('data', {})
            vm_name = data.get('name')
            vm_id = node.get('id')

            if not vm_name:
                continue

            tags = data.get('tags', {})
            ansible_groups = tags.get('AnsibleGroup', '')

            # Parse comma-separated groups
            groups = [g.strip() for g in ansible_groups.split(',') if g.strip()]

            if not groups:
                # Skip VMs without AnsibleGroup tags
                continue

            # Get VM's internal IP from first NIC
            nics = data.get('nics', [])
            if not nics:
                raise AnsibleError(f"VM {vm_name} has no NICs")

            vm_ip = nics[0].get('ip')
            if not vm_ip:
                raise AnsibleError(f"VM {vm_name} first NIC has no IP")

            # Add host to inventory
            self.inventory.add_host(vm_name)

            # Add to groups
            for group in groups:
                self.inventory.add_group(group)
                self.inventory.add_child(group, vm_name)

            # Set host variables
            self.inventory.set_variable(vm_name, 'troshka_vm_id', vm_id)
            self.inventory.set_variable(vm_name, 'troshka_vm_name', vm_name)

            # Configure connection
            if vm_name == bastion_hostname:
                # Bastion: use external IP
                self.inventory.set_variable(vm_name, 'ansible_host', bastion_external_ip)
            else:
                # Non-bastion: use internal IP with ProxyJump through bastion
                self.inventory.set_variable(vm_name, 'ansible_host', vm_ip)
                self.inventory.set_variable(
                    vm_name,
                    'ansible_ssh_common_args',
                    f'-o ProxyJump={bastion_external_ip}'
                )
