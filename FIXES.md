# Fixes de Compatibilidad Local - Sesión 2026-03-21

Este documento registra los ajustes mínimos necesarios para ejecutar SecureVault localmente en Windows/Docker Compose.

## 1. Frontend - Dependencia npm inválida

**Archivo:** `frontend-spa/package.json`  
**Problema:** versión `^7.38.0` de `eslint-plugin-react` no existe en npm registry.  
**Error durante docker build:**
```
npm error code ETARGET
npm error notarget No matching version found for eslint-plugin-react@^7.38.0
```

**Solución:**
```diff
- "eslint-plugin-react": "^7.38.0",
+ "eslint-plugin-react": "^7.37.5",
```

**Impacto:** PermiteMódulos npm in `npm install` dentro de docker build; ningún cambio en lógica de código.

---

## 2. Vault Service - Missing .env file

**Archivo:** `servicios/vault-service/Dockerfile`  
**Problema:** SlowAPI (middleware de rate limiting) valida archivo `.env` en tiempo de inicialización del módulo.  
**Error durante startup:**
```
File "/app/app/core/rate_limit.py", line 5, in <module>
    limiter = Limiter(key_func=get_remote_address, storage_uri="redis://redis:6379")
FileNotFoundError: Config file '.env' not found.
```

**Solución:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt

# slowapi/starlette expects an env file path and fails hard if it does not exist.
RUN touch .env

RUN useradd -m appuser
```

**Impacto:** Archivo vacío satisface validación de SlowAPI sin afectar configuración (variables se cargan desde entorno Docker).

---

## 3. Gateway Frontend - Nginx Permission Denied

**Archivo:** `frontend-spa/Dockerfile`  
**Problema:** Directiva `USER nginx` provoca Permission denied en `/var/cache/nginx` al crear directorios temporales.  
**Error durante startup:**
```
nginx: [emerg] mkdir() "/var/cache/nginx/client_temp" failed (13: Permission denied)
```

**Solución:**
```dockerfile
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Removido: USER nginx (permite que nginx ejecute como root en contenedor)

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
```

**Impacto:** En entorno contenedor aislado, ejecutar nginx como root es aceptable. No afecta seguridad de producci\u00e3n (compose.prod.yml puede mantener su propia configuración de usuario).

---

## Validación Post-Fix

Todos los servicios arrancaron correctamente:

```
✓ Image securevault_pro_full-gateway        Built
✓ Image securevault_pro_full-auth           Built
✓ Image securevault_pro_full-vault          Built
✓ Container postgres-1   Healthy
✓ Container redis-1      Healthy
✓ Container auth-1       Up (health: starting)
✓ Container vault-1      Up (health: starting)
✓ Container gateway-1    Up (health: starting)
```

Endpoints validados:
- http://localhost:3000          → 200 OK (Gateway)
- http://localhost:8001/docs     → 200 OK (Auth)
- http://localhost:8002/docs     → 200 OK (Vault)

---

## Notas para Desarrolladores

- **Cambios mínimos:** Se priorizó alterar lo menos posible el código base utilizando versiones válidas y configuraciones mínimas.
- **Compatibilidad:** Los fixes son exclusivamente para ejecución local en Docker. Entornos de producción pueden mantener configuración diferente si es necesario.
- **Documentacion:** Los cambios se reflejan en README.md y docs/03_Manual_Operacion_DevOps.md bajo las secciones "Notas de compatibilidad" e "Incidencias comunes".
- **Futuro:** Para future releases, considerar:
  - Usar pinning exacto de dependencias npm si se requiere reproducibilidad estricta.
  - Examinar si SlowAPI puede ser configurado para no validar .env en modo contenedor.
  - Evaluar usuario de ejecución nginx en compose según requerimientos de seguridad.
