# SecureVault Pro

[![CI DevSecOps](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/ci-devsecops.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/ci-devsecops.yml)
[![DAST ZAP](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/dast-zap.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/dast-zap.yml)
[![Container Release](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/container-release.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/container-release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Proyecto final de Especializacion en Ciberseguridad con enfasis DevSecOps.

SecureVault Pro implementa una plataforma para gestion segura de secretos con arquitectura de microservicios y pipeline DevSecOps de ciclo completo.

## 1. Objetivo

Demostrar integracion end-to-end de practicas DevSecOps:

- Arquitectura de microservicios contenerizada.
- Automatizacion CI/CD con controles de seguridad en cada fase.
- Infraestructura como codigo para despliegue.
- Evidencia de pruebas, threat modeling y monitoreo.

## 2. Arquitectura

Componentes principales:

- Frontend SPA en React + Vite (frontend-spa/).
- Auth Service en FastAPI (servicios/auth-service/).
- Vault Service en FastAPI (servicios/vault-service/).
- Worker Service asincrono en Python (servicios/worker-service/).
- PostgreSQL para persistencia.
- Redis para comunicacion asincrona y soporte de rate limiting.
- Gateway Nginx para exposicion unificada.

## 3. Estructura del repositorio

Estructura alineada con la guia del curso:

```text
securevault-pro/
├── LICENSE
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .github/workflows/
├── infraestructura/        # IaC (Ansible)
├── orquestacion/           # Kubernetes/K3s
├── servicios/              # Microservicios backend + worker
├── frontend-spa/           # SPA frontend
├── monitoring/             # Prometheus, Grafana, Loki, Falco
├── threat-model/           # OWASP Threat Dragon exports
└── docs/                   # Documentacion academica y tecnica
```

Notas:

- versions/ conserva versiones previas del proyecto.
- iac/ se mantiene por compatibilidad; la ruta activa para IaC es infraestructura/.

## 4. Quick start

Requisitos:

- Docker + Docker Compose
- Puertos libres: 3000, 8001, 8002, 5432, 6379

Arranque local:

```powershell
docker compose up -d --build
docker compose ps
```

Accesos:

- Frontend/Gateway: http://localhost:3000
- Auth API docs: http://localhost:8001/docs
- Vault API docs: http://localhost:8002/docs

## 5. Pipeline DevSecOps

Workflows principales:

- .github/workflows/ci-devsecops.yml
- .github/workflows/container-release.yml
- .github/workflows/dast-zap.yml
- .github/workflows/deploy-production.yml

Controles implementados:

- Plan: Threat modeling con OWASP Threat Dragon.
- Code: secret scanning, SAST y SCA.
- Build: construccion y escaneo de imagenes.
- Test: pruebas backend/frontend y DAST con OWASP ZAP.
- Release/Deploy: publicacion de imagenes + despliegue automatizado.
- Operate/Monitor: Prometheus, Grafana, Loki/Promtail y Falco.

## 6. Documentacion

Documentos principales en docs/:

- 01_Manual_Usuario.md
- 02_Manual_Tecnico.md
- 03_Manual_Operacion_DevOps.md
- 04_Seguridad_y_Riesgos.md
- 05_Plan_Pruebas.md
- 06_Checklist_Entrega.md
- 07_SecureVault_Threat_Dragon.json
- 08_SecureVault_CICD_Threat_Dragon.json

## 7. Entregables academicos

Estado esperado de entrega:

- Repositorio GitHub publico con codigo, pipelines, IaC y documentacion.
- Imagenes publicadas y versionadas en Docker Hub/GHCR.
- Informe tecnico en PDF.
- Video de demostracion del ciclo completo.

Checklist operativo en docs/06_Checklist_Entrega.md.

## 8. Licencia

Este proyecto usa licencia MIT. Ver LICENSE.
# SecureVault Pro

[![CI DevSecOps](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/ci-devsecops.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/ci-devsecops.yml)
[![DAST ZAP](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/dast-zap.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/dast-zap.yml)
[![Container Release](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/container-release.yml/badge.svg)](https://github.com/johngutierrez80/Securevault-pro/actions/workflows/container-release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Proyecto final de Especializacion en Ciberseguridad con enfasis DevSecOps.

SecureVault Pro implementa una plataforma para gestion segura de secretos con arquitectura de microservicios y pipeline DevSecOps de ciclo completo.

## 1. Objetivo

Demostrar integracion end-to-end de practicas DevSecOps:

- Arquitectura de microservicios contenerizada.
- Automatizacion CI/CD con controles de seguridad en cada fase.
- Infraestructura como codigo para despliegue.
- Evidencia de pruebas, threat modeling y monitoreo.

## 2. Arquitectura

Componentes principales:

- Frontend SPA en React + Vite (`frontend-spa/`).
- Auth Service en FastAPI (`servicios/auth-service/`).
- Vault Service en FastAPI (`servicios/vault-service/`).
- Worker Service asincrono en Python (`servicios/worker-service/`).
- PostgreSQL para persistencia.
- Redis para comunicacion asincrona y soporte de rate limiting.
- Gateway Nginx para exposicion unificada.

## 3. Estructura del repositorio

Estructura alineada con la guia del curso:

```text
securevault-pro/
├── LICENSE
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .github/workflows/
├── infraestructura/        # IaC (Ansible)
├── orquestacion/           # Kubernetes/K3s
├── servicios/              # Microservicios backend + worker
├── frontend-spa/           # SPA frontend
├── monitoring/             # Prometheus, Grafana, Loki, Falco
├── threat-model/           # OWASP Threat Dragon exports
└── docs/                   # Documentacion academica y tecnica
```

Notas:

- `versions/` conserva versiones previas del proyecto.
- `iac/` se mantiene por compatibilidad; la ruta activa para IaC es `infraestructura/`.

## 4. Quick start

Requisitos:

- Docker + Docker Compose
- Puertos libres: `3000`, `8001`, `8002`, `5432`, `6379`

<<<<<<< HEAD
### Tabla secrets

- id: integer, PK.
- site: string.
- encrypted_password: string.
- owner: string (usuario propietario).

## 5. Seguridad implementada

- Hash de contraseña: bcrypt mediante passlib.
- JWT firmado con HS256 y expiración configurable.
- Validación de token en endpoints de bóveda.
- Cifrado de secretos con Fernet.
- Rate limiting en vault: 10 requests/minute por IP.

## 6. Endpoints principales

### Auth Service

- POST /auth/register
- POST /auth/login

### Vault Service

- GET /vault/secret
- POST /vault/secret
- PUT /vault/secret/{secret_id}
- DELETE /vault/secret/{secret_id}

## 7. Variables y configuración

- database_url: conexión PostgreSQL.
- secret_key: clave de firma JWT.
- algorithm: algoritmo JWT (HS256).
- token_exp_minutes: expiración del token.
- ENCRYPTION_KEY: clave de cifrado de secretos recomendada para persistencia.

## 8. Notas técnicas relevantes

- Si ENCRYPTION_KEY no está definida, se genera una clave efímera y los secretos previos pueden no descifrarse tras reinicio.
- Nginx enruta /auth/ a auth y /vault/ a vault.
- El frontend consume rutas relativas /auth/_ y /vault/_.
- Se incluyen modelos de amenazas importables en OWASP Threat Dragon para arquitectura y cadena CI/CD.
- Exportes disponibles en `threat-model/` para evidencia formal de evaluación.

## 9. Mejoras futuras sugeridas

- Migraciones formales con Alembic.
- Gestión segura de secretos con vault manager o variables protegidas.
- Endurecimiento de observabilidad (dashboards, alertas y correlación de eventos de seguridad).
- Pruebas automatizadas de integración.

## 10. Notas de compatibilidad y fixes locales

### Dependencias ajustadas

- **eslint-plugin-react (frontend-spa)**: versionado a `^7.37.5` (npm registry public).
  - Motivo: la versión `^7.38.0` no existe en el registro npm. Ajuste mínimo para construcción Docker.

### Ajustes de Dockerfile

- **servicios/vault-service/Dockerfile**: agregado `RUN touch .env` después de `pip install`.
  - Motivo: SlowAPI (rate limiter) valida existencia de archivo .env en tiempo de inicialización. Archivo vacío es suficiente para desarrollo local.

- **frontend-spa/Dockerfile**: eliminada directiva `USER nginx`.
  - Motivo: evita Permission denied en `/var/cache/nginx` cuando Nginx intenta crear directorios temporales. El contenedor nginx ejecuta como root por defecto en Alpine.

Estos cambios son necesarios para ejecución local con Docker Compose y no afectan lógica de negocio ni seguridad en producción.

## 11. Pipeline CI/CD DevSecOps en GitHub Actions

El repositorio  incluye un pipeline completo en GitHub Actions:

- CI + seguridad en `.github/workflows/ci-devsecops.yml`.
- Release de contenedores a GHCR en `.github/workflows/container-release.yml`.
- CD manual a producción por SSH en `.github/workflows/deploy-production.yml`.
- DAST automatizado con ZAP en `.github/workflows/dast-zap.yml`.
- IaC con Ansible en `infraestructura/ansible/deploy-compose.yml`.

### Flujo recomendado

- Pull Request a `main`: ejecuta calidad, build y escaneos de seguridad.
- Push a `main`: construye y publica imágenes en GHCR y Docker Hub.
- Deploy: se ejecuta manualmente con `workflow_dispatch` sobre el entorno protegido.

### Secretos requeridos en GitHub

Configurar en Settings > Secrets and variables > Actions:

- `DEPLOY_HOST`: IP o dominio del servidor de despliegue.
- `DEPLOY_USER`: usuario SSH del servidor.
- `DEPLOY_SSH_KEY`: llave privada SSH para el servidor.
- `GHCR_USERNAME`: usuario con permisos para leer paquetes en GHCR.
- `GHCR_TOKEN`: token con scope `read:packages` para el servidor destino.
- `DOCKERHUB_USERNAME`: usuario de Docker Hub para publicación.
- `DOCKERHUB_TOKEN`: access token de Docker Hub para publicación.

### Protección recomendada

- Habilitar Branch Protection en `main` y exigir estado exitoso de los workflows de CI.
- Configurar el environment `production` con aprobación manual antes de ejecutar deploy.

### Compose de producción

- El archivo `docker-compose.prod.yml` consume imágenes de GHCR usando:
  - `GITHUB_REPOSITORY_OWNER`
  - `IMAGE_TAG`
- El workflow de deploy exporta ambas variables antes de ejecutar `docker compose`.

### Cobertura de seguridad implementada

- SAST: Bandit en servicios Python.
- SAST adicional: Semgrep sobre el repositorio.
- SCA: pip-audit y npm audit.
- Secret scan: Gitleaks y TruffleHog.
- Image scan: Trivy y Grype sobre imágenes publicadas.
- DAST: OWASP ZAP baseline contra el gateway del entorno levantado por compose.
- IaC scan: Checkov sobre Terraform, Dockerfile, Compose y Ansible.
- Shift-left local: pre-commit con Gitleaks y TruffleHog en `.pre-commit-config.yaml`.
- Pruebas automatizadas Python: pytest con cobertura sobre servicios auth y vault.
- Pruebas frontend: Vitest + Testing Library en `frontend-spa`.
- Monitor básico: Prometheus + Grafana + cAdvisor + Loki + Promtail + Falco en `docker-compose.prod.yml`.

### Caso funcional de worker asíncrono

Se implementó una tarea de negocio evaluable en `worker-service`:

- Limpieza periódica de secretos expirados.
- El `vault-service` permite establecer `expires_in_days` al crear o actualizar un secreto.
- La expiración se programa en Redis (`jobs:secret_expirations`).
- El worker ejecuta limpieza periódica y elimina secretos vencidos en PostgreSQL.

### Política de bloqueo por severidad

- Trivy (filesystem e imágenes) bloquea en severidad `CRITICAL`.
- Grype bloquea en severidad `critical`.
- npm audit bloquea en severidad `critical`.
- Gitleaks, Checkov y Bandit bloquean al detectar hallazgos en sus políticas.

### Política de bloqueo de CVEs

El pipeline aplica un control de bloqueo estricto para evitar liberar artefactos con vulnerabilidades críticas.

| Control | Herramienta | Umbral | Bloquea release |
|---|---|---|---|
| Escaneo de imagen local | Trivy | `CRITICAL` + `exit-code: 1` | Sí |
| Escaneo de imagen local | Grype | `critical` + `fail-build: true` | Sí |
| SCA de dependencias | OWASP Dependency-Check | `--failOnCVSS 9` | Sí (falla CI) |
| SCA JS | npm audit | `critical` | Sí (falla CI) |
| SCA Python | pip-audit | Vulnerabilidades detectadas | Sí (falla CI) |

Flujo aplicado:

1. Build local de imagen por servicio (sin publicar).
2. Escaneo de la imagen local con Trivy (umbral `CRITICAL`, `exit-code: 1`).
3. Escaneo de la misma imagen local con Grype (umbral `critical`, `fail-build: true`).
4. Solo si ambos escaneos pasan, se ejecuta el push a GHCR y Docker Hub.

Controles complementarios en CI:

- OWASP Dependency-Check en SCA con `--failOnCVSS 9`.
- Trivy filesystem scan en severidad `CRITICAL`.

Evidencia técnica en workflows:

- `.github/workflows/container-release.yml`: build local -> scan -> push.
- `.github/workflows/ci-devsecops.yml`: controles SCA y threshold crítico.

### Uso local de pre-commit
=======
Arranque local:
>>>>>>> b023018 (chore: limpiar duplicados legacy y alinear estructura/documentacion)

```powershell
docker compose up -d --build
docker compose ps
```

Accesos:

- Frontend/Gateway: `http://localhost:3000`
- Auth API docs: `http://localhost:8001/docs`
- Vault API docs: `http://localhost:8002/docs`

## 5. Pipeline DevSecOps

Workflows principales:

- `.github/workflows/ci-devsecops.yml`
- `.github/workflows/container-release.yml`
- `.github/workflows/dast-zap.yml`
- `.github/workflows/deploy-production.yml`

Controles implementados:

- Plan: Threat modeling con OWASP Threat Dragon.
- Code: secret scanning, SAST y SCA.
- Build: construccion y escaneo de imagenes.
- Test: pruebas backend/frontend y DAST con OWASP ZAP.
- Release/Deploy: publicacion de imagenes + despliegue automatizado.
- Operate/Monitor: Prometheus, Grafana, Loki/Promtail y Falco.

## 6. Documentacion

Documentos principales en `docs/`:

- `01_Manual_Usuario.md`
- `02_Manual_Tecnico.md`
- `03_Manual_Operacion_DevOps.md`
- `04_Seguridad_y_Riesgos.md`
- `05_Plan_Pruebas.md`
- `06_Checklist_Entrega.md`
- `07_SecureVault_Threat_Dragon.json`
- `08_SecureVault_CICD_Threat_Dragon.json`

## 7. Entregables academicos

Estado esperado de entrega:

- Repositorio GitHub publico con codigo, pipelines, IaC y documentacion.
- Imagenes publicadas y versionadas en Docker Hub/GHCR.
- Informe tecnico en PDF.
- Video de demostracion del ciclo completo.

Checklist operativo en `docs/06_Checklist_Entrega.md`.

## 8. Licencia

Este proyecto usa licencia MIT. Ver `LICENSE`.
