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

## 4. Quick start

Requisitos:

- Docker + Docker Compose
- Conexion a internet para descargar las imagenes publicadas en Docker Hub
- Puertos libres: 3000, 8001, 8002, 5432, 6379

Ejecucion local recomendada  usando imagenes publicadas:

```powershell
.\scripts\pull-images.ps1
$env:IMAGE_TAG = "v1.0.0"
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
```

Nota: este flujo se ejecuta localmente en el equipo, pero reutiliza las imagenes publicadas en Docker Hub en lugar de reconstruir los servicios desde el codigo fuente.

Arranque local por build desde codigo fuente:

```powershell
.\scripts\pull-images.ps1
$env:IMAGE_TAG = "v1.0.0"
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

Diagramas clave para sustentacion:

- DFD Nivel 0 y DFD Nivel 1: docs/02_Manual_Tecnico.md (secciones 4 y 5).
- Diagrama de Casos de Uso: docs/02_Manual_Tecnico.md (seccion 3).
- Threat models (OWASP Threat Dragon): threat-model/ y docs/07_*.json + docs/08_*.json.

## 7. Entregables academicos

Estado esperado de entrega:

- Repositorio GitHub publico con codigo, pipelines, IaC y documentacion.
- Imagenes publicadas y versionadas en Docker Hub/GHCR.
- Script de apoyo para descarga de imagenes: scripts/pull-images.ps1.
- Informe tecnico en PDF.
- Video de demostracion del ciclo completo.

Checklist operativo en docs/06_Checklist_Entrega.md.

## 8. Licencia

Este proyecto usa licencia MIT. Ver LICENSE.
