# Análisis Completo: SecureVault Pro — Cambios v0.1 → v1.0

## 1. Objetivo del documento

Este documento registra y justifica todos los cambios estructurales, tecnológicos y de seguridad realizados entre la versión inicial del proyecto (v0.1) y la versión final (v1.0), tomando como referencia la comparación directa de archivos, la arquitectura implementada y el proceso de remediación de vulnerabilidades documentado en `Remediación de vulnerabilidades.docx`.

---

## 2. Resumen ejecutivo de cambios

| Dimensión                    | v0.1 inicial                        | v1.0 final                                      |
| ---------------------------- | ----------------------------------- | ----------------------------------------------- |
| Runtime de servicios         | Node.js 20 / Express                | Python 3.11 / FastAPI                           |
| Imagen base contenedores     | `node:20-alpine`                    | `python:3.11-slim` / `nginx:alpine`             |
| Frontend                     | Dev server Vite (puerto 5173)       | Build multi-stage → Nginx (puerto 80/3000)      |
| Cifrado de secretos          | AES-256-GCM (`node:crypto`)         | Fernet (`cryptography` 41.x)                    |
| Autenticación JWT            | `jsonwebtoken` (npm)                | `PyJWT 2.12.1` + `bcrypt 4.1.2`                |
| Rate limiting                | `express-rate-limit`                | SlowAPI 0.1.8 + Redis                           |
| Orquestación                 | Docker Swarm (base)                 | Docker Compose + Kubernetes manifests           |
| Monitoreo                    | No implementado                     | Prometheus + Grafana + Loki + Promtail + Falco  |
| Pipelines CI/CD              | Workflow único básico               | 4 workflows DevSecOps especializados            |
| Pruebas                      | Pendientes (placeholder)            | pytest (backend) + vitest (frontend)            |
| Threat modeling              | No implementado                     | OWASP Threat Dragon (2 modelos JSON)            |
| Vulnerabilidades en imágenes | 3 críticas, 16 altas, 28 medias     | 0 críticas, 2 altas, 9 medias                  |

---

## 3. Cambios por componente

### 3.1 Microservicios backend

#### v0.1 — Node.js/Express
Los tres servicios (auth, vault, worker) estaban implementados en Node.js 20 con Express, cada uno con:
- `package.json` gestionando dependencias npm.
- `src/index.js` como punto de entrada.
- `src/db.js` para conexión a PostgreSQL.
- Imagen base `node:20-alpine`.
- Sin usuario no-root en contenedor.
- Sin healthcheck definido.

#### v1.0 — Python/FastAPI
Los tres servicios fueron reescritos en Python 3.11 con FastAPI, con estructura:

```
servicios/{servicio}/
├── Dockerfile                 # python:3.11-slim + usuario appuser + healthcheck
├── requirements.txt           # dependencias pip con versiones fijas
├── app/
│   ├── main.py                # punto de entrada FastAPI
│   ├── core/                  # config y seguridad
│   ├── dependencies/          # inyección de dependencias (DB session)
│   ├── models/                # modelos SQLAlchemy
│   ├── routers/               # endpoints
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # lógica de negocio
│   └── utils/                 # jwt, crypto, job_queue
└── tests/                     # tests pytest
```

Mejoras de seguridad en Dockerfiles:
- `RUN useradd -m appuser` + `USER appuser` — proceso no corre como root.
- `HEALTHCHECK` definido en auth y vault service.
- `--no-cache-dir` en pip install para reducir tamaño de imagen.

### 3.2 Auth Service

| Aspecto              | v0.1                                      | v1.0                                             |
| -------------------- | ----------------------------------------- | ------------------------------------------------ |
| Framework            | Express                                   | FastAPI + Pydantic v2                            |
| Hash de contraseñas  | bcrypt (npm)                              | `passlib[bcrypt]` + `bcrypt 4.1.2`              |
| JWT                  | `jsonwebtoken`                            | `PyJWT 2.12.1`                                  |
| Validación de inputs | Express middleware                        | Pydantic schemas + validación en service layer  |
| Puerto               | 3001                                      | 8001                                             |
| Endpoint registro    | `POST /auth/register` (campo: `email`)    | `POST /register` (campo: `username`)            |
| Endpoint login       | `POST /auth/login`                        | `POST /login`                                   |

