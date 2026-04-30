# Seguridad y Riesgos

## 1. Controles de seguridad implementados

- Autenticación con JWT firmado (HS256).
- Expiración de token en auth-service.
- Verificación de token en vault-service.
- Hash de contraseñas de usuario con bcrypt.
- Cifrado de secretos de la bóveda con Fernet.
- Rate limiting en endpoints de vault (10/minuto por IP) usando Redis.
- Worker asíncrono independiente para consumo de eventos de seguridad desde Redis.
- Separación de servicios detrás de gateway Nginx.

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

| Elemento o flujo         | STRIDE dominante       | Riesgo principal                                     | Mitigación actual o propuesta                                         |
| ------------------------ | ---------------------- | ---------------------------------------------------- | --------------------------------------------------------------------- |
| Usuario / navegador      | Spoofing               | Robo de token o suplantación de sesión               | Validación JWT, expiración de token, endurecimiento futuro contra XSS |
| Flujo usuario -> gateway | Information Disclosure | Exposición de credenciales y tokens en tránsito      | Uso de HTTPS en despliegues reales                                    |
| Auth Service             | Elevation of Privilege | Emisión fraudulenta de JWT por secretos débiles      | Variables de entorno seguras y rotación de claves                     |
| Vault Service            | Elevation of Privilege | Acceso no autorizado a secretos                      | Verificación de token y control de autorización por endpoint          |
| Vault Service            | Denial of Service      | Abuso por múltiples solicitudes                      | Rate limiting con Redis y SlowAPI                                     |
| PostgreSQL               | Information Disclosure | Exposición de datos sensibles y backups              | Cifrado de secretos, backups protegidos y control de acceso           |
| Redis                    | Tampering              | Manipulación del estado de rate limiting             | Aislamiento en red privada y endurecimiento futuro                    |
| GitHub Actions           | Information Disclosure | Fuga de secretos de CI/CD                            | GitHub Secrets, environments protegidos y revisión de workflows       |
| Registros de imágenes    | Tampering              | Publicación o reemplazo de imágenes maliciosas       | Escaneo de imágenes, control de permisos y tags versionados           |
| Deploy Workflow          | Elevation of Privilege | Uso indebido de llave SSH o aprobación no autorizada | Aprobación manual en environment production y secretos protegidos     |

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
