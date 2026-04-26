# Manual de Operación y DevOps

## 1. Requisitos

- Docker y Docker Compose instalados.
- Conexion a internet para descargar las imagenes publicadas en Docker Hub.
- Puerto 3000 disponible para el gateway.
- Puertos 8001, 8002, 5432 y 6379 disponibles.

## 2. Ejecucion del proyecto

### Descarga de imagenes publicadas

Desde la raiz del proyecto ejecutar:

```powershell
.\scripts\pull-images.ps1
```

El script descarga las imagenes publicadas en Docker Hub para los servicios:

- securevault-auth
- securevault-vault
- securevault-worker
- securevault-frontend

### Levantar entorno con imagenes descargadas

Definir el tag publicado y levantar el compose de operacion:

```powershell
$env:IMAGE_TAG = "v1.0.0"
docker compose -f docker-compose.prod.yml up -d
```

Verificar estado:

```powershell
docker compose -f docker-compose.prod.yml ps
```

### Arranque local por build desde codigo fuente

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
- worker
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
- worker

## 4. Acceso funcional

- UI principal: http://localhost:3000
- Auth directo: http://localhost:8001/docs
- Vault directo: http://localhost:8002/docs

Acceso de monitoreo en producción:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- cAdvisor: http://localhost:8080
- Loki: http://localhost:3100

## 5. Consultas de validacion funcional

Las siguientes pruebas permiten evidenciar que el proyecto esta operativo mas alla del arranque de contenedores.

### Registro de usuario

```powershell
curl -X POST http://localhost:3000/auth/register ^
	-H "Content-Type: application/json" ^
	-d "{\"username\":\"evaluador1\",\"password\":\"ClaveSegura123!\"}"
```

### Login y obtencion de token

```powershell
curl -X POST http://localhost:3000/auth/login ^
	-H "Content-Type: application/json" ^
	-d "{\"username\":\"evaluador1\",\"password\":\"ClaveSegura123!\"}"
```

El resultado esperado es un `access_token`. Ese valor debe reutilizarse en las consultas autenticadas.

### Crear un secreto

```powershell
curl -X POST http://localhost:3000/vault/secret ^
	-H "Authorization: Bearer TOKEN_AQUI" ^
	-H "Content-Type: application/json" ^
	-d "{\"site\":\"correo-institucional\",\"password\":\"MiClave123!\"}"
```

### Listar secretos

```powershell
curl -X GET http://localhost:3000/vault/secret ^
	-H "Authorization: Bearer TOKEN_AQUI"
```

### Actualizar un secreto

```powershell
curl -X PUT http://localhost:3000/vault/secret/1 ^
	-H "Authorization: Bearer TOKEN_AQUI" ^
	-H "Content-Type: application/json" ^
	-d "{\"site\":\"correo-actualizado\",\"password\":\"NuevaClave456!\"}"
```

### Eliminar un secreto

```powershell
curl -X DELETE http://localhost:3000/vault/secret/1 ^
	-H "Authorization: Bearer TOKEN_AQUI"
```

### Verificacion de persistencia en PostgreSQL

```powershell
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT id, username FROM users;"
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT id, site, owner_id FROM secrets;"
```

### Verificacion de Redis

```powershell
docker compose exec redis redis-cli KEYS "*"
docker compose exec redis redis-cli DBSIZE
```

### Prueba de acceso no autorizado

```powershell
curl http://localhost:3000/vault/secret
```

El resultado esperado es rechazo por falta de token, normalmente `401 Unauthorized`.

### Prueba de rate limiting

```powershell
for ($i = 1; $i -le 15; $i++) {
	curl -X GET http://localhost:3000/vault/secret -H "Authorization: Bearer TOKEN_AQUI"
}
```

Si la limitacion de peticiones esta activa, algunas respuestas deberian finalizar con `429 Too Many Requests`.

### Verificacion de monitoreo

```powershell
curl http://localhost:9090/-/healthy
curl http://localhost:8080/healthz
curl http://localhost:3100/ready
```

### Revision de logs

```powershell
docker compose -f docker-compose.prod.yml logs auth --tail=50
docker compose -f docker-compose.prod.yml logs vault --tail=50
docker compose -f docker-compose.prod.yml logs worker --tail=50
```

## 6. Operación diaria

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

## 7. Base de datos

Acceso a PostgreSQL:

```powershell
docker compose exec postgres psql -U vault -d vaultdb
```

Comandos útiles:

- \dt
- SELECT \* FROM users;
- SELECT \* FROM secrets;

## 8. Copias y recuperación

### Backup lógico

```powershell
docker compose exec postgres pg_dump -U vault -d vaultdb > backup_vaultdb.sql
```

### Restore lógico

```powershell
docker compose exec -T postgres psql -U vault -d vaultdb < backup_vaultdb.sql
```

## 9. Incidencias comunes

- Mensaje no se pudieron cargar los datos de la bóveda: revisar logs de vault y estado de token.
- Error de servicio no existe: usar nombres de servicio reales en compose (auth, vault, postgres, redis, gateway).
- Cambios de frontend no reflejados: recargar con Ctrl+F5 o reconstruir gateway.
- Error `FileNotFoundError: Config file '.env' not found` en vault-1: Asegurar que servicios/vault-service/Dockerfile contiene `RUN touch .env` después de pip install. El archivo es requerido por SlowAPI aunque esté vacío.
- Error de permisos en nginx (Permission denied /var/cache/nginx): Asegurar que frontend-spa/Dockerfile NO contiene `USER nginx`. Remover esa línea si existe; el contenedor debe ejecutar como root (user por defecto en nginx:alpine).

## 10. Shift-left local con pre-commit

Instalación recomendada para validación antes del commit:

```powershell
pip install pre-commit
pre-commit install
```

La configuración incluida ejecuta higiene básica de archivos y Gitleaks sobre cambios staged.

## 11. Cobertura de pruebas en CI

El pipeline de CI ejecuta pruebas Python con cobertura para los servicios backend:

```powershell
pytest -q --cov=app --cov-report=term-missing --cov-report=xml
```

Actualmente la cobertura se enfoca en hashing, JWT, cifrado, validación de token y operaciones base de secretos.

## 12. Compatibilidad de dependencias

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

## 13. Runtime security con Falco

El compose productivo incluye `falco` para detectar comportamientos anómalos en runtime.

Requisitos importantes:

- Host Linux con soporte para eBPF moderno.
- Permisos elevados para inspeccionar eventos del sistema.
- Acceso a `/proc`, `/boot`, `/lib/modules`, `/usr` y al socket Docker según la configuración de compose.

Las reglas locales incluidas están en `monitoring/falco/falco_rules.local.yaml`.
