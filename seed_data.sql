-- ============================================================
-- LIMPIEZA PREVIA (elimina datos existentes respetando FK)
-- ============================================================
TRUNCATE TABLE
  public."Reportes",
  public.profesorespecializacion,
  public.profesores_horario,
  public.estudianteips,
  public.novedades,
  public.notas,
  public.padres,
  public.asignaciones,
  public."Asistencia_Aula",
  public."Asistencia",
  public.estudiantes,
  public.profesores,
  public.administrador,
  public.usuario,
  public."Horario",
  public.tiposnovedad,
  public.cursos,
  public.materias,
  public.especializaciones,
  public.roles
RESTART IDENTITY CASCADE;

-- ============================================================
-- SEED DATA - Eyes School Backend
-- Credenciales de prueba:
--   admin@eyesschool.edu.co          -> Admin2026*
--   carlos.jimenez@eyes.edu.co       -> Profe2026*
--   sofia.rodriguez@student.eyes.co  -> Estu2026*
--   rosa.perez@gmail.com             -> Padre2026*
-- ============================================================

INSERT INTO public.roles ("nombreRol") VALUES
('docente'),
('estudiante'),
('admin'),
('padre');


INSERT INTO public.especializaciones ("nombreEspecializacion", "descripcion", "activo") VALUES
('Matemáticas Aplicadas',      'Especialización en matemáticas y cálculo', true),
('Ciencias Naturales',         'Biología, química y física', true),
('Lengua y Literatura',        'Español y comprensión lectora', true),
('Historia y Geografía',       'Ciencias sociales y territorios', true),
('Educación Física',           'Deporte y salud', true),
('Informática Educativa',      'TIC y programación básica', true),
('Artes Plásticas',            'Dibujo, pintura y escultura', true),
('Música',                     'Teoría musical e instrumentos', true),
('Inglés como Segunda Lengua', 'Enseñanza del inglés', true),
('Psicopedagogía',             'Aprendizaje y desarrollo infantil', true);

INSERT INTO public.materias ("nombreMateria", "codigoMateria", "activa") VALUES
('Matemáticas',       'MAT001', true),
('Español',           'ESP001', true),
('Ciencias Naturales','CNA001', true),
('Ciencias Sociales', 'CSO001', true),
('Inglés',            'ING001', true),
('Educación Física',  'EDF001', true),
('Artes',             'ART001', true),
('Música',            'MUS001', true),
('Informática',       'INF001', true),
('Ética y Valores',   'ETI001', true);


INSERT INTO public.cursos ("nombreCurso","grado","jornada","ano","area","intensidadHoraria","descripcion","activo","fechaCreacion") VALUES
('Sexto A',   '6°',  'Mañana', 2026, 'Básica Secundaria', 30, 'Primer grupo de sexto grado',    true, NOW()),
('Sexto B',   '6°',  'Tarde',  2026, 'Básica Secundaria', 30, 'Segundo grupo de sexto grado',   true, NOW()),
('Séptimo A', '7°',  'Mañana', 2026, 'Básica Secundaria', 30, 'Primer grupo de séptimo grado',  true, NOW()),
('Séptimo B', '7°',  'Tarde',  2026, 'Básica Secundaria', 30, 'Segundo grupo de séptimo grado', true, NOW()),
('Octavo A',  '8°',  'Mañana', 2026, 'Básica Secundaria', 32, 'Primer grupo de octavo grado',   true, NOW()),
('Noveno A',  '9°',  'Mañana', 2026, 'Básica Secundaria', 32, 'Primer grupo de noveno grado',   true, NOW()),
('Décimo A',  '10°', 'Mañana', 2026, 'Media Vocacional',  35, 'Primer grupo de décimo grado',   true, NOW()),
('Décimo B',  '10°', 'Tarde',  2026, 'Media Vocacional',  35, 'Segundo grupo de décimo grado',  true, NOW()),
('Once A',    '11°', 'Mañana', 2026, 'Media Vocacional',  35, 'Primer grupo de once grado',     true, NOW()),
('Once B',    '11°', 'Tarde',  2026, 'Media Vocacional',  35, 'Segundo grupo de once grado',    true, NOW());


