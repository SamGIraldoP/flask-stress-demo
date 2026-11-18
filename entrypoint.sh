#!/usr/bin/env sh
# Selector de modo de ejecución mediante la variable SERVER_MODE.
#
#   SERVER_MODE=gunicorn  (por defecto)
#       Servidor de producción con 2 workers. El contenedor es RESILIENTE:
#       cuando un worker muere por OOM, el master lo relanza y el contenedor
#       sigue vivo (OOMKilled=true pero el contenedor no cae).
#
#   SERVER_MODE=single
#       Un unico proceso (servidor de desarrollo de Flask). El contenedor es
#       FRAGIL: al superar el limite de RAM, el OOM killer mata ese unico
#       proceso = PID 1, y el CONTENEDOR ENTERO cae con exit code 137.
#
set -e

MODE="${SERVER_MODE:-gunicorn}"

if [ "$MODE" = "single" ]; then
    echo "[entrypoint] Modo SINGLE: un unico proceso. El contenedor caera (exit 137) al saturar la RAM."
    exec python app.py
else
    echo "[entrypoint] Modo GUNICORN: 2 workers. El contenedor es resiliente a la muerte de workers."
    exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 --timeout 600 app:app
fi
