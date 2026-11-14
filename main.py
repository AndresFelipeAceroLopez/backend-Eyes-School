import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import DBAPIError

from app.api.v1.contrato import instalar_contrato, metodos_permitidos
from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger(__name__)
logger_seguridad = logging.getLogger("eyes.seguridad")

# Respuestas que se registran como evento de seguridad (A09): sesión rechazada, sin permiso,
# recurso inexistente (sondeo de ids) y bloqueo por intentos.
ESTADOS_DE_SEGURIDAD = {401, 403, 404, 429}


def _configurar_logs() -> None:
    """A09 (BC-10): que los avisos de la app lleguen al Log stream de Azure, con fecha y hora.

    uvicorn configura solo sus propios loggers. Los de la app (`app.*`, `eyes.*`) propagan a la
    raíz, que no tenía handler: lo de nivel INFO se perdía y lo demás salía sin hora.
    """
    raiz = logging.getLogger()
    if not raiz.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )


def _es_dato_invalido(error: DBAPIError) -> bool:
    """¿El error viene de un VALOR que el cliente mandó, y no de un fallo de la base?

    asyncpg lanza `DataError` cuando el valor no cabe en la columna: por ejemplo un id mayor que
    el rango de `bigint`. Eso es culpa de la petición, no del servidor, y debe responder 422.
    Cualquier otro `DBAPIError` (conexión caída, tiempo agotado, permisos) sí es un fallo del
    servidor y se deja pasar para que responda 500: convertirlo en 422 escondería una caída real.
    """
    try:
        from asyncpg.exceptions import DataError
    except ImportError:  # pragma: no cover - solo si se cambia de controlador
        return False
    return isinstance(getattr(getattr(error, "orig", None), "__cause__", None), DataError)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    _configurar_logs()
    app = FastAPI(
        title="Eyes School API",
        version="0.1.0",
        description="Backend API para el sistema de gestión escolar Eyes School",
        lifespan=lifespan,
    )

    origins = settings.origenes_cors
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        # Con "*" Starlette refleja cualquier origen si hay credenciales, lo que
        # abre la API a cualquier sitio. Las credenciales solo con lista explícita.
        allow_credentials=origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DBAPIError)
    async def error_de_dato(request: Request, exc: DBAPIError):
        """DEF-039: un id fuera del rango de PostgreSQL devolvía 500 en todos los endpoints.

        FastAPI valida que el parámetro sea un entero, pero no su magnitud, así que el valor
        llegaba a la consulta y la base lo rechazaba sin que nadie capturara el error.

        - Si el valor viene de la RUTA (`/cursos/9223372036854775808`), responde **404**: un id
          que no cabe en la columna no puede existir. Hasta el 13/11/2026 respondía 422, y
          schemathesis lo marcó (ST202): para el contrato ese id es un entero válido.
        - Si viene del cuerpo o de la query, responde **422** con la misma forma que los demás
          errores de validación (`detail` es una lista), que es lo que declara el contrato (ST108).
        """
        if not _es_dato_invalido(exc):
            raise exc
        logger.info("Valor fuera de rango en %s %s", request.method, request.url.path)
        if request.path_params:
            return JSONResponse(status_code=404, content={"detail": "Recurso no encontrado"})
        return JSONResponse(
            status_code=422,
            content={"detail": [{
                "type": "value_error", "loc": ["body"], "msg": "Valor fuera del rango permitido.",
                "input": None,
            }]},
        )

    @app.middleware("http")
    async def cabeceras_de_seguridad(request: Request, call_next):
        """CP-NF-003: las dos cabeceras que marcó OWASP ZAP en el escaneo del 10/11/2026.

        - `X-Content-Type-Options: nosniff` importa más de lo que parece en esta API: los
          avatares se sirven públicos desde `/static/avatars` (BE-14). Sin esta cabecera, un
          navegador puede ignorar el `Content-Type` y ejecutar como HTML un archivo subido por
          un usuario. La validación de BE-14 ya impide subir algo que no sea imagen; esto es la
          segunda barrera.
        - `Strict-Transport-Security` obliga al navegador a usar HTTPS en las siguientes
          visitas, así que un enlace `http://` no llega a salir en claro con el token dentro.
          Solo se envía sobre HTTPS, como manda la especificación: en local no estorba.
        """
        respuesta = await call_next(request)
        if respuesta.status_code in ESTADOS_DE_SEGURIDAD:
            # Solo método, ruta y estado. Ni la query string, ni las cabeceras, ni el cuerpo:
            # ahí viajan el token y la contraseña.
            origen = request.headers.get("x-forwarded-for") or (
                request.client.host if request.client else "-"
            )
            logger_seguridad.warning(
                "%s %s -> %s desde %s",
                request.method, request.url.path, respuesta.status_code, origen.split(",")[0],
            )
        if respuesta.status_code == 405:
            # BC-07 / ST205: Starlette pone en `Allow` solo los métodos de la primera ruta que
            # coincide; si GET y DELETE de la misma URL son rutas distintas, faltaba uno.
            permitidos = metodos_permitidos(app, request.url.path)
            if permitidos:
                respuesta.headers["Allow"] = ", ".join(permitidos)
        respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
        if request.url.scheme == "https":
            respuesta.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return respuesta

    app.include_router(api_router, prefix="/api/v1")
    instalar_contrato(app)

    import os
    os.makedirs("static/avatars", exist_ok=True)
    os.makedirs("static/reportes", exist_ok=True)
    # Solo los avatares son públicos. Los reportes se descargan únicamente por
    # GET /reportes/{id}/archivo, que exige un administrador autenticado.
    app.mount("/static/avatars", StaticFiles(directory="static/avatars"), name="avatars")

    return app


app = create_app()
