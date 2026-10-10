import logging

from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.db import connection, transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import send_test_event

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response(
        {
            "status": "ok",
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENVIRONMENT,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ready(request):
    """Readiness: database and cache reachable. Liveness is /health/."""
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = True
    except Exception:
        logger.exception("readiness: database check failed")
        checks["database"] = False
    try:
        cache.set("readiness-probe", "1", timeout=5)
        checks["cache"] = cache.get("readiness-probe") == "1"
    except Exception:
        logger.exception("readiness: cache check failed")
        checks["cache"] = False
    ok = all(checks.values())
    return Response({"ready": ok, "checks": checks}, status=200 if ok else 503)


def user_payload(user) -> dict:
    return {"id": user.pk, "email": user.email, "username": user.username}


class LogoutView(APIView):
    """Logout for the SPA. Login itself runs through allauth's pages (/accounts/)."""

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(user_payload(request.user))


class TestEventView(APIView):
    """Demo of the async path: Django -> Celery -> Redis pub/sub -> realtime -> browser."""

    def post(self, request):
        # Enqueue after commit: the worker must never see data the request rolls back.
        user_id = request.user.pk
        transaction.on_commit(lambda: send_test_event.delay(user_id))
        return Response(status=status.HTTP_202_ACCEPTED)
