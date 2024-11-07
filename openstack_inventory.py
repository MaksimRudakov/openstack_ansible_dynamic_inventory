#!/usr/bin/env python3

import json
import os
import argparse
from openstack import connection

class OpenStackInventory(object):
    """
    Dynamic inventory script for OpenStack that supports multiple networks
    and Terraform-style metadata grouping.
    """
    def __init__(self):
        self.inventory = {}
        self.conn = self._get_connection()
        # Define key metadata fields for grouping
        # These fields are expected from Terraform's metadata configuration
        self.important_metadata = [
            'environment',    # e.g., prod, stage, dev
            'project',        # project name
            'service_type',   # e.g., postgres, redis, web
            'role'           # e.g., master, slave, frontend
        ]

    def _get_connection(self):
        """
        Establishes connection to OpenStack using environment variables.
        """
        return connection.Connection(
            auth_url=os.getenv('OS_AUTH_URL'),
            project_name=os.getenv('OS_PROJECT_NAME'),
            username=os.getenv('OS_USERNAME'),
            password=os.getenv('OS_PASSWORD'),
            region_name=os.getenv('OS_REGION_NAME'),
            project_domain_name=os.getenv('OS_PROJECT_DOMAIN_NAME', 'default'),
            user_domain_name=os.getenv('OS_USER_DOMAIN_NAME', 'default')
        )

    def _get_groups(self):
        """
        Initialize the base inventory structure and metadata type groups.
        Creates hierarchy of groups based on metadata types.
        """
        # Initialize basic inventory structure with _meta and all groups
        self.inventory = {
            '_meta': {
                'hostvars': {}
            },
            'all': {
                'hosts': [],
                'vars': {}
            }
        }
        
        # Create base groups for each metadata type
        # These will serve as parent groups for actual metadata values
        for metadata_key in self.important_metadata:
            self.inventory[f'type_{metadata_key}'] = {
                'children': []
            }

    def _add_to_groups(self, server_name, metadata):
        """
        Add server to appropriate groups based on its metadata.
        Creates hierarchical group structure and handles metadata-based grouping.
        
        Args:
            server_name (str): Name of the server with network suffix
            metadata (dict): Server metadata from OpenStack
        """
        for key, value in metadata.items():
            # Create group name based on metadata key-value pair
            tag_group = f"tag_{key}_{value}"
            
            # Initialize group if it doesn't exist
            if tag_group not in self.inventory:
                self.inventory[tag_group] = {
                    'hosts': [],
                    'vars': {
                        f'{key}_value': value
                    }
                }
            
            # Add server to the tag group
            if server_name not in self.inventory[tag_group]['hosts']:
                self.inventory[tag_group]['hosts'].append(server_name)
            
            # Add tag group to its parent metadata type group
            if key in self.important_metadata:
                type_group = f'type_{key}'
                if tag_group not in self.inventory[type_group]['children']:
                    self.inventory[type_group]['children'].append(tag_group)

    def _create_combined_groups(self):
        """
        Create combined groups based on environment and service type.
        This allows for convenient targeting of specific services in specific environments.
        Example: postgres_dwh group contains all postgres servers in dwh environment.
        """
        # Get all environment and service type groups
        env_groups = [g for g in self.inventory.keys() if g.startswith('tag_environment_')]
        service_groups = [g for g in self.inventory.keys() if g.startswith('tag_service_type_')]
        
        # Create combinations of environment and service type
        for env_group in env_groups:
            for service_group in service_groups:
                env_name = env_group.split('_')[-1]
                service_name = service_group.split('_')[-1]
                combined_group = f"{service_name}_{env_name}"
                
                # Initialize combined group
                self.inventory[combined_group] = {
                    'hosts': [],
                    'vars': {}
                }
                
                # Find hosts that belong to both groups
                common_hosts = set(self.inventory[env_group]['hosts']) & \
                            set(self.inventory[service_group]['hosts'])
                if common_hosts:
                    self.inventory[combined_group]['hosts'] = list(common_hosts)

    def _get_hosts(self):
        """
        Retrieve and process all servers from OpenStack.
        Handles multiple networks and metadata grouping.
        """
        servers = self.conn.compute.servers()
        
        for server in servers:
            # Process each network interface of the server
            for network_name, addresses in server.addresses.items():
                for address in addresses:
                    if address['version'] == 4:  # IPv4 only
                        # Create unique host name including network
                        host_name = f"{server.name}_{network_name}"
                        
                        # Collect server information
                        server_vars = {
                            'ansible_host': address['addr'],
                            'openstack_id': server.id,
                            'openstack_name': server.name,
                            'openstack_status': server.status,
                            'network_name': network_name,
                            'network_interfaces': server.addresses
                        }
                        
                        # Process server metadata if available
                        if hasattr(server, 'metadata'):
                            server_vars.update(server.metadata)
                            # Add server to groups based on its metadata
                            self._add_to_groups(host_name, server.metadata)
                        
                        # Store host variables
                        self.inventory['_meta']['hostvars'][host_name] = server_vars

    def json_format_dict(self, data):
        """
        Format inventory data as JSON.
        
        Args:
            data (dict): Inventory data
        Returns:
            str: JSON formatted string
        """
        return json.dumps(data, sort_keys=True, indent=2)

    def get_inventory(self):
        """
        Build and return the complete inventory.
        """
        self._get_groups()
        self._get_hosts()
        self._create_combined_groups()
        return self.json_format_dict(self.inventory)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', action='store')
    args = parser.parse_args()

    inventory = OpenStackInventory()
    
    if args.list:
        print(inventory.get_inventory())
    elif args.host:
        # Empty dict as we store host variables in _meta
        print(json.dumps({}))

if __name__ == '__main__':
    main()
