# Database Analysis — Eyes School

> Fuente de verdad: `schema.sql` | Schema de negocio: `public`

---

## 1. Resumen general

| Schema     | Tablas | FKs | Naturaleza                       |
|------------|--------|-----|----------------------------------|
| `public`   | 20     | 29  | Dominio de negocio               |
| `auth`     | 23     | 18  | Supabase Auth (infraestructura)  |
| `storage`  | 8      | 5   | Supabase Storage (infraestructura)|
| `realtime` | 3      | 0   | Supabase Realtime (infraestructura)|
| **Total**  | **54** | **52** |                               |

Vistas del schema `public`: 5
(`asistencia_por_estudiante`, `estudiantes_por_curso`, `mejor_estudiante`, `promedio_por_estudiante`, `promedio_total_notas`)

---

## 2. Tablas del schema `public`

### 2.1 `usuario`
Entidad central del sistema. Todo actor del sistema (admin, docente, estudiante, padre) es primero un `usuario`.

| Columna             | Tipo                  | Restricciones                                    |
|---------------------|-----------------------|--------------------------------------------------|
| `idUsuario`         | integer               | PK, NOT NULL, auto-increment                     |
| `tipoDocumento`     | varchar(10)           | NOT NULL, CHECK IN ('CC','CE','TI','PAS')        |
| `numeroDocumento`   | varchar(20)           | NOT NULL                                         |
| `primerNombre`      | varchar(50)           | NOT NULL                                         |
| `segundoNombre`     | varchar(50)           | nullable                                         |
| `primerApellido`    | varchar(50)           | NOT NULL                                         |
| `segundoApellido`   | varchar(50)           | nullable                                         |
| `genero`            | char(1)               | nullable, CHECK IN ('M','F','O')                 |
| `direccion`         | varchar(200)          | nullable                                         |
| `correo`            | varchar(45)           | nullable, CHECK formato email                    |
| `password`          | varchar(255)          | nullable (hash bcrypt)                           |
| `telefono`          | varchar(20)           | nullable                                         |
| `estado`            | boolean               | NOT NULL, DEFAULT true                           |
| `fechaRegistro`     | timestamp             | NOT NULL, DEFAULT now()                          |
| `ultimoAcceso`      | timestamp             | nullable                                         |
| `idRol`             | integer               | NOT NULL, FK → roles.idRol                       |
| `auth_id`           | uuid                  | nullable (Supabase Auth UUID)                    |
| `idUsuario_uuid`    | uuid                  | DEFAULT gen_random_uuid()                        |

---

### 2.2 `roles`
Catálogo de roles del sistema.

| Columna      | Tipo        | Restricciones       |
|--------------|-------------|---------------------|
| `idRol`      | integer     | PK, NOT NULL        |
| `nombreRol`  | varchar(30) | NOT NULL            |

**Valores conocidos:** 1=docente, 2=estudiante, 3=admin, 4=padre

---

### 2.3 `administrador`
Perfil extendido de administrador sobre `usuario`.

| Columna            | Tipo        | Restricciones                                      |
|--------------------|-------------|----------------------------------------------------|
| `idAdministrador`  | integer     | PK, NOT NULL                                       |
| `idUsuario`        | integer     | NOT NULL, FK → usuario.idUsuario                   |
| `cargo`            | varchar(100)| NOT NULL                                           |
| `nivelAcceso`      | varchar(10) | NOT NULL, DEFAULT 'Bajo', CHECK IN (Bajo/Medio/Alto)|
| `estado`           | varchar(10) | NOT NULL, DEFAULT 'Activo', CHECK IN (Activo/Inactivo/Suspendido)|
| `fechaAsignacion`  | date        | NOT NULL, DEFAULT CURRENT_DATE                     |
| `fechaFin`         | date        | nullable, CHECK ≥ fechaAsignacion                  |

---

### 2.4 `profesores`
Perfil extendido de docente.

