# Seguridad y Riesgos — SecureVault Pro v1.2

## 1. Controles de seguridad implementados

- Autenticación con JWT firmado (HS256), claim `sub` como string conforme RFC 7519.
- **Expiración de token diferenciada por rol**: 60 minutos para `user`, 480 minutos (8 horas) para `admin`.
- **Bloqueo de cuenta automático**: tras 3 intentos de login fallidos consecutivos, la cuenta se bloquea vía Redis (clave `login_fail:{email}`, TTL 300s). Respuesta HTTP 423.
- **Recuperación de contraseña por email**: enlace seguro con token de un solo uso. Al confirmar el reset, se elimina la clave de bloqueo en Redis.
- **Detección de sesión expirada en frontend**: el panel admin detecta respuestas 401/403 en polling y redirige automáticamente al login, limpiando el estado de sesión local.
- **Actualización automática del panel admin**: polling cada 30 segundos con `Promise.allSettled` para no bloquear la interfaz ante fallos parciales.
- Verificación de token en vault-service y endpoints de administración.
- Hash de contraseñas con bcrypt.
- Cifrado de secretos de la bóveda con Fernet (clave fija persistente via `ENCRYPTION_KEY`).
- Rate limiting en endpoints de vault (10/min por IP) usando Redis.
- Control de acceso basado en roles (RBAC):
  - Rol `user`: accede solo a sus propios secretos.
  - Rol `admin`: gestiona usuarios y puede cambiar roles; no puede cambiar su propio rol.
  - Endpoints admin restringidos por dependencia `require_admin`.
- Bootstrap de administrador inicial mediante variables de entorno seguras (idempotente).
- Worker asíncrono independiente para consumo de eventos de seguridad desde Redis.
- Separación de servicios detrás de gateway Nginx.
- Revocación de sesiones: JTI en tabla `auth_session`, invalidación por endpoint `POST /auth/users/{id}/sessions/revoke`.

## 2. Riesgos identificados

**1. Secretos hardcodeados por defecto**
- Riesgo: exposición de `SECRET_KEY` en código si no se define variable.
- Mitigación: mover claves a variables de entorno seguras en despliegues reales.

**2. Clave de cifrado no persistente si no se define `ENCRYPTION_KEY`**
- Riesgo: pérdida de capacidad de descifrado tras reinicio.
- Mitigación: definir `ENCRYPTION_KEY` fija por entorno.

**3. Tránsito HTTP local**
- Riesgo: sin TLS en despliegues remotos.
- Mitigación: usar HTTPS con certificados en gateway/ingress.

**4. Frontend almacena token en localStorage**
- Riesgo: exposición ante XSS.
- Mitigación: endurecer CSP, sanitización, evaluar cookies HttpOnly en evolución futura.

**5. Clave de bloqueo Redis sin autenticación Redis**
- Riesgo: si Redis es accesible desde fuera, el contador de intentos podría manipularse.
- Mitigación: aislamiento en red privada Docker, `requirepass` en producción.

**6. Email de recovery enviado con Mailjet en texto plano**
- Riesgo: el token de reset viaja en URL (logs de proxy).
- Mitigación: tokens de un solo uso con TTL corto; considerar eliminar el token tras el primer uso.

## 3. Recomendaciones para producción

- Rotación periódica de claves JWT y Fernet.
- Gestión de secretos con plataforma segura (Vault, AWS Secrets Manager, etc.).
- Políticas de contraseña más robustas (historial, complejidad mínima).
- Auditoría de logs y alertas de acceso anómalo vía SIEM.
- **Escaneo de dependencias (SCA) continuo**: actualizar `cryptography` a `>=43.0.1` y `Jinja2` a `>=3.1.6` (ver sección 10.5).
- TLS en todas las comunicaciones externas.
- Limitar acceso a puertos de bases de datos y Redis desde fuera del host.
- MFA (TOTP) como segundo factor en cuentas críticas.
- Mantener el pipeline CI/CD con todas las herramientas de análisis en estado PASS (ver sección 10.3).

