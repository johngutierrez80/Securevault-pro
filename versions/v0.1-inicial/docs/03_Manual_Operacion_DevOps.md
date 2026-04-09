# Manual de Operación y DevOps

## 1. Requisitos
- Docker y Docker Compose instalados.
- Puerto 3000 disponible para el gateway.
- Puertos 8001, 8002, 5432 y 6379 disponibles.

## 2. Levantar entorno
Desde la raíz del proyecto:

```powershell
docker compose up -d --build
```

Verificar estado:

```powershell
docker compose ps
```

## 3. Servicios esperados
- auth
- vault
- postgres
- redis
- gateway

## 4. Acceso funcional
- UI principal: http://localhost:3000
- Auth directo: http://localhost:8001/docs
- Vault directo: http://localhost:8002/docs

## 5. Operación diaria
### Reiniciar un servicio
```powershell
docker compose restart auth
```

### Reconstruir un servicio específico
```powershell
docker compose up -d --build vault
```

### Ver logs
```powershell
docker compose logs auth --tail=100
docker compose logs vault --tail=100
docker compose logs gateway --tail=100
```

## 6. Base de datos
Acceso a PostgreSQL:

```powershell
docker compose exec postgres psql -U vault -d vaultdb
```

Comandos útiles:
- \dt
- SELECT * FROM users;
- SELECT * FROM secrets;

## 7. Copias y recuperación
### Backup lógico
```powershell
docker compose exec postgres pg_dump -U vault -d vaultdb > backup_vaultdb.sql
```

### Restore lógico
```powershell
docker compose exec -T postgres psql -U vault -d vaultdb < backup_vaultdb.sql
```

## 8. Incidencias comunes
- Mensaje no se pudieron cargar los datos de la bóveda: revisar logs de vault y estado de token.
- Error de servicio no existe: usar nombres de servicio reales en compose (auth, vault, postgres, redis, gateway).
- Cambios de frontend no reflejados: recargar con Ctrl+F5 o reconstruir gateway.