INSERT INTO public.tiposnovedad ("nombreTipo","descripcion","nivelGravedad","requiereAccion","activo") VALUES
('Inasistencia Reiterada',  'Ausencias frecuentes sin justificación',       'Alto',  true,  true),
('Bajo Rendimiento',        'Notas por debajo del mínimo aprobatorio',      'Medio', true,  true),
('Conflicto entre pares',   'Problemas de convivencia entre estudiantes',   'Alto',  true,  true),
('Incumplimiento de tareas','No entrega de trabajos asignados',             'Bajo',  false, true),
('Problemas de salud',      'Enfermedad o malestar reportado',              'Medio', true,  true),
('Dificultad de aprendizaje','Posible necesidad de apoyo pedagógico',       'Medio', true,  true),
('Violencia escolar',       'Agresión física o verbal',                     'Alto',  true,  true),
('Uso de dispositivos',     'Uso no autorizado de celular u otros',         'Bajo',  false, true),
('Daño a bienes',           'Daño o pérdida de material escolar',           'Medio', true,  true),
('Situación familiar',      'Problemas en el entorno familiar',             'Alto',  true,  true);


INSERT INTO public."Horario" ("idCurso","idMateria","dia","horaInicio","horaFin","salon","activo") VALUES
(1, 1, 'Lunes',     '07:00:00', '08:00:00', 'Aula 101',     true),
(1, 2, 'Lunes',     '08:00:00', '09:00:00', 'Aula 101',     true),
(1, 3, 'Martes',    '07:00:00', '08:00:00', 'Lab. Ciencias',true),
(2, 1, 'Martes',    '14:00:00', '15:00:00', 'Aula 201',     true),
(2, 5, 'Miércoles', '14:00:00', '15:00:00', 'Aula 201',     true),
(3, 4, 'Jueves',    '07:00:00', '08:00:00', 'Aula 102',     true),
(4, 6, 'Viernes',   '14:00:00', '15:00:00', 'Cancha',       true),
(5, 9, 'Lunes',     '07:00:00', '08:00:00', 'Sala Sistemas',true),
(6, 7, 'Martes',    '07:00:00', '08:00:00', 'Aula Arte',    true),
(7, 8, 'Miércoles', '07:00:00', '08:00:00', 'Aula Música',  true);



INSERT INTO public.usuario (
  "tipoDocumento","numeroDocumento","primerNombre","segundoNombre",
  "primerApellido","segundoApellido","genero","direccion","correo",
  "password","telefono","estado","fechaRegistro","idRol","idUsuario_uuid"
) VALUES

 ('CC','10000001','Carlos','Eduardo','Mendoza','Suárez','M',
  'Calle 1 #10-20','admin@eyesschool.edu.co',
  '$2b$12$QlWdugko6fUlcuQHVq3iBewuBcoV2e6rqjnSg.0I0VZBN49WZ3wJS',
  '3101234567',true,NOW(),3,gen_random_uuid()),


 ('CC','10000002','Carlos','Andrés','Jiménez','Morales','M',
  'Carrera 5 #20-30','carlos.jimenez@eyes.edu.co',
  '$2b$12$eKB/sdPZwks5d.77lPaLJuYtQtBv1bzRFCKRxiNpLVSnCgrMinXHe',
  '3112345678',true,NOW(),1,gen_random_uuid()),


 ('TI','20000001','Sofía','Valentina','Rodríguez','Torres','F',
  'Av. 7 #15-40','sofia.rodriguez@student.eyes.co',
  '$2b$12$fiuChcwm2i/lue4e84nvU.9l6xPHDzDNq8/5WJeZBMVAqao6XIgBu',
  '3123456789',true,NOW(),2,gen_random_uuid()),