Nota: el campo de identificación cambió de `email` a `username`, lo que se refleja en el frontend y en los endpoints de la API.

### 3.3 Vault Service

| Aspecto        | v0.1                               | v1.0                                              |
| -------------- | ---------------------------------- | ------------------------------------------------- |
| Framework      | Express                            | FastAPI + Pydantic v2                             |
| Cifrado        | AES-256-GCM (módulo `crypto` nativo) | Fernet (`cryptography 41.x`)                    |
| Rate limiting  | `express-rate-limit` (en memoria)  | SlowAPI 0.1.8 respaldado en Redis                |
| Puerto         | 3002                               | 8002                                              |
| Expiración     | Campo `expiresAt` (datetime-local) | Campo `expires_in_days` (días enteros)           |

### 3.4 Worker Service

| Aspecto       | v0.1                           | v1.0                                       |
| ------------- | ------------------------------ | ------------------------------------------ |
| Runtime       | Node.js 20                     | Python 3.11                                |
| Función       | Limpieza por cron `*/1 * * * *` | Proceso asíncrono Python                  |
| Imagen base   | `node:20-alpine`               | `python:3.11-slim`                         |
| Usuario root  | Sí                             | No (usa appuser en v1.0 auth/vault)        |

### 3.5 Frontend SPA

| Aspecto           | v0.1                                        | v1.0                                              |
| ----------------- | ------------------------------------------- | ------------------------------------------------- |
| Build strategy    | Dev server Vite (producción no optimizada)  | Multi-stage: builder Vite → Nginx estático        |
| Puerto exposición | 5173                                        | 3000 (redirige a :80 del contenedor)              |
| Gestor de estado  | useState + axios                            | useState + fetch nativo                           |
| Routing           | No implementado                             | `react-router-dom v6`                             |
| Campo de login    | `email`                                     | `username`                                        |
| Mensajes de error | Se renderizaba payload de FastAPI           | Mensajes genéricos (`"Credenciales incorrectas"`) |
| Tests             | Placeholder (`console.log`)                 | vitest + @testing-library/react                   |
| Linting           | No configurado                              | ESLint 9 + eslint-plugin-react                    |

### 3.6 Docker Compose

| Aspecto                  | v0.1                                       | v1.0                                           |
| ------------------------ | ------------------------------------------ | ---------------------------------------------- |
| Versión del schema       | `version: "3.9"` (declarado)               | Sin declaración de versión (compatible actual) |
| Nombre de servicios      | `auth-service`, `vault-service`, `frontend-spa` | `auth`, `vault`, `worker`, `gateway`      |
| Variables de entorno     | Inline en compose con defaults             | Movidas a archivo `.env`                       |
| Health checks            | No definidos                               | Definidos en postgres y redis                  |
| Dependencias             | `depends_on` simple                        | `depends_on` con `condition: service_healthy`  |
| Gateway                  | No existía                                 | `build: ./frontend-spa` sirviendo desde Nginx  |

### 3.7 Pipelines CI/CD

#### v0.1 — Workflow único
Un solo workflow `ci-cd.yml` con checks básicos de Node.js, Gitleaks, Semgrep y Trivy.

#### v1.0 — 4 workflows especializados

| Workflow                     | Trigger                         | Propósito                                          |
| ---------------------------- | ------------------------------- | -------------------------------------------------- |
| `ci-devsecops.yml`           | push/PR a main y develop        | QA Python, tests, Bandit SAST, pip-audit SCA       |
| `dast-zap.yml`               | push a main, PR                 | DAST con OWASP ZAP contra la aplicación en vivo    |
| `container-release.yml`      | push a main o tags `v*`         | Build + escaneo Trivy + push a GHCR                |
| `deploy-production.yml`      | Aprobación manual (environment) | Deploy SSH con aprobación en environment production |

