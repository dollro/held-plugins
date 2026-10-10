from django.urls import path

from . import internal, views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("health/ready/", views.ready, name="ready"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("events/test/", views.TestEventView.as_view(), name="events-test"),
    # Internal: called by the realtime service only, guarded by X-Internal-Secret.
    path("internal/validate-session/", internal.ValidateSessionView.as_view()),
    path("internal/validate-key/", internal.ValidateKeyView.as_view()),
]
