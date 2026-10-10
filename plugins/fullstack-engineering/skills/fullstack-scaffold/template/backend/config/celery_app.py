import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings.local")

app = Celery("__PROJECT_SNAKE__")
# All Celery settings live in Django settings with the CELERY_ prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