('CC','30000001','Rosa','María','Pérez','Gómez','F',
 'Calle 8 #12-34','rosa.perez@gmail.com',
 '$2b$12$/EkMcIP/sbERG5EL.FVRCuoATfQpVyFi0LgqxjKQogmS6R4cN/VOK',
 '3134567890',true,NOW(),4,gen_random_uuid()),

 ('CC','10000003','María','Camila','Herrera','Díaz','F',
  'Calle 12 #8-90','maria.herrera@eyes.edu.co',
  '$2b$12$eKB/sdPZwks5d.77lPaLJuYtQtBv1bzRFCKRxiNpLVSnCgrMinXHe',
  '3145678901',true,NOW(),1,gen_random_uuid()),

 ('TI','20000002','Juan','David','Pérez','Castro','M',
  'Calle 3 #5-10','juan.perez@student.eyes.co',
  '$2b$12$fiuChcwm2i/lue4e84nvU.9l6xPHDzDNq8/5WJeZBMVAqao6XIgBu',
  '3156789012',true,NOW(),2,gen_random_uuid()),

 ('TI','20000003','Santiago','Andrés','López','Vargas','M',
  'Cra 10 #30-60','santiago.lopez@student.eyes.co',
  '$2b$12$fiuChcwm2i/lue4e84nvU.9l6xPHDzDNq8/5WJeZBMVAqao6XIgBu',
  '3167890123',true,NOW(),2,gen_random_uuid()),

('CC','30000002','Roberto','Hernán','Díaz','Silva','M',
 'Calle 20 #10-5','roberto.diaz@gmail.com',
 '$2b$12$/EkMcIP/sbERG5EL.FVRCuoATfQpVyFi0LgqxjKQogmS6R4cN/VOK',
 '3178901234',true,NOW(),4,gen_random_uuid()),

 ('CC','10000004','Lucía','Patricia','Soto','Ramos','F',
  'Av. 15 #40-20','lucia.soto@eyes.edu.co',
  '$2b$12$eKB/sdPZwks5d.77lPaLJuYtQtBv1bzRFCKRxiNpLVSnCgrMinXHe',
  '3189012345',true,NOW(),1,gen_random_uuid()),

 ('CC','10000005','Diana','Rocío','Vega','Castillo','F',
  'Carrera 18 #5-60','diana.vega@eyesschool.edu.co',
  '$2b$12$QlWdugko6fUlcuQHVq3iBewuBcoV2e6rqjnSg.0I0VZBN49WZ3wJS',
  '3190123456',true,NOW(),3,gen_random_uuid());

INSERT INTO public.administrador ("idUsuario","cargo","nivelAcceso","estado","fechaAsignacion") VALUES
(1,  'Rector',                  'Total', 'Activo', '2026-01-01'),
(10, 'Coordinadora Académica',  'Alto',  'Activo', '2026-01-15');


INSERT INTO public.profesores ("idUsuario","codigoProfesor","titulo","nivelEstudios","fechaVinculacion","estado","fechaRegistro") VALUES
(2, 'PRF001', 'Licenciado en Matemáticas',       'Pregrado',        '2024-01-15', 'Activo', NOW()),
(5, 'PRF002', 'Licenciada en Ciencias Naturales', 'Especialización', '2023-08-01', 'Activo', NOW()),
(9, 'PRF003', 'Magíster en Humanidades',          'Maestría',        '2022-03-10', 'Activo', NOW());


INSERT INTO public.estudiantes ("idUsuario","codigoEstudiante","fechaIngreso","estado","idCursoActual","fechaRegistro") VALUES
(3, 'EST001', '2026-01-20', 'Activo', 1, NOW()),
(6, 'EST002', '2026-01-20', 'Activo', 1, NOW()),
(7, 'EST003', '2026-01-20', 'Activo', 2, NOW());

INSERT INTO public."Asistencia" ("idEstudiante","fecha","estado","observacion","registradoPor","fechaRegistro","tipo","codigo_qr","activo") VALUES
(1, '2026-06-16', 'Presente',  NULL,                    2, NOW(), 'Manual', NULL,                    true),
(1, '2026-06-17', 'Ausente',   'Sin justificación',     2, NOW(), 'Manual', NULL,                    true),
(1, '2026-06-18', 'Presente',  NULL,                    2, NOW(), 'QR',    'QR-EST001-20260618',     true),
(2, '2026-06-16', 'Presente',  NULL,                    2, NOW(), 'QR',    'QR-EST002-20260616',     true),
(2, '2026-06-17', 'Tardanza',  'Llegó 15 min tarde',    2, NOW(), 'Manual', NULL,                    true),
(2, '2026-06-18', 'Presente',  NULL,                    2, NOW(), 'Manual', NULL,                    true),
(3, '2026-06-16', 'Ausente',   'Permiso médico',        2, NOW(), 'Manual', NULL,                    true),
(3, '2026-06-17', 'Presente',  NULL,                    2, NOW(), 'QR',    'QR-EST003-20260617',     true),
(3, '2026-06-18', 'Presente',  NULL,                    2, NOW(), 'Manual', NULL,                    true),
(1, '2026-06-19', 'Presente',  NULL,                    2, NOW(), 'QR',    'QR-EST001-20260619',     true);


