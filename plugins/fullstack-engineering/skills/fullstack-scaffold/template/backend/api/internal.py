"""Endpoints for other services in the stack, never for browsers.

They skip user authentication and require the shared X-Internal-Secret instead.
"""

import hmac
from importlib import import_module

from django.conf import settings
from django.contrib.auth import get_user
from django.http import HttpRequest
from rest_framework import serializers
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.users.models import ApiKey
# >>> accounts
from backend.users.policy import mfa_setup_required
# <<< accounts


class HasInternalSecret(BasePermission):
    def has_permission(self, request, view) -> bool:
        expected = settings.INTERNAL_API_SECRET
        provided = request.headers.get("X-Internal-Secret", "")
        # Fail closed and compare in constant time (as bytes: non-ASCII input
        # must be refused, not crash).
        return bool(expected) and hmac.compare_digest(
            provided.encode(), expected.encode()
        )


class InternalView(APIView):
    authentication_classes: list = []
    permission_classes = [HasInternalSecret]


class KeySerializer(serializers.Serializer):
    api_key = serializers.CharField()


class SessionSerializer(serializers.Serializer):
    session_key = serializers.CharField()


def principal(user) -> dict:
    return {"valid": True, "user_id": user.pk, "email": user.email}


INVALID = {"valid": False}


def user_from_session(session_key: str):
    """Resolve a session cookie value exactly as Django would for a request.

    get_user() also checks the session auth hash, so a password change or a
    logout elsewhere invalidates the session for the realtime service too.
    """
    engine = import_module(settings.SESSION_ENGINE)
    request = HttpRequest()
    request.session = engine.SessionStore(session_key)
    user = get_user(request)
    if not (user.is_authenticated and user.is_active):
        return None
    # >>> accounts
    if mfa_setup_required(request, user):
        return None  # same rule as RequireMfaMiddleware for Django's own pages
    # <<< accounts
    return user


class ValidateSessionView(InternalView):
    def post(self, request):
        data = SessionSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        user = user_from_session(data.validated_data["session_key"])
        return Response(principal(user) if user else INVALID)


class ValidateKeyView(InternalView):
    def post(self, request):
        data = KeySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        api_key = ApiKey.resolve(data.validated_data["api_key"])
        return Response(principal(api_key.user) if api_key else INVALID)