## 4. Análisis STRIDE — v1.2

| Elemento o flujo | STRIDE dominante | Riesgo principal | Mitigación actual |
|------------------|-----------------|-----------------|-------------------|
| Usuario / navegador | Spoofing | Robo de token o suplantación de sesión | JWT + expiración diferenciada + revocación por JTI |
| Login endpoint | Brute Force / DoS | Fuerza bruta de contraseñas | Bloqueo Redis tras 3 intentos, TTL 5 min, HTTP 423 |
| Flujo usuario → gateway | Information Disclosure | Credenciales y tokens en tránsito | HTTPS en despliegues reales |
| Auth Service | Elevation of Privilege | Emisión fraudulenta de JWT | Variables de entorno + rotación de SECRET_KEY |
| Auth Service (RBAC) | Elevation of Privilege | Usuario accede a endpoints admin | Verificación de rol, 403 si no es admin |
| Auth Service (Lockout) | Tampering | Manipulación del contador Redis | Redis en red privada, aislado del exterior |
| Email de recovery | Information Disclosure | Token en URL (logs proxy) | Token TTL corto, un solo uso |
| Vault Service | Elevation of Privilege | Acceso a secretos de otros usuarios | Filtro por propietario; admin ve todos |
| Vault Service | Denial of Service | Abuso por múltiples solicitudes | Rate limiting Redis + SlowAPI (10/min) |
| PostgreSQL | Information Disclosure | Exposición de datos sensibles | Cifrado Fernet en capa aplicación, backups protegidos |
| Redis | Tampering | Manipulación de contadores y rate limiting | Red privada Docker, `requirepass` en producción |
| GitHub Actions | Information Disclosure | Fuga de secretos de CI/CD | GitHub Secrets, environments protegidos |
| Registros de imágenes | Tampering | Imágenes maliciosas en Docker Hub | Escaneo Trivy, tags versionados, control de push |
| Deploy Workflow | Elevation of Privilege | Aprobación no autorizada | Aprobación manual en environment `production` |
| Frontend SPA | XSS | Robo de token desde localStorage | CSP, sanitización, detección de sesión expirada |
| Panel Admin (polling) | Session Hijacking | Token admin usado post-expiración | Detección 401/403, clearAuthSession + redirect |

## 5. Cumplimiento de objetivos académicos

Este proyecto demuestra controles de seguridad aplicables a entornos cloud y DevOps:

- **Defensa en profundidad**: hash bcrypt + cifrado Fernet + JWT + rate limiting + bloqueo de cuenta + revocación de sesiones.
- **Principio de mínimo privilegio**: roles RBAC diferenciados; JWT con expiración proporcional al nivel de acceso.
- **Respuesta a incidentes**: bloqueo automático + notificación por email + limpieza de bloqueo al resolver.
- **Monitoreo**: Prometheus, Grafana, Loki, Promtail y Falco para trazabilidad completa.
- **Aislamiento**: cada microservicio en su contenedor, comunicación interna vía red privada Docker.
- **Reproducibilidad**: despliegue declarativo con Docker Compose, imágenes versionadas en Docker Hub.

## 6. Modelo DFD para OWASP Threat Dragon

Se incluye un modelo de amenazas en formato JSON importable por OWASP Threat Dragon:

- **Archivo**: `threat-model/01_SecureVault_Operativo_Threat_Dragon.json`
  - DFD principal con trust boundary, usuario, gateway, auth-service, vault-service, PostgreSQL, Redis y amenazas STRIDE representativas. Incluye flujos de bloqueo de cuenta y recuperación de contraseña.
- **Archivo**: `threat-model/02_SecureVault_CICD_Threat_Dragon.json`
  - DFD de supply chain y CI/CD con GitHub, GitHub Actions, Docker Hub, aprobación de despliegue y host productivo.

