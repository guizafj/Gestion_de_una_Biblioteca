FROM python:3.11-slim

WORKDIR /app

# Instalar PDM
RUN pip install --no-cache-dir pdm

# Copiar solo archivos necesarios para instalar dependencias
COPY pyproject.toml README.md ./

# Instalar dependencias (sin grupo dev)
RUN pdm install --prod --no-self --no-editable

# Copiar el resto de la aplicación
COPY . .

# Instalar la aplicación herself
RUN pdm install --prod --no-editable

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
