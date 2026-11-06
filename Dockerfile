FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/media /app/staticfiles && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --run-syncdb --noinput && python manage.py collectstatic --noinput && gunicorn library_project.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 90"]
