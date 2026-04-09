# Pipeline Demo (Educativo)

Esta guia crea escenarios controlados para demostrar como el pipeline bloquea cambios defectuosos o inseguros.

## Importante

- Usar solo en rama de demostracion (`demo/*`).
- No aplicar en `main`.
- Revertir siempre al finalizar.

## Escenarios incluidos

1. `test-fail`: fuerza fallo de test en `servicios/auth-service/tests/test_security_and_jwt.py`.
2. `sast-fail`: inserta patron inseguro en `servicios/vault-service/app/core/security.py`.
3. `healthcheck-fail`: rompe healthcheck en `servicios/auth-service/Dockerfile`.

## Uso rapido

```bash
# Ver estado
python scripts/pipeline-demo/pipeline_demo.py status

# Aplicar escenario
python scripts/pipeline-demo/pipeline_demo.py apply test-fail

# Revertir escenario
python scripts/pipeline-demo/pipeline_demo.py revert test-fail
```

## Flujo recomendado para sustentacion

1. Crear rama demo:

```bash
git checkout -b demo/pipeline-control
```

2. Aplicar un escenario:

```bash
python scripts/pipeline-demo/pipeline_demo.py apply test-fail
```

3. Commit + push de la rama demo:

```bash
git add -A
git commit -m "demo: trigger pipeline test failure"
git push -u origin demo/pipeline-control
```

4. Abrir PR y mostrar fallo en GitHub Actions.

5. Revertir escenario y volver a ejecutar:

```bash
python scripts/pipeline-demo/pipeline_demo.py revert test-fail
git add -A
git commit -m "demo: revert pipeline test failure"
git push
```

6. Mostrar pipeline en verde y cerrar demo.

## Nota

El script guarda respaldo temporal del contenido original en:

- `scripts/pipeline-demo/.pipeline_demo_state.json`

No editar este archivo manualmente.
