# Plan de Pruebas — SecureVault Pro v1.2

## 1. Objetivo

Validar funcionamiento, seguridad y persistencia de SecureVault Pro v1.2 para la entrega. Incluye casos de prueba para las funcionalidades incorporadas en v1.2: bloqueo de cuenta, recuperación por email, expiración diferenciada de JWT y polling del panel admin.

## 2. Alcance

- Registro e inicio de sesión.
- Bloqueo de cuenta por intentos fallidos y recovery.
- Acceso autenticado a bóveda.
- CRUD de secretos.
- Panel de administración y actualización automática.
- Expiración diferenciada de JWT por rol.
- Detección de sesión expirada y redirección.
- Persistencia en PostgreSQL y Redis.
- Rate limiting en Vault.

## 3. Casos de prueba funcionales

### CP-01 Registro exitoso

- **Dado** un usuario nuevo con email y contraseña válidos
- **Cuando** envío POST /auth/register
- **Entonces** retorna 200 y mensaje `User created`

### CP-02 Registro duplicado

- **Dado** un usuario ya existente
- **Cuando** envío POST /auth/register con el mismo email
- **Entonces** retorna 400

### CP-03 Login exitoso (usuario regular)

- **Dado** un usuario válido con rol `user`
- **Cuando** envío POST /auth/login
- **Entonces** retorna `access_token` con `exp` = 60 minutos

### CP-04 Login exitoso (administrador)

- **Dado** un usuario con rol `admin`
- **Cuando** envío POST /auth/login
- **Entonces** retorna `access_token` con `exp` = 480 minutos (8 horas)

### CP-05 Login con credenciales inválidas

- **Dado** usuario o clave inválidos
- **Cuando** envío POST /auth/login
- **Entonces** retorna 401 con indicación de intentos restantes

### CP-06 Crear secreto autenticado

- **Dado** token válido
- **Cuando** envío POST /vault/secret
- **Entonces** retorna 200

### CP-07 Listar secretos

- **Dado** token válido
- **Cuando** envío GET /vault/secret
- **Entonces** retorna lista solo del owner autenticado

### CP-08 Editar secreto

- **Dado** token válido y secreto existente del owner
- **Cuando** envío PUT /vault/secret/{id}
- **Entonces** retorna updated

### CP-09 Eliminar secreto

- **Dado** token válido y secreto existente del owner
- **Cuando** envío DELETE /vault/secret/{id}
- **Entonces** retorna deleted

### CP-10 Acceso sin token

- **Dado** request sin header Authorization
- **Cuando** llamo endpoints protegidos de vault o auth
- **Entonces** retorna 401

### CP-11 Rate limiting

- **Dado** múltiples requests consecutivas al vault
- **Cuando** supero 10/min por IP
- **Entonces** retorna 429 Too Many Requests

## 4. Casos de bloqueo de cuenta y recovery (v1.2)

### CP-12 Bloqueo por 3 intentos fallidos

- **Dado** un usuario existente
- **Cuando** envío POST /auth/login con clave incorrecta 3 veces consecutivas
- **Entonces** el 3er intento retorna 423 Locked y el contador Redis `login_fail:{email}` = 3

