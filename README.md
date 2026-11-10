# EyeSchool — API

API REST de EyeSchool en FastAPI. La consumen la app móvil (Flutter) y el panel web (Next.js). Se despliega en Azure App Service con Python 3.11 y usa PostgreSQL.

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
| `SECRET_KEY` | Firma de los JWT. Use al menos 32 caracteres aleatorios. |
| `ENVIRONMENT` | Con `production`, la API no arranca si `SECRET_KEY` es la de ejemplo. |
| `CORS_ORIGINS` | Orígenes del navegador permitidos, separados por coma. `*` acepta cualquiera, sin cookies. |
| `RESEND_API_KEY`, `MAIL_FROM`, `FRONTEND_URL` | Correo de recuperación de contraseña. |
| `FIREBASE_CREDENTIALS_JSON` | Cuenta de servicio de Firebase para las notificaciones push al acudiente. Solo en Azure; vacía = no se envían. |

Ningún script lleva credenciales escritas: `create_admin.py` y `run_seed.py` leen la misma configuración.

## Calidad: lint, pruebas y auditoría

```bash
pip install pytest pytest-asyncio pytest-cov ruff pip-audit
ruff check app main.py tests scripts
pytest --cov=app                       # unitarias (no necesitan base de datos)
pip-audit -r requirements.txt
```

Las pruebas unitarias no necesitan base de datos: `tests/conftest.py` fija direcciones ficticias antes de importar la app, así que nunca tocan datos reales aunque el `.env` apunte a producción.

Las pruebas de integración (`pytest -m integration`) usan un PostgreSQL **desechable** indicado en `TEST_DATABASE_URL` (el `DATABASE_URL` del `.env` se ignora a propósito):

```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=eyes_test postgres:18
TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/eyes_test pytest -m integration
```

Sin Docker sirve PostgreSQL 18 nativo: `winget install PostgreSQL.PostgreSQL.18 --custom '--mode unattended --superpassword test --serverport 5432'` y después `createdb -U postgres eyes_test`. **Si `TEST_DATABASE_URL` no está definida las pruebas de integración se omiten en silencio** (`53 skipped`), así que hay que revisar el conteo y no solo que no haya fallos.

La guía completa de pruebas (qué archivo cubre cada corrección, Newman, k6, análisis estático) está en [`tests/README.md`](tests/README.md). Los resultados de cada corrida van en [`docs/test/Resultados/`](docs/test/Resultados/) y las planeaciones de QA en [`docs/test/`](docs/test/).

El workflow [`ci.yml`](.github/workflows/ci.yml) corre lint, pruebas unitarias y de integración (PostgreSQL 18), auditoría de dependencias, SonarQube Cloud y detección de secretos en cada pull request. Es el punto de control QG3 del modelo de calidad (MC-01). El despliegue a Azure está en `main_apieyeschool.yml`.

## Estructura

- `app/api/v1/` — routers HTTP, uno por recurso.
- `app/application/<recurso>/` — esquemas Pydantic y servicios con las reglas de negocio.
- `app/infrastructure/` — modelos y repositorios de SQLAlchemy.
- `app/core/` — configuración, seguridad (JWT, bcrypt), dependencias de autenticación y errores.
- `alembic/` — migraciones. `schema.sql` y `seed_data.sql` describen la base.
- `docs/` — análisis de arquitectura, dominio y base de datos.
