FROM python:3.12-slim

# No generar .pyc y salida sin buffer para ver logs en tiempo real.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

# Varios workers para poder saturar los 2 núcleos asignados.
# --threads permite que las peticiones de CPU usen hilos dentro de cada worker.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--workers", "2", "--threads", "4", \
     "--timeout", "600", "app:app"]
