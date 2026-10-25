# EyeSchool — API

API REST de EyeSchool en FastAPI. La consumen la app móvil (Flutter) y el panel web (Next.js). Se despliega en Azure App Service con Python 3.11 y usa PostgreSQL y Redis.

## Cómo correrla

```bash
python -m venv venv
venv\Scripts\activate          # Windows (en Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # y complete DATABASE_URL, SECRET_KEY, etc.
uvicorn main:app --reload
```

La documentación interactiva queda en `http://localhost:8000/docs`.

### Variables de entorno

| Variable | Para qué |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL (`postgresql+asyncpg://…`). |
| `REDIS_URL` | Refresh tokens vigentes: cerrar sesión los borra. |
| `SECRET_KEY` | Firma de los JWT. Use al menos 32 caracteres aleatorios. |
| `ENVIRONMENT` | Con `production`, la API no arranca si `SECRET_KEY` es la de ejemplo. |
| `CORS_ORIGINS` | Orígenes del navegador permitidos, separados por coma. `*` acepta cualquiera, sin cookies. |
| `RESEND_API_KEY`, `MAIL_FROM`, `FRONTEND_URL` | Correo de recuperación de contraseña. |

Ningún script lleva credenciales escritas: `create_admin.py` y `run_seed.py` leen la misma configuración.

## Calidad: lint, pruebas y auditoría

```bash
pip install pytest pytest-asyncio pytest-cov ruff pip-audit
ruff check app main.py tests
pytest --cov=app
pip-audit -r requirements.txt
```

Las pruebas no necesitan base de datos ni Redis: `tests/conftest.py` fija direcciones ficticias antes de importar la app, así que nunca tocan datos reales aunque el `.env` apunte a producción.

| Prueba | Qué verifica |
|---|---|
| `test_authorization.py` | Solo los endpoints públicos declarados aceptan peticiones sin token; los demás responden 401 sin token y 403 con un rol sin permiso. También verifica CORS. |
| `test_register.py` | El registro crea el perfil de cada rol; docentes y administradores quedan inactivos hasta que un administrador los apruebe. |
| `test_security.py` | Hash de contraseñas y tokens: tipo, firma, alteración y vencimiento. |
| `test_config.py` | La configuración rechaza desplegar sin `SECRET_KEY` propia. |
| `test_app.py` | Todas las rutas se montan y los modelos de SQLAlchemy se relacionan bien. |

El workflow [`ci.yml`](.github/workflows/ci.yml) corre lint, pruebas y auditoría en cada pull request. Es el punto de control QG3 del modelo de calidad (MC-01). El despliegue a Azure está en `main_apieyeschool.yml`.

## Estructura

- `app/api/v1/` — routers HTTP, uno por recurso.
- `app/application/<recurso>/` — esquemas Pydantic y servicios con las reglas de negocio.
- `app/infrastructure/` — modelos y repositorios de SQLAlchemy.
- `app/core/` — configuración, seguridad (JWT, bcrypt), dependencias de autenticación y errores.
- `alembic/` — migraciones. `schema.sql` y `seed_data.sql` describen la base.
- `docs/` — análisis de arquitectura, dominio y base de datos.
