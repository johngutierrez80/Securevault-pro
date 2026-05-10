# Manual de Usuario — SecureVault Pro v1.2

## 1. Objetivo

Este documento explica el uso funcional de SecureVault Pro para usuarios finales: crear cuenta, iniciar sesión, guardar credenciales, editar, eliminar y cerrar sesión. Incluye los flujos de seguridad activos en v1.2: bloqueo de cuenta, recuperación de contraseña por email y comportamiento diferenciado según rol.

## 2. Acceso al sistema

1. Levantar servicios del proyecto.
2. Abrir el navegador en http://localhost:3000.
3. En la pantalla principal:

- Iniciar sesión con usuario y contraseña existentes.
- O crear cuenta con el botón **Crear cuenta gratuita**.

## 3. Flujo principal de uso

### 3.1 Registro de cuenta

1. Ingresar correo electrónico.
2. Ingresar contraseña (mínimo 8 caracteres, mayúsculas, números y símbolo).
3. Presionar **Crear cuenta gratuita**.
4. Verificar mensaje de confirmación. Si `REQUIRE_EMAIL_VERIFICATION=true` está activo, revisar el correo para verificar la cuenta antes de iniciar sesión.

### 3.2 Inicio de sesión

1. Ingresar correo y contraseña.
2. Presionar **Iniciar Sesión**.
3. Si las credenciales son válidas, se abre la bóveda (usuario) o el panel admin (administrador).
4. Si no son válidas, el sistema muestra el mensaje de error y el conteo de intentos restantes.

### 3.3 Bloqueo de cuenta tras intentos fallidos

El sistema bloquea automáticamente la cuenta después de **3 intentos fallidos consecutivos**:

1. **1er intento fallido**: mensaje de error + "Te quedan 2 intentos".
2. **2do intento fallido**: mensaje de error + "Te quedan 1 intento".
3. **3er intento fallido**: 
   - El botón de login se desactiva (muestra "Acceso bloqueado").
   - Aparece un **banner rojo de bloqueo** con instrucciones.
   - El panel de recuperación de contraseña se abre automáticamente.
   - Se envía un **correo electrónico automático** con un enlace de restablecimiento.
4. El bloqueo dura **5 minutos** en Redis. Después del tiempo, se puede volver a intentar.

> Si recibe el correo con el enlace de recuperación, haga clic en él. El sistema pre-cargará automáticamente el token y el email en el panel de recuperación.

### 3.4 Recuperación de contraseña

**Opción A — Desde el panel de login:**
1. Hacer clic en **¿Olvidaste tu contraseña?** o en el panel que aparece al bloquearse.
2. Ingresar el correo registrado en el campo "Email de recuperación".
3. Solicitar el token de recuperación.
4. Ingresar el token recibido por correo.
5. Ingresar y confirmar la nueva contraseña.
6. Presionar **Cambiar contraseña**.
7. El sistema desbloqueará la cuenta automáticamente y habilitará el login.

**Opción B — Desde el enlace del correo electrónico:**
1. Hacer clic en el botón **"Restablecer contraseña ahora"** del correo recibido.
2. El navegador abrirá el login con el token y email pre-cargados.
3. Ingresar la nueva contraseña directamente.
4. Presionar **Cambiar contraseña**.

### 3.5 Guardar una contraseña

1. En la bóveda, escribir **Sitio/Aplicación**.
2. Escribir **Contraseña**.
3. Presionar **Guardar**.
4. Se actualiza la tabla de la bóveda.

### 3.6 Visualizar contraseñas guardadas

1. La tabla **Mi Vault** lista los registros del usuario autenticado.
2. Cada contraseña se muestra enmascarada.
3. El botón de ojo permite mostrar u ocultar cada contraseña.

### 3.7 Editar un registro

1. Presionar el botón Editar (ícono lápiz).
2. Ingresar nuevo sitio y/o contraseña.
3. Confirmar.
4. Verificar actualización en la tabla.

### 3.8 Eliminar un registro

1. Presionar el botón Eliminar (ícono papelera).
2. Confirmar la acción.
3. Verificar que el registro desaparece de la tabla.

### 3.9 Cerrar sesión

1. Presionar **Cerrar sesión**.
2. El sistema elimina el token local y vuelve a la pantalla de login.

### 3.10 Expiración automática de sesión

Las sesiones expiran automáticamente según el rol:

| Rol | Duración |
|-----|----------|
| Usuario regular | 60 minutos |
| Administrador | 8 horas |

Al expirar, el sistema redirige automáticamente al login. No se pierden datos guardados.

## 4. Panel de administración (solo rol `admin`)

Los usuarios con rol `admin` acceden a un panel diferente que incluye:

- **Estadísticas en tiempo real**: total de usuarios, administradores, usuarios regulares, activos y conectados en este momento.
- **Usuarios conectados**: tabla con email, rol y sesiones activas; permite revocar sesiones individualmente.
- **Usuarios registrados**: tabla con ID, email, estado, rol y acciones (cambiar rol, activar/desactivar, eliminar).
- **Sesiones activas**: selector de usuario con tabla de sesiones y opción de revocar todas.
- **Bitácora de auditoría**: registro cronológico de todas las acciones administrativas.
- **Actualización automática cada 30 segundos**: el panel refresca todos los datos sin necesidad de recargar. El contador regresivo y la hora de última actualización son visibles en la barra superior. El botón **"Actualizar ahora"** permite un refresh inmediato.

## 5. Mensajes esperados

| Mensaje | Significado |
|---------|-------------|
| Credenciales incorrectas | Usuario o clave inválidos |
| Te quedan X intentos | Fallo de login, quedan intentos antes del bloqueo |
| Cuenta bloqueada temporalmente | 3 intentos fallidos; usar el panel de recovery |
| Contraseña restablecida. Ya puedes iniciar sesión. | Reset exitoso, cuenta desbloqueada |
| No se pudieron cargar los datos de la bóveda | Error de lectura del vault service |
| No hay secretos guardados | Estado vacío normal |
| Sesión expirada | Token vencido; el sistema redirige al login |

## 6. Recomendaciones de uso

- No compartir usuario ni contraseña.
- Cerrar sesión al terminar, especialmente en equipos compartidos.
- Si recibe un correo de recuperación que no solicitó, cambie su contraseña inmediatamente.
- Usar contraseñas únicas y fuertes para cada sitio guardado en la bóveda.