### 3.8 Infraestructura y orquestación

| Aspecto              | v0.1                           | v1.0                                             |
| -------------------- | ------------------------------ | ------------------------------------------------ |
| IaC                  | Ansible `site.yml`             | Ansible `deploy-compose.yml` + `inventory.example.ini` |
| Orquestación         | Docker Swarm (`docker-swarm.yml`) | Kubernetes manifests (`namespace.yaml`, `securevault-stack.yaml`) |
| Gateway externo      | No existía                     | `nginx/` con configuración dedicada              |

### 3.9 Monitoreo (nuevo en v1.0)

Componente completamente nuevo, disponible en `docker-compose.prod.yml`:

- **Prometheus** — recolección de métricas.
- **Grafana** — visualización con datasource provisionado.
- **cAdvisor** — métricas de contenedores Docker.
- **Loki** — agregación de logs.
- **Promtail** — recolección de logs de contenedores.
- **Falco** — detección de comportamiento anómalo en runtime (requiere soporte eBPF en host).

### 3.10 Threat Modeling (nuevo en v1.0)

Dos modelos OWASP Threat Dragon exportados como JSON:

- `threat-model/01_SecureVault_Operativo_Threat_Dragon.json` — DFD del sistema operativo con amenazas STRIDE.
- `threat-model/02_SecureVault_CICD_Threat_Dragon.json` — DFD de la cadena de suministro y CI/CD.

---

## 4. Documentación: antes y después

### Documentos eliminados (v0.1)

| Archivo                          | Contenido                          |
| -------------------------------- | ---------------------------------- |
| `docs/01_Arquitectura.md`        | Arquitectura inicial Node.js       |
| `docs/02_Desarrollo.md`          | Guía de desarrollo inicial         |
| `docs/03_Despliegue.md`          | Instrucciones de despliegue v0.1   |
| `docs/04_Seguridad.md`           | Seguridad inicial                  |
| `docs/05_Usuario.md`             | Manual de usuario v0.1             |
| `docs/06_Checklist_Avance1.md`   | Checklist de primer avance         |
| `docs/07_Informe_Avance1_Plantilla.md` | Plantilla de informe         |
| `docs/diagrama-*.md` (4 archivos) | Diagramas de casos de uso y DFD   |

### Documentos creados (v1.0)

| Archivo                                                 | Contenido                                              |
| ------------------------------------------------------- | ------------------------------------------------------ |
| `docs/01_Manual_Usuario.md`                             | Manual de usuario de la versión final                  |
| `docs/02_Manual_Tecnico.md`                             | Arquitectura FastAPI + diagramas Mermaid               |
| `docs/03_Manual_Operacion_DevOps.md`                    | Operación con Docker Compose y pipelines               |
| `docs/04_Seguridad_y_Riesgos.md`                        | Controles, STRIDE, remediación CVEs                    |
| `docs/05_Plan_Pruebas.md`                               | Casos de prueba funcionales y de seguridad             |
| `docs/06_Checklist_Entrega.md`                          | Checklist de requisitos del curso                      |
| `docs/07_SecureVault_Threat_Dragon.json`                | Copia del modelo de amenazas operativo                 |
| `docs/08_SecureVault_CICD_Threat_Dragon.json`           | Copia del modelo de amenazas CI/CD                     |
| `docs/09_Guia_Documentacion_Detallada_SecureVault_Pro.md` | Guía de documentación completa                       |
| `docs/10_Analisis_Cambios_v0.1_v1.0.md`                 | Este documento                                         |
| `Remediación de vulnerabilidades.docx`                  | Evidencia con capturas del escaneo de imágenes         |

---

## 5. Remediación de vulnerabilidades en imágenes

### 5.1 Métricas comparativas

