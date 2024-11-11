# OpenStack Dynamic Inventory for Ansible

A dynamic inventory script for Ansible that filters and groups OpenStack hosts based on metadata and manages network interface priority for connections.

## Features

- Instance filtering by environment tag
- Automatic grouping by metadata
- Network interface prioritization for connections
- Instance flavor information retrieval
- Multiple network interface support
- Flexible YAML configuration

## Requirements

- Python 3.6+
- OpenStack SDK
- PyYAML
- OpenStack API access

## Installation

1. Install dependencies:
```bash
pip install openstacksdk pyyaml
```

2. Copy the script and make it executable:
```bash
cp openstack_inventory.py /etc/ansible/inventory/
chmod +x /etc/ansible/inventory/openstack_inventory.py
```

3. Create configuration file:
```bash
cp inventory_config.yaml /etc/ansible/inventory/
```

## Configuration

### Configuration File Structure (inventory_config.yaml)

```yaml
all:
  vars:
    inventory_settings:
      environment_tag: "environment"    # tag name for filtering
      environment_value: "dwh"          # tag value for filtering
      base_group_name: "dwh"           # base group name in inventory
      network_priority:                 # network priority (highest to lowest)
        - "internal_cloud_network"
        - "ps_colo_int_1"
      debug:
        enabled: false
        log_file: "inventory.log"
```

### Environment Variables

1. For script configuration:
```bash
export INVENTORY_CONFIG=/etc/ansible/inventory/inventory_config.yaml
```

2. For OpenStack connection:
```bash
export OS_AUTH_URL=http://your-openstack-auth-url:5000/v3
export OS_PROJECT_NAME=your-project
export OS_USERNAME=your-username
export OS_PASSWORD=your-password
export OS_REGION_NAME=your-region
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
```

## Usage

### Basic Usage

1. Test script operation:
```bash
./openstack_inventory.py --list
```

2. Use with Ansible:
```bash
ansible-playbook -i openstack_inventory.py playbook.yml
```

### Host Grouping

The script automatically creates the following groups:

1. Base group (default "dwh")
2. Metadata-based groups (e.g., "project_analytics", "role_master")

Example of using groups in playbook:
```yaml
- hosts: dwh
  tasks:
    - name: All hosts with environment=dwh
      # tasks...

- hosts: role_master
  tasks:
    - name: All master nodes
      # tasks...

- hosts: project_analytics
  tasks:
    - name: All hosts in analytics project
      # tasks...
```

### Available Host Variables

The following variables are available for each host:

```yaml
hostvars:
  your-server-name:
    ansible_host: "10.0.0.2"              # Connection IP
    ansible_ssh_host: "10.0.0.2"          # Connection IP (duplicate for compatibility)
    openstack_id: "instance-id"           # Instance ID
    openstack_name: "server-name"         # Server name
    preferred_network: "network-name"      # Used network name
    network_interfaces:                    # All available network interfaces
      network1: ["10.0.0.2"]
      network2: ["192.168.1.2"]
    openstack_metadata:                    # Server metadata
      environment: "dwh"
      project: "analytics"
      role: "master"
    openstack_flavor_id: "flavor-id"      # Instance type ID
    openstack_flavor_name: "flavor-name"  # Instance type name
```

## Debugging

1. Check list of all hosts and groups:
```bash
./openstack_inventory.py --list | jq
```

2. View information about specific host:
```bash
./openstack_inventory.py --host hostname | jq
```

## Network Priority

The script selects connection IP in the following order:
1. Looks for networks from network_priority list in specified order
2. If network is found, uses first available IPv4 address from that network
3. If priority networks not found, uses first available IPv4 address from any network

## Error Handling

The script will exit with error in the following cases:
- Configuration file not found
- Configuration file format error
- Missing required configuration parameters
- Failed to connect to OpenStack
- Error retrieving data from OpenStack

## Known Limitations

1. Only IPv4 addresses are supported
2. OpenStack API access required
3. Host will not be added to inventory if no suitable IP address is found
4. All group names are generated in `key_value` format from metadata