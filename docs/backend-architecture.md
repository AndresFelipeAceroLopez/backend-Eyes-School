# Backend Architecture — Eyes School

---

## 1. Stack tecnológico

| Componente        | Tecnología                    | Versión   |
|-------------------|-------------------------------|-----------|
| Lenguaje          | Python                        | 3.12      |
| Framework HTTP    | FastAPI                       | 0.115+    |
| ORM               | SQLAlchemy (Async)            | 2.x       |
| Migraciones       | Alembic                       | 1.14+     |
| Validación        | Pydantic v2                   | 2.x       |
| Base de datos     | PostgreSQL                    | 15+       |
| Caché / Sesiones  | Redis                         | 7+        |
| Autenticación     | JWT (python-jose + bcrypt)    | —         |
| Servidor ASGI     | Uvicorn                       | —         |

---

## 2. Capas de Clean Architecture

```
┌─────────────────────────────────────────────────────┐
│  API Layer (FastAPI routers)                        │  ← HTTP in/out
│  app/api/v1/                                        │
├─────────────────────────────────────────────────────┤
│  Application Layer (Services + Schemas)             │  ← Use cases
│  app/application/{modulo}/                         │
├─────────────────────────────────────────────────────┤
│  Domain Layer (Entities + Repository Interfaces)   │  ← Business rules
│  app/domain/                                        │
├─────────────────────────────────────────────────────┤
│  Infrastructure Layer (SQLAlchemy + Redis)          │  ← I/O
│  app/infrastructure/                               │
└─────────────────────────────────────────────────────┘
```

### Regla de dependencias
- API → Application → Domain ← Infrastructure
- Domain NO conoce FastAPI, SQLAlchemy ni Redis
- Infrastructure implementa interfaces del Domain

---

## 3. Estructura de directorios

```
app/
├── core/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── database.py         # AsyncEngine + AsyncSession factory
│   ├── redis.py            # Redis async client
│   ├── security.py         # JWT encode/decode, bcrypt hash/verify
│   ├── exceptions.py       # Excepciones de dominio personalizadas
│   └── dependencies.py     # FastAPI DI: get_db, get_current_user, etc.
│
├── domain/
│   ├── entities/           # Pydantic BaseModel (sin ORM)
│   │   ├── usuario.py
│   │   ├── rol.py
│   │   ├── administrador.py
│   │   ├── profesor.py
│   │   ├── estudiante.py
│   │   ├── padre.py
│   │   ├── curso.py
│   │   ├── materia.py
│   │   ├── especializacion.py
│   │   ├── asignacion.py
│   │   ├── horario.py
│   │   ├── asistencia.py
│   │   ├── asistencia_aula.py
│   │   ├── nota.py
│   │   ├── novedad.py
│   │   ├── tipo_novedad.py
│   │   ├── estudiante_ips.py
│   │   └── reporte.py
│   └── repositories/       # ABC interfaces
│       ├── base.py
│       └── {entidad}_repository.py
│
├── infrastructure/
│   ├── models/             # SQLAlchemy ORM models
│   │   ├── base.py         # DeclarativeBase
│   │   └── {tabla}.py
│   └── repositories/       # Implementaciones concretas
│       ├── base_repository.py
│       └── {entidad}_repository.py
│
├── application/            # Servicios + Schemas Pydantic
│   ├── auth/
│   │   ├── service.py
│   │   └── schemas.py
│   ├── usuarios/
│   ├── profesores/
│   ├── estudiantes/
│   ├── cursos/
│   ├── materias/
│   ├── asignaciones/
│   ├── horarios/
│   ├── asistencia/
│   ├── notas/
│   ├── novedades/
│   ├── reportes/
│   └── dashboard/
│
└── api/
    └── v1/
        ├── router.py       # Incluye todos los sub-routers
        ├── auth.py
        ├── usuarios.py
        ├── roles.py
        ├── administradores.py
        ├── profesores.py
        ├── estudiantes.py
        ├── padres.py
        ├── cursos.py
        ├── materias.py
        ├── especializaciones.py
        ├── asignaciones.py
        ├── horarios.py
        ├── asistencia.py
        ├── notas.py
        ├── novedades.py
        ├── reportes.py
        └── dashboard.py
```

---

## 4. Endpoints API v1

### Auth
| Método | Ruta                     | Descripción                        | Rol     |
|--------|--------------------------|------------------------------------|---------|
| POST   | /auth/login              | Login → JWT tokens                 | Todos   |
| POST   | /auth/refresh            | Renovar access token               | Todos   |
| POST   | /auth/logout             | Invalida refresh token             | Todos   |
| GET    | /auth/me                 | Perfil del usuario autenticado     | Todos   |

### Usuarios
| Método | Ruta                     | Descripción                        | Rol     |
|--------|--------------------------|------------------------------------|---------|
| GET    | /usuarios                | Listar con filtros                 | admin   |
| POST   | /usuarios                | Crear usuario                      | admin   |
| GET    | /usuarios/{id}           | Obtener por ID                     | admin   |
| PUT    | /usuarios/{id}           | Actualizar                         | admin   |
| PATCH  | /usuarios/{id}/estado    | Activar/desactivar                 | admin   |