| Severidad | v0.1 inicial | v1.0 final | Reducción  |
| --------- | ------------ | ---------- | ---------- |
| Críticas  | 3            | 0          | −100 %     |
| Altas     | 16           | 2          | −87,5 %    |
| Medias    | 28           | 9          | −67,9 %    |
| Bajas     | 2            | 2          | 0 %        |
| **Total** | **49**       | **13**     | **−73,5 %** |

### 5.2 CVEs remediados

| CVE            | Acción aplicada                                          |
| -------------- | -------------------------------------------------------- |
| CVE-2025-68121 | Actualización de versión de imagen/paquete afectado      |
| CVE-2024-24790 | Actualización de versión de componente de red            |
| CVE-2026-26996 | Actualización de versión de dependencia de runtime       |

### 5.3 Causa raíz de la reducción

La mayor parte de las vulnerabilidades críticas y altas en v0.1 provenía del ecosistema npm empaquetado en `node:20-alpine`. La migración a Python 3.11/FastAPI con `python:3.11-slim` eliminó esa superficie de ataque. Las 2 vulnerabilidades altas residuales en v1.0 corresponden a componentes del sistema base de la imagen slim y están bajo seguimiento.

---

## 6. Controles de seguridad: comparativa

| Control                      | v0.1                          | v1.0                                              |
| ---------------------------- | ----------------------------- | ------------------------------------------------- |
| Hash de contraseñas          | bcrypt (npm, sin límite bytes) | bcrypt con normalización de 72 bytes (passlib)   |
| JWT                          | Sin expiración explícita      | Expiración configurable (`token_exp_minutes`)    |
| Cifrado de secretos          | AES-256-GCM                   | Fernet (autenticado, con IV aleatorio por mensaje)|
| Rate limiting                | En memoria (sin persistencia) | Redis-backed (persiste entre reinicios)          |
| Mensajes de error frontend   | Payload raw del backend       | Mensajes genéricos (no expone estructura interna)|
| Usuario no-root en contenedor | No                           | Sí (`appuser`) en auth y vault service            |
| Healthcheck en contenedor    | No                            | Sí en auth, vault y gateway                       |
| Pre-commit hooks              | No                            | Sí (Gitleaks + hooks de higiene)                 |
| Secret scanning en CI        | Gitleaks básico               | Gitleaks + TruffleHog en pipeline dedicado       |
| SAST                         | Semgrep                       | Bandit (Python) + Semgrep                        |
| SCA                          | npm audit                     | pip-audit + Trivy                                |
| DAST                         | No                            | OWASP ZAP workflow dedicado                      |

---

## 7. Deuda técnica pendiente

Los siguientes puntos fueron identificados durante el análisis y quedan como mejoras futuras:

1. **Token en localStorage** — Riesgo XSS. Evaluar migración a cookies HttpOnly en evolución futura.
2. **TLS en tránsito local** — Los servicios se comunican en HTTP dentro de la red Docker. En producción real se requiere HTTPS en el ingress.
3. **secret_key con valor por defecto** — `core/config.py` en auth-service tiene `secret_key: str = "securevaultsecret"`. Debe ser obligatoriamente sobreescrita por variable de entorno en producción.
4. **ENCRYPTION_KEY dinámica** — Si no se define `ENCRYPTION_KEY` en vault-service, se genera una nueva en cada inicio, perdiendo capacidad de descifrado tras reinicio.
5. **Worker service sin usuario no-root** — A diferencia de auth y vault, el Dockerfile del worker no define `appuser`.
6. **Vulnerabilidades altas residuales (2)** — Pendientes de resolución en próxima actualización de imagen base.

---

## 8. Referencias

- `versions/v0.1-inicial/` — Snapshot completo de la versión inicial conservado en el repositorio.
- `Remediación de vulnerabilidades.docx` — Evidencia fotográfica del escaneo y remediación.
- `docs/04_Seguridad_y_Riesgos.md` — Análisis STRIDE y controles de seguridad.
- `docs/02_Manual_Tecnico.md` — Arquitectura técnica de la versión final.
- `threat-model/` — Modelos OWASP Threat Dragon exportados.
