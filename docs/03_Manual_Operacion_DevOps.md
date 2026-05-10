# Manual de Operación y DevOps — SecureVault Pro v1.2

## 1. Requisitos

- Docker y Docker Compose instalados.
- Conexión a internet para descargar las imágenes publicadas en Docker Hub.
- Puerto 3000 disponible para el gateway.
- Puertos 8001, 8002, 5432 y 6379 disponibles.

## 2. Ejecución del proyecto

### Descarga de imágenes publicadas

Desde la raíz del proyecto ejecutar:

```powershell
.\scripts\pull-images.ps1
```

El script descarga las imágenes publicadas en Docker Hub para los servicios:

- `necromanoger/securevault-auth:v1.2.0`
- `necromanoger/securevault-vault:v1.2.0`
- `necromanoger/securevault-worker:v1.2.0`
- `necromanoger/securevault-frontend:v1.2.0`

### Levantar entorno con imágenes descargadas

```powershell
$env:IMAGE_TAG = "v1.2.0"
docker compose -f docker-compose.prod.yml up -d
```

Verificar estado:

```powershell
docker compose -f docker-compose.prod.yml ps
```

### Arranque local por build desde código fuente

```powershell
docker compose up -d --build
```

Verificar estado:

```powershell
docker compose ps
```

## 3. Servicios esperados

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| auth | 8001 | FastAPI — Autenticación y administración |
| vault | 8002 | FastAPI — Secretos cifrados |
| worker | — | Consumo asíncrono de eventos |
| gateway | 3000 | Nginx — Frontend + reverse proxy |
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Redis 7 (rate limit, lockout, jobs) |

## 4. Acceso funcional

- **UI principal:** http://localhost:3000
- **Auth API Docs:** http://localhost:8001/docs
- **Vault API Docs:** http://localhost:8002/docs

### Credenciales de acceso inicial

| Rol | Email | Contraseña |
|-----|-------|------------|
| Administrador | admin@securevault.local | AdminSecure123!@# |
| Usuario | (registro libre desde la UI) | (definida al crear) |

El administrador inicial se crea automáticamente al arrancar auth-service si no existe (bootstrap idempotente).

### Comportamiento según rol

- **Usuario regular** (`user`): accede a `/boveda` con su bóveda personal. JWT expira en **60 minutos**.
- **Administrador** (`admin`): accede a `/admin` con el panel de administración. JWT expira en **8 horas**.
  - Panel se actualiza automáticamente cada 30 segundos.
  - Al expirar la sesión, el panel detecta 401 y redirige al login automáticamente.
  - Puede gestionar usuarios, sesiones, roles y consultar la bitácora de auditoría.

### Acceso de monitoreo en producción

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- cAdvisor: http://localhost:8080
- Loki: http://localhost:3100

## 5. Consultas de validación funcional

### Registro de usuario

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/register `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"evaluador1@test.com","password":"ClaveSegura123!"}'
```

### Login y obtención de token

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/login `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"evaluador1@test.com","password":"ClaveSegura123!"}'
```

El resultado esperado incluye un `access_token`. Guardarlo para las consultas autenticadas.

### Login como administrador

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/login `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"admin@securevault.local","password":"AdminSecure123!@#"}'
```

### Verificar bloqueo de cuenta (3 intentos fallidos)

```powershell
# Simular 3 intentos fallidos
for ($i = 1; $i -le 3; $i++) {
    Invoke-WebRequest -Method POST http://localhost:3000/auth/login `
      -Headers @{"Content-Type"="application/json"} `
      -Body '{"email":"evaluador1@test.com","password":"ClaveIncorrecta"}' `
      -ErrorAction SilentlyContinue
}
# El 3er intento debe retornar 423 Locked
```

### Verificar clave Redis de bloqueo

```powershell
docker compose exec redis redis-cli -n 1 GET "login_fail:evaluador1@test.com"
# Debe mostrar "3"
docker compose exec redis redis-cli -n 1 TTL "login_fail:evaluador1@test.com"
# Debe mostrar segundos restantes (max 300)
```

### Solicitar recuperación de contraseña

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/password-reset/request `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"evaluador1@test.com"}'
```

### Confirmar reset de contraseña (limpia Redis)

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/password-reset/confirm `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"evaluador1@test.com","reset_token":"TOKEN_RECIBIDO","new_password":"NuevaClave123!"}'
# Después verificar que Redis limpió la clave:
docker compose exec redis redis-cli -n 1 GET "login_fail:evaluador1@test.com"
# Debe retornar (nil)
```

### Ver perfil del usuario autenticado

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/me `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Listar usuarios registrados (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/users `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Cambiar rol de un usuario (solo admin)

```powershell
Invoke-WebRequest -Method PATCH http://localhost:3000/auth/users/2/role `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"role":"admin"}'
```

### Crear un secreto

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/vault/secret `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"site":"correo-institucional","password":"MiClave123!","category":"password"}'
```

### Listar secretos

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/vault/secret `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Actualizar un secreto

