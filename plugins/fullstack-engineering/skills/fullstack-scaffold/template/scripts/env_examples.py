#!/usr/bin/env python3
"""Regenerate .envs/*/app.env.example from the decrypted app.env files.

Values of keys that look like external credentials are blanked; everything else
(local infra defaults) is kept so the stack boots from the example alone.

  python scripts/env_examples.py          write examples
  python scripts/env_examples.py --check  exit 1 if an example is out of date
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Local: blank credential-shaped keys unless listed in KEEP (local infra values
# stay, so the stack boots from the example alone). Extend MASK for new shapes.
MASK = re.compile(
    r"(KEY|TOKEN|PASS|PASSWORD|PWD|SECRET|CREDENTIAL|CREDENTIALS|_URL|_DSN|ADMIN_URL)$"
    r"|CREDENTIAL|SECRET"
)
KEEP_LOCAL = {
    "DJANGO_SECRET_KEY",
    "DJANGO_SUPERUSER_PASSWORD",
    "POSTGRES_PASSWORD",
    "FLOWER_PASSWORD",
    "INTERNAL_API_SECRET",
    "DATABASE_URL",
    "EMAIL_URL",
    "REDIS_URL",
    "DJANGO_INTERNAL_URL",
}
# Deployed environments: default deny. Only these known non-secret keys keep their
# value in the committed example; everything else is blanked.
PUBLIC = {
    "APP_ENVIRONMENT",
    "DJANGO_SETTINGS_MODULE",
    "DJANGO_ALLOWED_HOSTS",
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "SESSION_COOKIE_NAME",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "LOCAL_LOGIN_ENABLED",
    "SIGNUP_OPEN",
    "MFA_REQUIRED",
    "TIME_ZONE",
    "SSO_ISSUER_URL",
    "SSO_CLIENT_ID",
    "SSO_PROVIDER_ID",
    "SSO_DISPLAY_NAME",
    "SSO_AUTO_PROVISION",
    "SSO_VERIFIED_EMAIL_DOMAINS",
    "DEFAULT_FROM_EMAIL",
}
LINE = re.compile(r"^(?P<key>[A-Z0-9_]+)=(?P<value>.*)$")


def blank(env_name: str, key: str) -> bool:
    if env_name == "local":
        return bool(MASK.search(key)) and key not in KEEP_LOCAL
    return key not in PUBLIC


def render(env_name: str, source: str) -> str:
    out = []
    for line in source.splitlines():
        match = LINE.match(line)
        if match and blank(env_name, match["key"]):
            line = f"{match['key']}="
        out.append(line)
    return "\n".join(out) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for source in sorted(ROOT.glob(".envs/*/app.env")):
        env_name = source.parent.name
        example = source.with_name("app.env.example")
        expected = render(env_name, source.read_text())
        if example.exists() and example.read_text() == expected:
            continue
        if check:
            stale.append(str(example.relative_to(ROOT)))
        else:
            example.write_text(expected)
            print(f"wrote {example.relative_to(ROOT)}")
    if stale:
        print("Out of date, run `task secrets:examples`:", *stale, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