INSERT INTO public."Asistencia_Aula" ("idEstudiante","idHorario","fecha","estado","observacion","registradoPor","fechaRegistro") VALUES
(1, 1, '2026-06-16', 'Presente', 'Sin novedad',   2, NOW()),
(1, 2, '2026-06-16', 'Presente', 'Sin novedad',   2, NOW()),
(2, 1, '2026-06-16', 'Tardanza', 'Llegó tarde',   2, NOW()),
(2, 4, '2026-06-17', 'Presente', 'Sin novedad',   2, NOW()),
(3, 4, '2026-06-17', 'Ausente',  'No asistió',    2, NOW()),
(1, 3, '2026-06-17', 'Presente', 'Sin novedad',   2, NOW()),
(2, 5, '2026-06-18', 'Presente', 'Sin novedad',   2, NOW()),
(3, 7, '2026-06-18', 'Presente', 'Sin novedad',   2, NOW()),
(1, 8, '2026-06-19', 'Presente', 'Sin novedad',   2, NOW()),
(2, 9, '2026-06-19', 'Presente', 'Sin novedad',   2, NOW());


INSERT INTO public.notas ("idEstudiante","idMateria","idPeriodo","nota","observacion","fechaRegistro","registradoPor") VALUES
(1, 1, 1, 4.5, 'Excelente desempeño',       NOW(), 2),
(1, 2, 1, 3.8, 'Buen trabajo',              NOW(), 2),
(1, 3, 1, 4.0, NULL,                        NOW(), 5),
(2, 1, 1, 3.2, 'Necesita refuerzo',         NOW(), 2),
(2, 2, 1, 4.2, 'Muy buena participación',   NOW(), 2),
(2, 5, 1, 3.7, NULL,                        NOW(), 9),
(3, 1, 1, 2.9, 'Bajo rendimiento',          NOW(), 2),
(3, 3, 1, 3.5, NULL,                        NOW(), 5),
(3, 4, 1, 4.1, 'Activo en clase',           NOW(), 9),
(1, 5, 1, 4.8, 'Sobresaliente',             NOW(), 9);


INSERT INTO public.novedades ("idEstudiante","idTipoNovedad","fecha","descripcion","accionTomada","registradoPor","estado") VALUES
(1, 4, '2026-06-10', 'No entregó trabajo de matemáticas',       'Se notificó al padre',           2, 'Resuelta'),
(2, 1, '2026-06-12', 'Tres inasistencias seguidas',             'Llamada a acudiente',             2, 'Pendiente'),
(3, 7, '2026-06-15', 'Agresión verbal a compañero',             'Citación a padres',               2, 'En proceso'),
(1, 5, '2026-06-14', 'Dolor de cabeza recurrente',              'Revisión enfermería',             2, 'Resuelta'),
(2, 2, '2026-06-16', 'Notas por debajo de 3.0 en dos materias', 'Plan de apoyo pedagógico',        2, 'Pendiente'),
(3, 6, '2026-06-17', 'Dificultad con lectoescritura',           'Derivación a psicopedagogía',     2, 'En proceso'),
(1, 8, '2026-06-18', 'Uso de celular en clase',                 'Amonestación verbal',             2, 'Resuelta'),
(2, 9, '2026-06-11', 'Daño a pupitre del salón',                'Se informó a coordinación',       2, 'Resuelta'),
(3,10, '2026-06-13', 'Situación de separación de padres',       'Seguimiento con orientador',      2, 'En proceso'),
(1, 3, '2026-06-19', 'Conflicto con compañero por un balón',    'Mediación escolar',               2, 'Resuelta');