```powershell
Invoke-WebRequest -Method PUT http://localhost:3000/vault/secret/1 `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"site":"correo-actualizado","password":"NuevaClave456!","category":"password"}'
```

### Eliminar un secreto

```powershell
Invoke-WebRequest -Method DELETE http://localhost:3000/vault/secret/1 `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Activar o desactivar un usuario (solo admin)

```powershell
Invoke-WebRequest -Method PATCH http://localhost:3000/auth/users/2/status `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"is_active":false}'
```

### Ver usuarios conectados en este momento (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/admin/active-users `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Ver sesiones activas de un usuario (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/users/2/sessions `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Revocar todas las sesiones de un usuario (solo admin)

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/users/2/sessions/revoke `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Ver bitácora de auditoría (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/admin/audit-logs `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Validar sesión activa

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/session/validate `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Verificación de persistencia en PostgreSQL

```powershell
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT id, email, role, is_active FROM users;"
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT id, site, owner FROM secrets;"
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT id, user_id, issued_at, expires_at FROM auth_session ORDER BY issued_at DESC LIMIT 5;"
```

### Verificación de Redis

```powershell
docker compose exec redis redis-cli KEYS "*"
docker compose exec redis redis-cli -n 1 KEYS "*"   # db=1 auth (login_fail)
docker compose exec redis redis-cli DBSIZE
```

### Prueba de acceso no autorizado

```powershell
curl http://localhost:3000/vault/secret
```

Resultado esperado: `401 Unauthorized`.

### Prueba de rate limiting

```powershell
for ($i = 1; $i -le 15; $i++) {
    curl -X GET http://localhost:3000/vault/secret -H "Authorization: Bearer TOKEN_AQUI"
}
```

Algunas respuestas deberían terminar en `429 Too Many Requests`.

### Verificación de monitoreo

```powershell
curl http://localhost:9090/-/healthy
curl http://localhost:8080/healthz
curl http://localhost:3100/ready
```

### Revisión de logs

```powershell
docker compose logs auth --tail=50
docker compose logs vault --tail=50
docker compose logs worker --tail=50
docker compose logs gateway --tail=50
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

### Ver logs en tiempo real

```powershell
docker compose logs auth -f
docker compose logs vault -f
```

### Publicar nuevas imágenes a Docker Hub

```powershell
$pat = "dckr_pat_XXXXXXXX"
$pat | docker login -u necromanoger --password-stdin
docker compose build
docker push necromanoger/securevault-auth:v1.2.0
docker push necromanoger/securevault-vault:v1.2.0
docker push necromanoger/securevault-worker:v1.2.0
docker push necromanoger/securevault-frontend:v1.2.0
```

## 7. Base de datos

Acceso a PostgreSQL:

```powershell
docker compose exec postgres psql -U vault -d vaultdb
```

Comandos útiles en psql:

```sql
\dt                          -- listar tablas
SELECT * FROM users;         -- todos los usuarios
SELECT * FROM secrets;       -- todos los secretos
SELECT * FROM auth_session;  -- sesiones activas
SELECT * FROM admin_audit_log ORDER BY created_at DESC LIMIT 10; -- auditoría
```

### Promover usuario a admin manualmente

```sql
UPDATE users SET role = 'admin' WHERE email = 'tu_correo@dominio.com';
```

### Limpiar bloqueo Redis manualmente

```powershell
docker compose exec redis redis-cli -n 1 DEL "login_fail:email@dominio.com"
```

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

| Síntoma | Causa probable | Solución |
|---------|---------------|----------|
| No se pudieron cargar los datos de la bóveda | Vault caído o token inválido | Revisar `docker compose logs vault` |
| 423 Locked al hacer login | 3 intentos fallidos en Redis | Esperar 5 min o limpiar clave Redis manualmente |
| Email de recovery no llega | Mailjet no configurado | Verificar `MAILJET_API_KEY` y `MAILJET_SENDER_EMAIL` en compose |
| Panel admin no se actualiza | Error de red o token expirado | El panel detecta 401 y redirige; volver a hacer login |
| Secretos no descifran al reiniciar | `ENCRYPTION_KEY` cambió | Usar la misma clave Fernet que usó al crear los secretos |
| `Permission denied /var/cache/nginx` | `USER nginx` en Dockerfile frontend | Remover esa línea del Dockerfile |
| `FileNotFoundError: Config file '.env'` | SlowAPI busca `.env` | Agregar `RUN touch .env` en Dockerfile de vault |


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

### Credenciales de acceso inicial

| Rol           | Email                        | Contrasena          |
|---------------|------------------------------|---------------------|
| Administrador | admin@securevault.local      | AdminSecure123!@#   |
| Usuario       | (registro libre desde la UI) | (definida al crear) |

El administrador inicial se crea automaticamente al arrancar auth-service si no existe.

### Comportamiento segun rol

- **Usuario regular** (rol `user`): al autenticarse accede a `/boveda` con su boveda personal de secretos (crear, editar, eliminar sus propios secretos).
- **Administrador** (rol `admin`): al autenticarse accede a `/admin` con el panel de administracion. Puede:
  - Ver todos los usuarios registrados con su estado (activo/inactivo) y rol.
  - Ver usuarios conectados en tiempo real con contador de sesiones activas.
  - Cambiar el rol de un usuario (user ↔ admin).
  - Activar o desactivar cuentas de usuario.
  - Revocar sesiones activas de usuarios individuales.
  - Gestionar sesiones por usuario con opciones de revocación masiva.
  - Acceder a bitácora de auditoría con registro de todas las acciones administrativas.
  - No puede cambiar su propio rol ni desactivarse a sí mismo.

Acceso de monitoreo en producción:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- cAdvisor: http://localhost:8080
- Loki: http://localhost:3100

## 5. Consultas de validacion funcional

Las siguientes pruebas permiten evidenciar que el proyecto esta operativo mas alla del arranque de contenedores.

### Registro de usuario

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/register `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"evaluador1@test.com","password":"ClaveSegura123!"}'
```

### Login y obtencion de token

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/login `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"evaluador1@test.com","password":"ClaveSegura123!"}'
```

El resultado esperado es un `access_token`. Ese valor debe reutilizarse en las consultas autenticadas.

### Login como administrador

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/login `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"admin@securevault.local","password":"AdminSecure123!@#"}'
```

### Ver perfil del usuario autenticado

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/me `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Listar usuarios registrados (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/users `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Cambiar rol de un usuario (solo admin)

```powershell
Invoke-WebRequest -Method PATCH http://localhost:3000/auth/users/2/role `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"role":"admin"}'
```

### Crear un secreto

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/vault/secret `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"site":"correo-institucional","password":"MiClave123!","category":"password"}'
```

### Listar secretos

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/vault/secret `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Actualizar un secreto

