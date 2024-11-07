# Динамический инвентарь Ansible для OpenStack

Скрипт динамического инвентаря для Ansible, который автоматически обнаруживает и группирует хосты в OpenStack с поддержкой множественных сетей и метаданных в стиле Terraform.

## Возможности

- Автоматическое обнаружение всех инстансов в OpenStack
- Поддержка множественных сетевых интерфейсов
- Группировка на основе метаданных Terraform
- Иерархическая структура групп
- Автоматическое создание комбинированных групп
- Поддержка разных сетей для SSH-подключений

## Требования

Установите необходимые зависимости:
```bash
pip install -r requirements.txt
```

Содержимое `requirements.txt`:
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

## Настройка окружения

### Переменные окружения OpenStack

Настройте переменные окружения:

```bash
export OS_AUTH_URL=http://your-openstack-auth-url:5000/v3
export OS_PROJECT_NAME=your-project
export OS_USERNAME=your-username
export OS_PASSWORD=your-password
export OS_REGION_NAME=your-region
export OS_PROJECT_DOMAIN_NAME=default
export OS_USER_DOMAIN_NAME=default
```

### Или используйте clouds.yaml

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

## Установка

1. Скопируйте скрипт `openstack_inventory.py` в директорию вашего проекта
2. Сделайте скрипт исполняемым:
```bash
chmod +x openstack_inventory.py
```

## Конфигурация Ansible

### ansible.cfg
```ini
[inventory]
enable_plugins = script

[defaults]
inventory = /path/to/openstack_inventory.py
```

### Проверка инвентаря
```bash
./openstack_inventory.py --list
```

## Использование с Terraform

### Пример метаданных Terraform
```hcl
resource "openstack_compute_instance_v2" "instance" {
  name = "postgres-master-01"
  # ... другие параметры ...

  metadata = {
    environment  = "dwh"
    project     = "dwh"
    service_type = "postgres"
    role        = "master"
  }
}
```

## Примеры использования

### 1. Базовое использование
```yaml
- hosts: tag_environment_dwh
  tasks:
    - name: Настройка серверов DWH окружения
      # tasks...
```

### 2. Использование с конкретной сетью
```yaml
- hosts: tag_service_type_postgres:&network_private
  tasks:
    - name: Настройка PostgreSQL через приватную сеть
      # tasks...
```

### 3. Комбинированные группы
```yaml
- hosts: postgres_dwh
  tasks:
    - name: Настройка PostgreSQL в DWH окружении
      # tasks...
```

### 4. С использованием бастиона
```yaml
- hosts: tag_role_master
  vars:
    ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p bastion.internal"'
  tasks:
    - name: Настройка master-нод
      # tasks...
```

## Структура групп

Скрипт создает следующую структуру групп:

1. Группы по типам метаданных:
   - `type_environment`
   - `type_project`
   - `type_service_type`
   - `type_role`

2. Группы по значениям метаданных:
   - `tag_environment_dwh`
   - `tag_service_type_postgres`
   - `tag_role_master`
   и т.д.

3. Группы по сетям:
   - `network_private`
   - `network_public`

4. Комбинированные группы:
   - `postgres_dwh`
   - `redis_prod`
   и т.д.

## Переменные хоста

Для каждого хоста доступны следующие переменные:

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

## Отладка

### Просмотр всех групп и хостов
```bash
./openstack_inventory.py --list | jq
```

### Просмотр переменных конкретного хоста
```bash
./openstack_inventory.py --host hostname | jq
```

## Известные ограничения

1. Поддерживаются только IPv4 адреса
2. Требуется доступ к API OpenStack
3. Производительность зависит от количества серверов и скорости API OpenStack

## Советы по использованию

1. Используйте консистентную схему именования серверов
2. Добавляйте все необходимые метаданные при создании серверов в Terraform
3. Группируйте серверы по всем важным признакам через метаданные
4. Используйте разные сети для разных типов доступа
5. Настраивайте SSH через бастион для безопасного доступа

