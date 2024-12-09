# OpenStack Dynamic Inventory для Ansible

Скрипт динамического инвентаря для Ansible, который фильтрует и группирует хосты OpenStack на основе метаданных, управляет приоритетом сетевых интерфейсов для подключения и собирает информацию о сетевых интерфейсах, включая MAC-адреса и теги.

## Возможности

- Фильтрация инстансов по тегу environment
- Автоматическая группировка по метаданным
- Приоритизация сетевых интерфейсов для подключения
- Получение информации о flavor'ах инстансов
- Сбор информации о сетевых интерфейсах (MAC-адреса, теги)
- Гибкая конфигурация через YAML файл

## Требования

- Python 3.6+
- OpenStack SDK
- PyYAML
- Доступ к API OpenStack

## Установка

1. Установите зависимости:
```bash
pip install openstacksdk pyyaml
```

2. Скопируйте скрипт и сделайте его исполняемым:
```bash
cp openstack_inventory.py /etc/ansible/inventory/
chmod +x /etc/ansible/inventory/openstack_inventory.py
```

3. Создайте конфигурационный файл:
```bash
cp inventory_config.yaml /etc/ansible/inventory/
```

## Конфигурация

### Структура конфигурационного файла (inventory_config.yaml)

```yaml
all:
  vars:
    inventory_settings:
      environment_tag: "environment"    # имя тега для фильтрации
      environment_value: "dwh"          # значение тега для фильтрации
      base_group_name: "dwh"           # имя базовой группы в инвентаре
      network_priority:                 # приоритет сетей (от высшего к низшему)
        - "internal_cloud_network"
        - "ps_colo_int_1"
```

### Переменные окружения OpenStack

```bash
export OS_AUTH_URL=http://your-openstack-auth-url:5000/v3
export OS_PROJECT_NAME=your-project
export OS_USERNAME=your-username
export OS_PASSWORD=your-password
export OS_REGION_NAME=your-region
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
```

## Структура инвентаря

### Информация о хостах

Для каждого хоста доступны следующие переменные:

```yaml
hostvars:
  your-server-name:
    ansible_host: "10.0.0.2"              # IP для подключения
    ansible_ssh_host: "10.0.0.2"          # IP для подключения (дублирование для совместимости)
    openstack_id: "instance-id"           # ID инстанса
    openstack_name: "server-name"         # Имя сервера
    preferred_network: "network-name"      # Имя используемой сети
    openstack_metadata:                    # Метаданные сервера
      environment: "dwh"
      project: "analytics"
      role: "master"
    openstack_flavor_id: "flavor-id"      # ID типа инстанса
    openstack_flavor_name: "flavor-name"  # Имя типа инстанса
    network_interfaces:                    # Информация о сетевых интерфейсах
      network_name:                        # Имя сети
        ipv4_addresses:                    # Список IPv4 адресов
          - "10.0.0.2"
        mac_addresses:                     # Список MAC-адресов
          - "fa:16:3e:xx:xx:xx"
        port_id: "port-id-xxx"            # ID порта
        port_name: "port-name"            # Имя порта
        tags:                             # Теги интерфейса
          - "tag1"
          - "tag2"
        network_id: "net-id"              # ID сети
```

### Группы

Скрипт автоматически создает следующие группы:
1. Базовая группа (по умолчанию "dwh")
2. Группы на основе метаданных (например, "project_analytics", "role_master")

## Примеры использования

### Базовое использование

```bash
# Проверка инвентаря
./openstack_inventory.py --list

# Использование с Ansible
ansible-playbook -i openstack_inventory.py playbook.yml
```

### Примеры плейбуков

1. Работа с группами:
```yaml
- hosts: dwh
  tasks:
    - name: Все хосты с environment=dwh
      debug:
        msg: "DWH host: {{ inventory_hostname }}"

- hosts: role_master
  tasks:
    - name: Все master-ноды
      debug:
        msg: "Master node: {{ inventory_hostname }}"
```

2. Работа с сетевыми интерфейсами:
```yaml
- hosts: dwh
  tasks:
    - name: Показать информацию о сетевых интерфейсах
      debug:
        msg: >
          Interface {{ item.key }}:
          MAC: {{ item.value.mac_addresses | join(', ') }}
          Tags: {{ item.value.tags | join(', ') }}
          Port ID: {{ item.value.port_id }}
      loop: "{{ hostvars[inventory_hostname].network_interfaces | dict2items }}"

    - name: Проверка тегов интерфейса
      debug:
        msg: "Found interface with required tag"
      when: "'required-tag' in hostvars[inventory_hostname].network_interfaces[item.key].tags"
      loop: "{{ hostvars[inventory_hostname].network_interfaces | dict2items }}"
```

## Отладка

```bash
# Просмотр всего инвентаря
./openstack_inventory.py --list | jq

# Просмотр информации о конкретном хосте
./openstack_inventory.py --host hostname | jq
```

## Известные ограничения

1. Поддерживаются только IPv4 адреса
2. Требуется доступ к API OpenStack
3. При отсутствии подходящего IP адреса хост не будет добавлен в инвентарь
4. Имена групп генерируются в формате `key_value` из метаданных
5. Требуются права на получение информации о портах в OpenStack