| Columna            | Tipo        | Restricciones                                            |
|--------------------|-------------|----------------------------------------------------------|
| `idProfesor`       | integer     | PK, NOT NULL                                             |
| `idUsuario`        | integer     | NOT NULL, FK → usuario.idUsuario                         |
| `codigoProfesor`   | varchar(20) | NOT NULL                                                 |
| `titulo`           | varchar(100)| NOT NULL                                                 |
| `nivelEstudios`    | varchar(50) | NOT NULL                                                 |
| `fechaVinculacion` | date        | NOT NULL, CHECK ≤ CURRENT_DATE                           |
| `estado`           | varchar(10) | NOT NULL, DEFAULT 'Activo', CHECK IN (Activo/Inactivo/Vacaciones/Licencia)|
| `fechaRegistro`    | timestamp   | NOT NULL, DEFAULT now()                                  |

---

### 2.5 `estudiantes`
Perfil extendido de estudiante.

| Columna              | Tipo        | Restricciones                                                   |
|----------------------|-------------|-----------------------------------------------------------------|
| `idEstudiante`       | integer     | PK, NOT NULL                                                    |
| `idUsuario`          | integer     | NOT NULL, FK → usuario.idUsuario                                |
| `codigoEstudiante`   | varchar(20) | NOT NULL                                                        |
| `fechaIngreso`       | date        | NOT NULL, CHECK ≤ fechaEgreso                                   |
| `fechaEgreso`        | date        | nullable                                                        |
| `estado`             | varchar(10) | NOT NULL, DEFAULT 'Activo', CHECK IN (Activo/Inactivo/Retirado/Graduado/Suspendido)|
| `idCursoActual`      | integer     | nullable, FK → cursos.idCurso                                   |
| `Horario_idHorario`  | integer     | nullable (referencia sin FK explícita)                          |
| `fechaRegistro`      | timestamp   | NOT NULL, DEFAULT now()                                         |

---

### 2.6 `padres`
Perfil de padre/acudiente, ligado a un estudiante específico.

| Columna        | Tipo        | Restricciones                                          |
|----------------|-------------|--------------------------------------------------------|
| `idPadre`      | integer     | PK, NOT NULL                                           |
| `idUsuario`    | integer     | NOT NULL, FK → usuario.idUsuario                       |
| `idEstudiante` | integer     | NOT NULL, FK → estudiantes.idEstudiante                |
| `parentesco`   | varchar(30) | NOT NULL, CHECK IN (Padre/Madre/Tutor/Abuelo/Otro)     |
| `ocupacion`    | varchar(100)| nullable                                               |

---

### 2.7 `cursos`
Unidad académica de agrupación de estudiantes.

| Columna            | Tipo        | Restricciones                                          |
|--------------------|-------------|--------------------------------------------------------|
| `idCurso`          | integer     | PK, NOT NULL                                           |
| `nombreCurso`      | varchar(30) | NOT NULL                                               |
| `grado`            | varchar(20) | NOT NULL                                               |
| `jornada`          | varchar(10) | NOT NULL, CHECK IN (mañana/tarde/unica/1/2/3/4)        |
| `ano`              | integer     | NOT NULL, CHECK BETWEEN 2000 AND year+10               |
| `area`             | varchar(50) | nullable                                               |
| `intensidadHoraria`| integer     | nullable, CHECK > 0                                    |
| `descripcion`      | text        | nullable                                               |
| `activo`           | boolean     | NOT NULL, DEFAULT true                                 |
| `fechaCreacion`    | timestamp   | NOT NULL, DEFAULT now()                                |

---

### 2.8 `materias`
Catálogo de asignaturas.

| Columna         | Tipo        | Restricciones |
|-----------------|-------------|---------------|
| `idMateria`     | integer     | PK, NOT NULL  |
| `nombreMateria` | varchar(100)| NOT NULL      |
| `codigoMateria` | varchar(20) | NOT NULL      |
| `activa`        | boolean     | NOT NULL, DEFAULT true |

---

### 2.9 `especializaciones`
Catálogo de especializaciones docentes.

