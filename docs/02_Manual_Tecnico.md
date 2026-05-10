# Manual Técnico — SecureVault Pro v1.2

## 1. Arquitectura general

SecureVault Pro está implementado con arquitectura de microservicios ligeros:

- **Frontend SPA** (React + Vite) servido por Nginx (gateway).
- **Auth Service** (FastAPI, Python 3.11): registro, login con bloqueo de cuenta, recuperación de contraseña, gestión de sesiones y administración RBAC.
- **Vault Service** (FastAPI, Python 3.11): CRUD de secretos cifrados por usuario autenticado.
- **Worker Service** (Python): proceso asíncrono para consumo de eventos de seguridad desde Redis.
- **PostgreSQL**: persistencia de usuarios, secretos, sesiones y auditoría.
- **Redis** (db=0 vault / db=1 auth): rate limiting, cola de eventos, contador de intentos fallidos de login (bloqueo de cuenta).
- **Mailjet API v3.1**: envío de emails de verificación y recuperación de contraseña.
- **Docker Compose**: orquestación local.

## 2. Estructura de componentes

```
securevault-pro/
├── frontend-spa/           # React + Vite, SPA con RBAC, bloqueo y recovery UI
├── servicios/
│   ├── auth-service/      # FastAPI — auth, JWT, RBAC, lockout, email, admin
│   ├── vault-service/     # FastAPI — secretos cifrados Fernet, compartir por email
│   └── worker-service/    # Python — eventos asíncronos vía Redis BLPOP
├── gateway/               # Nginx reverse proxy (enruta /auth/, /vault/)
├── infraestructura/       # Ansible IaC
├── orquestacion/          # Kubernetes/K3s manifests
└── monitoring/            # Prometheus, Grafana, Loki, Promtail, Falco
```

## 3. Diagrama de Casos de Uso — Completo v1.2

Cubre todos los actores y flujos incluyendo bloqueo, recuperación y administración en tiempo real.

```mermaid
flowchart LR
    U([Usuario Regular])
    A([Administrador])
    S([Sistema / Redis])

    subgraph Auth[Autenticación]
        UC1([Registrar cuenta])
        UC2([Iniciar sesión])
        UC3([Ver intentos fallidos])
        UC4([Bloquear cuenta])
        UC5([Recibir email de recovery])
        UC6([Recuperar contraseña])
        UC7([Cerrar sesión])
    end

    subgraph Vault[Bóveda Personal]
        UC8([Crear secreto])
        UC9([Listar secretos])
        UC10([Editar secreto])
        UC11([Eliminar secreto])
        UC12([Compartir secreto por email])
    end

    subgraph Admin[Panel Administración]
        UC13([Ver estadísticas tiempo real])
        UC14([Ver usuarios conectados])
        UC15([Cambiar rol de usuario])
        UC16([Activar/Desactivar cuenta])
        UC17([Revocar sesiones])
        UC18([Ver bitácora de auditoría])
        UC19([Actualización automática 30s])
    end

    U --> UC1
    U --> UC2
    UC2 --> UC3
    UC3 --> UC4
    UC4 --> UC5
    UC5 --> UC6
    UC6 --> UC2
    U --> UC7
    U --> UC8
    U --> UC9
    U --> UC10
    U --> UC11
    U --> UC12

    A --> UC2
    A --> UC13
    A --> UC14
    A --> UC15
    A --> UC16
    A --> UC17
    A --> UC18
    S --> UC19
    UC19 --> UC13
    UC19 --> UC14

    UC2 -. usa .-> AuthSvc[(Auth Service)]
    UC4 -. redis .-> Redis[(Redis db=1)]
    UC6 -. limpia .-> Redis
    UC8 -. usa .-> VaultSvc[(Vault Service)]
    UC15 -. usa .-> AuthSvc
    UC18 -. usa .-> AuthSvc
```

## 4. DFD Nivel 0 — Vista de Contexto

