# Domain Analysis — Eyes School

> Análisis de dominio derivado de schema.sql (fuente de verdad) y frontend (referencia de casos de uso).

---

## 1. Módulos de dominio

| Módulo              | Tablas principales                              | Rol principal              |
|---------------------|-------------------------------------------------|----------------------------|
| Auth & Usuarios     | `usuario`, `roles`                              | Todos                      |
| Administración      | `administrador`                                 | admin                      |
| Docentes            | `profesores`, `profesorespecializacion`         | admin, docente             |
| Estudiantes         | `estudiantes`, `estudianteips`                  | admin, docente, padre      |
| Familia             | `padres`                                        | admin, padre               |
| Estructura Académica| `cursos`, `materias`, `especializaciones`       | admin                      |
| Asignaciones        | `asignaciones`                                  | admin                      |
| Horarios            | `Horario`, `profesores_horario`                 | admin, docente, estudiante |
| Asistencia          | `Asistencia`, `Asistencia_Aula`                 | admin, docente             |
| Calificaciones      | `notas`                                         | docente, admin             |
| Novedades           | `novedades`, `tiposnovedad`                     | docente, admin             |
| Reportes            | `Reportes`                                      | admin                      |
| Dashboard           | Vistas + joins                                  | Todos (diferenciado)       |

---

## 2. Roles y permisos (RBAC)

### Roles definidos en BD (`roles.idRol`)
| idRol | nombreRol  |
|-------|-----------|
| 1     | docente   |
| 2     | estudiante|
| 3     | admin     |
| 4     | padre     |

### Matriz de permisos por módulo

| Módulo              | admin | docente | estudiante | padre |
|---------------------|-------|---------|------------|-------|
| Gestión usuarios    | CRUD  | -       | -          | -     |
| Administrador       | CRUD  | -       | -          | -     |
| Profesores          | CRUD  | R (own) | -          | -     |
| Estudiantes         | CRUD  | R       | R (own)    | R (hijo)|
| Padres              | CRUD  | -       | -          | R (own)|
| Cursos              | CRUD  | R       | R          | R     |
| Materias            | CRUD  | R       | R          | R     |
| Especializaciones   | CRUD  | R       | -          | -     |
| Asignaciones        | CRUD  | R (own) | -          | -     |
| Horarios            | CRUD  | R       | R          | R     |
| Asistencia          | R     | CRU     | R (own)    | R (hijo)|
| Asistencia Aula     | R     | CRU     | R (own)    | R (hijo)|
| Notas               | R     | CRUD    | R (own)    | R (hijo)|
| Novedades           | CRUD  | CRUD    | R (own)    | R (hijo)|
| Tipos Novedad       | CRUD  | R       | -          | -     |
| Reportes            | CRUD  | -       | -          | -     |
| Dashboard admin     | R     | -       | -          | -     |
| Dashboard docente   | -     | R       | -          | -     |
| Dashboard estudiante| -     | -       | R          | -     |
| Dashboard padre     | -     | -       | -          | R     |

---

## 3. Casos de uso por módulo

### 3.1 Autenticación
- **UC-AUTH-01**: Login con correo y password → JWT (access + refresh)
- **UC-AUTH-02**: Refresh de token de acceso usando refresh token
- **UC-AUTH-03**: Logout (invalida refresh token en Redis)
- **UC-AUTH-04**: Obtener perfil propio (`/me`)
- **UC-AUTH-05**: Actualizar `ultimoAcceso` al login

### 3.2 Usuarios
- **UC-USR-01**: Listar usuarios con filtros (rol, estado, búsqueda por nombre/documento)
- **UC-USR-02**: Crear usuario (hash de password, asignar rol)
- **UC-USR-03**: Obtener usuario por ID
- **UC-USR-04**: Actualizar datos de usuario
- **UC-USR-05**: Activar/desactivar usuario (cambio de `estado`)
- **UC-USR-06**: Usuarios pendientes de validación (estado=false)

### 3.3 Administradores
- **UC-ADM-01**: Crear perfil administrador sobre usuario existente
- **UC-ADM-02**: Listar administradores con estado y nivel de acceso
- **UC-ADM-03**: Actualizar cargo/nivel/estado del administrador