| Columna                  | Tipo        | Restricciones          |
|--------------------------|-------------|------------------------|
| `idEspecializacion`      | integer     | PK, NOT NULL           |
| `nombreEspecializacion`  | varchar(100)| NOT NULL               |
| `descripcion`            | text        | nullable               |
| `activo`                 | boolean     | NOT NULL, DEFAULT true |

---

### 2.10 `asignaciones`
Relación profesor–materia–curso (asignación docente).

| Columna              | Tipo      | Restricciones                                         |
|----------------------|-----------|-------------------------------------------------------|
| `idAsignacion`       | integer   | PK, NOT NULL                                          |
| `idProfesor`         | integer   | NOT NULL, FK → profesores.idProfesor                  |
| `idCurso`            | integer   | NOT NULL, FK → cursos.idCurso                         |
| `idMateria`          | integer   | NOT NULL, FK → materias.idMateria                     |
| `fechaAsignacion`    | timestamp | NOT NULL, DEFAULT now()                               |
| `fechaFinalizacion`  | date      | nullable, CHECK ≥ fechaAsignacion                     |
| `activo`             | boolean   | NOT NULL, DEFAULT true                                |

---

### 2.11 `Horario`
Franja horaria de una materia en un curso.

| Columna      | Tipo        | Restricciones                                              |
|--------------|-------------|------------------------------------------------------------|
| `idHorario`  | integer     | PK, NOT NULL                                               |
| `idCurso`    | integer     | NOT NULL, FK → cursos.idCurso                              |
| `idMateria`  | integer     | NOT NULL, FK → materias.idMateria                          |
| `dia`        | varchar(10) | NOT NULL, CHECK IN (Lunes/Martes/Miercoles/Jueves/Viernes) |
| `horaInicio` | time        | NOT NULL, CHECK < horaFin                                  |
| `horaFin`    | time        | NOT NULL                                                   |
| `salon`      | varchar(20) | NOT NULL                                                   |
| `activo`     | boolean     | NOT NULL, DEFAULT true                                     |

---

### 2.12 `profesores_horario`
Asignación de un docente a una franja horaria (tabla pivote).

| Columna           | Tipo      | Restricciones                                         |
|-------------------|-----------|-------------------------------------------------------|
| `idProfesor`      | integer   | NOT NULL, FK → profesores.idProfesor                  |
| `idHorario`       | integer   | NOT NULL, FK → Horario.idHorario                      |
| `fechaAsignacion` | timestamp | NOT NULL, DEFAULT now()                               |
| `activo`          | boolean   | NOT NULL, DEFAULT true                                |

---

### 2.13 `profesorespecializacion`
Tabla pivote entre profesores y especializaciones.

| Columna             | Tipo        | Restricciones                                           |
|---------------------|-------------|--------------------------------------------------------|
| `idProfesor`        | integer     | NOT NULL, FK → profesores.idProfesor                   |
| `idEspecializacion` | integer     | NOT NULL, FK → especializaciones.idEspecializacion     |
| `institucion`       | varchar(100)| NOT NULL                                               |

---

### 2.14 `Asistencia`
Registro de asistencia general (entrada/salida/clase). Soporta escaneo QR.

| Columna         | Tipo        | Restricciones                                                    |
|-----------------|-------------|------------------------------------------------------------------|
| `idAsistencia`  | integer     | PK, NOT NULL                                                     |
| `idEstudiante`  | integer     | NOT NULL, FK → estudiantes.idEstudiante                          |
| `fecha`         | date        | NOT NULL                                                         |
| `estado`        | varchar(15) | NOT NULL, CHECK IN (Presente/Ausente/Tarde/Excusa/Suspensión)    |
| `observacion`   | text        | nullable                                                         |
| `registradoPor` | integer     | NOT NULL, FK → usuario.idUsuario                                 |
| `fechaRegistro` | timestamp   | NOT NULL, DEFAULT now()                                          |
| `tipo`          | text        | nullable, COMMENT: 'entrada,salida,clase'                        |
| `codigo_qr`     | text        | nullable (código QR usado para el registro)                      |
| `activo`        | boolean     | DEFAULT true                                                     |

---

### 2.15 `Asistencia_Aula`
Registro de asistencia por clase específica (asociada a un horario).

