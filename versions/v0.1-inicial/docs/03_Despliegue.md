# Manual de Despliegue

## Docker Compose (entorno dev)
```bash
docker compose up -d --build
```

## Docker Compose (entorno prod)
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Docker Swarm (base)
```bash
docker swarm init
docker stack deploy -c orquestacion/docker-swarm.yml securevault
```

## Ansible
Archivo base: infraestructura/ansible/site.yml

Ejemplo:
```bash
ansible-playbook -i inventario.ini infraestructura/ansible/site.yml
```
