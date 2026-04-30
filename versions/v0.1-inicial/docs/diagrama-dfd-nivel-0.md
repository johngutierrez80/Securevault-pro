# DFD Nivel 0

```mermaid
flowchart LR
  User((Usuario)) --> System[SecureVault Pro]
  System --> DB[(PostgreSQL)]
  System --> Cache[(Redis)]
```
