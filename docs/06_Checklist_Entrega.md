# Checklist de Entrega — SecureVault Pro v1.2

## 1. Entregables obligatorios del curso

- [ ] Repositorio GitHub público con código, pipelines, IaC y documentación
- [ ] Imágenes publicadas y versionadas en Docker Hub (`necromanoger/*:v1.2.0`)
- [ ] Informe técnico en PDF
- [ ] Video-demostración de 10 a 15 minutos: [Ver video](https://uniminuto0-my.sharepoint.com/:v:/g/personal/jherna81_uniminuto_edu_co/IQDKXkT3QqwZQrViDljWGCt0AdUlnprv_MN20rGWoyLWZo4?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=afMmrV)
- [ ] El video debe evidenciar el despliegue del proyecto en Windows y Linux

## 2. Estructura del repositorio

- [ ] `LICENSE` (MIT/Apache-2.0/GPL-3.0)
- [ ] `README.md` principal con quick start actualizado a v1.2.0
- [ ] `docker-compose.yml` y `docker-compose.prod.yml` con tag `v1.2.0`
- [ ] `.github/workflows/` con CI/CD DevSecOps
- [ ] `infraestructura/` (IaC — Ansible)
- [ ] `orquestacion/` (Kubernetes/K3s manifests)
- [ ] `servicios/` (microservicios: auth, vault, worker)
- [ ] `frontend-spa/` (React + Vite)
- [ ] `docs/` (manuales y evidencias)
- [ ] `threat-model/` (modelos OWASP Threat Dragon)
- [ ] `monitoring/` (Prometheus, Grafana, Loki, Promtail, Falco)

## 3. Validación técnica y ejecución

### Core
- [ ] Proyecto levanta con `docker compose up -d --build`
- [ ] Imágenes producción disponibles: `$env:IMAGE_TAG = "v1.2.0"; docker compose -f docker-compose.prod.yml up -d`
- [ ] Todos los servicios en estado `running/healthy`
- [ ] Acceso funcional por gateway en `http://localhost:3000`
- [ ] Registro, login y CRUD de secretos funcionando
- [ ] Administrador inicial creado automáticamente al arrancar (bootstrap idempotente)

### RBAC y roles
- [ ] Usuario regular ve solo su bóveda personal en `/boveda`
- [ ] Administrador ve panel de gestión en `/admin`
- [ ] Cambio de roles funcional desde panel de administración
- [ ] Ruta `/admin` bloqueada para usuarios sin rol `admin` (403)
- [ ] Worker asíncrono ejecutando tarea verificable

### Bloqueo de cuenta (v1.2)
- [ ] 3 intentos fallidos de login devuelven HTTP 423 en el 3er intento
- [ ] Redis almacena `login_fail:{email}` con TTL 300s tras el bloqueo
- [ ] Se envía email automático de recovery al bloquearse (Mailjet)
- [ ] El enlace del email pre-carga token y email en el panel de recovery
- [ ] Reset de contraseña exitoso elimina la clave `login_fail:{email}` de Redis
- [ ] Login funciona correctamente después del reset
- [ ] Frontend muestra banner rojo de bloqueo y abre panel de recovery automáticamente
- [ ] Frontend limpia el estado de bloqueo (`isLockedOut=false`) tras reset exitoso

### Expiración diferenciada de JWT (v1.2)
- [ ] Token de usuario regular tiene `exp` = 60 minutos
- [ ] Token de administrador tiene `exp` = 480 minutos (8 horas)
- [ ] Variable `ADMIN_TOKEN_EXP_MINUTES=480` en config.py

### Panel admin con polling (v1.2)
- [ ] Panel admin se actualiza automáticamente cada 30 segundos
- [ ] Contador regresivo visible en la barra superior del panel
- [ ] Botón "Actualizar ahora" dispara refresh inmediato
- [ ] Al expirar el token del admin (401/403 en polling), redirige automáticamente al login

## 4. Seguridad mínima requerida

- [ ] JWT implementado y validado en endpoints protegidos
- [ ] Claim `sub` del JWT como string (RFC 7519)
- [ ] Control de acceso basado en roles (RBAC) con roles `admin` y `user`
- [ ] Contraseñas hasheadas con bcrypt
- [ ] Secretos cifrados en reposo con clave persistente (`ENCRYPTION_KEY`)
- [ ] Rate limiting activo (429 al superar 10/min por IP en vault)
- [ ] Bloqueo de cuenta tras 3 intentos fallidos (HTTP 423, Redis TTL 5min)
- [ ] Recuperación de contraseña por email (Mailjet)
- [ ] Revocación de sesiones por JTI desde panel admin
- [ ] Secret scanning integrado (Gitleaks/TruffleHog)
- [ ] SAST integrado (Bandit/Semgrep)
- [ ] SCA integrado (Trivy/pip-audit/npm audit)
- [ ] DAST automatizado (OWASP ZAP)

### Remediaciones DevSecOps aplicadas (P1–P9)

- [ ] SAST Bandit: **0 HIGH, 0 MEDIUM** (56 LOW — B101 assert en tests, B110 Redis except-pass aceptados)
- [ ] SCA `cryptography`: versión `46.0.7` — **0 CVEs** ✅ (actualizó desde `41.0.7` eliminando 7 CVEs)
- [ ] SCA `Jinja2`: versión `3.1.6` — **0 CVEs** ✅ (actualizó desde `3.1.2` eliminando 1 CVE HIGH)
- [ ] SCA `vite`: versión `6.3.4` — 5 CVEs residuales (dev-server únicamente, riesgo nulo en producción)
- [ ] `urllib` migrado a `httpx` en vault-service (elimina Bandit B310 MEDIUM)
- [ ] Node.js `24` en GitHub Actions CI (actualizado desde v20)
- [ ] TruffleHog con `--results=verified` (reduce falsos positivos en secret scanning)

## 5. Pipeline DevSecOps por fases

- [ ] Plan: Threat modeling en OWASP Threat Dragon + STRIDE
- [ ] Code: controles de seguridad sobre código y dependencias
- [ ] Build: build de imágenes + escaneo de CVE críticos
- [ ] Test: pruebas unitarias + DAST
- [ ] Release/Deploy: publicación y despliegue automatizado
- [ ] Operate/Monitor: monitoreo y logs (Prometheus, Grafana, Loki, Falco)

## 6. Documentación obligatoria

- [ ] `README.md` principal actualizado (v1.2.0)
- [ ] `docs/01_Manual_Usuario.md` (incluye bloqueo, recovery, expiración)
- [ ] `docs/02_Manual_Tecnico.md` (incluye diagramas nuevos de lockout, polling, JWT)
- [ ] `docs/03_Manual_Operacion_DevOps.md` (incluye validación de bloqueo Redis, comandos v1.2.0)
- [ ] `docs/04_Seguridad_y_Riesgos.md` (incluye STRIDE actualizado, bloqueo, expiración diferenciada)
- [ ] `docs/05_Plan_Pruebas.md` (incluye CP-12 a CP-27 de v1.2)
- [ ] `docs/11_Analisis_Cambios_v1.0_v1.2.md` (tabla comparativa v1.0 → v1.2)
- [ ] Evidencias de ejecución y reportes de seguridad

## 7. Sustentación

- [ ] Arquitectura explicada con diagramas Mermaid
- [ ] Flujo end-to-end demostrado en vivo (incluyendo bloqueo y recovery)
- [ ] Diagrama de polling y expiración de sesión admin
- [ ] Riesgos y mitigaciones presentados (STRIDE actualizado)
- [ ] Lecciones aprendidas y mejoras futuras declaradas

- [ ] Imagenes publicadas y versionadas en Docker Hub
- [ ] Informe tecnico en PDF
- [ ] Video-demostracion de 10 a 15 minutos: [Ver video](https://uniminuto0-my.sharepoint.com/:v:/g/personal/jherna81_uniminuto_edu_co/IQDKXkT3QqwZQrViDljWGCt0AdUlnprv_MN20rGWoyLWZo4?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=afMmrV)
- [ ] Observacion: el video debe evidenciar el despliegue del proyecto en Windows y Linux

## 2. Estructura del repositorio

- [ ] `LICENSE` (MIT/Apache-2.0/GPL-3.0)
- [ ] `README.md` principal con quick start
- [ ] `docker-compose.yml`
- [ ] `.github/workflows/` con CI/CD
- [ ] `infraestructura/` (IaC)
- [ ] `orquestacion/` (Kubernetes/K3s/Swarm)
- [ ] `servicios/` (microservicios)
- [ ] `docs/` (manuales y evidencias)

## 3. Validacion tecnica y ejecucion

- [ ] Proyecto levanta con `docker compose up -d --build`
- [ ] Servicios en estado running/healthy
- [ ] Acceso funcional por gateway en `http://localhost:3000`
- [ ] Registro, login y CRUD de secretos funcionando
- [ ] Administrador inicial creado automaticamente al arrancar (bootstrap)
- [ ] Usuario regular ve solo su boveda personal en `/boveda`
- [ ] Administrador ve panel de gestion de usuarios en `/boveda`
- [ ] Cambio de roles funcional desde panel de administracion
- [ ] Ruta `/admin` bloqueada para usuarios sin rol admin
- [ ] Worker asincrono ejecutando tarea verificable

## 4. Seguridad minima requerida

- [ ] JWT implementado y validado en endpoints protegidos
- [ ] Claim `sub` del JWT como string (RFC 7519)
- [ ] Control de acceso basado en roles (RBAC) con roles `admin` y `user`
- [ ] Contrasenas hasheadas
- [ ] Secretos cifrados en reposo con clave persistente (ENCRYPTION_KEY)
- [ ] Rate limiting activo
- [ ] Secret scanning integrado (Gitleaks/TruffleHog)
- [ ] SAST integrado (Bandit/Semgrep)
- [ ] SCA integrado (Trivy/Dependency-Check/pip-audit/npm audit)
- [ ] DAST automatizado (OWASP ZAP)

## 5. Pipeline DevSecOps por fases

- [ ] Plan: Threat modeling en OWASP Threat Dragon + STRIDE
- [ ] Code: controles de seguridad sobre codigo y dependencias
- [ ] Build: build de imagenes + escaneo de CVE criticos
- [ ] Test: pruebas unitarias + DAST
- [ ] Release/Deploy: publicacion y despliegue automatizado
- [ ] Operate/Monitor: monitoreo y logs (bonificable)

## 6. Documentacion obligatoria

- [ ] README principal actualizado
- [ ] Manual de Usuario
- [ ] Manual Tecnico (arquitectura y diagramas)
- [ ] Manual de Operacion y DevOps
- [ ] Manual de Seguridad y Riesgos
- [ ] Plan de Pruebas
- [ ] Evidencias de ejecucion y reportes de seguridad

## 7. Sustentacion

- [ ] Arquitectura explicada con diagramas
- [ ] Flujo end-to-end demostrado en vivo
- [ ] Riesgos y mitigaciones presentados
- [ ] Lecciones aprendidas y mejoras futuras declaradas
