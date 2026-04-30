# Manual de Arquitectura

## Vision general
SecureVault Pro implementa una arquitectura de microservicios para gestionar secretos con cifrado de datos en reposo y autenticacion basada en JWT.

## Casos de uso (Mermaid)
```mermaid
flowchart LR
  U[Usuario] --> R[Registrarse]
  U --> L[Iniciar sesion]
  U --> C[Crear secreto]
  U --> V[Ver secretos]
  U --> D[Eliminar secreto]

  R --> A[Auth Service]
  L --> A
  C --> VS[Vault Service]
  V --> VS
  D --> VS
  WS[Worker Service] --> VS
```

## Diagrama de componentes (Mermaid)
```mermaid
flowchart TD
  FE[Frontend React SPA] -->|REST| AS[Auth Service]
  FE -->|REST + JWT| VS[Vault Service]
  AS --> PG[(PostgreSQL)]
  VS --> PG
  WS[Worker Service] --> PG
  AS --> RD[(Redis)]
  VS --> RD
  WS --> RD
```

## DFD Nivel 0 (Mermaid)
```mermaid
flowchart LR
  User((Usuario)) --> App[SecureVault Pro]
  App --> DB[(PostgreSQL)]
  App --> Cache[(Redis)]
```

## DFD Nivel 1 (Mermaid)
```mermaid
flowchart LR
  User((Usuario)) --> FE[Frontend SPA]
  FE --> AuthP[Proceso Auth]
  FE --> VaultP[Proceso Vault]
  VaultP --> Crypto[Cifrado AES-256-GCM]
  AuthP --> Users[(Tabla users)]
  VaultP --> Secrets[(Tabla secrets)]
  WorkerP[Proceso Worker] --> Secrets
```