```mermaid
flowchart LR
    U[Usuario / Navegador] --> SV[SecureVault Pro Platform]
    SV --> DB[(PostgreSQL)]
    SV --> R[(Redis)]
    SV --> Mail[Mailjet API]
    SV --> GH[GitHub Actions / Docker Hub]
```

## 5. DFD Nivel 1 — Flujos internos

```mermaid
flowchart LR
    U[Usuario] --> G[Gateway Nginx]
    G --> FE[Frontend SPA]
    G --> A[Auth Service]
    G --> V[Vault Service]
    A --> DB[(PostgreSQL)]
    A --> R[(Redis db=1\nlogin_fail / sesiones)]
    A --> Mail[Mailjet API]
    V --> DB
    V --> R2[(Redis db=0\nrate limit / jobs)]
    V --> W[Worker Service]
    W --> DB
```

## 6. Diagrama de Despliegue

```mermaid
flowchart TB
    Dev[Developer] --> GH[GitHub Repository]
    GH --> CI[GitHub Actions CI/Security]
    CI --> DH[(Docker Hub\nnecromanoger/*:v1.2.0)]
    CI --> CD[Deploy Workflow]

    subgraph Prod[Production Host]
      GW[Gateway Container :3000]
      AU[Auth Container :8001]
      VA[Vault Container :8002]
      WK[Worker Container]
      PG[(PostgreSQL :5432)]
      RD[(Redis :6379)]
    end

    CD --> GW
    CD --> AU
    CD --> VA
    CD --> WK
    AU --> PG
    AU --> RD
    VA --> PG
    VA --> RD
    WK --> PG
    WK --> RD
```

## 7. Diagrama de Secuencia — Login con bloqueo de cuenta

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend SPA
    participant AUTH as Auth Service
    participant Redis as Redis (db=1)
    participant Mail as Mailjet API
    participant DB as PostgreSQL

    User->>FE: Login(email, password)
    FE->>AUTH: POST /auth/login
    AUTH->>DB: Validar credenciales
    DB-->>AUTH: Credenciales inválidas

    AUTH->>Redis: INCR login_fail:{email}
    Redis-->>AUTH: count = 1 (o 2)
    AUTH->>Redis: EXPIRE login_fail:{email} 300s
    AUTH-->>FE: 401 Unauthorized (quedan X intentos)
    FE-->>User: Muestra intentos restantes

    Note over User,Redis: 3er intento fallido
    AUTH->>Redis: INCR → count = 3
    AUTH->>Mail: send_reset_email(locked_out=True)
    Mail-->>User: Email con enlace ?reset_token=T&email=E
    AUTH-->>FE: 423 Locked
    FE-->>User: Banner bloqueo + panel recovery abierto
```

## 8. Diagrama de Secuencia — Recuperación de contraseña

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend SPA
    participant AUTH as Auth Service
    participant Redis as Redis (db=1)
    participant DB as PostgreSQL

    User->>FE: Clic enlace email (?reset_token=T&email=E)
    FE-->>User: Login abierto con token/email pre-cargados + panel recovery

    User->>FE: Ingresa nueva contraseña
    FE->>AUTH: POST /auth/password-reset/confirm
    AUTH->>DB: reset_password(email, token, new_password)
    DB-->>AUTH: updated = True
    AUTH->>Redis: DEL login_fail:{email}
    Redis-->>AUTH: OK (bloqueo eliminado)
    AUTH-->>FE: 200 {"msg": "Password updated"}
    FE-->>User: setIsLockedOut(false) + setFailedAttempts(0)
    FE-->>User: "Contraseña restablecida. Ya puedes iniciar sesión."
```

## 9. Diagrama de Secuencia — Panel Admin con polling

