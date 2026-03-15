# Manual de Usuario

## 1. Objetivo
Este documento explica el uso funcional de SecureVault para usuarios finales: crear cuenta, iniciar sesión, guardar credenciales, editar, eliminar y cerrar sesión.

## 2. Acceso al sistema
1. Levantar servicios del proyecto.
2. Abrir el navegador en http://localhost:3000.
3. En la pantalla principal:
- Iniciar sesión con usuario y contraseña existentes.
- O crear cuenta con el botón Crear cuenta gratuita.

## 3. Flujo principal de uso
### 3.1 Registro de cuenta
1. Ingresar usuario.
2. Ingresar contraseña.
3. Presionar Crear cuenta gratuita.
4. Verificar mensaje de confirmación.

### 3.2 Inicio de sesión
1. Ingresar usuario y contraseña.
2. Presionar Iniciar Sesión.
3. Si las credenciales son válidas, se abre el dashboard.
4. Si no son válidas, se muestra el mensaje: Credenciales incorrectas.

### 3.3 Guardar una contraseña
1. En el dashboard, escribir Sitio/Aplicación.
2. Escribir Contraseña.
3. Presionar Guardar.
4. Se actualiza la tabla de la bóveda.

### 3.4 Visualizar contraseñas guardadas
1. La tabla Mi Vault lista los registros del usuario autenticado.
2. Cada contraseña se muestra enmascarada.
3. El botón de ojo permite mostrar u ocultar cada contraseña.

### 3.5 Editar un registro
1. Presionar el botón Editar (ícono lápiz).
2. Ingresar nuevo sitio y/o contraseña.
3. Confirmar.
4. Verificar actualización en la tabla.

### 3.6 Eliminar un registro
1. Presionar el botón Eliminar (ícono papelera).
2. Confirmar la acción.
3. Verificar que el registro desaparece de la tabla.

### 3.7 Cerrar sesión
1. Presionar Cerrar sesión.
2. El sistema elimina el token local y vuelve a la pantalla de login.

## 4. Mensajes esperados
- Credenciales incorrectas: Usuario/clave inválidos o faltantes.
- No se pudieron cargar los datos de la bóveda: Error de lectura del servicio vault.
- No hay secretos guardados: Estado vacío normal.

## 5. Recomendaciones de uso
- No compartir usuario ni contraseña.
- Cerrar sesión al terminar.
- Evitar usar el sistema en equipos públicos sin cerrar sesión.
