from celery import shared_task
from django.utils import timezone

from .events import publish_user_event


@shared_task
def send_test_event(user_id: int) -> None:
    publish_user_event(
        user_id,
        "test",
        {"message": "Hello from Celery", "at": timezone.now().isoformat()},
    )
