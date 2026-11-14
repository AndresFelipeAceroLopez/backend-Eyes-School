"""Contrato OpenAPI fiel a lo que la API responde de verdad (BC-07, PR-05).

schemathesis (corrida I1 del 10/11/2026) marcó tres desvíos entre el `openapi.json` y las
respuestas reales:

- **ST103 (50 casos).** Las rutas responden 401, 403, 404, 400 y 409 a través de
  `core/exceptions.py`, pero el contrato solo declaraba 200 y 422.
- **ST108 (25 casos).** Las fechas salían sin zona (`2026-11-03T03:03:37.192536`), que no es un
  `date-time` válido (RFC 3339 exige la zona). Ver `application/common/tipos.py`.
- **ST205 (3 casos).** En un 405, `Allow` listaba solo los métodos de la primera ruta que
  coincidía con la URL, no los de todas las que comparten esa URL. Ver `metodos_permitidos`.

Los errores se declaran sobre el esquema ya generado y no ruta por ruta: así una ruta nueva queda
documentada sin que nadie se acuerde de hacerlo.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from pydantic import BaseModel


class ErrorOut(BaseModel):
    """Cuerpo de todos los errores de la API (`HTTPException` de FastAPI)."""

    detail: str



_DESCRIPCION = {
    400: "Regla de negocio incumplida",
    401: "Sin token, token inválido o vencido, o credenciales incorrectas",
    403: "El rol o el usuario no tienen acceso a este recurso",
    404: "El recurso o alguno de los que referencia no existe",
    409: "Conflicto con un dato ya registrado (duplicado)",
    429: "Demasiados intentos: el inicio de sesión está bloqueado temporalmente",
}
_ESCRITURA = {"post", "put", "patch", "delete"}
# Rutas públicas que igual pueden responder 401 o 429 (credenciales, token de recuperación).
_PUBLICAS_CON_401 = {"/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/reset-password"}
_CON_429 = {"/api/v1/auth/login"}
# POST de sesión que no crean ni modifican recursos: no responden 400, 404 ni 409.
_SESION = {
    "/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/auth/logout",
    "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password",
}


def _errores_de(ruta: str, metodo: str, operacion: dict) -> list[int]:
    codigos: set[int] = set()
    if operacion.get("security"):
        codigos |= {401, 403}
    if ruta in _PUBLICAS_CON_401:
        codigos.add(401)
    if ruta in _CON_429:
        codigos.add(429)
    if "{" in ruta:
        codigos.add(404)
    if metodo in _ESCRITURA and ruta not in _SESION:
        codigos |= {400, 404, 409}
    return sorted(codigos)


def declarar_errores(esquema: dict) -> dict:
    esquema.setdefault("components", {}).setdefault("schemas", {})["ErrorOut"] = (
        ErrorOut.model_json_schema()
    )
    referencia = {"$ref": "#/components/schemas/ErrorOut"}
    for ruta, operaciones in esquema.get("paths", {}).items():
        for metodo, operacion in operaciones.items():
            respuestas = operacion.setdefault("responses", {})
            for codigo in _errores_de(ruta, metodo, operacion):
                respuestas.setdefault(
                    str(codigo),
                    {
                        "description": _DESCRIPCION[codigo],
                        "content": {"application/json": {"schema": referencia}},
                    },
                )
    return esquema


def instalar_contrato(app: FastAPI) -> None:
    """Reemplaza `app.openapi` por uno que declara los errores reales (se calcula una vez)."""

    def openapi() -> dict:
        if app.openapi_schema is None:
            app.openapi_schema = declarar_errores(
                get_openapi(
                    title=app.title,
                    version=app.version,
                    description=app.description,
                    routes=app.routes,
                )
            )
        return app.openapi_schema

    app.openapi = openapi


def _rutas_efectivas(app: FastAPI):
    """Rutas con su `path_regex` y `methods`, también las de los routers incluidos.

    Desde FastAPI 0.137 `include_router` ya no copia las rutas a `app.routes`: deja un
    `_IncludedRouter` que las expone con `effective_route_contexts()`.
    """
    for r in app.routes:
        if isinstance(r, APIRoute):
            yield r
        elif hasattr(r, "effective_route_contexts"):
            yield from r.effective_route_contexts()


def metodos_permitidos(app: FastAPI, ruta: str) -> list[str]:
    """Todos los métodos que acepta `ruta`, sumando las rutas que comparten esa URL."""
    metodos: set[str] = set()
    for r in _rutas_efectivas(app):
        if r.methods and r.path_regex.match(ruta):
            metodos |= set(r.methods)
    return sorted(metodos)
