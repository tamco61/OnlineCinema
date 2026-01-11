import os

from kombu import Queue

broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/Moscow'
enable_utc = True

task_routes = {
    'tasks.transcoding.transcode_video': {'queue': 'transcoding'},
    'tasks.thumbnails.generate_thumbnails': {'queue': 'thumbnails'},
}

task_queues = (
    Queue('transcoding', routing_key='transcoding'),
    Queue('thumbnails', routing_key='thumbnails'),
    Queue('default', routing_key='default'),
)

task_acks_late = True
worker_prefetch_multiplier = 1
task_time_limit = 3600
task_soft_time_limit = 3300

result_expires = 86400

worker_max_tasks_per_child = 10
worker_disable_rate_limits = True

worker_hijack_root_logger = False
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

imports = (
    'tasks.transcoding',
    'tasks.thumbnails',
)