### 3.4 Docentes / Profesores
- **UC-DOC-01**: Crear perfil docente sobre usuario existente
- **UC-DOC-02**: Listar docentes con filtros (estado, especialización)
- **UC-DOC-03**: Ver perfil docente con especializaciones y horarios
- **UC-DOC-04**: Asignar especialización a docente
- **UC-DOC-05**: Quitar especialización de docente
- **UC-DOC-06**: Ver materias asignadas al docente

### 3.5 Estudiantes
- **UC-EST-01**: Crear perfil estudiante con código único
- **UC-EST-02**: Listar estudiantes con filtros (curso, estado)
- **UC-EST-03**: Ver perfil completo (datos + curso + historial)
- **UC-EST-04**: Cambiar curso actual del estudiante
- **UC-EST-05**: Registrar/actualizar afiliación IPS del estudiante
- **UC-EST-06**: Ver historial académico del estudiante

### 3.6 Padres / Acudientes
- **UC-PAD-01**: Crear padre vinculado a un estudiante
- **UC-PAD-02**: Listar padres (admin) o ver perfil propio
- **UC-PAD-03**: Consultar información de su(s) hijo(s)

### 3.7 Cursos
- **UC-CUR-01**: Crear curso con año y jornada
- **UC-CUR-02**: Listar cursos activos con total de estudiantes
- **UC-CUR-03**: Ver estudiantes de un curso
- **UC-CUR-04**: Ver horario completo de un curso

### 3.8 Materias
- **UC-MAT-01**: CRUD básico de catálogo de materias
- **UC-MAT-02**: Activar/desactivar materia

### 3.9 Especializaciones
- **UC-ESP-01**: CRUD de catálogo de especializaciones docentes

### 3.10 Asignaciones docentes
- **UC-ASG-01**: Asignar docente a materia+curso
- **UC-ASG-02**: Listar asignaciones (filtrar por docente, curso, materia)
- **UC-ASG-03**: Finalizar asignación (setear fechaFinalizacion)
- **UC-ASG-04**: Ver carga académica de un docente

### 3.11 Horarios
- **UC-HOR-01**: Crear franja horaria para curso+materia
- **UC-HOR-02**: Asignar docente a franja horaria (`profesores_horario`)
- **UC-HOR-03**: Ver horario semanal de un curso
- **UC-HOR-04**: Ver horario semanal de un docente
- **UC-HOR-05**: Ver horario de un estudiante (por su curso)

### 3.12 Asistencia
Dos tipos de asistencia:
- **`Asistencia`**: entrada/salida/clase (general, vía QR o manual)
- **`Asistencia_Aula`**: por clase específica (ligada a un horario)

Casos de uso:
- **UC-ASI-01**: Registrar asistencia manual (docente/admin)
- **UC-ASI-02**: Registrar asistencia vía QR (escaneo → `codigo_qr`)
- **UC-ASI-03**: Listar asistencias por fecha, estudiante, curso
- **UC-ASI-04**: Ver porcentaje de asistencia de un estudiante
- **UC-ASI-05**: Registrar asistencia de aula (docente por clase)
- **UC-ASI-06**: Exportar resumen de asistencia

### 3.13 Notas / Calificaciones
- **UC-NOT-01**: Registrar nota de un estudiante (materia + período)
- **UC-NOT-02**: Actualizar nota existente
- **UC-NOT-03**: Ver notas de un estudiante por período
- **UC-NOT-04**: Ver promedio por estudiante / materia / período
- **UC-NOT-05**: Ver ranking de estudiantes (mejores promedios)
- **UC-NOT-06**: Exportar boletín de notas

### 3.14 Novedades / Incidentes
- **UC-NOV-01**: Registrar novedad sobre un estudiante
- **UC-NOV-02**: Cambiar estado de novedad (Pendiente → En Proceso → Resuelta → Cerrada)
- **UC-NOV-03**: Listar novedades por estudiante, tipo, estado
- **UC-NOV-04**: CRUD de catálogo de tipos de novedad
- **UC-NOV-05**: Ver novedades del día / semana

### 3.15 Reportes
- **UC-REP-01**: Crear solicitud de reporte (tipo + rango de fechas)
- **UC-REP-02**: Listar reportes generados
- **UC-REP-03**: Descargar archivo de reporte generado
- **UC-REP-04**: Cambiar estado del reporte

