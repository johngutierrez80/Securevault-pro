# Seguridad y Riesgos

## 1. Controles de seguridad implementados
- Autenticación con JWT firmado (HS256).
- Expiración de token en auth-service.
- Verificación de token en vault-service.
- Hash de contraseñas de usuario con bcrypt.
- Cifrado de secretos de la bóveda con Fernet.
- Rate limiting en endpoints de vault (10/minuto por IP) usando Redis.
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

## 4. Cumplimiento de objetivos académicos
Este proyecto demuestra controles de seguridad aplicables a entornos cloud y DevOps:
- Defensa en profundidad (hash + cifrado + JWT + rate limiting).
- Aislamiento por servicio y despliegue reproducible con Docker.
- Configuración operativa y trazabilidad por logs de contenedor.