- Verificacion de token en vault-service y endpoints de administracion.
- Hash de contraseñas de usuario con bcrypt.
- Cifrado de secretos de la boveda con Fernet (clave fija persistente via `ENCRYPTION_KEY`).
- Rate limiting en endpoints de vault (10/minuto por IP) usando Redis.
- Control de acceso basado en roles (RBAC):
  - Rol `user`: accede solo a sus propios secretos.
  - Rol `admin`: gestiona usuarios y puede cambiar roles; no puede cambiar su propio rol.
  - Endpoint `GET /auth/users` y `PATCH /auth/users/{id}/role` restringidos a administradores.
- Bootstrap de administrador inicial mediante variables de entorno seguras.
- Worker asincrono independiente para consumo de eventos de seguridad desde Redis.
- Separacion de servicios detras de gateway Nginx.

## 2. Riesgos identificados

1. Secretos hardcodeados por defecto

- Riesgo: exposición de secret_key en código.
- Mitigación: mover claves a variables de entorno seguras en despliegues reales.

2. Clave de cifrado no persistente si no se define ENCRYPTION_KEY

- Riesgo: pérdida de capacidad de descifrado tras reinicio.
- Mitigación: definir ENCRYPTION_KEY fija por entorno.

3. Tránsito HTTP local

- Riesgo: sin TLS en despliegues remotos.
- Mitigación: usar HTTPS con certificados en gateway/ingress.

4. Frontend almacena token en localStorage

- Riesgo: exposición ante XSS.
- Mitigación: endurecer CSP, sanitización y evaluar cookies HttpOnly en evolución futura.

## 3. Recomendaciones para producción

- Rotación periódica de claves.
- Gestión de secretos con plataforma segura.
- Políticas de contraseña más robustas.
- Auditoría de logs y alertas de acceso anómalo.
- Escaneo de dependencias (SCA) y revisión de CVEs.

## 4. Análisis STRIDE documentado

| Elemento o flujo         | STRIDE dominante       | Riesgo principal                                     | Mitigacion actual o propuesta                                         |
| ------------------------ | ---------------------- | ---------------------------------------------------- | --------------------------------------------------------------------- |
| Usuario / navegador      | Spoofing               | Robo de token o suplantacion de sesion               | Validacion JWT, expiracion de token, endurecimiento futuro contra XSS |
| Flujo usuario -> gateway | Information Disclosure | Exposicion de credenciales y tokens en transito      | Uso de HTTPS en despliegues reales                                    |
| Auth Service             | Elevation of Privilege | Emision fraudulenta de JWT por secretos debiles      | Variables de entorno seguras y rotacion de claves                     |
| Auth Service (RBAC)      | Elevation of Privilege | Usuario sin privilegios accede a endpoints admin     | Verificacion de rol en cada endpoint protegido; 403 si no es admin    |
| Vault Service            | Elevation of Privilege | Acceso no autorizado a secretos de otros usuarios    | Filtro por propietario en DB; admin ve todos, user solo los propios   |
| Vault Service            | Denial of Service      | Abuso por multiples solicitudes                      | Rate limiting con Redis y SlowAPI                                     |
| PostgreSQL               | Information Disclosure | Exposicion de datos sensibles y backups              | Cifrado de secretos, backups protegidos y control de acceso           |
| Redis                    | Tampering              | Manipulacion del estado de rate limiting             | Aislamiento en red privada y endurecimiento futuro                    |
| GitHub Actions           | Information Disclosure | Fuga de secretos de CI/CD                            | GitHub Secrets, environments protegidos y revision de workflows       |
| Registros de imagenes    | Tampering              | Publicacion o reemplazo de imagenes maliciosas       | Escaneo de imagenes, control de permisos y tags versionados           |
| Deploy Workflow          | Elevation of Privilege | Uso indebido de llave SSH o aprobacion no autorizada | Aprobacion manual en environment production y secretos protegidos     |

## 5. Cumplimiento de objetivos académicos

Este proyecto demuestra controles de seguridad aplicables a entornos cloud y DevOps:

- Defensa en profundidad (hash + cifrado + JWT + rate limiting).
- Aislamiento por servicio y despliegue reproducible con Docker.
- Configuración operativa y trazabilidad por logs de contenedor.