```powershell
Invoke-WebRequest -Method PUT http://localhost:3000/vault/secret/1 `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"site":"correo-actualizado","password":"NuevaClave456!","category":"password"}'
```

### Eliminar un secreto

```powershell
Invoke-WebRequest -Method DELETE http://localhost:3000/vault/secret/1 `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Activar o desactivar un usuario (solo admin)

```powershell
Invoke-WebRequest -Method PATCH http://localhost:3000/auth/users/2/status `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"; "Content-Type"="application/json"} `
  -Body '{"is_active":false}'
```

### Ver usuarios conectados en este momento (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/admin/active-users `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Ver sesiones activas de un usuario (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/users/2/sessions `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Revocar todas las sesiones de un usuario (solo admin)

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/users/2/sessions/revoke `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Ver bitácora de auditoría (solo admin)

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/admin/audit-logs `
  -Headers @{"Authorization"="Bearer TOKEN_ADMIN_AQUI"}
```

### Validar sesión activa

```powershell
Invoke-WebRequest -Method GET http://localhost:3000/auth/session/validate `
  -Headers @{"Authorization"="Bearer TOKEN_AQUI"}
```

### Verificacion de persistencia en PostgreSQL

```powershell
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT id, email, role FROM users;"
docker compose exec postgres psql -U vault -d vaultdb -c "SELECT id, site, owner FROM secrets;"
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
