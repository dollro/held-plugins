"""Alembic for the realtime service. It shares the database with Django, so it
must only ever see its own tables."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from realtime.config import get_settings
from realtime.db import Base

config = context.config
# ConfigParser treats % as interpolation; URL-encoded passwords contain it.
config.set_main_option(
    "sqlalchemy.url", get_settings().async_database_url.replace("%", "%%")
)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the modules that define this service's tables here, so they register
# on Base.metadata before autogenerate runs, e.g.: from realtime import models
target_metadata = Base.metadata
# Own version table, so it never collides with another Alembic user of the database.
VERSION_TABLE = "alembic_version_realtime"


def include_object(obj, name, type_, reflected, compare_to):
    # Tables that exist in the database but not in our metadata belong to Django:
    # never propose to drop or alter them.
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def configure(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        version_table=VERSION_TABLE,
        include_object=include_object,
        compare_type=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    configure(url=config.get_main_option("sqlalchemy.url"), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
