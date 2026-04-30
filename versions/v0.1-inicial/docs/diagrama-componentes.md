# Diagrama de Componentes

```mermaid
flowchart TD
  FE[Frontend SPA] --> AS[Auth Service]
  FE --> VS[Vault Service]
  AS --> PG[(PostgreSQL)]
  VS --> PG
  WS[Worker Service] --> PG
  AS --> RD[(Redis)]
  VS --> RD
```
