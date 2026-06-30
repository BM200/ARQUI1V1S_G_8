# Proyecto 1 ARQUITECTURA DE COMPUTADORAS Y ENSAMBLADORES 1

## Dashboard Render/Raspberry

El dashboard Flask de la Raspberry usa el puerto `5000`.

En Render, configura:

```env
RASPBERRY_URL=http://IP_PUBLICA_O_TUNEL_RASP:5000
BRIDGE_SECRET=un-secreto-largo-compartido
```

En la Raspberry, configura el mismo `BRIDGE_SECRET`. Ese secreto solo se valida
en estas rutas ARM64:

- `/api/arm64/fase1/run`
- `/api/arm64/fase2/run`
- `/api/arm64/historical/run`

Las rutas del dashboard en tiempo real (`/api/estado`, `/api/lecturas`,
`/api/comando` y `/api/modo`) no se reenvian por el puente ARM64.
