"""
API Flask de demostración para pruebas de saturación de recursos.

Expone endpoints normales y endpoints diseñados para consumir CPU y RAM,
de modo que se pueda observar cómo el contenedor llega a sus límites
(2 núcleos y memoria acotada definidos en docker-compose.yml).

USO PREVISTO: stress testing sobre TU PROPIO contenedor para comprobar
los límites de recursos y el comportamiento del OOM killer.
"""
import math
import os
import threading
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

# Almacén en memoria para el endpoint de saturación de RAM.
# Mantener referencias globales evita que el recolector de basura libere la memoria.
_memory_hog: list[bytearray] = []
_memory_lock = threading.Lock()


@app.get("/")
def index():
    """Endpoint de salud / información básica."""
    return jsonify(
        {
            "service": "flask-stress-demo",
            "status": "ok",
            "cpu_count": os.cpu_count(),
            "pid": os.getpid(),
            "endpoints": {
                "GET /": "info del servicio",
                "GET /health": "healthcheck",
                "GET /burn-cpu?seconds=N&workers=M": "satura CPU durante N seg con M hilos",
                "POST /eat-ram": "reserva memoria (body JSON: {\"mb\": 128})",
                "POST /free-ram": "libera la memoria reservada",
                "GET /stats": "memoria reservada actualmente",
            },
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "healthy", "memory_blocks": len(_memory_hog)})


def _cpu_worker(deadline: float) -> None:
    """Bucle de cómputo puro para mantener un núcleo ocupado hasta 'deadline'."""
    x = 0.0
    while time.time() < deadline:
        # Operaciones matemáticas que no se optimizan a nada trivial.
        for i in range(10000):
            x += math.sqrt(i * 2.7) * math.sin(i)


@app.get("/burn-cpu")
def burn_cpu():
    """
    Satura la CPU lanzando varios hilos de cómputo.

    Parámetros de query:
      seconds: duración de la carga (por defecto 10, máx 300)
      workers: número de hilos (por defecto = nº de núcleos)
    """
    seconds = min(int(request.args.get("seconds", 10)), 300)
    workers = int(request.args.get("workers", os.cpu_count() or 2))

    deadline = time.time() + seconds
    threads = [threading.Thread(target=_cpu_worker, args=(deadline,)) for _ in range(workers)]

    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return jsonify(
        {
            "burned_seconds": round(time.time() - start, 2),
            "workers": workers,
            "cpu_count": os.cpu_count(),
        }
    )


@app.post("/eat-ram")
def eat_ram():
    """
    Reserva memoria de forma persistente para empujar al contenedor
    contra su límite de RAM (y provocar el OOM killer si se excede).

    Body JSON: {"mb": 128}  -> reserva 128 MiB adicionales.
    """
    data = request.get_json(silent=True) or {}
    mb = int(data.get("mb", 64))

    # Reservamos y "tocamos" cada página para forzar su residencia en RAM.
    block = bytearray(mb * 1024 * 1024)
    for i in range(0, len(block), 4096):
        block[i] = 1

    with _memory_lock:
        _memory_hog.append(block)
        total_mb = sum(len(b) for b in _memory_hog) // (1024 * 1024)

    return jsonify({"added_mb": mb, "total_reserved_mb": total_mb})


@app.post("/free-ram")
def free_ram():
    """Libera toda la memoria reservada."""
    with _memory_lock:
        freed = len(_memory_hog)
        _memory_hog.clear()
    return jsonify({"freed_blocks": freed})


@app.get("/stats")
def stats():
    with _memory_lock:
        total_mb = sum(len(b) for b in _memory_hog) // (1024 * 1024)
        blocks = len(_memory_hog)
    return jsonify({"reserved_blocks": blocks, "reserved_mb": total_mb})


if __name__ == "__main__":
    # Para desarrollo local. En el contenedor se usa gunicorn (ver Dockerfile).
    app.run(host="0.0.0.0", port=5000)
