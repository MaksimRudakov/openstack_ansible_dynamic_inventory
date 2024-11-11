# OpenStack Dynamic Inventory для Ansible

Скрипт динамического инвентаря для Ansible, который фильтрует и группирует хосты OpenStack на основе метаданных и управляет приоритетом сетевых интерфейсов для подключения.

## Возможности

- Фильтрация инстансов по тегу environment
- Автоматическая группировка по метаданным
- Приоритизация сетевых интерфейсов для подключения
- Получение информации о flavor'ах инстансов
- Поддержка множественных сетевых интерфейсов
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
      debug:
        enabled: false
        log_file: "inventory.log"
```

### Переменные окружения

1. Для конфигурации скрипта:
```bash
export INVENTORY_CONFIG=/etc/ansible/inventory/inventory_config.yaml
```

2. Для подключения к OpenStack:
```bash
export OS_AUTH_URL=http://your-openstack-auth-url:5000/v3
export OS_PROJECT_NAME=your-project
export OS_USERNAME=your-username
export OS_PASSWORD=your-password
export OS_REGION_NAME=your-region
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
```

## Использование

### Базовое использование

1. Проверка работы скрипта:
```bash
./openstack_inventory.py --list
```

2. Использование в Ansible:
```bash
ansible-playbook -i openstack_inventory.py playbook.yml
```

### Группировка хостов

Скрипт автоматически создает следующие группы:

1. Базовая группа (по умолчанию "dwh")
2. Группы на основе метаданных (например, "project_analytics", "role_master")

Пример использования групп в плейбуке:
```yaml
- hosts: dwh
  tasks:
    - name: Все хосты с environment=dwh
      # tasks...

- hosts: role_master
  tasks:
    - name: Все master-ноды
      # tasks...

- hosts: project_analytics
  tasks:
    - name: Все хосты проекта analytics
      # tasks...
```

### Доступные переменные хоста

Для каждого хоста доступны следующие переменные:

```yaml
hostvars:
  your-server-name:
    ansible_host: "10.0.0.2"              # IP для подключения
    ansible_ssh_host: "10.0.0.2"          # IP для подключения (дублирование для совместимости)
    openstack_id: "instance-id"           # ID инстанса
    openstack_name: "server-name"         # Имя сервера
    preferred_network: "network-name"      # Имя используемой сети
    network_interfaces:                    # Все доступные сетевые интерфейсы
      network1: ["10.0.0.2"]
      network2: ["192.168.1.2"]
    openstack_metadata:                    # Метаданные сервера
      environment: "dwh"
      project: "analytics"
      role: "master"
    openstack_flavor_id: "flavor-id"      # ID типа инстанса
    openstack_flavor_name: "flavor-name"  # Имя типа инстанса
```

## Отладка

1. Проверка списка всех хостов и групп:
```bash
./openstack_inventory.py --list | jq
```

2. Просмотр информации о конкретном хосте:
```bash
./openstack_inventory.py --host hostname | jq
```

## Приоритет сетей

Скрипт выбирает IP для подключения в следующем порядке:
1. Ищет сети из списка network_priority в указанном порядке
2. Если сеть найдена, использует первый доступный IPv4 адрес из этой сети
3. Если приоритетные сети не найдены, использует первый доступный IPv4 адрес из любой сети

## Обработка ошибок

Скрипт завершится с ошибкой в следующих случаях:
- Не найден конфигурационный файл
- Ошибка в формате конфигурационного файла
- Отсутствуют обязательные параметры конфигурации
- Не удалось подключиться к OpenStack
- Ошибка при получении данных из OpenStack

## Известные ограничения

1. Поддерживаются только IPv4 адреса
2. Требуется доступ к API OpenStack
3. При отсутствии подходящего IP адреса хост не будет добавлен в инвентарь
4. Все имена групп генерируются в формате `key_value` из метаданных
