FROM python:3.12-slim

# No generar .pyc y salida sin buffer para ver logs en tiempo real.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 5000

# El modo lo decide la variable de entorno SERVER_MODE (ver entrypoint.sh):
#   gunicorn (por defecto) -> contenedor resiliente (muere el worker, no el contenedor)
#   single                 -> contenedor fragil   (muere el unico proceso = cae el contenedor, exit 137)
CMD ["./entrypoint.sh"]
