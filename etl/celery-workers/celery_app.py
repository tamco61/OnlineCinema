from celery import Celery

app = Celery("etl_tasks")
app.config_from_object("celeryconfig")
