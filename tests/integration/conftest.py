"""Infraestructura de las pruebas de integración contra PostgreSQL real (BE-INF-1).

Se activan con una base DESECHABLE indicada en `TEST_DATABASE_URL` (nunca la de producción:
el DATABASE_URL del .env se ignora). Sin esa variable, las pruebas se omiten.

    docker run -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=eyes_test postgres:18
    TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/eyes_test \
        pytest -m integration

Esquema: se crea desde los modelos SQLAlchemy (`Base.metadata.create_all`) y no desde
`schema.sql`, porque ese archivo es un dump de Supabase (roles, extensiones y políticas RLS)
que no carga en un PostgreSQL limpio y además no incluye las tablas nuevas.
Datos: `seed_data.sql` + `seed_estudiantes_sinteticos.sql`. Cada prueba corre dentro de una
transacción que se revierte al terminar.
"""

import asyncio
import os
import re
from pathlib import Path

import asyncpg
import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import get_db
from app.core.security import hash_password
from main import app

RAIZ = Path(__file__).resolve().parents[2]
URL = os.environ.get("TEST_DATABASE_URL", "")
PASSWORD = "Colegio#2026"

# Usuarios del seed_data.sql
ADMIN = "admin@eyesschool.edu.co"  # id 1
DOCENTE = "carlos.jimenez@eyes.edu.co"  # id 2 · profesor 1: curso 1 y 2, materia 1
DOCENTE_AJENO = "lucia.soto@eyes.edu.co"  # id 9 · profesor 3: no dicta materia 1 en curso 1
ESTUDIANTE = "sofia.rodriguez@student.eyes.co"  # id 3 · estudiante 1, curso 1
PADRE_DOS_HIJOS = "rosa.perez@gmail.com"  # id 4 · estudiantes 1 y 3
PADRE_UN_HIJO = "roberto.diaz@gmail.com"  # id 8 · estudiante 2


def pytest_collection_modifyitems(config, items):
    if URL:
        return
    omitir = pytest.mark.skip(reason="Defina TEST_DATABASE_URL para correr las de integración")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(omitir)


def _dsn() -> str:
    return URL.replace("postgresql+asyncpg://", "postgresql://")


async def _preparar_base() -> None:
    from app.infrastructure.models.base import Base

    conn = await asyncpg.connect(_dsn())
    try:
        await conn.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
    finally:
        await conn.close()

    engine = create_async_engine(URL, poolclass=NullPool)
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    await engine.dispose()

    conn = await asyncpg.connect(_dsn())
    try:
        for archivo in ("seed_data.sql", "seed_estudiantes_sinteticos.sql"):
            sql = (RAIZ / archivo).read_text(encoding="utf-8-sig")
            # psql-only: los meta-comandos con barra invertida no los entiende el servidor.
            sql = re.sub(r"^\\.*$", "", sql, flags=re.MULTILINE)
            await conn.execute(sql)
        # Las contraseñas del seed no se conocen: se fija una de pruebas.
        await conn.execute("UPDATE public.usuario SET password = $1", hash_password(PASSWORD))
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
def base_de_datos():
    if not URL:
        yield
        return
    asyncio.run(_preparar_base())
    yield


@pytest.fixture
async def db():
    """Sesión ligada a una transacción que se revierte; los `commit()` del código son savepoints."""
    engine = create_async_engine(URL, poolclass=NullPool)
    conn = await engine.connect()
    transaccion = await conn.begin()
    session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)

    async def _get_db():
        yield session

    app.dependency_overrides[get_db] = _get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        await session.close()
        await transaccion.rollback()
        await conn.close()
        await engine.dispose()


@pytest.fixture
async def api(db):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as cliente:
        yield cliente


async def iniciar_sesion(api, correo: str, password: str = PASSWORD) -> dict:
    respuesta = await api.post("/api/v1/auth/login", json={"correo": correo, "password": password})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


async def encabezado(api, correo: str) -> dict[str, str]:
    tokens = await iniciar_sesion(api, correo)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
