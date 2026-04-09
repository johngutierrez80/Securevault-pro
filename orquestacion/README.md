# Orquestacion

Este directorio contiene artefactos de orquestacion para despliegue fuera de Docker Compose.

## Kubernetes / K3s

Aplicar namespace y stack base:

```bash
kubectl apply -f orquestacion/kubernetes/namespace.yaml
kubectl apply -f orquestacion/kubernetes/securevault-stack.yaml
```

Verificar recursos:

```bash
kubectl get all -n securevault
```

Acceso al gateway (NodePort):

- http://<ip-del-nodo>:30080
