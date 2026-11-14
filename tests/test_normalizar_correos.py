"""BE-12: el script de datos detecta los correos que chocan al pasar a minúsculas."""

from scripts.normalizar_correos import detectar_choques, pendientes_de_normalizar

USUARIOS = [(1, "ana@x.com"), (2, "Ana@x.com "), (3, "luis@x.com"), (4, "Maria@X.com")]


def test_detecta_las_cuentas_que_solo_se_diferencian_en_mayusculas():
    assert detectar_choques(USUARIOS) == {"ana@x.com": [1, 2]}


def test_sin_choques_devuelve_vacio():
    assert detectar_choques([(1, "a@x.com"), (2, "b@x.com")]) == {}


def test_lista_los_correos_que_necesitan_normalizarse():
    assert pendientes_de_normalizar(USUARIOS) == [2, 4]
