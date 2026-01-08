#!/usr/bin/env bash

echo "[fix-volume-permissions] setting permissions in $(pwd)"
echo "[fix-volume-permissions] code/config: 775 (dags, plugins, celery-workers)"
chmod -R 775 airflow/dags airflow/plugins celery-workers

echo "[fix-volume-permissions] logs/data: 777 (airflow/logs, volumes/*)"
chmod -R 777 airflow/logs volumes

echo "[fix-volume-permissions] done"