### Roles
| Método | Ruta                     | Descripción                        | Rol     |
|--------|--------------------------|------------------------------------|---------|
| GET    | /roles                   | Listar roles                       | admin   |

### Administradores
| Método | Ruta                     | Descripción                        | Rol     |
|--------|--------------------------|------------------------------------|---------|
| GET    | /administradores         | Listar                             | admin   |
| POST   | /administradores         | Crear perfil admin                 | admin   |
| GET    | /administradores/{id}    | Obtener                            | admin   |
| PUT    | /administradores/{id}    | Actualizar                         | admin   |

### Profesores
| Método | Ruta                              | Descripción                | Rol            |
|--------|-----------------------------------|----------------------------|----------------|
| GET    | /profesores                       | Listar                     | admin          |
| POST   | /profesores                       | Crear perfil docente        | admin          |
| GET    | /profesores/{id}                  | Obtener con especializaciones | admin, docente|
| PUT    | /profesores/{id}                  | Actualizar                 | admin          |
| GET    | /profesores/{id}/asignaciones     | Ver materias asignadas      | admin, docente |
| GET    | /profesores/{id}/horarios         | Ver horarios               | admin, docente |
| POST   | /profesores/{id}/especializaciones| Agregar especialización    | admin          |
| DELETE | /profesores/{id}/especializaciones/{esp_id} | Quitar           | admin          |

### Estudiantes
| Método | Ruta                          | Descripción                   | Rol                   |
|--------|-------------------------------|-------------------------------|-----------------------|
| GET    | /estudiantes                  | Listar con filtros             | admin, docente        |
| POST   | /estudiantes                  | Crear perfil                   | admin                 |
| GET    | /estudiantes/{id}             | Obtener                        | admin, docente, padre |
| PUT    | /estudiantes/{id}             | Actualizar                     | admin                 |
| GET    | /estudiantes/{id}/notas       | Ver notas                      | admin, docente, estudiante, padre |
| GET    | /estudiantes/{id}/asistencia  | Ver asistencia                 | admin, docente, estudiante, padre |
| GET    | /estudiantes/{id}/novedades   | Ver novedades                  | admin, docente, padre |
| GET    | /estudiantes/{id}/ips         | Ver afiliación IPS             | admin                 |
| POST   | /estudiantes/{id}/ips         | Registrar/actualizar IPS       | admin                 |

### Padres
| Método | Ruta               | Descripción            | Rol           |
|--------|--------------------|------------------------|---------------|
| GET    | /padres            | Listar                 | admin         |
| POST   | /padres            | Crear                  | admin         |
| GET    | /padres/{id}       | Obtener                | admin, padre  |
| PUT    | /padres/{id}       | Actualizar             | admin         |

### Cursos
| Método | Ruta                       | Descripción               | Rol    |
|--------|----------------------------|---------------------------|--------|
| GET    | /cursos                    | Listar activos            | Todos  |
| POST   | /cursos                    | Crear                     | admin  |
| GET    | /cursos/{id}               | Obtener                   | Todos  |
| PUT    | /cursos/{id}               | Actualizar                | admin  |
| GET    | /cursos/{id}/estudiantes   | Ver estudiantes           | admin, docente |
| GET    | /cursos/{id}/horarios      | Ver horario semanal       | Todos  |

### Materias
| Método | Ruta               | Descripción   | Rol   |
|--------|--------------------|---------------|-------|
| GET    | /materias          | Listar        | Todos |
| POST   | /materias          | Crear         | admin |
| GET    | /materias/{id}     | Obtener       | Todos |
| PUT    | /materias/{id}     | Actualizar    | admin |

### Especializaciones
| Método | Ruta                      | Descripción   | Rol   |
|--------|---------------------------|---------------|-------|
| GET    | /especializaciones        | Listar        | admin, docente |
| POST   | /especializaciones        | Crear         | admin |
| GET    | /especializaciones/{id}   | Obtener       | admin |
| PUT    | /especializaciones/{id}   | Actualizar    | admin |

### Asignaciones
| Método | Ruta                   | Descripción         | Rol   |
|--------|------------------------|---------------------|-------|
| GET    | /asignaciones          | Listar con filtros  | admin, docente |
| POST   | /asignaciones          | Crear               | admin |
| GET    | /asignaciones/{id}     | Obtener             | admin, docente |
| PUT    | /asignaciones/{id}     | Actualizar          | admin |
| DELETE | /asignaciones/{id}     | Eliminar (soft)     | admin |

### Horarios
| Método | Ruta                  | Descripción       | Rol   |
|--------|-----------------------|-------------------|-------|
| GET    | /horarios             | Listar con filtros| Todos |
| POST   | /horarios             | Crear franja      | admin |
| GET    | /horarios/{id}        | Obtener           | Todos |
| PUT    | /horarios/{id}        | Actualizar        | admin |
| DELETE | /horarios/{id}        | Eliminar (soft)   | admin |
| POST   | /horarios/{id}/profesores | Asignar docente| admin |

