FROM python:3.11-slim

# Evita que Python genere archivos .pyc innecesarios
ENV PYTHONDONTWRITEBYTECODE 1
# Permite ver logs en tiempo real en la terminal
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalamos dependencias del sistema para PostgreSQL y compilación
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero los requerimientos para optimizar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código fuente
COPY . .

# Comando por defecto para iniciar el pipeline ETL
CMD ["python", "src/main.py"]