| Columna              | Tipo      | Restricciones                                                 |
|----------------------|-----------|---------------------------------------------------------------|
| `idAsistenciaAula`   | integer   | PK, NOT NULL                                                  |
| `idEstudiante`       | integer   | NOT NULL, FK → estudiantes.idEstudiante                       |
| `idHorario`          | integer   | NOT NULL, FK → Horario.idHorario                              |
| `fecha`              | date      | NOT NULL                                                      |
| `estado`             | varchar(15)| NOT NULL                                                     |
| `observacion`        | text      | NOT NULL                                                      |
| `registradoPor`      | integer   | NOT NULL, FK → usuario.idUsuario                              |
| `fechaRegistro`      | timestamp | NOT NULL, DEFAULT now()                                       |

---

### 2.16 `notas`
Calificaciones académicas por período.

| Columna         | Tipo         | Restricciones                              |
|-----------------|--------------|--------------------------------------------|
| `idNota`        | integer      | PK, NOT NULL                               |
| `idEstudiante`  | integer      | NOT NULL, FK → estudiantes.idEstudiante    |
| `idMateria`     | integer      | NOT NULL, FK → materias.idMateria          |
| `idPeriodo`     | integer      | NOT NULL, CHECK BETWEEN 1 AND 4            |
| `nota`          | numeric(4,2) | NOT NULL, CHECK BETWEEN 0 AND 10           |
| `observacion`   | text         | nullable                                   |
| `fechaRegistro` | timestamp    | NOT NULL, DEFAULT now()                    |
| `registradoPor` | integer      | NOT NULL, FK → usuario.idUsuario           |

---

### 2.17 `novedades`
Registro de eventos/incidentes sobre un estudiante.

| Columna             | Tipo        | Restricciones                                             |
|---------------------|-------------|-----------------------------------------------------------|
| `idNovedad`         | integer     | PK, NOT NULL                                              |
| `idEstudiante`      | integer     | NOT NULL, FK → estudiantes.idEstudiante                   |
| `idTipoNovedad`     | integer     | NOT NULL, FK → tiposnovedad.idTipoNovedad                 |
| `fecha`             | date        | NOT NULL, DEFAULT CURRENT_DATE                            |
| `descripcion`       | text        | NOT NULL                                                  |
| `accionTomada`      | text        | nullable                                                  |
| `registradoPor`     | integer     | NOT NULL, FK → usuario.idUsuario                          |
| `fechaResolucion`   | date        | nullable, CHECK ≥ fecha                                   |
| `estado`            | varchar(15) | NOT NULL, DEFAULT 'Pendiente', CHECK IN (Pendiente/En Proceso/Resuelta/Cerrada)|

---

### 2.18 `tiposnovedad`
Catálogo de tipos de novedades/incidentes.

| Columna            | Tipo        | Restricciones                                       |
|--------------------|-------------|-----------------------------------------------------|
| `idTipoNovedad`    | integer     | PK, NOT NULL                                        |
| `nombreTipo`       | varchar(50) | NOT NULL                                            |
| `descripcion`      | text        | nullable                                            |
| `nivelGravedad`    | varchar(10) | NOT NULL, DEFAULT 'Bajo', CHECK IN (Bajo/Medio/Alto/Crítico)|
| `requiereAccion`   | boolean     | NOT NULL, DEFAULT false                             |
| `activo`           | boolean     | NOT NULL, DEFAULT true                              |

---

### 2.19 `estudianteips`
Afiliación de salud (IPS: Institución Prestadora de Servicios de Salud) del estudiante.

| Columna             | Tipo        | Restricciones                                          |
|---------------------|-------------|--------------------------------------------------------|
| `idEstudiante`      | integer     | NOT NULL, FK → estudiantes.idEstudiante (parte de PK) |
| `idIPS`             | integer     | NOT NULL (parte de PK)                                 |
| `nombreIPS`         | varchar(100)| NOT NULL                                               |
| `fechaAfiliacion`   | date        | NOT NULL                                               |
| `fechaVencimiento`  | date        | nullable, CHECK > fechaAfiliacion                      |
| `tipoAfiliacion`    | varchar(20) | NOT NULL, CHECK IN (Contributivo/Subsidiado/Especial)  |
| `activo`            | boolean     | NOT NULL, DEFAULT true                                 |