```mermaid
sequenceDiagram
    autonumber
    actor Admin
    participant FE as AdminPage (React)
    participant AUTH as Auth Service
    participant Timer as setInterval (30s)

    Admin->>FE: Accede a /admin
    FE->>AUTH: GET /auth/users + /auth/admin/active-users + /auth/admin/audit-logs
    AUTH-->>FE: Datos completos (Promise.allSettled)
    FE-->>Admin: Renderiza panel con contador regresivo 30s

    loop Cada 30 segundos
        Timer->>FE: tick → refreshAll()
        FE->>AUTH: GET paralelo: users + active-users + audit-logs + sessions
        alt Token válido
            AUTH-->>FE: 200 Datos actualizados
            FE-->>Admin: Panel actualizado + "justo ahora"
        else Token expirado (401/403)
            AUTH-->>FE: 401 Unauthorized
            FE->>FE: clearAuthSession() + navigate("/")
            FE-->>Admin: Redirige al login
        end
    end
```

## 10. Diagrama de Secuencia — Login exitoso con JWT diferenciado

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend SPA
    participant AUTH as Auth Service
    participant DB as PostgreSQL

    User->>FE: Login(email, password)
    FE->>AUTH: POST /auth/login
    AUTH->>DB: Validar credenciales
    DB-->>AUTH: User{role: "admin" | "user"}

    alt role == "admin"
        AUTH->>AUTH: exp = 480min (8 horas)
    else role == "user"
        AUTH->>AUTH: exp = 60min (1 hora)
    end

    AUTH->>DB: INSERT auth_session (jti, expires_at)
    AUTH-->>FE: JWT con exp diferenciado + rol en payload
    FE-->>User: Redirige a /admin (admin) o /boveda (user)
```

## 11. Diagrama de Secuencia DevSecOps (CI/CD)

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant GH as GitHub
    participant CI as CI DevSecOps Workflow
    participant REG as Docker Hub
    participant CD as Deploy Workflow
    participant PROD as Production Host

    Dev->>GH: Push / Pull Request
    GH->>CI: Trigger CI pipeline
    CI->>CI: SAST (Semgrep+Bandit) + SCA (Trivy+pip-audit+npm audit)
    CI->>CI: Secret scanning (Gitleaks+TruffleHog)
    CI->>CI: IaC scan (Checkov) + Dockerfile lint (hadolint)
    CI->>CI: Tests (pytest + vitest) + DAST (OWASP ZAP)
    CI-->>GH: Pass / Fail checks
    GH->>CI: Merge a main
    CI->>REG: Build + push necromanoger/*:v1.2.0
    Dev->>CD: Aprobación de despliegue
    CD->>PROD: docker compose up -d (imágenes v1.2.0)
    PROD-->>CD: Servicios healthy
```

## 12. Modelo de datos

### Tabla `users`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | integer PK | Identificador único |
| email | string unique | Identificador de login |
| hashed_password | string | bcrypt hash |
| role | string | `admin` o `user` (default `user`) |
| is_active | boolean | Estado de la cuenta |
| email_verified | boolean | Verificación de correo |

### Tabla `auth_session`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | integer PK | Identificador único |
| user_id | integer FK | Referencia a users |
| token_jti | string | JWT ID único (para revocación) |
| issued_at | datetime | Emisión del token |
| expires_at | datetime | Expiración (60min user / 480min admin) |

### Tabla `secrets`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | integer PK | Identificador único |
| site | string | Nombre del sitio o servicio |
| encrypted_password | string | Cifrado Fernet |
| category | string | password, api_key, token, etc. |
| description | string | Descripción opcional |
| owner | string | Email del propietario |
| expires_at | datetime | Expiración opcional |

### Claves Redis (auth, db=1)

| Clave | TTL | Descripción |
|-------|-----|-------------|
| `login_fail:{email}` | 300s | Contador intentos fallidos (bloqueo de cuenta) |

## 13. Seguridad implementada

