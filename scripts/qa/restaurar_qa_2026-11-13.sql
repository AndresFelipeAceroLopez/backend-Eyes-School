-- Restaura en QA lo que alteró la corrida de schemathesis del 13/11/2026.
--
-- QUÉ PASÓ: la repetición de schemathesis (contrato, BC-07) se lanzó con --include-method GET y
-- un --include-path-regex. schemathesis los combina con OR, no con AND, así que también probó 11
-- operaciones de escritura con el token de administrador. Se detuvo a los ~12 minutos. Los
-- profesores 1–3, las asignaciones 1, 3, 6 y 10 y la descripción de la especialización 1 ya se
-- restauraron por API. Lo que el API no permite restaurar queda aquí:
--   · especializaciones 1, 3, 6 y 10 desactivadas (PUT no admite `activo`);
--   · novedades 1, 2, 5 y 9 borradas (DELETE es físico; el API no fija id ni estos estados).
--
-- Se corre UNA vez contra la base de QA, con `python -m scripts.qa.restaurar_qa --base <nombre>`
-- desde la consola SSH de apieyeschool-q. Es idempotente y se niega a correr en otra base.

-- La base de QA se declara antes de correr esto (el nombre real de la de QA es el que muestra
-- la consola de apieyeschool-q; el 14/11 resultó ser eyesschool_wru2, no «qaeyesschool»):
--     SET eyes.base_qa = '<nombre>';
-- scripts/qa/restaurar_qa.py lo hace solo, después de comprobar que corre en apieyeschool-q.
DO $$
BEGIN
    IF current_database() IS DISTINCT FROM current_setting('eyes.base_qa', true) THEN
        RAISE EXCEPTION 'Esta restauración es solo para la base de QA declarada en eyes.base_qa (actual: %, declarada: %)',
            current_database(), current_setting('eyes.base_qa', true);
    END IF;
END $$;

BEGIN;

UPDATE public.especializaciones SET activo = true
WHERE "idEspecializacion" IN (1, 3, 6, 10) AND activo = false;

-- Valores exactos de seed_data.sql (filas 1, 2, 5 y 9 de public.novedades).
INSERT INTO public.novedades
    ("idNovedad", "idEstudiante", "idTipoNovedad", "fecha", "descripcion", "accionTomada", "registradoPor", "estado")
VALUES
    (1, 1, 4,  '2026-06-10', 'No entregó trabajo de matemáticas',       'Se notificó al padre',        2, 'Resuelta'),
    (2, 2, 1,  '2026-06-12', 'Tres inasistencias seguidas',             'Llamada a acudiente',         2, 'Pendiente'),
    (5, 2, 2,  '2026-06-16', 'Notas por debajo de 3.0 en dos materias', 'Plan de apoyo pedagógico',    2, 'Pendiente'),
    (9, 3, 10, '2026-06-13', 'Situación de separación de padres',       'Seguimiento con orientador',  2, 'En proceso')
ON CONFLICT ("idNovedad") DO NOTHING;

-- Que la secuencia no vuelva a entregar un id ya usado.
SELECT setval(pg_get_serial_sequence('public.novedades', 'idNovedad'),
              GREATEST((SELECT max("idNovedad") FROM public.novedades), 1));

COMMIT;

-- Verificación: 10 especializaciones activas y las novedades 1–10 presentes.
SELECT count(*) FILTER (WHERE activo) AS especializaciones_activas FROM public.especializaciones;
SELECT array_agg("idNovedad" ORDER BY "idNovedad") AS novedades FROM public.novedades WHERE "idNovedad" <= 10;