### 3.16 Dashboard
- **UC-DASH-01 (admin)**: KPIs globales — total estudiantes, promedio general, tasa aprobación, % asistencia, total novedades activas
- **UC-DASH-02 (docente)**: Sus cursos y estudiantes, notas recientes, asistencia hoy
- **UC-DASH-03 (estudiante)**: Su promedio, su asistencia, próximas clases, novedades
- **UC-DASH-04 (padre)**: Notas, asistencia y novedades de su hijo

---

## 4. Flujos de negocio principales

### 4.1 Registro y activación de usuario
```
Admin crea usuario (estado=false) 
  → Admin activa usuario (estado=true)
  → Sistema envía credenciales
  → Usuario hace login
```

### 4.2 Flujo de asistencia vía QR
```
Docente abre escáner QR
  → Escanea QR del estudiante (codigo_qr)
  → Sistema busca estudiante por codigo_qr
  → Sistema crea registro en Asistencia(tipo='entrada') o Asistencia_Aula
  → Retorna confirmación con nombre del estudiante
```

### 4.3 Flujo de calificaciones por período
```
Docente selecciona curso → materia → período
  → Ingresa notas de cada estudiante (0-10)
  → Sistema valida y guarda
  → Admin puede ver estadísticas en dashboard
  → Padre/estudiante puede consultar su nota
```

### 4.4 Flujo de novedades
```
Docente/Admin detecta incidente
  → Selecciona estudiante + tipo de novedad
  → Registra descripción
  → Estado inicial: 'Pendiente'
  → Admin/Docente actualiza estado + acción tomada
  → Estado final: 'Resuelta' o 'Cerrada'
```

### 4.5 Flujo de asignación docente
```
Admin crea cursos y materias
  → Crea horarios (Horario) para cada curso+materia
  → Crea asignaciones (profesor+curso+materia)
  → Asigna docente a franja horaria (profesores_horario)
```

---

## 5. Restricciones de negocio (extraídas de CHECK constraints)

| Entidad        | Restricción                                              |
|----------------|----------------------------------------------------------|
| `usuario`      | `genero` IN ('M','F','O')                                |
| `usuario`      | `tipoDocumento` IN ('CC','CE','TI','PAS')                |
| `usuario`      | `correo` debe tener formato x@xx.xx                      |
| `administrador`| `nivelAcceso` IN (Bajo/Medio/Alto)                       |
| `administrador`| `fechaFin >= fechaAsignacion`                            |
| `cursos`       | `jornada` IN (mañana/tarde/unica/1/2/3/4)                |
| `cursos`       | `ano` BETWEEN 2000 AND (año actual + 10)                 |
| `Horario`      | `dia` IN (Lunes/Martes/Miercoles/Jueves/Viernes)         |
| `Horario`      | `horaFin > horaInicio`                                   |
| `Asistencia`   | `estado` IN (Presente/Ausente/Tarde/Excusa/Suspensión)   |
| `notas`        | `nota` BETWEEN 0 AND 10                                  |
| `notas`        | `idPeriodo` BETWEEN 1 AND 4                              |
| `tiposnovedad` | `nivelGravedad` IN (Bajo/Medio/Alto/Crítico)             |
| `Reportes`     | `tipoReporte` IN (Academico/Disciplinario/Medico/Asistencia/Estadistico)|
| `Reportes`     | `estado` IN (Pendiente/Procesando/Completado/Error)      |
| `estudianteips`| `tipoAfiliacion` IN (Contributivo/Subsidiado/Especial)   |
| `padres`       | `parentesco` IN (Padre/Madre/Tutor/Abuelo/Otro)          |

---

## 6. Agregados de dominio (DDD)

| Agregado          | Raíz          | Entidades hijas                                    |
|-------------------|---------------|----------------------------------------------------|
| IdentidadUsuario  | `usuario`     | `roles`                                            |
| Administrador     | `administrador`| —                                                 |
| Docente           | `profesores`  | `profesorespecializacion`, `profesores_horario`    |
| Estudiante        | `estudiantes` | `estudianteips`, `padres`                          |
| OfertaAcademica   | `cursos`      | `materias`, `especializaciones`, `asignaciones`    |
| PlanHorario       | `Horario`     | `profesores_horario`                               |
| RegistroAsistencia| `Asistencia`  | `Asistencia_Aula`                                  |
| Calificacion      | `notas`       | —                                                  |
| Novedad           | `novedades`   | `tiposnovedad`                                     |
| Reporte           | `Reportes`    | —                                                  |