- **Hash de contraseña**: bcrypt mediante passlib.
- **JWT HS256**: expiración diferenciada: 60 min (user) / 480 min (admin, configurable con `ADMIN_TOKEN_EXP_MINUTES`).
- **Claim `sub`**: string (str(user.id)), conforme RFC 7519.
- **Bloqueo de cuenta**: Redis TTL 300s, HTTP 423, reset limpia la clave automáticamente.
- **Email de recovery**: Mailjet API v3.1, HTML responsivo con enlace directo `?reset_token=TOKEN&email=EMAIL`.
- **Cifrado de secretos**: Fernet (clave fija persistente `ENCRYPTION_KEY`).
- **Rate limiting**: vault — 10 req/min por IP (SlowAPI + Redis).
- **RBAC**: rol validado en cada endpoint protegido; admin 403 si intenta acceder a rutas de user y viceversa.
- **Revocación de sesión**: via JTI en tabla `auth_session`; `POST /auth/users/{id}/sessions/revoke` invalida tokens activos.
- **Expiración automática en frontend**: polling detecta 401/403 y redirige al login con `clearAuthSession()`.
- **Separación de servicios**: Gateway Nginx separa frontend de backends.

## 14. Endpoints principales

### Auth Service (puerto 8001)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/auth/register` | Registro de usuario | — |
| POST | `/auth/login` | Login + JWT (bloqueo a 3 intentos) | — |
| GET | `/auth/me` | Perfil autenticado | JWT |
| GET | `/auth/session/validate` | Validar sesión activa | JWT |
| POST | `/auth/password-reset/request` | Solicitar token de reset | — |
| POST | `/auth/password-reset/confirm` | Confirmar reset + limpiar Redis | — |
| POST | `/auth/confirm-email` | Verificar correo | — |
| GET | `/auth/users` | Listar usuarios | admin |
| PATCH | `/auth/users/{id}/role` | Cambiar rol | admin |
| PATCH | `/auth/users/{id}/status` | Activar/desactivar | admin |
| DELETE | `/auth/users/{id}` | Eliminar usuario | admin |
| GET | `/auth/users/{id}/sessions` | Ver sesiones | admin |
| POST | `/auth/users/{id}/sessions/revoke` | Revocar sesiones | admin |
| GET | `/auth/admin/active-users` | Usuarios conectados ahora | admin |
| GET | `/auth/admin/audit-logs` | Bitácora de auditoría | admin |

### Vault Service (puerto 8002)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/vault/secret` | Listar secretos (user: propios; admin: todos) | JWT |
| POST | `/vault/secret` | Crear secreto | JWT |
| PUT | `/vault/secret/{id}` | Actualizar secreto | JWT |
| DELETE | `/vault/secret/{id}` | Eliminar secreto | JWT |
| POST | `/vault/secret/{id}/share` | Compartir secreto por email | JWT |

## 15. Variables de configuración

| Variable | Servicio | Default | Descripción |
|----------|----------|---------|-------------|
| `DATABASE_URL` | auth, vault | postgresql://... | Conexión PostgreSQL |
| `SECRET_KEY` | auth | securevaultsecret | Clave firma JWT |
| `ALGORITHM` | auth | HS256 | Algoritmo JWT |
| `TOKEN_EXP_MINUTES` | auth | 60 | Expiración JWT para rol `user` |
| `ADMIN_TOKEN_EXP_MINUTES` | auth | 480 | Expiración JWT para rol `admin` |
| `ENCRYPTION_KEY` | vault | (Fernet key) | Clave cifrado secretos (fija y persistente) |
| `BOOTSTRAP_ADMIN_EMAIL` | auth | admin@securevault.local | Email admin inicial |
| `BOOTSTRAP_ADMIN_PASSWORD` | auth | AdminSecure123!@# | Contraseña admin inicial |
| `REQUIRE_EMAIL_VERIFICATION` | auth | true | Verificación de correo al registrar |
| `MAILJET_API_KEY` | auth, vault | — | API Key Mailjet |
| `MAILJET_SECRET_KEY` | auth, vault | — | Secret Key Mailjet |
| `MAILJET_SENDER_EMAIL` | auth, vault | — | Email remitente |
| `MAILJET_SENDER_NAME` | auth, vault | SecureVault Pro | Nombre remitente |

