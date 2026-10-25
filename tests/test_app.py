"""La app arranca completa: todas las rutas montadas y los modelos relacionados."""

from sqlalchemy.orm import configure_mappers

from app.infrastructure.models.base import Base
from main import app


def test_la_api_expone_todas_sus_rutas():
    operaciones = sum(len(methods) for methods in app.openapi()["paths"].values())

    assert operaciones >= 100


def test_los_modelos_y_sus_relaciones_se_configuran():
    # Falla si un modelo referenciado en una relación dejó de importarse.
    configure_mappers()

    assert len(Base.registry.mappers) >= 20
