# Load the Celery app when Django starts so that @shared_task uses it.
from .celery_app import app as celery_app

__all__ = ("celery_app",)
