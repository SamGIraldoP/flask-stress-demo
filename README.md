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

> Nota: el contenedor expone el puerto **8080** del host (`8080:5000`). Si usas `stress.sh`
> apuntando a otro host/puerto, pásalo con `BASE_URL`, por ejemplo:
> `BASE_URL=http://localhost:8080 ./stress.sh ram`

### Qué esperar

- **CPU**: con `burn-cpu` verás el contenedor fijado en ~200% (sus 2 núcleos al 100%).
  Como está limitado a 2 CPUs, no podrá pasar de ahí aunque lances más hilos.
- **RAM**: con `eat-ram` en bucle, al superar los 256 MiB el **OOM killer** del kernel
  mata un proceso dentro del contenedor.

## Dos modos: resiliente vs. frágil

Importa qué proceso mata el OOM killer:

- **Modo `gunicorn` (por defecto)** — hay un proceso *master* y 2 *workers*. Al saturar
  la RAM, el kernel mata un **worker**; el master lo relanza y el **contenedor sigue vivo**.
  Lo verás como `OOMKilled=true` pero el contenedor en estado `Up` y `ExitCode=0`.
  Es el comportamiento de un servicio resiliente que se degrada pero no cae del todo.

- **Modo `single` (frágil)** — un **único proceso** (PID 1). Al saturar la RAM, el OOM
  killer mata ese proceso y **el contenedor entero cae** con **exit code 137**.

El modo se elige con la variable de entorno `SERVER_MODE` (ver `entrypoint.sh`).

### Tumbar el contenedor ENTERO (exit 137)

```bash
# Levanta la variante frágil (puerto 8081, un solo proceso):
docker compose --profile fragil up --build flask-api-fragil

# En otra terminal, satura su RAM:
BASE_URL=http://localhost:8081 ./stress.sh ram

# Comprueba que el contenedor cayó por OOM:
docker inspect flask-stress-demo-fragil --format '{{.State.OOMKilled}} exit={{.State.ExitCode}}'
# Esperado: true exit=137
```

### Verificar un OOM kill (cualquier modo)

```bash
docker inspect <nombre-contenedor> --format '{{.State.OOMKilled}} exit={{.State.ExitCode}}'
```

- `OOMKilled=true` confirma que el kernel mató un proceso por falta de memoria.
- `ExitCode=137` (= 128 + SIGKILL 9) significa que **el contenedor** cayó por ello.
  En modo gunicorn verás `OOMKilled=true` con `ExitCode=0` porque solo cayó un worker.

## Nota

El objetivo es validar los límites de recursos y el comportamiento del contenedor bajo carga.
Úsalo únicamente contra contenedores propios / en tu entorno de pruebas.
