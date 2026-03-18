# Plan de Pruebas

## 1. Objetivo

Validar funcionamiento, seguridad básica y persistencia de SecureVault para la entrega.

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
- Cuando envío POST /auth/register con mismo username
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

- Capturas de login, dashboard y CRUD.
- Capturas de consultas SQL en users y secrets.
- Captura de respuesta 401 sin token.
- Captura de respuesta 429 por rate limiting.
- Salida de docker compose ps.
