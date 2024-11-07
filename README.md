# Ansible Dynamic Inventory for OpenStack

A dynamic inventory script for Ansible that automatically discovers and groups hosts in OpenStack with support for multiple networks and Terraform-style metadata.

## Features

- Automatic discovery of all instances in OpenStack
- Support for multiple network interfaces
- Terraform metadata-based grouping
- Hierarchical group structure
- Automatic creation of combined groups
- Support for different networks for SSH connections

## Requirements

Install the required dependencies:
```bash
pip install -r requirements.txt
```

Contents of `requirements.txt`:
```
python-openstackclient>=6.0.0
openstacksdk>=1.0.0
ansible-core>=2.13.0
jmespath>=1.0.1
netaddr>=0.8.0
PyYAML>=6.0
requests>=2.28.0
cryptography>=38.0.0
python-keystoneclient>=5.0.0
```

## Environment Setup

### OpenStack Environment Variables

Configure environment variables:

```bash
export OS_AUTH_URL=http://your-openstack-auth-url:5000/v3
export OS_PROJECT_NAME=your-project
export OS_USERNAME=your-username
export OS_PASSWORD=your-password
export OS_REGION_NAME=your-region
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
```

### Or use clouds.yaml

```yaml
clouds:
  openstack:
    auth:
      auth_url: http://your-openstack-auth-url:5000/v3
      username: your-username
      password: your-password
      project_name: your-project
      project_domain_name: default
      user_domain_name: default
    region_name: your-region
```

## Installation

1. Copy the `openstack_inventory.py` script to your project directory
2. Make the script executable:
```bash
chmod +x openstack_inventory.py
```

## Ansible Configuration

### ansible.cfg
```ini
[inventory]
enable_plugins = script

[defaults]
inventory = /path/to/openstack_inventory.py
```

### Verify inventory
```bash
./openstack_inventory.py --list
```

## Usage with Terraform

### Example Terraform Metadata
```hcl
resource "openstack_compute_instance_v2" "instance" {
  name = "postgres-master-01"
  # ... other parameters ...

  metadata = {
    environment  = "dwh"
    project     = "dwh"
    service_type = "postgres"
    role        = "master"
  }
}
```

## Usage Examples

### 1. Basic Usage
```yaml
- hosts: tag_environment_dwh
  tasks:
    - name: Configure DWH environment servers
      # tasks...
```

### 2. Using with Specific Network
```yaml
- hosts: tag_service_type_postgres:&network_private
  tasks:
    - name: Configure PostgreSQL via private network
      # tasks...
```

### 3. Combined Groups
```yaml
- hosts: postgres_dwh
  tasks:
    - name: Configure PostgreSQL in DWH environment
      # tasks...
```

### 4. Using with Bastion Host
```yaml
- hosts: tag_role_master
  vars:
    ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p bastion.internal"'
  tasks:
    - name: Configure master nodes
      # tasks...
```

## Group Structure

The script creates the following group structure:

1. Metadata Type Groups:
   - `type_environment`
   - `type_project`
   - `type_service_type`
   - `type_role`

2. Metadata Value Groups:
   - `tag_environment_dwh`
   - `tag_service_type_postgres`
   - `tag_role_master`
   etc.

3. Network Groups:
   - `network_private`
   - `network_public`

4. Combined Groups:
   - `postgres_dwh`
   - `redis_prod`
   etc.

## Host Variables

The following variables are available for each host:

```yaml
hostvars:
  webserver_private:
    ansible_host: "10.0.0.2"
    network_name: "private"
    network_interfaces:
      private: ["10.0.0.2"]
      public: ["203.0.113.2"]
    openstack_id: "instance-id"
    openstack_name: "server-name"
    openstack_status: "ACTIVE"
    environment: "dwh"
    project: "dwh"
    service_type: "postgres"
    role: "master"
```

## Debugging

### View all groups and hosts
```bash
./openstack_inventory.py --list | jq
```

### View variables for a specific host
```bash
./openstack_inventory.py --host hostname | jq
```

## Known Limitations

1. Only IPv4 addresses are supported
2. Requires access to OpenStack API
3. Performance depends on the number of servers and OpenStack API speed

## Usage Tips

1. Use consistent server naming scheme
2. Add all necessary metadata when creating servers in Terraform
3. Group servers by all important attributes using metadata
4. Use different networks for different types of access
5. Configure SSH through bastion for secure access
