#!/usr/bin/env bash
#
# Script para tumbar el contenedor saturando sus recursos.
# Lánzalo contra tu propio contenedor (flask-stress-demo) en localhost:5000.
#
# Uso:
#   ./stress.sh cpu          -> satura los 2 núcleos
#   ./stress.sh ram          -> reserva RAM en bucle hasta provocar el OOM killer
#   ./stress.sh all          -> ambas cosas a la vez
#
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:5000}"

burn_cpu() {
  echo ">> Saturando CPU (4 hilos x 60s, en paralelo)..."
  for _ in 1 2 3 4; do
    curl -s "${BASE_URL}/burn-cpu?seconds=60&workers=4" >/dev/null &
  done
}

eat_ram() {
  echo ">> Reservando RAM en bloques de 64 MiB hasta que el contenedor caiga..."
  while true; do
    resp=$(curl -s -X POST "${BASE_URL}/eat-ram" \
      -H 'Content-Type: application/json' \
      -d '{"mb": 64}') || { echo ">> El contenedor dejo de responder (probable OOM kill)."; break; }
    echo "   $resp"
    sleep 0.3
  done
}

case "${1:-all}" in
  cpu) burn_cpu; wait ;;
  ram) eat_ram ;;
  all) burn_cpu; eat_ram ;;
  *) echo "Uso: $0 [cpu|ram|all]"; exit 1 ;;
esac
