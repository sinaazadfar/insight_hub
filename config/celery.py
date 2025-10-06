import os
import platform
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Prefer the 'solo' pool on Windows to avoid billiard/semaphore errors
if platform.system().lower().startswith("win"):
    app.conf.worker_pool = "solo"