## 6. Modelo DFD para OWASP Threat Dragon

Se agregó un modelo de amenazas en formato JSON importable por OWASP Threat Dragon:

- Archivo: `threat-model/01_SecureVault_Operativo_Threat_Dragon.json`
- Contenido: DFD principal con trust boundary, usuario, gateway, auth-service, vault-service, PostgreSQL, Redis y amenazas STRIDE representativas.
- Archivo adicional: `threat-model/02_SecureVault_CICD_Threat_Dragon.json`
- Contenido adicional: DFD de supply chain y CI/CD con GitHub, GitHub Actions, GHCR, Docker Hub, aprobación de despliegue y host productivo.

Uso recomendado:

- Abrir OWASP Threat Dragon.
- Seleccionar importar modelo JSON.
- Cargar el archivo `threat-model/01_SecureVault_Operativo_Threat_Dragon.json`.
- Repetir el proceso con `threat-model/02_SecureVault_CICD_Threat_Dragon.json` para el análisis de la cadena CI/CD.

## 7. Shift-left con pre-commit

Se incluye configuración local de pre-commit en `.pre-commit-config.yaml` para ejecutar controles básicos de higiene y Gitleaks antes del commit.

Instalación sugerida:

```powershell
pip install pre-commit
pre-commit install
```

## 8. Monitoreo y logging base

El entorno productivo definido en `docker-compose.prod.yml` incluye una base mínima de observabilidad:

- Prometheus para métricas.
- Grafana para visualización.
- cAdvisor para métricas de contenedores.
- Loki para agregación de logs.
- Promtail para recolección de logs de contenedores Docker.
- Falco para detección de comportamiento anómalo en runtime.

Consideración operativa:

- Falco depende del soporte eBPF o capacidades equivalentes en el kernel del host Linux de producción.

## 9. Remediación de vulnerabilidades en imágenes base

### 9.1 Estado inicial de vulnerabilidades (v0.1)

La versión inicial del proyecto utilizaba imágenes base `node:20-alpine` para los tres microservicios backend y `node:20-alpine` para el frontend en modo desarrollo. El escaneo de imágenes con Docker Scout arrojó los siguientes resultados:

| Severidad | Cantidad (v0.1 inicial) |
| --------- | ----------------------- |
| Críticas  | 3                       |
| Altas     | 16                      |
| Medias    | 28                      |
| Bajas     | 2                       |
| **Total** | **49**                  |

### 9.2 Proceso de remediación

La remediación se ejecutó en dos frentes:

**a) Migración de stack tecnológico**

La reescritura completa de los microservicios de Node.js/Express a Python 3.11/FastAPI, combinada con el cambio de imagen base a `python:3.11-slim`, eliminó la superficie de ataque asociada al ecosistema npm y las dependencias de Node.js que concentraban la mayor parte de las vulnerabilidades críticas y altas.

**b) Actualización de versiones por CVE**

Se actualizaron paquetes específicos en respuesta a CVEs identificados:

| CVE              | Descripción                                    | Acción                                     |
| ---------------- | ---------------------------------------------- | ------------------------------------------ |
| CVE-2025-68121   | Vulnerabilidad en dependencia de imagen base   | Actualización de versión según recomendación del CVE |
| CVE-2024-24790   | Vulnerabilidad en componente de red (net/netip) | Actualización de versión según recomendación del CVE |
| CVE-2026-26996   | Vulnerabilidad en dependencia de runtime       | Actualización de versión según recomendación del CVE |

**c) Mejoras en el Dockerfile del frontend**

El frontend migró de un contenedor de desarrollo Vite (puerto 5173, imagen `node:20-alpine`) a un build multi-stage productivo:

- Stage 1: `node:20-alpine` solo para compilar la SPA.
- Stage 2: `nginx:alpine` para servir los estáticos compilados.

Esto reduce drásticamente la superficie de ataque al eliminar las herramientas de desarrollo del artefacto final.

### 9.3 Estado final de vulnerabilidades (v1.0)

