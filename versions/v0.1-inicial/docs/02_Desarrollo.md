# Manual de Desarrollo

## Requisitos
- Docker Desktop 4+
- Git
- Node.js 20+ (opcional para ejecucion sin Docker)

## Clonar y ejecutar
```bash
git clone https://github.com/TU-USUARIO/securevault-pro.git
cd securevault-pro
cp .env.example .env
docker compose up --build
```

## Endpoints principales
- Auth: http://localhost:3001
- Vault: http://localhost:3002
- Worker: http://localhost:3003
- Frontend: http://localhost:5173

## Pruebas basicas
```bash
docker compose ps
curl http://localhost:3001/health
curl http://localhost:3002/health
curl http://localhost:3003/health
```

## Flujo funcional MVP
1. Registrar usuario en frontend.
2. Iniciar sesion para obtener JWT.
3. Crear secreto en dashboard.
4. Ver y eliminar secretos propios.
