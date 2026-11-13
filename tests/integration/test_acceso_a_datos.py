"""Asistencia, acceso del padre a sus hijos y dashboards contra PostgreSQL (CP-INT-030 a 038, 060 a 065).

Seed: Rosa (usuario 4) es acudiente de los estudiantes 1 y 3; Roberto (usuario 8), del 2.
"""

import pytest

from tests.integration.conftest import (
    DOCENTE,
    ESTUDIANTE,
    PADRE_DOS_HIJOS,
    PADRE_UN_HIJO,
    encabezado,
)

pytestmark = pytest.mark.integration


def _registro(tipo, id_estudiante=1, fecha="2026-11-02"):
    return {"id_estudiante": id_estudiante, "fecha": fecha, "estado": "Presente", "tipo": tipo}


# --- asistencia -------------------------------------------------------------------------------


async def test_la_primera_entrada_se_guarda_y_la_segunda_responde_409(api):
    docente = await encabezado(api, DOCENTE)

    primera = await api.post("/api/v1/asistencia", json=_registro("entrada"), headers=docente)
    segunda = await api.post("/api/v1/asistencia", json=_registro("entrada"), headers=docente)

    assert primera.status_code == 201
    assert segunda.status_code == 409


async def test_entrada_y_salida_el_mismo_dia_se_guardan_y_la_segunda_salida_responde_409(api):
    docente = await encabezado(api, DOCENTE)

    entrada = await api.post("/api/v1/asistencia", json=_registro("entrada"), headers=docente)
    salida = await api.post("/api/v1/asistencia", json=_registro("salida"), headers=docente)
    otra_salida = await api.post("/api/v1/asistencia", json=_registro("salida"), headers=docente)

    assert (entrada.status_code, salida.status_code, otra_salida.status_code) == (201, 201, 409)


async def test_una_salida_sin_entrada_responde_400(api):
    docente = await encabezado(api, DOCENTE)

    respuesta = await api.post("/api/v1/asistencia", json=_registro("salida"), headers=docente)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "No hay entrada registrada hoy para este estudiante"


async def test_varios_registros_de_clase_el_mismo_dia_se_permiten(api):
    docente = await encabezado(api, DOCENTE)

    for _ in range(2):
        assert (
            await api.post("/api/v1/asistencia", json=_registro("clase"), headers=docente)
        ).status_code == 201


async def test_un_registro_anulado_no_cuenta_como_duplicado(api):
    docente = await encabezado(api, DOCENTE)
    admin_id = (await api.post("/api/v1/asistencia", json=_registro("entrada"), headers=docente)).json()
    from tests.integration.conftest import ADMIN

    admin = await encabezado(api, ADMIN)
    await api.delete(f"/api/v1/asistencia/{admin_id['id_asistencia']}", headers=admin)

    nueva = await api.post("/api/v1/asistencia", json=_registro("entrada"), headers=docente)

    assert nueva.status_code == 201


async def test_registrado_por_sale_del_token_aunque_el_cuerpo_diga_otra_cosa(api):
    docente = await encabezado(api, DOCENTE)

    respuesta = await api.post(
        "/api/v1/asistencia", json={**_registro("clase"), "registrado_por": 9}, headers=docente
    )

    assert respuesta.json()["registrado_por"] == 2


async def test_un_padre_no_lee_la_asistencia_de_un_estudiante_ajeno(api):
    roberto = await encabezado(api, PADRE_UN_HIJO)

    ajeno = await api.get("/api/v1/asistencia?id_estudiante=1", headers=roberto)
    propio = await api.get("/api/v1/asistencia?id_estudiante=2", headers=roberto)

    assert ajeno.status_code == 403
    assert propio.status_code == 200


async def test_un_padre_sin_filtro_recibe_400(api):
    roberto = await encabezado(api, PADRE_UN_HIJO)

    assert (await api.get("/api/v1/asistencia", headers=roberto)).status_code == 400


async def test_el_detalle_de_una_asistencia_ajena_responde_403(api):
    roberto = await encabezado(api, PADRE_UN_HIJO)

    # En el seed, la asistencia 1 es del estudiante 1.
    assert (await api.get("/api/v1/asistencia/1", headers=roberto)).status_code == 403


async def test_un_estudiante_solo_lee_su_propia_asistencia(api):
    sofia = await encabezado(api, ESTUDIANTE)

    assert (await api.get("/api/v1/asistencia?id_estudiante=1", headers=sofia)).status_code == 200
    assert (await api.get("/api/v1/asistencia?id_estudiante=2", headers=sofia)).status_code == 403


# --- padre con varios hijos -------------------------------------------------------------------


