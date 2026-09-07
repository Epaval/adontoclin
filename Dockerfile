# Etapa 1: Compilar assets con Node
FROM node:20-alpine AS assets

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY tailwind.config.js postcss.config.js ./
COPY static_src ./static_src
COPY templates ./templates
COPY apps ./apps

RUN npm run build:css


# Etapa 2: Imagen final de Python
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copiar CSS compilado desde la etapa assets
COPY --from=assets /app/static/css/app.css /app/static/css/app.css

# Variables de build
RUN DJANGO_SECRET_KEY=build-secret \
    DJANGO_ALLOWED_HOSTS=localhost \
    DATABASE_URL=postgres://build:build@localhost/build \
    REDIS_URL=redis://localhost:6379/1 \
    CELERY_BROKER_URL=redis://localhost:6379/0 \
    python manage.py collectstatic --noinput || true

RUN addgroup --system django && \
    adduser --system --ingroup django django && \
    chown -R django:django /app

USER django

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
