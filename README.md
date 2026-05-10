# SecureVault Pro

[![CI DevSecOps](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/ci-devsecops.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/ci-devsecops.yml)
[![DAST ZAP](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/dast-zap.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/dast-zap.yml)
[![Container Release](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/container-release.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/container-release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**UNIMINUTO · Especialización en Ciberseguridad · Seguridad Entornos Cloud DevOps**

---

## Descripción del Proyecto

SecureVault Pro es una plataforma completa para la **gestión segura de secretos** basada en arquitectura de microservicios. Implementa controles de seguridad en cada etapa del ciclo de vida del desarrollo (Plan → Code → Build → Test → Release → Operate), demostrando un enfoque integral **DevSecOps** con automatización, threat modeling y monitoreo continuo.

La plataforma permite a equipos de desarrollo y operaciones almacenar, rotar y auditar el acceso a secretos (API keys, credenciales, certificados) de forma centralizada, con auditoría completa y cumplimiento de estándares de seguridad.

### Propósito principal

- **Centralizar gestión segura** de secretos con control de acceso basado en roles (RBAC).
- **Automatizar pipeline DevSecOps** de ciclo completo con controles de seguridad en cada fase.
- **Implementar arquitectura de microservicios** contenerizada con alta disponibilidad y escalabilidad.
- **Demostrar auditoría y trazabilidad** completa de acceso a secretos mediante logging inmutable.
- **Integrar herramientas DevSecOps** (SAST, SCA, DAST, threat modeling, monitoreo) en CI/CD.
- **Proveer infraestructura como código** (IaC) reproducible para despliegue en múltiples entornos.

### GUÍA RÁPIDA DE INSTALACIÓN

→ [Manual Técnico (arquitectura, componentes y endpoints)](docs/02_Manual_Tecnico.md)

→ [Manual de Operación y DevOps (arranque, despliegue y validaciones)](docs/03_Manual_Operacion_DevOps.md)

###  Ubicación Proyecto

- **Repositorio principal:** https://github.com/johngutierrez80/Securevault-pro
- **Imágenes Docker:** https://hub.docker.com/repositories/necromanoger

---

## Documentación Técnica

### Autenticación y seguridad

El módulo de autenticación trabaja con **correo electrónico como identificador**, aplica validación de correo y política mínima de contraseñas al registrar usuarios, y retorna un JWT que incluye el rol del usuario.

Incorpora flujos de **recuperación de contraseña**, **bloqueo automático de cuenta** y **expiración diferenciada de sesión por rol**.

RBAC implementado:

- Roles soportados: `admin`, `user`.
- Endpoints administrativos de roles (solo `admin`):
  - `GET /auth/users` para listar usuarios con rol y estado.
  - `GET /auth/admin/active-users` para ver usuarios conectados en tiempo real.
  - `GET /auth/users/{user_id}/sessions` para listar sesiones activas.
  - `POST /auth/users/{user_id}/sessions/revoke` para revocar sesiones de un usuario.
  - `PATCH /auth/users/{user_id}/role` para promover o degradar roles.
  - `PATCH /auth/users/{user_id}/status` para activar o desactivar cuentas.
  - `GET /auth/admin/audit-logs` para acceder a bitácora de auditoría completa.
- Aplicación de rol en vault:
  - `user` solo gestiona sus propios secretos.
  - `admin` puede listar, editar y eliminar secretos de cualquier usuario.
- Panel administrativo `/admin`:
  - Visualización de estadísticas (usuarios totales, admins, activos, conectados).
  - Tabla de usuarios registrados con opciones de cambio de rol, activacion/desactivacion.
  - Tabla de usuarios conectados en tiempo real con sesiones activas y revocacion individual.
  - Gestión de sesiones por usuario con revocación masiva.
  - Bitácora de auditoría con registro de todas las acciones administrativas.
  - **Actualización automática cada 30 segundos** con contador regresivo y botón de refresh manual.
  - **Redirección automática al login** cuando la sesión expira o es revocada.

### Seguridad de acceso: bloqueo de cuenta y recovery

- **Bloqueo automático** tras 3 intentos de login fallidos consecutivos:
  - El estado de bloqueo se almacena en Redis con TTL de 5 minutos.
  - El login devuelve HTTP 423 (Locked) e inicia el flujo de recovery.
  - Se envía un correo automático con un enlace directo de restablecimiento de contraseña.
- **Enlace de recovery en el email**: contiene `?reset_token=TOKEN&email=EMAIL` apuntando al login.
- **Frontend adaptado**:
  - Detecta HTTP 423 y muestra banner de bloqueo (rojo).
  - Muestra conteo regresivo de intentos restantes (3 → 2 → 1 → bloqueado).
  - Abre automáticamente el panel de recuperación con el email y token pre-cargados del enlace.
  - Deshabilita el botón de login mientras la cuenta está bloqueada.
- **Al restablecer contraseña exitosamente**:
  - El backend elimina el contador Redis (`login_fail:{email}`), desbloqueando la cuenta.
  - El frontend limpia el estado de bloqueo y reactiva el botón de login.

### Expiración de sesión diferenciada por rol

| Rol | Duración JWT | Comportamiento al expirar |
|-----|-------------|--------------------------|
| `user` | 60 minutos | Redirige al login al siguiente request |
| `admin` | 8 horas | Panel detecta 401, limpia sesión y redirige al login automáticamente |

Cómo saber quién es admin y quién es user:

- Rol del usuario autenticado: `GET /auth/me`.
- Listado de usuarios y roles: `GET /auth/users` (requiere rol `admin`).

Bootstrap del primer administrador:

- Todos los registros nuevos inician con rol `user`.
- El servicio auth **crea automáticamente el primer admin al iniciar** usando credenciales configuradas en `docker-compose.yml`:
  - Email: `admin@securevault.local`
  - Contraseña: `AdminSecure123!@#`
- El bootstrap es **idempotente**: si ya existe un admin, no crea ni modifica otro.
- Las credenciales están **hardcodeadas** en el archivo de composición, eliminando la necesidad de variables de entorno `.env`.

Ejecución (sin requiere variables de entorno):

```powershell
# Con compilación desde código fuente
docker compose up -d --build

# O con imágenes publicadas
$env:IMAGE_TAG = "v1.2.0"
docker compose -f docker-compose.prod.yml up -d
```

**Acceso inicial:**
- Email: `admin@securevault.local`
- Contraseña: `AdminSecure123!@#`

**Gestión de roles posterior:**
- Ese usuario admin puede gestionar roles de otros usuarios usando `PATCH /auth/users/{user_id}/role`.
- Para promover/degradar roles manualmente en la BD:

```sql
UPDATE users SET role = 'admin' WHERE email = 'tu_correo@dominio.com';
```

### Encriptación de secretos y persistencia

- Los secretos se **cifran en reposo** usando Fernet (symmetric encryption) de la librería `cryptography`.
- La clave de encriptación está **configurada como variable fija** en `docker-compose.yml` (`ENCRYPTION_KEY`).
- Esta clave **persiste entre reinicios de contenedores**, permitiendo descifrar secretos almacenados previamente.
- Cuando los contenedores se eliminan pero los volúmenes de PostgreSQL persisten, los datos cifrados se recuperan y descifran correctamente.

### Flujo de procesamiento de secretos

```
Usuario → POST /auth/login → API valida credenciales + emite JWT (60min user / 8h admin)
                                        ↓
                  Intento fallido × 3 → Redis bloquea (TTL 5min) + email recovery
                                        ↓
                            HTTP 200 OK + token (inmediato)
                                        ↓
                    Cliente almacena token en localStorage
                                        ↓
          Usuario → GET /vault/secrets/{id} (con Authorization header)
                                        ↓
                    Auth Service valida JWT + RBAC
                                        ↓
               Vault Service recupera secret cifrado de BD
                                        ↓
                  Secret se descifra usando ENCRYPTION_KEY
                                        ↓
                        Retorna secret desencriptado
                                        ↓
                        Worker registra evento en DB
```

> El API implementa validación de JWT stateless con roles, encriptación de secretos en reposo con clave fija persistente y auditoría asincrónica de todos los accesos.

### Estructura del repositorio

```
securevault-pro/
├── LICENSE                          # Licencia MIT
├── README.md                        # Este archivo
├── docker-compose.yml              # Stack desarrollo
├── docker-compose.prod.yml         # Stack producción
├── .github/
│   └── workflows/                  # Pipelines CI/CD DevSecOps
├── infraestructura/
│   └── ansible/                    # IaC - Playbooks Ansible
├── orquestacion/
│   └── kubernetes/                 # Manifiestos K3s
├── servicios/
│   ├── auth-service/              # FastAPI - Autenticación JWT
│   ├── vault-service/             # FastAPI - Gestión de secretos
│   └── worker-service/            # Redis + BLPOP - Procesamiento asincrónico
├── frontend-spa/                   # React + Vite + Nginx
├── monitoring/                     # Configuraciones de monitoreo y seguridad
│   ├── prometheus/                # Prometheus config
│   ├── grafana/                   # Grafana provisioning
│   ├── loki/                      # Loki config
│   ├── promtail/                  # Promtail config
│   └── falco/                     # Falco rules
├── threat-model/                   # OWASP Threat Dragon exports
├── scripts/                        # Utilidades (pull-images, etc.)
├── versions/                       # Versiones previas del proyecto
└── docs/                          # Documentación académica y técnica
```

### Persistencia de datos

La información registrada en la aplicación se guarda principalmente en PostgreSQL. Para evitar que se pierda al eliminar y recrear contenedores, los archivos de datos de PostgreSQL y Redis se montan en volúmenes nombrados.

Esto permite que, después de levantar de nuevo el stack, los usuarios sigan viendo todos los datos previamente guardados:

- `pgdata` → `/var/lib/postgresql/data` (usuarios, secretos cifrados)
- `redisdata` → `/data` (cola de mensajes, cache de rate limiting)

**Clave de encriptación persistente:**
- La variable `ENCRYPTION_KEY` en `docker-compose.yml` es una clave Fernet fija.
- Esto asegura que los secretos cifrados en la BD se puedan descifrar incluso después de:
  - Detener y reiniciar contenedores
  - Eliminar contenedores (mientras persistan los volúmenes de datos)
  - Desplegar en diferentes ambientes (con la misma clave)

**Ejemplo de continuidad:**
```powershell
# Crear un secreto
docker compose up -d
# ... usuario crea secreto "AWS_KEY" ...

# Detener y eliminar contenedores (pero no volúmenes)
docker compose down

# Reiniciar - el secreto sigue disponible
docker compose up -d
# ... usuario ve "AWS_KEY" intacto ...
```

---

## Tecnologías Empleadas

### Stack tecnológico principal

| Componente | Tecnología | Versión | Descripción |
|-----------|-----------|---------|-------------|
| **Frontend** | React + Vite | 18.x / 5.x | SPA dinámico servido por Nginx. RBAC oculta elementos según rol |
| **API Backend** | FastAPI + Pydantic | Python 3.12 / 0.104+ | Gateway asincrónico ASGI. JWT stateless con rate limiting |
| **Worker** | Redis (BLPOP) | 7.0+ | Procesamiento asincrónico de eventos. Cola persistente de jobs |
| **Message Broker** | Redis | 7.0+ | Cola de mensajes y soporte de rate limiting |
| **Base de datos** | PostgreSQL | 16 Alpine | Integridad ACID. Migraciones versionadas con Alembic |
| **Autenticación** | JWT + passlib | HS256 | Auth stateless. bcrypt para passwords |
| **Proxy/Gateway** | Nginx | Alpine | Reverse proxy. Sirve SPA estática |
| **Conteneurización** | Docker Compose | v2 | Stack reproducible con healthchecks |
| **Orquestación** | Kubernetes/K3s | 1.28+ | Alta disponibilidad y escalado horizontal en producción |
| **CI/CD** | GitHub Actions | ubuntu-latest / actions@v4 | Pipeline DevSecOps automatizado |
| **IaC** | Ansible | 2.15+ | Aprovisionamiento de infraestructura |
| **Secret Scanning** | Gitleaks + TruffleHog | gitleaks-action@v2 / trufflehog@main | Detección de secretos comprometidos |
| **SAST** | Semgrep + Bandit | semgrep-action@v1 / pip latest | Análisis estático de código |
| **SCA** | Trivy + Dependency-Check + pip-audit | trivy-action@v0.25.0 / Action@main / pip latest | Análisis de dependencias y vulnerabilidades |
| **Dockerfile Lint** | hadolint | hadolint-action@v3.1.0 | Validación de mejores prácticas en Dockerfiles |
| **IaC Security** | Checkov | checkov-action@v12 | Escaneo de seguridad en IaC |
| **Testing** | pytest (Python) + vitest (Node.js) | pip latest / ^3.0.8 | Pruebas unitarias y de integración |
| **DAST** | OWASP ZAP | action-baseline@v0.14.0 | Pruebas dinámicas de seguridad |

### Servicios del stack Docker Compose

| Servicio | Imagen Base | Puerto | RAM |
|---------|-----------|--------|-----|
| **auth** | Build local | 8001 | 384 MB |
| **vault** | Build local | 8002 | 384 MB |
| **worker** | Build local | — | 384 MB |
| **gateway** | Build local | 3000 | 128 MB |
| **postgres** | postgres:16-alpine | 5432 | 512 MB |
| **redis** | redis:7-alpine | 6379 | 256 MB |

---

## Inicio Rápido (Quick Start)

### Prerrequisitos

| Requisito | Comando de verificación | Versión mínima |
|----------|----------------------|-----------------|
| Git | `git --version` | Cualquiera |
| Docker Engine | `docker --version` | 20.10+ |
| Docker Compose v2 | `docker compose version` | 2.0+ |
| RAM disponible | — | 4 GB (8 GB recomendado) |
| Disco libre | — | ~3 GB para imágenes |
| Puertos libres | — | 3000, 8001, 8002, 5432, 6379 |

**Nota:** Opcional (solo si desarrollas fuera de Docker): Python 3.12 y Node.js 20.

### Ejecución con imágenes publicadas (recomendado)

```powershell
# Descargar imágenes desde Docker Hub
.\scripts\pull-images.ps1

# Establecer versión
$env:IMAGE_TAG = "v1.2.0"

# Iniciar stack con compose producción
docker compose -f docker-compose.prod.yml up -d

# Verificar estado
docker compose -f docker-compose.prod.yml ps

# Acceso inmediato
# - Frontend: http://localhost:3000
# - Email: admin@securevault.local
# - Contraseña: AdminSecure123!@#
```

**Características:**
- No requiere compilación (reutiliza imágenes publicadas en Docker Hub).
- Las credenciales de bootstrap y clave de encriptación están **preconfiguradas** en `docker-compose.prod.yml`.
- PostgreSQL y Redis usan volúmenes nombrados para persistencia automática de datos.

### Ejecución con compilación desde código fuente

```powershell
# Descargar imágenes base
.\scripts\pull-images.ps1

# Establecer versión (opcional, para tagging local)
$env:IMAGE_TAG = "v1.2.0"

# Construir y ejecutar
docker compose up -d --build

# Verificar estado
docker compose ps

# Acceso inmediato
# - Frontend: http://localhost:3000
# - Email: admin@securevault.local
# - Contraseña: AdminSecure123!@#
```

**Características:**
- Compila los servicios (`auth`, `vault`, `worker`, `gateway`) desde Dockerfile locales.
- Las credenciales de bootstrap y clave de encriptación están **preconfiguradas** en `docker-compose.yml`.
- PostgreSQL y Redis usan volúmenes nombrados para persistencia automática.

### Accesos después de iniciar

| Componente | URL | Credenciales | Descripción |
|-----------|-----|--------------|-------------|
| **Frontend** | http://localhost:3000 | admin@securevault.local / AdminSecure123!@# | Interfaz de usuario SPA |
| **Auth API Docs** | http://localhost:8001/docs | — | Swagger - Autenticación |
| **Vault API Docs** | http://localhost:8002/docs | — | Swagger - Gestión de secretos |

**Primer acceso:**
- El usuario administrador se crea automáticamente al iniciar el stack.
- Email: `admin@securevault.local`
- Contraseña: `AdminSecure123!@#`
- Rol: `admin` (acceso a todos los secretos y gestión de usuarios)

---

## Pipeline CI/CD (DevSecOps)

Cada `push` o `pull_request` en la rama `main` ejecuta automáticamente:

```
[security]                [build]              [test]
Gitleaks               →  docker build    →  pytest (backend)
TruffleHog             →  trivy scan      →  vitest (frontend)
Semgrep                →  hadolint        →  ZAP baseline (DAST)
Bandit                 →  dependency-check→
pip-audit              →  checkov (IaC)   →
npm audit              →
```

**Workflows configurados:**

| Workflow | Archivo | Triggers | Controles |
|----------|---------|----------|-----------|
| **CI DevSecOps** | `.github/workflows/ci-devsecops.yml` | push, PR | SAST, SCA, build, test |
| **Container Release** | `.github/workflows/container-release.yml` | push a main | Build + Push a Docker Hub |
| **DAST ZAP** | `.github/workflows/dast-zap.yml` | push, PR | Escaneo dinámico de seguridad |
| **Deploy Production** | `.github/workflows/deploy-production.yml` | release | Deploy a infraestructura |

**Controles implementados en cada etapa:**

- **Plan:** Threat modeling con OWASP Threat Dragon.
- **Code:** 
  - Secret scanning: Gitleaks + TruffleHog
  - SAST: Semgrep + Bandit
  - SCA: Trivy filesystem + Dependency-Check + pip-audit + npm audit
- **Build:** 
  - Construcción de imágenes Docker
  - Escaneo de vulnerabilidades (Trivy)
  - Validación de Dockerfiles (hadolint)
  - Escaneo IaC (Checkov)
- **Test:** 
  - Pruebas unitarias backend (pytest)
  - Pruebas unitarias frontend (vitest)
  - Pruebas dinámicas (OWASP ZAP)
- **Release/Deploy:** Publicación de imágenes versionadas en Docker Hub + despliegue automatizado.
- **Operate:** Configuraciones de monitoreo disponibles (Prometheus, Grafana, Loki/Promtail, Falco) - ver `monitoring/` para integración.

---

## Documentación del Proyecto

SecureVault Pro cuenta con documentación técnica completa organizada en manuales especializados. Cada uno está pensado para un perfil distinto — desde el usuario final hasta el equipo de infraestructura.

### Manual de Usuario

¿Eres usuario final y quieres aprender a usar la plataforma?

El manual de usuario guía paso a paso: inicio de sesión, gestión de secretos, auditoría de accesos y controles de rol. Incluye el flujo recomendado y resolución de errores frecuentes.

→ [Leer Manual de Usuario](docs/01_Manual_Usuario.md)

### Manual Técnico

¿Quieres entender cómo está construido SecureVault Pro por dentro?

El manual técnico describe en detalle la arquitectura de microservicios, las decisiones de diseño, los patrones implementados y los 7 diagramas UML completos: Componentes, Despliegue, Secuencia de autenticación, Casos de Uso RBAC, DFD Nivel 0 y DFD Nivel 1.

→ [Leer Manual Técnico](docs/02_Manual_Tecnico.md)

### Manual de Operación DevOps

¿Necesitas gestionar el despliegue y el día a día operativo?

El manual operativo cubre la gestión de la infraestructura con Ansible, escalado con Kubernetes, playbooks para tareas comunes como rotación de secretos y backups, y guía de integración de herramientas de monitoreo opcionales (Prometheus, Grafana, Loki/Promtail).

→ [Leer Manual de Operación](docs/03_Manual_Operacion_DevOps.md)

### Seguridad y Gestión de Riesgos

¿Quieres conocer el modelo de amenazas y cómo se gestionan las vulnerabilidades?

Este documento describe el modelo de amenazas (STRIDE), los activos protegidos, los actores del sistema, la matriz de riesgos con SLA por severidad, y la política de divulgación responsable.

→ [Leer Análisis de Seguridad](docs/04_Seguridad_y_Riesgos.md)

### Plan de Pruebas

¿Necesitas conocer la estrategia de testing del proyecto?

El plan de pruebas detalla las pruebas unitarias, de integración, de carga y de seguridad ejecutadas en cada etapa del pipeline. Incluye cobertura esperada y resultados de ejecución.

→ [Leer Plan de Pruebas](docs/05_Plan_Pruebas.md)

### Checklist de Entrega

¿Estás validando que el proyecto cumple todos los requisitos de entrega?

El checklist operativo detalla todos los entregables esperados, criterios de aceptación y evidencia de cumplimiento: repositorio, imagenes versionadas, documentación, video, informe técnico y pruebas.

→ [Leer Checklist de Entrega](docs/06_Checklist_Entrega.md)

### Modelado de Amenazas (OWASP Threat Dragon)

**Modelos de amenazas del proyecto:**

- [SecureVault Threat Dragon (Sistema Operativo)](docs/07_SecureVault_Threat_Dragon.json) — Threat model completo del flujo de secretos y autenticación.
- [SecureVault CICD Threat Dragon (Pipeline)](docs/08_SecureVault_CICD_Threat_Dragon.json) — Threat model del pipeline CI/CD y automatización.

### Video de Demostración

→ [Ver video explicativo del ciclo DevSecOps completo](https://uniminuto0-my.sharepoint.com/:v:/g/personal/jherna81_uniminuto_edu_co/IQDKXkT3QqwZQrViDljWGCt0AdUlnprv_MN20rGWoyLWZo4?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=afMmrV)

**Nota:** El video evidencia despliegue tanto en Windows como en Linux.

---

## Autores

| Rol | Nombre | Institución |
|-----|--------|-------------|
| Integrante | Leidy Dayana Avendaño Moreno | UNIMINUTO — Especialización en Ciberseguridad |
| Integrante | Jeisson Andres Hernandez Martinez | UNIMINUTO — Especialización en Ciberseguridad |
| Integrante | Michael Giovanny Sierra Leon | UNIMINUTO — Especialización en Ciberseguridad |
| Integrante | John Edilvar Gutierrez Rojas | UNIMINUTO — Especialización en Ciberseguridad |

---

## Licencia

Este proyecto está distribuido bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

**SecureVault Pro** · UNIMINUTO · Especialización en Ciberseguridad · Seguridad Entornos Cloud DevOps
