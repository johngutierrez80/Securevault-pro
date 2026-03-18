# Checklist de Entrega

## 1. Código y ejecución

- [ ] Proyecto levanta con docker compose up -d --build
- [ ] Todos los servicios en estado running/healthy
- [ ] Acceso web en http://localhost:3000

## 2. Funcionalidad

- [ ] Registro de usuario
- [ ] Login con token
- [ ] Guardar secreto
- [ ] Listar secretos
- [ ] Editar secreto
- [ ] Eliminar secreto
- [ ] Logout

## 3. Seguridad

- [ ] Mensajes de login sin exposición técnica
- [ ] Endpoints de vault protegidos con JWT
- [ ] Token con expiración
- [ ] Rate limiting activo
- [ ] Contraseñas hasheadas
- [ ] Secretos cifrados

## 4. Persistencia y datos

- [ ] Datos persisten tras reinicio de servicios
- [ ] Tablas users y secrets verificadas en PostgreSQL
- [ ] ENCRYPTION_KEY definida para entorno de demostración

## 5. Documentación

- [ ] README actualizado
- [ ] Manual de Usuario
- [ ] Manual Técnico
- [ ] Manual de Operación y DevOps
- [ ] Seguridad y Riesgos
- [ ] Plan de Pruebas
- [ ] Evidencias (capturas) anexadas

## 6. Presentación

- [ ] Arquitectura explicada en 1 diagrama
- [ ] Flujo end-to-end demostrado en vivo
- [ ] Riesgos y mitigaciones presentados
- [ ] Limitaciones actuales y mejoras futuras declaradas
