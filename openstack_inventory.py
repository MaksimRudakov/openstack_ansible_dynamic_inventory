#!/usr/bin/env python3

import json
import os
import sys
import argparse
import yaml
from openstack import connection

class OpenStackInventory(object):
    def __init__(self):
        self.inventory = {}
        self.conn = None
        self._load_config()
        self._init_connection()

    def _validate_config(self, config):
        """
        Validate configuration values
        """
        settings = config.get('all', {}).get('vars', {}).get('inventory_settings', {})
        required_fields = ['environment_tag', 'environment_value', 'base_group_name']
        
        for field in required_fields:
            if field not in settings:
                sys.exit(f"Required configuration field missing: {field}")
                
        if 'network_priority' not in settings or not isinstance(settings['network_priority'], list):
            sys.exit("network_priority must be a list of network names")

    def _load_config(self):
        """
        Load configuration from YAML file
        """
        config_path = os.getenv('INVENTORY_CONFIG', 'inventory_config.yaml')
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            sys.exit(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            sys.exit(f"Error parsing configuration file: {e}")

        # Validate configuration
        self._validate_config(config)

        # Get settings from config
        settings = config.get('all', {}).get('vars', {}).get('inventory_settings', {})

        # Load configurations
        self.filter_config = {
            'environment_tag': settings.get('environment_tag', 'environment'),
            'environment_value': settings.get('environment_value', 'dwh'),
            'base_group_name': settings.get('base_group_name', 'dwh')
        }

        self.network_priority = settings.get('network_priority', [
            'internal_cloud_network',
            'PS-Colo-BilimLand2-int'
        ])

    def _init_connection(self):
        """
        Initialize OpenStack connection
        """
        try:
            self.conn = connection.Connection(
                auth_url=os.getenv('OS_AUTH_URL'),
                project_name=os.getenv('OS_PROJECT_NAME'),
                username=os.getenv('OS_USERNAME'),
                password=os.getenv('OS_PASSWORD'),
                region_name=os.getenv('OS_REGION_NAME'),
                project_domain_name=os.getenv('OS_PROJECT_DOMAIN_NAME', 'default'),
                user_domain_name=os.getenv('OS_USER_DOMAIN_NAME', 'default')
            )
        except Exception as e:
            sys.exit(f"Failed to connect to OpenStack: {e}")

    def _should_include_server(self, server):
        """
        Check if server should be included in inventory based on filter settings
        """
        if not hasattr(server, 'metadata'):
            return False
            
        env_tag = self.filter_config['environment_tag']
        env_value = self.filter_config['environment_value']
        
        return (env_tag in server.metadata and 
                server.metadata[env_tag] == env_value)

    def _get_preferred_ip(self, addresses):
        """
        Select IP address based on network priority
        """
        # First try priority list
        for network_name in self.network_priority:
            if network_name in addresses:
                for address in addresses[network_name]:
                    if address['version'] == 4:  # IPv4
                        return address['addr'], network_name

        # If not found in priority list, take first available IPv4
        for network_name, address_list in addresses.items():
            for address in address_list:
                if address['version'] == 4:
                    return address['addr'], network_name

        return None, None

    def _get_groups(self):
        """
        Initialize inventory structure
        """
        base_group = self.filter_config['base_group_name']
        self.inventory = {
            '_meta': {
                'hostvars': {}
            },
            'all': {
                'hosts': [],
                'vars': {}
            },
            base_group: {
                'hosts': [],
                'vars': {
                    'environment_tag': self.filter_config['environment_tag'],
                    'environment_value': self.filter_config['environment_value'],
                    'network_priority': self.network_priority
                }
            }
        }

    def _add_host_to_groups(self, hostname, metadata):
        """
        Add host to appropriate groups based on metadata
        """
        base_group = self.filter_config['base_group_name']
        env_tag = self.filter_config['environment_tag']
        
        # Add to base group
        if hostname not in self.inventory[base_group]['hosts']:
            self.inventory[base_group]['hosts'].append(hostname)

        # Create groups based on metadata
        for key, value in metadata.items():
            if key != env_tag:  # skip environment tag
                group_name = f"{key}_{value}"
                if group_name not in self.inventory:
                    self.inventory[group_name] = {
                        'hosts': [],
                        'vars': {
                            'group_tag': key,
                            'group_value': value
                        }
                    }
                if hostname not in self.inventory[group_name]['hosts']:
                    self.inventory[group_name]['hosts'].append(hostname)

    def _get_ports_info(self):
        """
        Get information about all network ports
        Returns a dict with port_id as key and port info as value
        """
        try:
            ports = self.conn.network.ports()
            return {
                port.id: {
                    'mac_address': port.mac_address,
                    'tags': port.tags if hasattr(port, 'tags') else [],
                    'fixed_ips': port.fixed_ips,
                    'name': port.name,
                    'network_id': port.network_id
                }
                for port in ports
            }
        except Exception as e:
            sys.exit(f"Failed to get ports from OpenStack: {e}")

    def _get_hosts(self):
        """
        Get and process hosts from OpenStack
        """
        try:
            servers = self.conn.compute.servers()
            # Get all flavors once to avoid multiple API calls
            flavors = {f.id: f.name for f in self.conn.compute.flavors()}
            # Get all ports information
            ports_info = self._get_ports_info()
        except Exception as e:
            sys.exit(f"Failed to get data from OpenStack: {e}")
        
        for server in servers:
            # Check if server matches filter criteria
            if not self._should_include_server(server):
                continue

            # Get preferred IP address
            ip_address, network_name = self._get_preferred_ip(server.addresses)
            if not ip_address:
                continue  # Skip if no suitable IP found

            # Collect network interfaces information
            network_interfaces = {}
            
            # Process all interfaces from server.addresses
            for net_name, addresses in server.addresses.items():
                if net_name not in network_interfaces:
                    network_interfaces[net_name] = {
                        'ipv4_addresses': [],
                        'mac_addresses': [],
                        'port_id': None,
                        'port_name': '',
                        'tags': [],
                        'network_id': ''
                    }

                for address in addresses:
                    # Get IPv4 addresses
                    if address['version'] == 4:
                        network_interfaces[net_name]['ipv4_addresses'].append(address['addr'])
                    
                    # Get MAC address and match with ports info
                    if 'OS-EXT-IPS-MAC:mac_addr' in address:
                        mac_addr = address['OS-EXT-IPS-MAC:mac_addr']
                        if mac_addr not in network_interfaces[net_name]['mac_addresses']:
                            network_interfaces[net_name]['mac_addresses'].append(mac_addr)
                        
                        # Find matching port info by MAC address
                        for port_id, port_info in ports_info.items():
                            if port_info['mac_address'] == mac_addr:
                                network_interfaces[net_name]['port_id'] = port_id
                                network_interfaces[net_name]['port_name'] = port_info['name']
                                network_interfaces[net_name]['tags'] = port_info['tags']
                                network_interfaces[net_name]['network_id'] = port_info['network_id']
                                break

            # Get flavor information
            flavor_id = server.flavor['id']
            flavor_name = flavors.get(flavor_id, f"{flavor_id}")

            # Add host information
            self.inventory['_meta']['hostvars'][server.name] = {
                'ansible_host': ip_address,
                'ansible_ssh_host': ip_address,
                'openstack_id': server.id,
                'openstack_name': server.name,
                'preferred_network': network_name,
                'network_interfaces': network_interfaces,
                'openstack_metadata': server.metadata,
                'openstack_flavor_id': flavor_id,
                'openstack_flavor_name': flavor_name
            }

            # Add host to groups
            self._add_host_to_groups(server.name, server.metadata)

    def json_format_dict(self, data):
        """
        Format dictionary as JSON
        """
        return json.dumps(data, sort_keys=True, indent=2)

    def get_inventory(self):
        """
        Build and return the inventory
        """
        self._get_groups()
        self._get_hosts()
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
        print(json.dumps({}))

if __name__ == '__main__':
    main()