async def test_un_padre_con_dos_hijos_lista_a_los_dos(api):
    rosa = await encabezado(api, PADRE_DOS_HIJOS)

    respuesta = await api.get("/api/v1/padres/me/hijos", headers=rosa)

    assert respuesta.status_code == 200
    assert sorted(h["id_estudiante"] for h in respuesta.json()) == [1, 3]


async def test_un_padre_con_dos_hijos_ya_no_provoca_error_500_en_padres_me(api):
    rosa = await encabezado(api, PADRE_DOS_HIJOS)

    primero = await api.get("/api/v1/padres/me", headers=rosa)
    segundo = await api.get("/api/v1/padres/me?id_estudiante=3", headers=rosa)

    assert primero.status_code == 200
    assert segundo.json()["id_estudiante"] == 3


async def test_un_padre_accede_a_los_dos_hijos_y_a_ningun_otro(api):
    rosa = await encabezado(api, PADRE_DOS_HIJOS)

    for id_hijo, esperado in ((1, 200), (3, 200), (2, 403)):
        respuesta = await api.get(f"/api/v1/estudiantes/{id_hijo}/asistencia", headers=rosa)
        assert respuesta.status_code == esperado, id_hijo


async def test_el_dashboard_del_padre_funciona_con_varios_hijos_y_rechaza_hijos_ajenos(api):
    rosa = await encabezado(api, PADRE_DOS_HIJOS)

    sin_filtro = await api.get("/api/v1/dashboard/padre", headers=rosa)
    segundo = await api.get("/api/v1/dashboard/padre?id_estudiante=3", headers=rosa)
    ajeno = await api.get("/api/v1/dashboard/padre?id_estudiante=2", headers=rosa)

    assert sin_filtro.status_code == 200
    assert segundo.json()["id_estudiante"] == 3
    assert ajeno.status_code == 403


async def test_el_inicio_del_estudiante_y_del_padre_responde_200_no_500(api):
    sofia = await encabezado(api, ESTUDIANTE)
    rosa = await encabezado(api, PADRE_DOS_HIJOS)

    assert (await api.get("/api/v1/dashboard/estudiante", headers=sofia)).status_code == 200
    assert (await api.get("/api/v1/dashboard/estudiante", headers=rosa)).status_code == 200
    assert (
        await api.get("/api/v1/dashboard/estudiante?id_estudiante=3", headers=rosa)
    ).status_code == 200
    assert (
        await api.get("/api/v1/dashboard/estudiante?id_estudiante=2", headers=rosa)
    ).status_code == 403


async def test_el_docente_no_tiene_inicio_de_estudiante(api):
    docente = await encabezado(api, DOCENTE)

    assert (await api.get("/api/v1/dashboard/estudiante", headers=docente)).status_code == 403


async def test_un_padre_no_lee_el_vinculo_de_otro_padre(api):
    roberto = await encabezado(api, PADRE_UN_HIJO)
    rosa = await encabezado(api, PADRE_DOS_HIJOS)

    # padres.id 1 es de Rosa (usuario 4) en el seed
    assert (await api.get("/api/v1/padres/1", headers=roberto)).status_code == 403
    assert (await api.get("/api/v1/padres/1", headers=rosa)).status_code == 200


# --- DEF-039: un id fuera del rango de PostgreSQL responde 422, no 500 ---


async def test_un_id_fuera_de_rango_responde_422_contra_la_base_real(api):
    """Prueba de verdad del manejador: la base rechaza el valor y la API traduce a 422.

    Las unitarias de `tests/test_id_fuera_de_rango.py` simulan el error; esta lo provoca de
    verdad con PostgreSQL, que es donde se descubrió (schemathesis contra QA).
    """
    from tests.integration.conftest import ADMIN, encabezado

    h = await encabezado(api, ADMIN)
    fuera_de_rango = 9223372036854775808

    for ruta in (
        f"/api/v1/estudiantes/{fuera_de_rango}",
        f"/api/v1/cursos/{fuera_de_rango}",
        f"/api/v1/cursos/{fuera_de_rango}/horarios",
    ):
        r = await api.get(ruta, headers=h)
        assert r.status_code == 422, f"{ruta} respondió {r.status_code}"
        assert r.json()["detail"] == "Valor fuera del rango permitido."


async def test_un_id_valido_sigue_funcionando(api):
    """Red de seguridad: el manejador no puede afectar a las peticiones normales."""
    from tests.integration.conftest import ADMIN, encabezado

    h = await encabezado(api, ADMIN)
    assert (await api.get("/api/v1/cursos/1", headers=h)).status_code == 200
    assert (await api.get("/api/v1/cursos/999999", headers=h)).status_code == 404
