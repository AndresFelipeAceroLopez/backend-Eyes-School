from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Eyes School API",
        version="0.1.0",
        description="Backend API para el sistema de gestión escolar Eyes School",
        lifespan=lifespan,
    )

    origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        # Con "*" Starlette refleja cualquier origen si hay credenciales, lo que
        # abre la API a cualquier sitio. Las credenciales solo con lista explícita.
        allow_credentials=origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    import os
    os.makedirs("static/avatars", exist_ok=True)
    os.makedirs("static/reportes", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    return app


app = create_app()