### Asistencia
| Método | Ruta                        | Descripción                 | Rol          |
|--------|-----------------------------|-----------------------------|--------------|
| GET    | /asistencia                 | Listar con filtros          | admin, docente |
| POST   | /asistencia                 | Registrar manual            | admin, docente |
| POST   | /asistencia/qr              | Registrar por QR            | docente      |
| GET    | /asistencia/{id}            | Obtener                     | admin, docente |
| PUT    | /asistencia/{id}            | Actualizar                  | admin, docente |
| GET    | /asistencia/aula            | Listar asistencia de aula   | admin, docente |
| POST   | /asistencia/aula            | Registrar asistencia aula   | docente      |

### Notas
| Método | Ruta             | Descripción             | Rol         |
|--------|------------------|-------------------------|-------------|
| GET    | /notas           | Listar con filtros      | admin, docente |
| POST   | /notas           | Registrar nota          | docente     |
| GET    | /notas/{id}      | Obtener                 | admin, docente |
| PUT    | /notas/{id}      | Actualizar              | docente     |
| DELETE | /notas/{id}      | Eliminar                | admin       |

### Novedades
| Método | Ruta                      | Descripción         | Rol          |
|--------|---------------------------|---------------------|--------------|
| GET    | /novedades                | Listar con filtros  | admin, docente |
| POST   | /novedades                | Registrar           | admin, docente |
| GET    | /novedades/{id}           | Obtener             | admin, docente |
| PUT    | /novedades/{id}           | Actualizar          | admin, docente |
| DELETE | /novedades/{id}           | Eliminar            | admin        |
| GET    | /tipos-novedad            | Listar tipos        | admin, docente |
| POST   | /tipos-novedad            | Crear tipo          | admin        |
| PUT    | /tipos-novedad/{id}       | Actualizar tipo     | admin        |

### Reportes
| Método | Ruta                         | Descripción         | Rol   |
|--------|------------------------------|---------------------|-------|
| GET    | /reportes                    | Listar              | admin |
| POST   | /reportes                    | Crear solicitud     | admin |
| GET    | /reportes/{id}               | Obtener estado      | admin |
| GET    | /reportes/{id}/descargar     | Descargar archivo   | admin |
| PATCH  | /reportes/{id}/estado        | Cambiar estado      | admin |

### Dashboard
| Método | Ruta                 | Descripción                  | Rol        |
|--------|----------------------|------------------------------|------------|
| GET    | /dashboard/admin     | KPIs globales                | admin      |
| GET    | /dashboard/docente   | Dashboard docente            | docente    |
| GET    | /dashboard/estudiante| Dashboard estudiante         | estudiante |
| GET    | /dashboard/padre     | Dashboard padre              | padre      |

---

## 5. Estrategia de autenticación

### JWT
- **Access token**: TTL 30 min, payload: `{sub: idUsuario, rol: nombreRol, idRol: int}`
- **Refresh token**: TTL 7 días, almacenado en Redis (key: `refresh:{token_jti}`)
- En logout: el JTI del refresh token se elimina de Redis

### Validación de permisos
```python
# Dependency injection en FastAPI
get_current_user → verifica JWT → retorna UsuarioEntity
require_roles(["admin", "docente"]) → valida rol del usuario actual
```

---

## 6. Estrategia de caché (Redis)

| Clave                          | TTL     | Contenido                        |
|--------------------------------|---------|----------------------------------|
| `refresh:{jti}`                | 7 días  | idUsuario (refresh token válido) |
| `user:{idUsuario}`             | 5 min   | Datos del perfil del usuario     |
| `dashboard:admin`              | 2 min   | KPIs del dashboard admin         |
| `dashboard:docente:{id}`       | 2 min   | Dashboard de un docente          |
| `cursos:activos`               | 10 min  | Lista de cursos activos          |
| `materias:activas`             | 10 min  | Lista de materias activas        |

---

## 7. Manejo de errores

| Código | Excepción                 | Descripción                            |
|--------|---------------------------|----------------------------------------|
| 400    | `ValidationError`         | Datos inválidos (Pydantic)             |
| 401    | `UnauthorizedException`   | Token inválido / expirado              |
| 403    | `ForbiddenException`      | Sin permisos para el recurso           |
| 404    | `NotFoundException`       | Recurso no encontrado                  |
| 409    | `ConflictException`       | Conflicto (duplicado de documento/correo)|
| 422    | FastAPI default           | Error de validación de request body   |
| 500    | `InternalServerError`     | Error inesperado del servidor          |

---

## 8. Configuración de entorno

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/eyesschool
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<clave secreta JWT>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
```

---

## 9. Convenciones de código

- **Repository Pattern**: cada entidad tiene su propio repositorio
- **Service Layer**: toda lógica de negocio vive en services, no en routers
- **Dependency Injection**: `get_db`, `get_current_user`, `get_{service}` via FastAPI DI
- **Naming**: snake_case para Python, camelCase preservado en mapeos SQL
- **Paginación**: query params `skip` y `limit` en todos los listados
- **Respuestas**: siempre Pydantic schemas, nunca ORM objects directamente
