"""Smoke checks against the production stack behind the proxy (scripts/smoke.sh).

Runs inside the django image on the smoke network, standard library only.
Extend it whenever a production-only bug is found.
"""

import http.client
import os
import re
import socket
import ssl
import sys
import time

HOST = os.environ["SMOKE_HOST"]
PROXY = os.environ["SMOKE_PROXY"]
VERSION = os.environ["SMOKE_VERSION"]
ADMIN = os.environ["SMOKE_ADMIN"]
CONTEXT = ssl.create_default_context()
CONTEXT.check_hostname = False
CONTEXT.verify_mode = ssl.CERT_NONE  # throwaway proxy, self-signed certificate
failures: list[str] = []


class ProxyConnection(http.client.HTTPSConnection):
    """HTTPS to the proxy container with the public host name as SNI and Host."""

    def connect(self) -> None:
        sock = socket.create_connection((PROXY, 443), timeout=10)
        self.sock = CONTEXT.wrap_socket(sock, server_hostname=HOST)


def get(path: str) -> tuple[int, dict[str, str], str]:
    conn = ProxyConnection(HOST, 443, timeout=10)
    try:
        conn.request("GET", path, headers={"Host": HOST})
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", "replace")
        return resp.status, {k.lower(): v for k, v in resp.getheaders()}, body
    finally:
        conn.close()


def check(name: str, ok: bool, detail: str = "") -> None:
    print(
        f"{'ok  ' if ok else 'FAIL'} {name}{f' ({detail})' if detail and not ok else ''}"
    )
    if not ok:
        failures.append(name)


# The proxy picks up new containers within seconds; wait for the route.
for _ in range(30):
    try:
        if get("/api/v1/health/ready/")[0] == 200:
            break
    except OSError:
        pass
    time.sleep(2)

status, _, body = get("/api/v1/health/ready/")
check("readiness through the proxy", status == 200, f"{status}")
status, _, body = get("/api/v1/health/")
check(
    "health reports the release version", f'"version":"{VERSION}"' in body, body[:200]
)

status, headers, home = get("/")
check("home page renders with DEBUG off", status == 200, f"{status}")
check("HSTS header set", "strict-transport-security" in headers)
assets = sorted(set(re.findall(r'(?:src|href)="(/static/[^"]+)"', home)))
check("home page references static assets", bool(assets))
for asset in assets[:5]:
    status, _, _ = get(asset)
    check(f"static asset served: {asset}", status == 200, f"{status}")

status, _, _ = get("/smoke-page-that-does-not-exist/")
check("unknown page is 404, not 500", status == 404, f"{status}")
status, _, _ = get("/accounts/login/")
check("login page reachable", status < 400, f"{status}")
status, _, _ = get(f"/{ADMIN}")
check("admin redirects to login", status in (301, 302), f"{status}")
# >>> realtime
status, _, _ = get("/v1/events")
check("realtime refuses anonymous streams", 400 <= status < 500, f"{status}")
# <<< realtime

if failures:
    print(f"{len(failures)} smoke check(s) failed", file=sys.stderr)
    sys.exit(1)
