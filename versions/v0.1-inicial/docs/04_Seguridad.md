# Manual de Seguridad

## Amenazas identificadas (STRIDE basico)
- Spoofing: suplantacion de identidad de usuarios.
- Tampering: alteracion de secretos en transito.
- Repudiation: ausencia de trazabilidad.
- Information Disclosure: exposicion de secretos.
- Denial of Service: abuso de endpoints.
- Elevation of Privilege: escalamiento de rol.

## Controles implementados en Avance 1
- JWT con expiracion para autenticacion.
- Cifrado AES-256-GCM para secretos en base de datos.
- Helmet para cabeceras de seguridad.
- Rate limiting en Auth y Vault.
- Pipeline con deteccion de secretos (Gitleaks).
- SAST basico (Semgrep) y escaneo Trivy FS.

## Evidencias de seguridad esperadas
- Capturas de GitHub Actions exitosas.
- Reportes de Trivy y Semgrep en pipeline.
- Modelo inicial en Threat Dragon exportado a docs.