INSERT INTO public.padres ("idUsuario","idEstudiante","parentesco","ocupacion") VALUES
(4, 1, 'Madre',   'Enfermera'),
(8, 2, 'Padre',   'Ingeniero'),
(4, 3, 'Abuela',  'Pensionada');


INSERT INTO public.asignaciones ("idProfesor","idCurso","idMateria","fechaAsignacion","activo") VALUES
(1, 1, 1, NOW(), true),
(1, 2, 1, NOW(), true),
(2, 1, 3, NOW(), true),
(2, 3, 3, NOW(), true),
(3, 1, 2, NOW(), true),
(3, 3, 4, NOW(), true),
(1, 5, 1, NOW(), true),
(2, 5, 3, NOW(), true),
(3, 5, 2, NOW(), true),
(1, 6, 1, NOW(), true);


INSERT INTO public.profesores_horario ("idProfesor","idHorario","fechaAsignacion","activo") VALUES
(1, 1,  NOW(), true),
(1, 2,  NOW(), true),
(2, 3,  NOW(), true),
(1, 4,  NOW(), true),
(1, 5,  NOW(), true),
(3, 6,  NOW(), true),
(2, 7,  NOW(), true),
(1, 8,  NOW(), true),
(3, 9,  NOW(), true),
(2, 10, NOW(), true);


INSERT INTO public.profesorespecializacion ("idProfesor","idEspecializacion","institucion") VALUES
(1, 1, 'Universidad Nacional de Colombia'),
(1, 6, 'SENA'),
(2, 2, 'Universidad de Antioquia'),
(2, 10,'Universidad Pedagógica'),
(3, 3, 'Universidad del Valle'),
(3, 4, 'Universidad Externado'),
(1, 9, 'Institución Universitaria Colombo Americana'),
(2, 5, 'INDER'),
(3, 7, 'Bellas Artes'),
(3, 8, 'Conservatorio de Música');


INSERT INTO public.estudianteips ("idEstudiante","idIPS","nombreIPS","fechaAfiliacion","tipoAfiliacion","activo") VALUES
(1, 101, 'Sura EPS',    '2020-01-01', 'Contributivo', true),
(2, 102, 'Nueva EPS',   '2019-06-15', 'Subsidiado',   true),
(3, 103, 'Compensar',   '2021-03-20', 'Contributivo', true);


INSERT INTO public."Reportes" ("nombreReporte","tipoReporte","fechaGeneracion","fechaInicio","fechaFin","estado","idAdministrador","parametros","archivoGenerado") VALUES
('Reporte de Asistencia Junio',  'Asistencia',    '2026-06-30', '2026-06-01', '2026-06-30', 'Generado', 1, '-', 'asistencia_junio_2026.pdf'),
('Reporte de Notas P1',          'Notas',         '2026-06-30', '2026-03-01', '2026-06-30', 'Generado', 1, '-', 'notas_p1_2026.pdf'),
('Novedades Mayo',               'Novedades',     '2026-05-31', '2026-05-01', '2026-05-31', 'Generado', 2, '-', 'novedades_mayo.pdf'),
('Asistencia Curso 6A',          'Asistencia',    '2026-06-20', '2026-06-01', '2026-06-20', 'Generado', 1, '-', 'asistencia_6a.pdf'),
('Rendimiento General',          'Notas',         '2026-06-28', '2026-01-01', '2026-06-28', 'Generado', 2, '-', 'rendimiento_general.pdf'),
('Reporte Novedades Graves',     'Novedades',     '2026-06-25', '2026-06-01', '2026-06-25', 'Pendiente',1, '-', NULL),
('Asistencia Docentes',          'Asistencia',    '2026-06-30', '2026-06-01', '2026-06-30', 'Generado', 1, '-', 'asistencia_doc.pdf'),
('Reporte Matriculas',           'Administrativo','2026-02-15', '2026-01-15', '2026-02-15', 'Generado', 2, '-', 'matriculas_2026.pdf'),
('Indicadores Convivencia',      'Convivencia',   '2026-06-30', '2026-01-01', '2026-06-30', 'Pendiente',1, '-', NULL),
('Reporte Padres de Familia',    'Administrativo','2026-06-01', '2026-01-01', '2026-06-01', 'Generado', 2, '-', 'padres_2026.pdf');
