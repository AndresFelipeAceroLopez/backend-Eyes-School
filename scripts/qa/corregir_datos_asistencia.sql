-- N-07 · Corrige los registros de asistencia heredados del seed en una base ya cargada (QA).
--
-- 1. `tipo` admite 'entrada', 'salida' o 'clase' (AsistenciaCreate). Las filas del seed
--    traían 'Manual' o 'QR', que es CÓMO se tomó el registro, no si fue entrada o salida.
--    La app móvil mostraba esas filas como «Entrada». Se dejan en NULL (tipo desconocido);
--    el método sigue visible en `codigo_qr`.
-- 2. `estado` admite 'Presente', 'Ausente', 'Tarde', 'Excusa' o 'Suspensión'. El seed usaba
--    'Tardanza', que ningún cliente reconoce.
--
-- Uso (revisar primero con los SELECT):
--   psql "$DATABASE_URL" -f scripts/qa/corregir_datos_asistencia.sql

BEGIN;

SELECT tipo, count(*) FROM public."Asistencia"
WHERE tipo IS NOT NULL AND tipo NOT IN ('entrada', 'salida', 'clase')
GROUP BY tipo;

UPDATE public."Asistencia"
SET tipo = NULL
WHERE tipo IN ('Manual', 'QR');

UPDATE public."Asistencia"
SET estado = 'Tarde'
WHERE estado = 'Tardanza';

UPDATE public."Asistencia_Aula"
SET estado = 'Tarde'
WHERE estado = 'Tardanza';

COMMIT;
