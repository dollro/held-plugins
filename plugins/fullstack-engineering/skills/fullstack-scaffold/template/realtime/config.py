from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Realtime service settings. Same env file as Django; unknown keys are ignored."""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_version: str = Field(default="development", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="REALTIME_DEBUG")
    log_level: str = Field(default="INFO", alias="REALTIME_LOGLEVEL")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    django_internal_url: str = Field(
        default="http://django:5000", alias="DJANGO_INTERNAL_URL"
    )
    internal_api_secret: str = Field(alias="INTERNAL_API_SECRET")
    django_timeout_s: float = Field(default=5.0, alias="DJANGO_INTERNAL_TIMEOUT_S")

    # Browser auth: the Django session cookie (same env var as Django).
    session_cookie_name: str = Field(default="sessionid", alias="SESSION_COOKIE_NAME")
    # Cross-origin browser callers that may use the session cookie. Same-origin
    # requests (the normal case behind the reverse proxy) need no entry.
    # Comma-separated, like Django's list settings.
    allowed_origins_csv: str = Field(default="", alias="REALTIME_ALLOWED_ORIGINS")
    sse_keepalive_s: float = Field(default=15.0, alias="SSE_KEEPALIVE_S")

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins_csv.split(",") if o.strip()]

    @property
    def async_database_url(self) -> str:
        """Django-style postgres:// URL rewritten for SQLAlchemy's async psycopg driver.

        One driver (psycopg 3) for Django, this service and LangGraph's Postgres checkpointer.
        """
        url = self.database_url
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
