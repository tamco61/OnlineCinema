import logging
from celery_app import app

logger = logging.getLogger(__name__)
logger.info("Celery worker initialized")
logger.info("Broker: %s", app.conf.broker_url)
logger.info("Backend: %s", app.conf.result_backend)
