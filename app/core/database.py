from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# DEF-038: con 50 usuarios la API empezaba a encolar peticiones hasta agotar el tiempo de
# espera. El techo de throughput es (pool_size + max_overflow) / duración de cada consulta, y
# con la base en otro continente cada consulta tarda cerca de un segundo. Dos cambios:
#
#   * más conexiones, para que menos peticiones esperen turno;
#   * sin `pool_pre_ping`, que añadía un «SELECT 1» —un viaje completo a la base— antes de
#     entregar CADA conexión. En su lugar se reciclan las conexiones antes de que el servidor
#     las cierre por inactividad, que es para lo que servía el pre-ping.
#
# Todo configurable por entorno (ver app/core/config.py): subir el pool solo ayuda si el plan
# de PostgreSQL admite esas conexiones.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
