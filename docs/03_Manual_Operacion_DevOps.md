# Manual de Operación y DevOps

## 1. Requisitos

- Docker y Docker Compose instalados.
- Puerto 3000 disponible para el gateway.
- Puertos 8001, 8002, 5432 y 6379 disponibles.

## 2. Levantar entorno

Desde la raíz del proyecto:

```powershell
docker compose up -d --build
```

Verificar estado:

```powershell
docker compose ps
```

## 3. Servicios esperados

- auth
- vault
- postgres
- redis
- gateway

En entorno productivo con `docker-compose.prod.yml` también se esperan:

- prometheus
- grafana
- cadvisor
- loki
- promtail
- falco

## 4. Acceso funcional

- UI principal: http://localhost:3000
- Auth directo: http://localhost:8001/docs
- Vault directo: http://localhost:8002/docs

Acceso de monitoreo en producción:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- cAdvisor: http://localhost:8080
- Loki: http://localhost:3100

## 5. Operación diaria

### Reiniciar un servicio

```powershell
docker compose restart auth
```

### Reconstruir un servicio específico

```powershell
docker compose up -d --build vault
```

### Ver logs

```powershell
docker compose logs auth --tail=100
docker compose logs vault --tail=100
docker compose logs gateway --tail=100
```

Con compose productivo:

```powershell
docker compose -f docker-compose.prod.yml logs prometheus --tail=100
docker compose -f docker-compose.prod.yml logs grafana --tail=100
docker compose -f docker-compose.prod.yml logs cadvisor --tail=100
docker compose -f docker-compose.prod.yml logs loki --tail=100
docker compose -f docker-compose.prod.yml logs promtail --tail=100
docker compose -f docker-compose.prod.yml logs falco --tail=100
```

## 6. Base de datos

Acceso a PostgreSQL:

```powershell
docker compose exec postgres psql -U vault -d vaultdb
```

Comandos útiles:

- \dt
- SELECT \* FROM users;
- SELECT \* FROM secrets;

## 7. Copias y recuperación

### Backup lógico

```powershell
docker compose exec postgres pg_dump -U vault -d vaultdb > backup_vaultdb.sql
```

### Restore lógico

```powershell
docker compose exec -T postgres psql -U vault -d vaultdb < backup_vaultdb.sql
```

## 8. Incidencias comunes

- Mensaje no se pudieron cargar los datos de la bóveda: revisar logs de vault y estado de token.
- Error de servicio no existe: usar nombres de servicio reales en compose (auth, vault, postgres, redis, gateway).
- Cambios de frontend no reflejados: recargar con Ctrl+F5 o reconstruir gateway.
- Error `FileNotFoundError: Config file '.env' not found` en vault-1: Asegurar que vault-service/Dockerfile contiene `RUN touch .env` después de pip install. El archivo es requerido por SlowAPI aunque esté vacío.
- Error de permisos en nginx (Permission denied /var/cache/nginx): Asegurar que frontend-spa/Dockerfile NO contiene `USER nginx`. Remover esa línea si existe; el contenedor debe ejecutar como root (user por defecto en nginx:alpine).

## 9. Shift-left local con pre-commit

Instalación recomendada para validación antes del commit:

```powershell
pip install pre-commit
pre-commit install
```

La configuración incluida ejecuta higiene básica de archivos y Gitleaks sobre cambios staged.

## 10. Cobertura de pruebas en CI

El pipeline de CI ejecuta pruebas Python con cobertura para los servicios backend:

```powershell
pytest -q --cov=app --cov-report=term-missing --cov-report=xml
```

Actualmente la cobertura se enfoca en hashing, JWT, cifrado, validación de token y operaciones base de secretos.

## 9. Compatibilidad de dependencias

### Dependencias conocidas

- **eslint-plugin-react**: versionado a `^7.37.5` en frontend-spa. Versión `^7.38.0` no existe en npm registry.
- **Vault Dockerfile**: requiere archivo `.env` (vacío) en build context debido a validación de SlowAPI en startup.
- **Frontend Dockerfile**: no debe incluir `USER nginx` para evitar fallos de permisos en /var/cache/nginx.

### Validación post-arranque

Antes de considerar que el entorno está listo, verificar:

```powershell
# Estado de servicios
docker compose ps
# Todos deben estar en "Up" o "Healthy"

# Acceso a endpoints
curl http://localhost:3000               # Gateway (200)
curl http://localhost:8001/docs         # Auth API (200)
curl http://localhost:8002/docs         # Vault API (200)

# Salud de base de datos
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT 1;"

# Salud de Redis
docker compose exec redis redis-cli ping
# Esperado: PONG
```

## 10. Runtime security con Falco

El compose productivo incluye `falco` para detectar comportamientos anómalos en runtime.

Requisitos importantes:

- Host Linux con soporte para eBPF moderno.
- Permisos elevados para inspeccionar eventos del sistema.
- Acceso a `/proc`, `/boot`, `/lib/modules`, `/usr` y al socket Docker según la configuración de compose.

Las reglas locales incluidas están en `monitoring/falco/falco_rules.local.yaml`.
