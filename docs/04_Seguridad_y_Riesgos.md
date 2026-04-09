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
