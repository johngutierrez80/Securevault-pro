# Checklist de Entrega

## 1. Entregables obligatorios del curso

- [ ] Repositorio GitHub publico con codigo, pipelines, IaC y documentacion
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
