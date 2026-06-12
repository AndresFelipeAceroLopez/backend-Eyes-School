import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.config import settings
from app.infrastructure.models.base import Base
import app.infrastructure.models.usuario  # noqa: F401
import app.infrastructure.models.actores  # noqa: F401
import app.infrastructure.models.academico  # noqa: F401
import app.infrastructure.models.asistencia  # noqa: F401
import app.infrastructure.models.notas  # noqa: F401
import app.infrastructure.models.novedades  # noqa: F401
import app.infrastructure.models.reportes  # noqa: F401

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

INCLUDE_SCHEMAS = {"public"}


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in INCLUDE_SCHEMAS
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="public",
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema="public",
        include_name=include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