## 16. Notas técnicas relevantes

- `login_fail:{email}` en Redis (db=1) se incrementa por cada intento fallido y se elimina al resetear contraseña o tras TTL de 5 min.
- El endpoint `POST /auth/login` es `async def` para poder hacer `await send_reset_email()` en el tercer fallo.
- `build_access_token()` en `auth_service.py` elige `exp_minutes` según `user.role` antes de llamar a `create_access_token()`.
- El frontend usa `Promise.allSettled` en `refreshAll()` para que un fallo parcial no bloquee las demás cargas. Si alguno lanza `SessionExpiredError`, todos los intervalos se detienen y se redirige.
- `SessionExpiredError` es una clase personalizada en `users.js` que permite distinguir 401/403 de errores de red genéricos.
- El contador regresivo del admin panel usa un `setInterval` separado (tick de 1s) desacoplado del intervalo de polling (30s) para evitar desincronización.
- Nginx enruta `/auth/` a auth-service:8001 y `/vault/` a vault-service:8002. El frontend consume rutas relativas.
- Bootstrap de admin es idempotente: si ya existe, no se crea ni modifica.

## 17. Mejoras futuras sugeridas

- Migraciones formales con Alembic.
- Refresh tokens para evitar relogin al expirar la sesión de usuario.
- WebSockets para actualización en tiempo real del panel admin sin polling.
- Gestión de secretos con Vault Manager o variables protegidas en CI.
- Observabilidad centralizada (métricas, trazas distribuidas).
- MFA (TOTP) como segundo factor de autenticación.


- Frontend SPA (React + Vite) servido por Nginx.
- Auth Service (FastAPI): registro y login, emision de JWT.
- Vault Service (FastAPI): CRUD de secretos por usuario autenticado.
- Worker Service (Python): proceso asincrono para consumo de eventos de seguridad en segundo plano.
- PostgreSQL: persistencia de usuarios y secretos.
- Redis: backend de rate limiting para Vault Service.
- Docker Compose: orquestacion local.

## 2. Estructura de componentes

- frontend-spa/: interfaz React/Vite.
- servicios/auth-service/: autenticacion y token JWT.
- servicios/vault-service/: gestion de boveda con cifrado.
- servicios/worker-service/: worker asincrono para tareas desacopladas.
- infraestructura/ansible/: automatizacion IaC de despliegue.
- orquestacion/kubernetes/: manifests base para K3s/Kubernetes.
- nginx/: reverse proxy de entrada.
- docker-compose.yml: despliegue local integrado.

## 3. Diagrama de Casos de Uso

El siguiente diagrama resume las interacciones principales del usuario con el sistema SecureVault:

```mermaid
flowchart LR
    U([Usuario])

    subgraph SV[SecureVault]
        UC1([Registrar cuenta])
        UC2([Iniciar sesion])
        UC3([Guardar secreto])
        UC4([Listar secretos])
        UC5([Editar secreto])
        UC6([Eliminar secreto])
        UC7([Cerrar sesion])
    end

    subgraph ADM[Administracion]
        UC8([Ver todos los usuarios])
        UC9([Cambiar rol de usuario])
    end

    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    U --> UC5
    U --> UC6
    U --> UC7
    Admin([Administrador]) --> UC8
    Admin --> UC9

    UC1 -. usa .-> A[(Auth Service)]
    UC2 -. usa .-> A
    UC3 -. usa .-> V[(Vault Service)]
    UC4 -. usa .-> V
    UC5 -. usa .-> V
    UC6 -. usa .-> V
    UC8 -. usa .-> A
    UC9 -. usa .-> A

    A -. persiste .-> DB[(PostgreSQL)]
    V -. persiste .-> DB
    V -. rate limiting .-> R[(Redis)]
```

Cobertura funcional y trazabilidad:

- Registro e inicio de sesion: alineado con CP-01 a CP-04 del plan de pruebas.
- CRUD de secretos: alineado con CP-05 a CP-08 del plan de pruebas.
- Control de acceso y limites: relacionado con CP-09 y CP-10.