---

### 2.20 `Reportes`
Registro de reportes generados por administradores.

| Columna             | Tipo         | Restricciones                                                           |
|---------------------|--------------|-------------------------------------------------------------------------|
| `idReporte`         | integer      | PK, NOT NULL                                                            |
| `nombreReporte`     | text         | NOT NULL                                                                |
| `tipoReporte`       | text         | NOT NULL, CHECK IN (Academico/Disciplinario/Medico/Asistencia/Estadistico)|
| `fechaGeneracion`   | date         | NOT NULL, DEFAULT CURRENT_DATE                                          |
| `fechaInicio`       | date         | NOT NULL                                                                |
| `fechaFin`          | date         | NOT NULL, CHECK ≥ fechaInicio                                           |
| `estado`            | text         | NOT NULL, CHECK IN (Pendiente/Procesando/Completado/Error)              |
| `idAdministrador`   | integer      | NOT NULL, FK → administrador.idAdministrador                            |
| `parametros`        | varchar(1)   | NOT NULL (pendiente de expandir en futuras versiones)                   |
| `archivoGenerado`   | varchar(255) | nullable (ruta del archivo generado)                                    |

---

## 3. Relaciones (29 FKs en schema `public`)

```
usuario ──────────────────── roles (idRol)
administrador ─────────────── usuario (idUsuario)
profesores ────────────────── usuario (idUsuario)
estudiantes ───────────────── usuario (idUsuario)
padres ────────────────────── usuario (idUsuario)
padres ────────────────────── estudiantes (idEstudiante)
estudiantes ───────────────── cursos (idCursoActual)
asignaciones ──────────────── profesores (idProfesor)
asignaciones ──────────────── cursos (idCurso)
asignaciones ──────────────── materias (idMateria)
Horario ───────────────────── cursos (idCurso)
Horario ───────────────────── materias (idMateria)
profesores_horario ─────────── profesores (idProfesor)
profesores_horario ─────────── Horario (idHorario)
profesorespecializacion ────── profesores (idProfesor)
profesorespecializacion ────── especializaciones (idEspecializacion)
Asistencia ────────────────── estudiantes (idEstudiante)
Asistencia ────────────────── usuario (registradoPor)
Asistencia_Aula ────────────── estudiantes (idEstudiante)
Asistencia_Aula ────────────── Horario (idHorario)
Asistencia_Aula ────────────── usuario (registradoPor)
notas ─────────────────────── estudiantes (idEstudiante)
notas ─────────────────────── materias (idMateria)
notas ─────────────────────── usuario (registradoPor)
novedades ─────────────────── estudiantes (idEstudiante)
novedades ─────────────────── tiposnovedad (idTipoNovedad)
novedades ─────────────────── usuario (registradoPor)
estudianteips ──────────────── estudiantes (idEstudiante)
Reportes ──────────────────── administrador (idAdministrador)
```

---

## 4. Vistas del schema `public`

| Vista                        | Descripción                                           |
|------------------------------|-------------------------------------------------------|
| `asistencia_por_estudiante`  | % asistencia (Presente/total) agrupado por estudiante |
| `estudiantes_por_curso`      | Total estudiantes activos por curso                   |
| `mejor_estudiante`           | Estudiante con mayor promedio global (LIMIT 1)        |
| `promedio_por_estudiante`    | Promedio de notas por estudiante                      |
| `promedio_total_notas`       | Promedio global de todas las notas                    |

---

## 5. Nodo central: `usuario`

`usuario` es el hub del modelo. Todos los actores (admin, docente, estudiante, padre) son instancias de `usuario` especializadas mediante tablas separadas (patrón Table-Per-Type):

```
        usuario
       /  |  |  \
admin  prof est  padre
```

El campo `auth_id` (uuid) enlaza con Supabase Auth; el campo `password` permite auth directa.
