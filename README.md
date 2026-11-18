# Flask Stress Demo

Contenedor Python con una API Flask y **recursos limitados a 2 núcleos y 256 MiB de RAM**,
pensado para pruebas de saturación (stress testing) sobre tu propio contenedor.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `app.py` | API Flask con endpoints normales y de saturación de CPU/RAM. |
| `Dockerfile` | Imagen basada en `python:3.12-slim`, servida con gunicorn. |
| `docker-compose.yml` | Define los límites: `cpus: 2.0`, `mem_limit: 256m`. |
| `stress.sh` | Script de carga para tumbar el contenedor. |
| `requirements.txt` | Dependencias (Flask, gunicorn). |

## Arrancar

```bash
docker compose up --build
```

La API queda en `http://localhost:5000`.

## Endpoints

| Método | Ruta | Qué hace |
|--------|------|----------|
| GET | `/` | Info del servicio y lista de endpoints. |
| GET | `/health` | Healthcheck. |
| GET | `/burn-cpu?seconds=N&workers=M` | Satura CPU durante N segundos con M hilos. |
| POST | `/eat-ram` (body `{"mb": 128}`) | Reserva memoria de forma persistente. |
| POST | `/free-ram` | Libera la memoria reservada. |
| GET | `/stats` | Memoria reservada actualmente. |

## Tumbarlo

En otra terminal, con el contenedor en marcha:

```bash
chmod +x stress.sh

# Saturar los 2 núcleos (verás ~200% de CPU en 'docker stats'):
./stress.sh cpu

# Agotar la RAM hasta que el OOM killer mate el proceso:
./stress.sh ram

# Ambas a la vez:
./stress.sh all
```

Para observar el impacto en tiempo real, en otra terminal:

```bash
docker stats flask-stress-demo
```

### Qué esperar

- **CPU**: con `burn-cpu` verás el contenedor fijado en ~200% (sus 2 núcleos al 100%).
  Como está limitado a 2 CPUs, no podrá pasar de ahí aunque lances más hilos.
- **RAM**: con `eat-ram` en bucle, al superar los 256 MiB el **OOM killer** del kernel
  matará el worker de gunicorn (verás `Worker ... was sent SIGKILL! Perhaps out of memory?`
  o el contenedor saldrá con código 137). Ese es el "tumbado" por saturación de recursos.

## Nota

El objetivo es validar los límites de recursos y el comportamiento del contenedor bajo carga.
Úsalo únicamente contra contenedores propios / en tu entorno de pruebas.
