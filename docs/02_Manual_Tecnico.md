# Manual Tecnico

## 1. Arquitectura general

SecureVault esta implementado con arquitectura de microservicios ligeros:

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

    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    U --> UC5
    U --> UC6
    U --> UC7

    UC1 -. usa .-> A[(Auth Service)]
    UC2 -. usa .-> A
    UC3 -. usa .-> V[(Vault Service)]
    UC4 -. usa .-> V
    UC5 -. usa .-> V
    UC6 -. usa .-> V

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

    User->>FE: Login(username, password)
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
- username: string, unico.
- hashed_password: string.

### Tabla secrets

- id: integer, PK.
- site: string.
- encrypted_password: string.
- owner: string (usuario propietario).

## 10. Seguridad implementada

- Hash de contrasena: bcrypt mediante passlib.
- JWT firmado con HS256 y expiracion configurable.
- Validacion de token en endpoints de boveda.
- Cifrado de secretos con Fernet.
- Rate limiting en vault: 10 requests/minute por IP.

## 11. Endpoints principales

### Auth Service

- POST /auth/register
- POST /auth/login

### Vault Service

- GET /vault/secret
- POST /vault/secret
- PUT /vault/secret/{secret_id}
- DELETE /vault/secret/{secret_id}

## 12. Variables y configuracion

- database_url: conexion PostgreSQL.
- secret_key: clave de firma JWT.
- algorithm: algoritmo JWT (HS256).
- token_exp_minutes: expiracion del token.
- ENCRYPTION_KEY: clave de cifrado de secretos recomendada para persistencia.

## 13. Notas tecnicas relevantes

- Si ENCRYPTION_KEY no esta definida, se genera una clave efimera y los secretos previos pueden no descifrarse tras reinicio.
- Nginx enruta /auth/ a auth y /vault/ a vault.
- El frontend consume rutas relativas /auth/_ y /vault/_.
- Vault publica eventos asincronos en Redis (jobs:security_events) y worker-service los procesa.
- Se incluye un modelo DFD importable en OWASP Threat Dragon en threat-model/01_SecureVault_Operativo_Threat_Dragon.json.
- Se incluye un segundo modelo Threat Dragon para CI/CD y supply chain en threat-model/02_SecureVault_CICD_Threat_Dragon.json.

## 14. Mejoras futuras sugeridas

- Migraciones formales con Alembic.
- Gestion segura de secretos con vault manager o variables protegidas.
- Observabilidad centralizada (logs estructurados, metricas, trazas).
- Pruebas automatizadas de integracion.
