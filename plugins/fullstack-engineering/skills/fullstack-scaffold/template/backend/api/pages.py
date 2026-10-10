"""Server-rendered pages. Vue mounts into them; they set the CSRF cookie for fetch()."""

# >>> accounts
from django.conf import settings
# <<< accounts
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def home(request):
    # >>> accounts
    return render(request, "home.html", {"signup_open": settings.SIGNUP_OPEN})
    # <<< accounts
    # >>> !accounts
    return render(request, "home.html")
    # <<< !accounts


@ensure_csrf_cookie
def spa(request):
    return render(request, "app.html")


def not_found(request):
    raise Http404
