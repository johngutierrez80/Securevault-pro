# SecureVault

Un gestor seguro de contraseñas construido con FastAPI, PostgreSQL y Docker.

## Metas del Proyecto

- Aplicar autenticacion centralizada con JWT entre servicios.
- Garantizar persistencia real con PostgreSQL para usuarios y secretos.
- Proteger secretos mediante hash de contraseñas y cifrado de datos sensibles.
- Incorporar componentes de entorno cloud y DevOps como Nginx, Docker Compose, Redis y rate limiting.
- Evitar exposicion de detalles tecnicos innecesarios en la interfaz de usuario.
- Mantener una separacion clara entre frontend, auth service, vault service y gateway.

## Estructura del Proyecto

```
secure-vault/
├── docker-compose.yml
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
│       └── default.conf
├── auth-service/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   └── auth.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── dependencies/
│   │   ├── services/
│   │   ├── utils/          # jwt.py, crypto.py, security.py
│   │   └── core/           # config.py, security.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── vault-service/
│   ├── (estructura similar a auth)
│   ├── routers/
│   │   └── secrets.py
│   └── ...
├── frontend/
│   ├── index.html          # login
│   ├── dashboard.html
│   ├── assets/             # css, js, bootstrap
│   └── js/
│       └── main.js         # fetch + manejo JWT
├── .env.example
├── .gitignore
└── README.md
```

## Instalación y Ejecución

1. Clona el repositorio.
2. Copia `.env.example` a `.env` y configura las variables.
3. Ejecuta `docker-compose up --build`.

## Servicios

- **Auth Service**: Maneja registro y login de usuarios.
- **Vault Service**: Almacena y recupera contraseñas encriptadas.
- **Frontend**: Interfaz web para login y gestión de vault.
- **PostgreSQL**: Base de datos.
- **Nginx**: Proxy reverso.

## API Endpoints

### Auth
- POST `/auth/register` - Registrar usuario
- POST `/auth/login` - Login

### Vault
- POST `/vault/secret` - Guardar secreto
- GET `/vault/secret` - Obtener secretos

## Seguridad

- Contraseñas hasheadas con bcrypt.
- JWT para autenticación.
- Encriptación Fernet para secretos.
- Comunicación a través de Nginx.

## Documentación de Entrega

- [Manual de Usuario](docs/01_Manual_Usuario.md)
- [Manual Técnico](docs/02_Manual_Tecnico.md)
- [Manual de Operación y DevOps](docs/03_Manual_Operacion_DevOps.md)
- [Seguridad y Riesgos](docs/04_Seguridad_y_Riesgos.md)
- [Plan de Pruebas](docs/05_Plan_Pruebas.md)
- [Checklist de Entrega](docs/06_Checklist_Entrega.md)