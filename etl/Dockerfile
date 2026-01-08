FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AIRFLOW_HOME=/app/airflow \
    AIRFLOW__CORE__DAGS_FOLDER=/app/airflow/dags \
    AIRFLOW__CORE__PLUGINS_FOLDER=/app/airflow/plugins \
    AIRFLOW__LOGGING__BASE_LOG_FOLDER=/app/airflow/logs \
    AIRFLOW__CORE__EXECUTOR=CeleryExecutor

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY airflow/ /app/airflow/
COPY celery-workers/ /app/celery-workers/

RUN mkdir -p /app/airflow/logs /app/airflow/plugins /tmp/videos /tmp/thumbnails

ENV PYTHONPATH=/app/celery-workers:$PYTHONPATH

EXPOSE 8080 5555

CMD ["airflow", "webserver"]
