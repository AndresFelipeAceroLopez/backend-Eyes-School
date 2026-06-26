from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.infrastructure.models.base import Base


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
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
