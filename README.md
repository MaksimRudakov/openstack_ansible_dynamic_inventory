# OpenStack Dynamic Inventory for Ansible

A dynamic inventory script for Ansible that filters and groups OpenStack hosts based on metadata, manages network interface priority for connections, and collects information about network interfaces, including MAC addresses and tags.

## Features

- Instance filtering by environment tag
- Automatic grouping by metadata
- Network interface prioritization for connections
- Instance flavor information retrieval
- Network interface information collection (MAC addresses, tags)
- Flexible configuration via YAML file

## Requirements

- Python 3.6+
- OpenStack SDK
- PyYAML
- Access to OpenStack API

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
```

### OpenStack Environment Variables

```bash
export OS_AUTH_URL=http://your-openstack-auth-url:5000/v3
export OS_PROJECT_NAME=your-project
export OS_USERNAME=your-username
export OS_PASSWORD=your-password
export OS_REGION_NAME=your-region
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
```

## Inventory Structure

### Host Information

The following variables are available for each host:

```yaml
hostvars:
  your-server-name:
    ansible_host: "10.0.0.2"              # IP for connection
    ansible_ssh_host: "10.0.0.2"          # IP for connection (duplicate for compatibility)
    openstack_id: "instance-id"           # Instance ID
    openstack_name: "server-name"         # Server name
    preferred_network: "network-name"      # Used network name
    openstack_metadata:                    # Server metadata
      environment: "dwh"
      project: "analytics"
      role: "master"
    openstack_flavor_id: "flavor-id"      # Instance type ID
    openstack_flavor_name: "flavor-name"  # Instance type name
    network_interfaces:                    # Network interfaces information
      network_name:                        # Network name
        ipv4_addresses:                    # List of IPv4 addresses
          - "10.0.0.2"
        mac_addresses:                     # List of MAC addresses
          - "fa:16:3e:xx:xx:xx"
        port_id: "port-id-xxx"            # Port ID
        port_name: "port-name"            # Port name
        tags:                             # Interface tags
          - "tag1"
          - "tag2"
        network_id: "net-id"              # Network ID
```

### Groups

The script automatically creates the following groups:
1. Base group (default "dwh")
2. Groups based on metadata (e.g., "project_analytics", "role_master")

## Usage Examples

### Basic Usage

```bash
# Check inventory
./openstack_inventory.py --list

# Use with Ansible
ansible-playbook -i openstack_inventory.py playbook.yml
```

### Playbook Examples

1. Working with groups:
```yaml
- hosts: dwh
  tasks:
    - name: All hosts with environment=dwh
      debug:
        msg: "DWH host: {{ inventory_hostname }}"

- hosts: role_master
  tasks:
    - name: All master nodes
      debug:
        msg: "Master node: {{ inventory_hostname }}"
```

2. Working with network interfaces:
```yaml
- hosts: dwh
  tasks:
    - name: Show network interfaces information
      debug:
        msg: >
          Interface {{ item.key }}:
          MAC: {{ item.value.mac_addresses | join(', ') }}
          Tags: {{ item.value.tags | join(', ') }}
          Port ID: {{ item.value.port_id }}
      loop: "{{ hostvars[inventory_hostname].network_interfaces | dict2items }}"

    - name: Check interface tags
      debug:
        msg: "Found interface with required tag"
      when: "'required-tag' in hostvars[inventory_hostname].network_interfaces[item.key].tags"
      loop: "{{ hostvars[inventory_hostname].network_interfaces | dict2items }}"
```

## Debugging

```bash
# View entire inventory
./openstack_inventory.py --list | jq

# View specific host information
./openstack_inventory.py --host hostname | jq
```

## Known Limitations

1. Only IPv4 addresses are supported
2. OpenStack API access is required
3. Host will not be added to inventory if no suitable IP address is found
4. Group names are generated in `key_value` format from metadata
5. Requires permissions to get port information in OpenStack
