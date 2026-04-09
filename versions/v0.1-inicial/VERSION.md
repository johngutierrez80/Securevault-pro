# SecureVault Pro — v0.1 Fase Inicial

**Commit de origen:** `464205f` — "Initial commit - SecureVault Pro"  
**Fecha:** 15 de marzo de 2026  
**Estado:** Esqueleto funcional base — sin CI/CD, sin observabilidad, sin tests automatizados

---

## ¿Qué representa esta versión?

Esta carpeta es un snapshot exacto del estado inicial del proyecto SecureVault Pro.
Representa la **fase de inicio**: estructura de servicios definida, lógica de negocio
base implementada, despliegue local operativo con Docker Compose.

---

## Plan de implementación en fases

### Fase 1 — Inicio (esta versión, v0.1)
- [x] Estructura de microservicios definida (`auth-service`, `vault-service`, `frontend`, `nginx`)
- [x] Auth Service: registro y login con JWT (FastAPI + bcrypt)
- [x] Vault Service: CRUD de secretos con cifrado Fernet
- [x] Frontend HTML estático: login y dashboard con fetch + manejo de JWT
- [x] Docker Compose para orquestación local
- [x] PostgreSQL como base de datos persistente
- [x] Nginx como reverse proxy / gateway
- [x] Variables de entorno (`.env.example`)
- [x] Documentación inicial: manuales de usuario, técnico, DevOps, seguridad, pruebas y checklist
- [x] `auth_service/` y `vault_service/` (versión prototipo simple en Flask-style, sin estructura)

### Fase 2 — Calidad y Seguridad (commit `f338374`)
- [x] Rate limiting en Vault Service (SlowAPI + Redis)
- [x] Tests unitarios: seguridad, JWT, crypto (`auth-service/tests/`, `vault-service/tests/`)
- [x] Frontend SPA React/Vite (`frontend-spa/`) con API layer, páginas y tests (Vitest)
- [x] Amenazas documentadas (Threat Dragon JSON)
- [x] Threat modeling: CI/CD attack surface modelado
- [x] Pipeline CI básico (GitHub Actions)

### Fase 3 — DevSecOps y Observabilidad (commits `7e6ccf3`, `756740f`, `cace5d2`)
- [x] Pipeline CI/CD completo: lint, test, build, push de imagen, deploy
- [x] Pre-commit hooks (`.pre-commit-config.yaml`)
- [x] Monitoreo: Prometheus + Grafana + Loki + Promtail + Falco
- [x] Reglas de seguridad runtime Falco (`monitoring/falco/`)
- [x] IaC con Ansible (`iac/ansible/`)
- [x] `docker-compose.prod.yml` para entorno productivo
- [x] `.trunk/` para linting/formateo unificado
- [x] Fixes de compatibilidad documentados (`FIXES.md`)

---

## Estructura de esta versión (v0.1)

```
v0.1-inicial/
├── docker-compose.yml          ← Orquestación local: auth, vault, postgres, nginx
├── .env.example                ← Variables de entorno requeridas
├── auth-service/               ← Auth Service (FastAPI estructurado)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/               ← config.py, security.py
│       ├── routers/auth.py     ← POST /auth/register, POST /auth/login
│       ├── services/           ← lógica de negocio
│       ├── models/             ← ORM SQLAlchemy
│       ├── schemas/            ← Pydantic
│       ├── dependencies/       ← database.py
│       └── utils/jwt.py        ← generación/verificación de tokens
├── vault-service/              ← Vault Service (FastAPI estructurado)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/               ← config.py, security.py, rate_limit.py
│       ├── routers/secrets.py  ← CRUD /vault/secret
│       ├── services/           ← lógica de bóveda
│       ├── models/             ← ORM
│       ├── schemas/            ← Pydantic
│       ├── dependencies/       ← database.py
│       └── utils/crypto.py     ← cifrado Fernet
├── auth_service/               ← Prototipo inicial (Flask-style, sin estructura)
├── vault_service/              ← Prototipo inicial (Flask-style, sin estructura)
├── frontend/                   ← Frontend HTML estático
│   ├── index.html              ← Login
│   ├── dashboard.html          ← Dashboard de secretos
│   └── js/main.js              ← Fetch + manejo JWT
├── gateway/nginx.conf          ← Configuración de gateway
├── nginx/                      ← Configuración de reverse proxy
└── docs/                       ← Documentación completa de entrega
    ├── 01_Manual_Usuario.md
    ├── 02_Manual_Tecnico.md
    ├── 03_Manual_Operacion_DevOps.md
    ├── 04_Seguridad_y_Riesgos.md
    ├── 05_Plan_Pruebas.md
    └── 06_Checklist_Entrega.md
```

---

## Cómo levantar esta versión

```bash
# Desde esta carpeta
cp .env.example .env
# Editar .env con las variables requeridas (SECRET_KEY, ENCRYPTION_KEY, etc.)
docker compose up --build
```

Servicios disponibles:
- Frontend: http://localhost (via Nginx)
- Auth API: http://localhost/auth/
- Vault API: http://localhost/vault/

---

## Diferencias respecto a la versión final

| Característica              | v0.1 Inicial | Versión Final |
|-----------------------------|:------------:|:-------------:|
| Microservicios core         | ✅           | ✅            |
| Frontend HTML estático      | ✅           | ✅            |
| Frontend SPA React/Vite     | ❌           | ✅            |
| Tests unitarios backend     | ❌           | ✅            |
| Tests frontend (Vitest)     | ❌           | ✅            |
| Rate limiting               | ❌           | ✅            |
| Pipeline CI/CD              | ❌           | ✅            |
| Threat modeling             | ❌           | ✅            |
| Monitoreo (Prometheus/Loki) | ❌           | ✅            |
| IaC (Ansible)               | ❌           | ✅            |
| Runtime security (Falco)    | ❌           | ✅            |
| Pre-commit hooks            | ❌           | ✅            |