## 4. DFD Nivel 0 (Critico)

Este diagrama representa la vista de contexto del sistema, mostrando a SecureVault como una unidad frente al usuario y sus dependencias principales.

```mermaid
flowchart LR
    U[Usuario] --> SV[SecureVault Platform]
    SV --> DB[(PostgreSQL)]
    SV --> R[(Redis)]
    SV --> GH[GitHub Actions and Registries]
```

## 5. DFD Nivel 1 (Critico)

Este diagrama descompone SecureVault en sus procesos y almacenes principales.

```mermaid
flowchart LR
    U[Usuario] --> G[Gateway Nginx]
    G --> FE[Frontend SPA]
    G --> A[Auth Service]
    G --> V[Vault Service]
    A --> DB[(PostgreSQL)]
    V --> DB
    V --> R[(Redis)]
```

## 6. Diagrama de Despliegue (Critico)

Este diagrama representa el despliegue DevSecOps con CI/CD, registros de imagenes y entorno productivo.

```mermaid
flowchart TB
    Dev[Developer] --> GH[GitHub Repository]
    GH --> CI[GitHub Actions CI and Security]
    CI --> GHCR[(GHCR)]
    CI --> DH[(Docker Hub)]
    CI --> CD[Deploy Workflow with Approval]

    subgraph Prod[Production Host]
      GW[Gateway Container]
      AU[Auth Container]
      VA[Vault Container]
      PG[(PostgreSQL)]
      RD[(Redis)]
    end

    CD --> GW
    CD --> AU
    CD --> VA
    AU --> PG
    VA --> PG
    VA --> RD
```

## 7. Diagrama de Secuencia Funcional (Critico)

Flujo principal de autenticacion y guardado de secreto.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Frontend SPA
    participant GW as Nginx Gateway
    participant AUTH as Auth Service
    participant VAULT as Vault Service
    participant DB as PostgreSQL

    User->>FE: Login(email, password)
    FE->>GW: POST /auth/login
    GW->>AUTH: Forward request
    AUTH->>DB: Validate user credentials
    DB-->>AUTH: User valid
    AUTH-->>GW: JWT access token
    GW-->>FE: Token

    User->>FE: Save secret(site, password)
    FE->>GW: POST /vault/secret + Bearer token
    GW->>VAULT: Forward request
    VAULT->>VAULT: Validate JWT and rate-limit
    VAULT->>DB: Store encrypted secret
    DB-->>VAULT: OK
    VAULT-->>GW: 200 saved
    GW-->>FE: Success response
```

## 8. Diagrama de Secuencia DevSecOps (Critico)

Flujo principal desde PR hasta despliegue productivo con controles de seguridad.

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant GH as GitHub
    participant CI as CI DevSecOps Workflow
    participant REG as GHCR and Docker Hub
    participant CD as Deploy Workflow
    participant PROD as Production Host

    Dev->>GH: Push or Pull Request
    GH->>CI: Trigger CI pipeline
    CI->>CI: Run SAST, SCA, Secrets, IaC, DAST
    CI-->>GH: Pass or Fail checks
    GH->>CI: Merge to main
    CI->>REG: Build and publish versioned images
    Dev->>CD: Manual deploy approval
    CD->>PROD: Pull images and compose up
    PROD-->>CD: Healthy services status
```

## 9. Modelo de datos

### Tabla users

- id: integer, PK.
- email: string, unico (identificador principal).
- hashed_password: string (bcrypt).
- role: string, valores posibles: `admin` o `user` (por defecto `user`).

Nota: el usuario administrador inicial se crea automaticamente al arrancar el servicio con las variables de entorno `BOOTSTRAP_ADMIN_EMAIL` y `BOOTSTRAP_ADMIN_PASSWORD`.

### Tabla secrets

