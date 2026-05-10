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
- Escaneo de dependencias (SCA) y revisión de CVEs.
- TLS en todas las comunicaciones externas.
- Limitar acceso a puertos de bases de datos y Redis desde fuera del host.
- MFA (TOTP) como segundo factor en cuentas críticas.

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