```powershell
for ($i = 1; $i -le 3; $i++) {
    Invoke-WebRequest -Method POST http://localhost:3000/auth/login `
      -Headers @{"Content-Type"="application/json"} `
      -Body '{"email":"test@test.com","password":"ClaveIncorrecta"}' `
      -ErrorAction SilentlyContinue
}
docker compose exec redis redis-cli -n 1 GET "login_fail:test@test.com"
```

### CP-13 Email de recovery al bloquearse

- **Dado** que la cuenta se bloqueó por 3 intentos
- **Cuando** se registra el 3er fallo
- **Entonces** Mailjet recibe solicitud de envío con enlace `?reset_token=T&email=E` y asunto de bloqueo

### CP-14 Reset de contraseña con token válido

- **Dado** un token de reset válido obtenido por email
- **Cuando** envío POST /auth/password-reset/confirm con email, token y nueva contraseña
- **Entonces** retorna 200 `{"msg": "Password updated"}` y la clave Redis `login_fail:{email}` es eliminada

```powershell
Invoke-WebRequest -Method POST http://localhost:3000/auth/password-reset/confirm `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email":"test@test.com","reset_token":"TOKEN","new_password":"NuevaClave123!"}'
docker compose exec redis redis-cli -n 1 GET "login_fail:test@test.com"
# Resultado esperado: (nil)
```

### CP-15 Login exitoso post-reset

- **Dado** que se completó el reset de contraseña
- **Cuando** envío POST /auth/login con la nueva contraseña
- **Entonces** retorna 200 con `access_token` (cuenta desbloqueada)

### CP-16 Desbloqueo en frontend post-reset

- **Dado** que el frontend mostró el banner de cuenta bloqueada
- **Cuando** el usuario completa el reset exitosamente
- **Entonces** el banner desaparece, el botón de login vuelve a estar activo, `isLockedOut=false`

## 5. Casos de expiración de JWT por rol (v1.2)

### CP-17 Expiración de token de administrador

- **Dado** login exitoso con rol `admin`
- **Cuando** decodifico el JWT retornado (sin verificar firma)
- **Entonces** `exp - iat ≈ 28800` segundos (480 minutos = 8 horas)

```powershell
# Decodificar payload del JWT (parte central en base64)
$token = "eyJ..."
$payload = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(($token.Split(".")[1] + "==").Replace("-","+").Replace("_","/")))
$payload | ConvertFrom-Json | Select-Object exp, iat, role
```

### CP-18 Expiración de token de usuario regular

- **Dado** login exitoso con rol `user`
- **Cuando** decodifico el JWT retornado
- **Entonces** `exp - iat ≈ 3600` segundos (60 minutos)

### CP-19 Redirección al expirar sesión en panel admin

- **Dado** que el admin está en el panel con token expirado o revocado
- **Cuando** el polling de 30s ejecuta refreshAll()
- **Entonces** el frontend detecta 401/403, limpia la sesión y redirige a "/"

## 6. Casos de panel admin (v1.2)

### CP-20 Actualización automática del panel

- **Dado** que el administrador está en el panel admin
- **Cuando** transcurren 30 segundos
- **Entonces** los datos se refrescan automáticamente y el timestamp "Última actualización" se actualiza

### CP-21 Botón "Actualizar ahora"

- **Dado** que el administrador está en el panel admin
- **Cuando** presiona "Actualizar ahora"
- **Entonces** se dispara `refreshAll()` inmediatamente y el countdown vuelve a 30s

### CP-22 Ver usuarios activos

- **Dado** token admin válido
- **Cuando** envío GET /auth/admin/active-users
- **Entonces** retorna lista de usuarios con sesión activa no expirada

### CP-23 Revocar sesiones de un usuario

- **Dado** token admin válido y un usuario con sesiones activas
- **Cuando** envío POST /auth/users/{id}/sessions/revoke
- **Entonces** el usuario afectado recibe 401 en su próxima llamada autenticada

### CP-24 Ver bitácora de auditoría

- **Dado** token admin válido
- **Cuando** envío GET /auth/admin/audit-logs
- **Entonces** retorna lista de eventos con acción, actor y timestamp

## 7. Casos de persistencia

### CP-25 Persistencia de usuarios

- Crear usuario, reiniciar servicios, validar que sigue en tabla `users`.

### CP-26 Persistencia de secretos

- Crear secreto, reiniciar servicios, validar que sigue en tabla `secrets` y puede leerse descifrado.

### CP-27 Persistencia de sesiones

- Hacer login, reiniciar servicios, validar que `auth_session` mantiene el registro (token sigue válido o expiró correctamente).

## 8. Evidencias para anexar en entrega

- Captura de login exitoso con token (usuario y admin).
- Captura de respuesta 423 en 3er intento fallido.
- Captura de Redis mostrando `login_fail:{email}` = 3.
- Captura del correo de recovery recibido.
- Captura de reset exitoso y Redis = (nil) post-reset.
- Captura de login exitoso después del reset.
- Captura de payload JWT con `exp` diferente para admin vs user.
- Captura del panel admin con countdown visible y última actualización.
- Captura de bóveda con CRUD completo.
- Captura de respuesta 401 sin token.
- Captura de respuesta 429 por rate limiting.
- Salida de `docker compose ps`.
- Consultas SQL en `users`, `secrets` y `auth_session`.


## 2. Alcance

- Registro e inicio de sesión.
- Acceso autenticado a bóveda.
- CRUD de secretos.
- Persistencia en PostgreSQL.
- Rate limiting en Vault.

## 3. Casos de prueba funcionales

### CP-01 Registro exitoso

- Dado un usuario nuevo
- Cuando envío POST /auth/register
- Entonces retorna 200 y mensaje User created

### CP-02 Registro duplicado

- Dado un usuario existente
- Cuando envío POST /auth/register con mismo email
- Entonces retorna 400

### CP-03 Login exitoso

- Dado un usuario válido
- Cuando envío POST /auth/login
- Entonces retorna access_token

### CP-04 Login inválido

- Dado usuario o clave inválidos
- Cuando envío POST /auth/login
- Entonces retorna 401

### CP-05 Crear secreto autenticado

- Dado token válido
- Cuando envío POST /vault/secret
- Entonces retorna 200

### CP-06 Listar secretos

- Dado token válido
- Cuando envío GET /vault/secret
- Entonces retorna lista del owner autenticado

### CP-07 Editar secreto

- Dado token válido y secreto existente
- Cuando envío PUT /vault/secret/{id}
- Entonces retorna updated

### CP-08 Eliminar secreto

- Dado token válido y secreto existente
- Cuando envío DELETE /vault/secret/{id}
- Entonces retorna deleted

### CP-09 Acceso sin token

- Dado request sin Authorization
- Cuando llamo endpoints de vault
- Entonces retorna 401

### CP-10 Rate limiting

- Dado múltiples requests consecutivas a vault
- Cuando supero 10/min por IP
- Entonces retorna 429

## 4. Casos de persistencia

### CP-11 Persistencia de usuarios

- Crear usuario, reiniciar servicios, validar que sigue en users.

### CP-12 Persistencia de secretos

- Crear secreto, reiniciar servicios, validar que sigue en secrets y puede leerse.

## 5. Evidencias para anexar en entrega

- Capturas de login, bóveda y CRUD.
- Capturas de consultas SQL en users y secrets.
- Captura de respuesta 401 sin token.
- Captura de respuesta 429 por rate limiting.
- Salida de docker compose ps.