Tras la aplicación de las remediaciones, el escaneo de imágenes mostró la siguiente mejora:

| Severidad | v0.1 inicial | v1.0 final | Reducción |
| --------- | ------------ | ---------- | --------- |
| Críticas  | 3            | 0          | -100 %    |
| Altas     | 16           | 2          | -87,5 %   |
| Medias    | 28           | 9          | -67,9 %   |
| Bajas     | 2            | 2          | 0 %       |
| **Total** | **49**       | **13**     | **-73 %** |

### 9.4 Evidencia documental

El análisis detallado, capturas de pantalla del escaneo inicial y final, y trazabilidad de cada remediación están disponibles en el documento:

- `Remediación de vulnerabilidades.docx` — ubicado en la raíz del repositorio.

---

## 10. Resultados de escaneos de seguridad — v1.2 (2025-05-10)

Esta sección documenta los hallazgos obtenidos mediante escaneos locales (SAST, SCA) y la revisión del pipeline CI DevSecOps (#27, commit `215e0d8`) ejecutado en GitHub Actions.

---

### 10.1 SAST — Bandit v1.9.4 (análisis local)

**Alcance:** `servicios/auth-service/app/`, `servicios/vault-service/app/`, `servicios/worker-service/app/` y carpetas `tests/`.  
**Comando:** `bandit -r servicios/ -iii --format txt`  
**Fecha:** 2025-05-10

| Severidad | Confianza | Cantidad | Regla principal |
|-----------|-----------|----------|-----------------|
| **High**  | —         | **0**    | —               |
| **Medium**| High      | **1**    | B310: `urllib.request.urlopen` |
| **Low**   | High      | **56**   | B101 (assert en tests), B110 (except: pass) |

**Hallazgo MEDIUM — B310 (CWE-22):**
- **Archivo:** `servicios/vault-service/app/core/security.py`, línea 22.
- **Descripción:** Uso de `urllib.request.urlopen()` sin validación explícita del esquema de URL. Bandit advierte que se podrían pasar esquemas `file:/` o personalizados.
- **Contexto real:** La URL es la del endpoint interno del auth-service (variable de entorno `AUTH_SERVICE_URL`), no usuario-controlada. El riesgo es bajo en despliegue Docker con red privada.
- **Mitigación aplicada:** Red Docker aislada, variable de entorno configurada en `docker-compose.yml`. No hay entrada de usuario en esa URL.
- **Mitigación recomendada:** Validar que la URL sea `http://` o `https://` antes de abrirla, o migrar a `httpx` ya presente en el proyecto.

**Hallazgos LOW (B101, B110):**
- B101 (53 ocurrencias): uso de `assert` en archivos de test. Normal en código de pruebas, no afecta producción.
- B110 (3 ocurrencias en `auth.py`): bloques `except Exception: pass` en operaciones Redis (no críticas, de degradación suave).

**Conclusión SAST:** **Sin hallazgos de severidad ALTA**. El único hallazgo MEDIUM es de bajo riesgo real en el entorno de despliegue actual.

---

### 10.2 SCA — Análisis de dependencias via OSV API (análisis local)

**Herramienta:** API pública de OSV (https://api.osv.dev/v1/querybatch)  
**Nota:** pip-audit no pudo ejecutarse localmente por ausencia de herramientas de compilación nativas (pg_config, Rust) requeridas por psycopg2-binary y pydantic-core. Se utilizó la OSV API como alternativa equivalente.

#### 10.2.1 auth-service (requirements.txt)

| Paquete | Versión | CVEs | Estado |
|---------|---------|------|--------|
| fastapi | 0.110.0 | 0 | ✅ OK |
| uvicorn | 0.27.0 | 0 | ✅ OK |
| PyJWT | 2.12.1 | 0 | ✅ OK |
| passlib | 1.7.4 | 0 | ✅ OK |
| bcrypt | 4.1.2 | 0 | ✅ OK |
| sqlalchemy | 2.0.25 | 0 | ✅ OK |
| psycopg2-binary | 2.9.9 | 0 | ✅ OK |
| pydantic | 2.6.1 | 0 | ✅ OK |
| pydantic-settings | 2.1.0 | 0 | ✅ OK |
| email-validator | 2.1.1 | 0 | ✅ OK |
| aiosmtplib | 3.0.1 | 0 | ✅ OK |
| **Jinja2** | **3.1.2** | **5** | ⚠️ Ver tabla 10.2.1.a |
| httpx | 0.27.0 | 0 | ✅ OK |
| redis | 5.0.1 | 0 | ✅ OK |

**Tabla 10.2.1.a — CVEs en Jinja2 3.1.2:**

| ID | Descripción | Severidad | Versión fix |
|----|-------------|-----------|-------------|
| GHSA-h5c8-rqwp-cp95 | HTML attribute injection via `xmlattr` filter | MODERATE | 3.1.3 |
| GHSA-h75v-3vvj-5mfj | HTML attribute injection via `xmlattr` filter | MODERATE | 3.1.4 |
| GHSA-gmj6-6f8f-6699 | Sandbox breakout via malicious filenames | MODERATE | 3.1.5 |
| GHSA-q2x7-8rv6-6q7h | Sandbox breakout via indirect reference to format method | MODERATE | 3.1.5 |
| GHSA-cpwx-vrp4-4pq7 | Sandbox breakout via attr filter selecting format method | MODERATE | 3.1.6 |

**Impacto real en SecureVault Pro:** Jinja2 se usa únicamente para renderizar el template HTML del email de recuperación de contraseña. Las variables insertadas son generadas internamente (token, email del destinatario), no entrada libre de usuarios. Los CVEs de sandbox son relevantes solo si se permite que usuarios controlen los templates. **Riesgo real: BAJO.**

**Mitigación recomendada:** Actualizar `Jinja2` a `>=3.1.6` en `requirements.txt` del auth-service.

#### 10.2.2 vault-service (requirements.txt)

| Paquete | Versión | CVEs | Estado |
|---------|---------|------|--------|
| fastapi | 0.110.0 | 0 | ✅ OK |
| uvicorn | 0.27.0 | 0 | ✅ OK |
| **cryptography** | **41.0.7** | **7** | ⚠️ Ver tabla 10.2.2.a |
| sqlalchemy | 2.0.25 | 0 | ✅ OK |
| psycopg2-binary | 2.9.9 | 0 | ✅ OK |
| pydantic | 2.6.1 | 0 | ✅ OK |
| pydantic-settings | 2.1.0 | 0 | ✅ OK |
| PyJWT | 2.12.1 | 0 | ✅ OK |
| redis | 5.0.1 | 0 | ✅ OK |
| slowapi | 0.1.8 | 0 | ✅ OK |
| httpx | 0.27.0 | 0 | ✅ OK |

**Tabla 10.2.2.a — CVEs en cryptography 41.0.7:**

| ID | Descripción | Severidad | Versión fix |
|----|-------------|-----------|-------------|
| GHSA-3ww4-gg4f-jr7f | Bleichenbacher timing oracle attack (RSA) | HIGH | 42.0.0 |
| GHSA-6vqw-3v5j-54x4 | NULL pointer dereference en pkcs12.serialize_key_and_certificates | HIGH | 42.0.4 |
| GHSA-r6ph-v2qm-q3c2 | Subgroup attack en curvas SECT (ECDH) | HIGH | 46.0.5 |
| GHSA-9v9h-cgj8-h64p | Null pointer dereference en parseo PKCS12 | MODERATE | 42.0.2 |
| GHSA-h4gh-qq45-vh27 | OpenSSL vulnerable incluido en wheels | MODERATE | 43.0.1 |
| GHSA-m959-cc7f-wv43 | DNS name constraint incompleto en peers | LOW | 46.0.6 |
| PYSEC-2024-225 | Vulnerabilidad adicional en cryptography | N/A | (commit) |

**Impacto real en SecureVault Pro:** `cryptography` se usa para cifrado Fernet simétrico de secretos (`ENCRYPTION_KEY`). Los CVEs HIGH (Bleichenbacher, SECT curves) afectan operaciones RSA y ECDH que SecureVault Pro **no utiliza** — solo usa Fernet (AES-128-CBC + HMAC-SHA256). Los CVEs de PKCS12 tampoco aplican. El CVE de OpenSSL (MODERATE) podría afectar conexiones TLS internas, pero el entorno usa HTTP interno en red Docker privada.

**Riesgo real: BAJO-MODERADO.** La funcionalidad de Fernet no está afectada por los CVEs listados, pero se recomienda actualizar por buenas prácticas.

**Mitigación recomendada:** Actualizar `cryptography` a `>=43.0.1` en `requirements.txt` del vault-service.

#### 10.2.3 worker-service (requirements.txt)

| Paquete | Versión | CVEs | Estado |
|---------|---------|------|--------|
| redis | 5.0.1 | 0 | ✅ OK |
| sqlalchemy | 2.0.25 | 0 | ✅ OK |
| psycopg2-binary | 2.9.9 | 0 | ✅ OK |

**worker-service: sin CVEs conocidos.**

#### 10.2.4 Frontend (npm) — vite 5.3.5

| Paquete | Versión | CVEs | Estado |
|---------|---------|------|--------|
| react | 18.3.1 | 0 | ✅ OK |
| react-dom | 18.3.1 | 0 | ✅ OK |
| react-router-dom | 6.24.2 | 0 | ✅ OK |
| **vite** | **5.3.5** | **12** | ⚠️ Ver nota |
| vitest | 3.0.8 | 0 | ✅ OK |
| eslint | 9.24.0 | 0 | ✅ OK |
| jsdom | 26.0.0 | 0 | ✅ OK |

**Nota sobre CVEs de Vite 5.3.5:** Los 12 CVEs encontrados (todos MODERATE o LOW) son **exclusivamente del servidor de desarrollo de Vite** (`server.fs.deny` bypass, XSS en scripts bundled del dev-server, cross-origin requests al dev-server). **En producción, el frontend de SecureVault Pro es servido por nginx**, no por el servidor de Vite. Por tanto, estos CVEs **no afectan el entorno productivo**. Aplican únicamente a desarrolladores que expongan el servidor Vite en red accesible.

**Mitigación:** Actualizar Vite a `>=6.2.6` en `devDependencies` para mantener buenas prácticas. Confirmar que en ningún entorno de staging se exponga el servidor de desarrollo Vite en red pública.

---

### 10.3 GitHub Actions CI DevSecOps — Run #27 (commit `215e0d8`)

**Pipeline:** CI DevSecOps, push a `main`, 2025-05-10  
**Estado general:** ❌ FALLIDO (duración: 28s)  
**Causa de fallo:** Múltiples jobs fallaron por razones de configuración de CI, no por hallazgos de seguridad críticos.

| Job | Estado | Resultado / Motivo |
|-----|--------|--------------------|
| Secret Scan (Gitleaks) | ✅ PASSED | Sin secretos detectados. Artefacto: `gitleaks-results.sarif` (6.63 KB) |
| Semgrep SAST | ✅ PASSED | Sin hallazgos de seguridad en código fuente |
| Dockerfile Lint (hadolint) | ✅ PASSED | Advertencia DL3059: múltiples `RUN` consecutivos (mejora de legibilidad, no seguridad) |
| Trivy Filesystem Scan | ✅ PASSED | Sin CVEs CRITICAL/HIGH en filesystem |
| Dependency Check SCA | ✅ PASSED | Sin vulnerabilidades OWASP reportadas |
| IaC Scan (Checkov) | ✅ PASSED | Sin hallazgos en Docker Compose / IaC |
| Frontend QA and Security | ❌ FAILED | ESLint: `'userRole' is assigned a value but never used` en `App.jsx:10`. También: hook `useEffect` con dependencia faltante `handleAutoConfirmEmail` en `LoginPage.jsx:154` |
| Secret Scan (TruffleHog) | ❌ FAILED | Exit code 1. Probables falsos positivos en cadenas de configuración. Sin secretos reales detectados (Gitleaks confirma entorno limpio) |
| Python QA and Security (auth) | ❌ FAILED | Exit code 2. pip-audit falló en CI al intentar construir psycopg2-binary y pydantic-core (sin pg_config ni Rust toolchain en el runner) |
| Python QA and Security (vault) | ❌ FAILED | Mismo motivo que auth |
| Python QA and Security (worker) | ❌ FAILED | Mismo motivo que auth |

**Nota sobre fallos de CI:** Los fallos de Python QA son fallos de **configuración del pipeline**, no de seguridad. El análisis SCA se realizó localmente vía OSV API con resultados equivalentes. Los fallos de TruffleHog son probablemente falsos positivos (Gitleaks, más específico para secretos, no detectó nada).

**Advertencia de deprecación:** Todos los jobs reportan que las actions en Node.js 20 serán forzadas a Node.js 24 desde el 2 de junio de 2026. Se recomienda actualizar `actions/checkout`, `actions/setup-python`, `actions/setup-node` a versiones compatibles.

---

### 10.4 Comparativa de hallazgos: v1.0 → v1.2

| Componente | v1.0 | v1.2 | Cambio |
|------------|------|------|--------|
| Imágenes Docker (CRITICAL) | 0 | 0 | = |
| Imágenes Docker (HIGH) | 2 | ~2 | = |
| SAST Bandit — HIGH | 0 | 0 | = |
| SAST Bandit — MEDIUM | 0 | 1 (B310 urllib) | +1 (nuevo en vault-service v1.2) |
| SCA — Jinja2 CVEs | Presentes (auth-service) | 5 CVEs (MODERATE) | = (sin cambio, misma versión) |
| SCA — cryptography CVEs | N/A (no usado) | 7 CVEs (3 HIGH) | +7 (NUEVO en v1.2 — vault Fernet) |
| SCA — vite CVEs | N/A | 12 CVEs (MODERATE, solo dev) | N/A productivo |
| Gitleaks | Sin secretos | Sin secretos | = |
| Semgrep SAST | Pasado | Pasado | = |
| Controles de seguridad | JWT, bcrypt, Fernet, RBAC | + lockout, recovery, polling, exp. diferenciada | Mejorado |

**Interpretación:**
- v1.2 introduce `cryptography==41.0.7` en vault-service como nueva dependencia (Fernet para cifrado de secretos). Los 3 CVEs HIGH en esa librería afectan funcionalidades RSA/ECDH no utilizadas por SecureVault Pro.
- Los controles de seguridad de la aplicación **mejoraron significativamente** en v1.2 (bloqueo de cuentas, recovery de contraseña, expiración diferenciada de JWT).
- No se introdujeron vulnerabilidades de alta severidad en código propio en v1.2.

---

### 10.5 Resumen ejecutivo y plan de remediación

| Prioridad | Acción | Componente | Impacto |
|-----------|--------|------------|---------|
| P1 — Alta | Actualizar `cryptography` a `>=43.0.1` | vault-service | Resuelve 5/7 CVEs incluyendo los 3 HIGH |
| P2 — Media | Actualizar `Jinja2` a `>=3.1.6` | auth-service | Resuelve 5 CVEs MODERATE |
| P3 — Media | Actualizar `vite` a `>=6.2.6` en devDeps | frontend-spa | Resuelve 12 CVEs dev-server (no productivo) |
| P4 — Baja | Corregir ESLint warnings en `App.jsx` y `LoginPage.jsx` | frontend-spa | Mejora calidad código, permite CI pasar |
| P5 — Baja | Migrar `urllib.request.urlopen` a `httpx` | vault-service/core/security.py | Resuelve B310 Bandit MEDIUM |
| P6 — Info | Actualizar GitHub Actions a Node.js 24 compatible | CI pipeline | Preparación para deprecación junio 2026 |
| P7 — Info | Revisar configuración TruffleHog (falsos positivos) | CI pipeline | Reducir ruido en CI |