- id: integer, PK.
- site: string (nombre del sitio o servicio).
- encrypted_password: string (cifrado Fernet).
- category: string (ej. password, api_key, token).
- description: string, opcional.
- owner: string (email del usuario propietario).
- expires_at: datetime, opcional (gestion por worker).

## 10. Seguridad implementada

- Hash de contrasena: bcrypt mediante passlib.
- JWT firmado con HS256 y expiracion configurable (60 minutos).
- Claim `sub` del JWT codificado como string (`str(user.id)`) conforme RFC 7519.
- Validacion de token en endpoints de boveda y administracion.
- Cifrado de secretos con Fernet (clave fija persistente via `ENCRYPTION_KEY`).
- Rate limiting en vault: 10 requests/minute por IP.
- Control de acceso basado en roles (RBAC): rol `admin` y rol `user`.
  - Usuario regular: accede solo a sus propios secretos.
  - Administrador: accede al panel de gestion de usuarios y puede cambiar roles.
  - Restriccion: un administrador no puede cambiar su propio rol.

## 11. Endpoints principales

### Auth Service

- POST /auth/register — registro de usuario (rol `user` por defecto)
- POST /auth/login — autenticacion y emision de JWT
- GET /auth/me — perfil del usuario autenticado (requiere JWT)
- GET /auth/users — lista todos los usuarios (solo admin)
- PATCH /auth/users/{user_id}/role — cambia el rol de un usuario (solo admin)

### Vault Service

- GET /vault/secret — lista secretos del usuario; admin ve todos
- POST /vault/secret — crea un nuevo secreto
- PUT /vault/secret/{secret_id} — actualiza un secreto existente
- DELETE /vault/secret/{secret_id} — elimina un secreto

## 12. Variables y configuracion

- `DATABASE_URL`: conexion PostgreSQL.
- `SECRET_KEY`: clave de firma JWT.
- `ALGORITHM`: algoritmo JWT (HS256).
- `TOKEN_EXP_MINUTES`: expiracion del token (por defecto 60).
- `ENCRYPTION_KEY`: clave Fernet de 32 bytes en base64 para cifrado persistente de secretos. Debe ser fija entre reinicios.
- `BOOTSTRAP_ADMIN_EMAIL`: email del administrador inicial creado automaticamente al arrancar auth-service.
- `BOOTSTRAP_ADMIN_PASSWORD`: contrasena del administrador inicial. Debe cumplir politica de seguridad.

## 13. Notas tecnicas relevantes

- Si `ENCRYPTION_KEY` no esta definida, se genera una clave efimera y los secretos previos no pueden descifrarse tras reinicio. Siempre debe definirse con una clave Fernet fija.
- El claim `sub` del JWT debe ser string por RFC 7519; PyJWT rechaza valores enteros. El codigo usa `str(user.id)`.
- Nginx enruta `/auth/` a auth-service y `/vault/` a vault-service.
- El frontend consume rutas relativas `/auth/*` y `/vault/*`.
- El enrutamiento del frontend es basado en rol:
  - Usuario con rol `user` en `/boveda` ve `DashboardPage` (boveda personal).
  - Usuario con rol `admin` en `/boveda` ve `AdminPage` (panel de administracion).
  - La ruta `/admin` esta protegida exclusivamente para administradores.
- El bootstrap de admin es idempotente: si el usuario ya existe, no se crea de nuevo.
- Vault publica eventos asincronos en Redis (`jobs:security_events`) y worker-service los procesa.
- Se incluye modelo DFD importable en OWASP Threat Dragon en `threat-model/01_SecureVault_Operativo_Threat_Dragon.json`.
- Se incluye modelo Threat Dragon para CI/CD en `threat-model/02_SecureVault_CICD_Threat_Dragon.json`.

## 14. Mejoras futuras sugeridas

- Migraciones formales con Alembic.
- Gestion segura de secretos con vault manager o variables protegidas.
- Observabilidad centralizada (logs estructurados, metricas, trazas).
- Pruebas automatizadas de integracion.
