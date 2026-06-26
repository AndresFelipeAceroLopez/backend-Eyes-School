-- ============================================================================
--  Datos sintéticos: 10 estudiantes por cada curso activo
-- ----------------------------------------------------------------------------
--  Inserta 10 estudiantes "de prueba" en CADA curso activo de public.cursos.
--  Crea una fila en public.usuario (idRol = 2 = estudiante) y su fila asociada
--  en public.estudiantes, respetando los CHECK/NOT NULL del esquema real.
--
--  Características:
--    • Documento, correo y código de estudiante únicos y prefijados ("9..."/
--      "est.syn..."/"SYN...") para NO colisionar con datos reales.
--    • Contraseña común "Estudiante123*" (hash bcrypt) → pueden iniciar sesión.
--    • Idempotente: si ya existen estudiantes sintéticos (codigoEstudiante LIKE
--      'SYN%') NO vuelve a insertar.
--
--  Uso (PowerShell, contra Render Postgres):
--    psql "$env:DATABASE_URL" -f seed_estudiantes_sinteticos.sql
--  o desde el SQL editor del proveedor, pegando este archivo completo.
--
--  Para REVERTIR, ver el bloque comentado al final.
-- ============================================================================

DO $$
DECLARE
  c            RECORD;
  i            INT;
  v_seq        INT := 0;
  v_id_usuario INT;
  v_doc        TEXT;
  v_codigo     TEXT;
  v_correo     TEXT;
  -- bcrypt de 'Estudiante123*'
  v_pwd        TEXT := '$2b$12$cGeRdVNDTDPHzw4OWX0YS.MFku2QO0HRHRlMOMV5vCZdXJNVy/gF6';
  nombres      TEXT[]  := ARRAY['Juan','María','Carlos','Laura','Andrés','Valentina','Santiago','Camila','Sebastián','Daniela','Mateo','Sofía','Nicolás','Isabella','Samuel'];
  apellidos    TEXT[]  := ARRAY['García','Rodríguez','Martínez','López','González','Hernández','Pérez','Gómez','Díaz','Torres','Ramírez','Flores','Rojas','Castro','Vargas'];
  generos      CHAR[]  := ARRAY['M','F'];
  n_nombres    INT;
  n_apellidos  INT;
BEGIN
  -- Guard de idempotencia
  IF EXISTS (SELECT 1 FROM public.estudiantes WHERE "codigoEstudiante" LIKE 'SYN%') THEN
    RAISE NOTICE 'Ya existen estudiantes sintéticos (SYN%%). No se inserta nada.';
    RETURN;
  END IF;

  n_nombres   := array_length(nombres, 1);
  n_apellidos := array_length(apellidos, 1);

  FOR c IN
    SELECT "idCurso", "nombreCurso"
    FROM public.cursos
    WHERE activo = true
    ORDER BY "idCurso"
  LOOP
    FOR i IN 1..10 LOOP
      v_seq    := v_seq + 1;
      v_doc    := '9' || lpad(v_seq::text, 8, '0');                                   -- p. ej. 900000001
      v_codigo := 'SYN' || lpad(c."idCurso"::text, 2, '0') || lpad(i::text, 2, '0');  -- p. ej. SYN0101
      v_correo := 'est.syn' || v_seq || '@eyeschool.test';

      INSERT INTO public.usuario
        ("tipoDocumento", "numeroDocumento", "primerNombre", "primerApellido",
         "segundoApellido", genero, correo, password, estado, "fechaRegistro", "idRol")
      VALUES
        ('CC',
         v_doc,
         nombres[1 + (v_seq % n_nombres)],
         apellidos[1 + (v_seq % n_apellidos)],
         apellidos[1 + ((v_seq + 7) % n_apellidos)],
         generos[1 + (v_seq % 2)],
         v_correo,
         v_pwd,
         true,
         NOW(),
         2)
      RETURNING "idUsuario" INTO v_id_usuario;

      INSERT INTO public.estudiantes
        ("idUsuario", "codigoEstudiante", "fechaIngreso", estado, "idCursoActual", "fechaRegistro")
      VALUES
        (v_id_usuario, v_codigo, CURRENT_DATE, 'Activo', c."idCurso", NOW());
    END LOOP;

    RAISE NOTICE 'Curso % (id %): 10 estudiantes insertados.', c."nombreCurso", c."idCurso";
  END LOOP;

  RAISE NOTICE 'Total estudiantes sintéticos creados: %', v_seq;
END $$;

-- ----------------------------------------------------------------------------
-- REVERTIR (descomentar y ejecutar para borrar SOLO los datos sintéticos):
--
-- DELETE FROM public.usuario
--  WHERE "idUsuario" IN (
--    SELECT "idUsuario" FROM public.estudiantes WHERE "codigoEstudiante" LIKE 'SYN%'
--  );
-- DELETE FROM public.estudiantes WHERE "codigoEstudiante" LIKE 'SYN%';
--
-- (Si hay FK de estudiantes→usuario con ON DELETE CASCADE basta el primer DELETE;
--  si no, ejecuta primero el DELETE de estudiantes y luego el de usuario.)
-- ----------------------------------------------------------------------------
