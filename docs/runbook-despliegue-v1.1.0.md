# Runbook de despliegue — `v1.1.0` a producción

> **Qué cubre:** fusionar el PR #21 (`developer` → `main`), que dispara el despliegue automático a la Web App **`api-eyesschool`** (westus3) y **requiere una migración de base de datos**.
> **Preparado el:** 09/11/2026 · **Commit de `developer`:** `03bebef` · **Migración:** `b7d2e9a41c03`
> **Por qué existe:** el código de `v1.1.0` **no arranca** contra la base de producción actual. Si se fusiona el PR sin migrar antes, el login y el refresh fallan con `relation "sesiones_refresco" does not exist` para todos los usuarios. Es el mismo síntoma que tenía QA (DEF-020).

---

## 1. Qué cambia en la base

La migración `b7d2e9a41c03` (`a1b2c3d4e5f6` → `b7d2e9a41c03`) es **aditiva**: no borra ni altera nada existente.

| Cambio | Detalle | Para qué |
|---|---|---|
| Tabla `sesiones_refresco` | `id`, `jti` único, `idUsuario` FK, `emitido`, `expira`, `revocado` | BE-17: los refrescos salen de Redis y pasan a PostgreSQL |
| Tabla `dispositivos` | `id`, `idUsuario` FK, `tokenFcm` único, `plataforma`, `actualizado` | BE-18: notificaciones push al acudiente |
| `usuario.passwordActualizada` | `DateTime`, **nullable** | BE-13: enlace de recuperación de un solo uso |
| `usuario.intentosFallidos` | `Integer`, `NOT NULL`, **default 0** | BE-16: bloqueo tras 5 intentos |
| `usuario.bloqueadoHasta` | `DateTime`, **nullable** | BE-16 |
| Índices | `ix_sesiones_refresco_idUsuario`, `ix_dispositivos_idUsuario` | — |

## 2. Lo que se probó antes de escribir esto

Todo lo de esta sección se ejecutó el 09/11/2026 contra un PostgreSQL 18.6 local con **la misma estructura y volumen que producción** (21 tablas, 110 usuarios, 103 estudiantes, cargados con `seed_data.sql` y `seed_estudiantes_sinteticos.sql` sobre la revisión `a1b2c3d4e5f6`).

| Prueba | Resultado |
|---|---|
| `alembic upgrade head` sobre base poblada | ✅ **2,9 segundos** |
| Datos después de migrar | ✅ 110 usuarios intactos; `intentosFallidos = 0` en los 110, ningún NULL |
| **Código viejo contra base migrada** | ✅ `INSERT` en `usuario` sin las columnas nuevas funciona (toma los defaults); `SELECT` de las columnas viejas funciona |
| Código nuevo contra base migrada | ✅ login 200 → `/auth/me` 200 → `/usuarios` 200 → refresh 200 → logout 204 → refresh de nuevo **401** |
| Fila escrita en `sesiones_refresco` | ✅ 1 fila, marcada como revocada tras el logout |
| `alembic downgrade -1` | ✅ Vuelve a 21 tablas con los 110 usuarios intactos |
| `alembic upgrade head` otra vez | ✅ Reaplicable |

> **La conclusión que importa:** como el código viejo funciona con la base ya migrada, **se puede migrar primero y fusionar después, sin ventana de caída**. No hay que apagar nada.

## 3. Antes de empezar: en qué revisión está producción

Este es el único dato que no se pudo verificar desde aquí, y de él depende el procedimiento. Con `DATABASE_URL` de producción **fijada en la terminal** (nunca desde el `.env`):

```bash
# PowerShell: $env:DATABASE_URL = Read-Host "DATABASE_URL de produccion"
alembic current
```

| Lo que responde | Qué significa | Qué hacer |
|---|---|---|
| `a1b2c3d4e5f6` | Lo esperado | Siga a la sección 4 |
| `b7d2e9a41c03 (head)` | Ya está migrada | No hace falta migrar; siga al paso 4.4 |
| **Vacío, sin ninguna revisión** | La base se creó desde el dump y no tiene `alembic_version` | **No corra `upgrade head` a ciegas.** Vea la sección 5 |
| `7c1badcb31be` | Le falta también la de `fotoPerfil` | `alembic upgrade head` las aplica las dos en orden; probado |

## 4. Procedimiento

### 4.1 Respaldo (no se salta)

```bash
pg_dump "$DATABASE_URL_PRODUCCION" -Fc -f respaldo-prod-antes-v1.1.0.dump
```

Guárdelo fuera del repositorio. Confirme que el archivo pesa más de unos pocos KB antes de seguir.

### 4.2 Confirmar que apunta a producción y no a QA

```bash
psql "$DATABASE_URL_PRODUCCION" -tAc "select current_database();"
```

Producción y QA **están en el mismo Render**, así que el host no distingue: lo que distingue es el nombre de la base. Si responde `qaeyesschool`, está en QA y se detiene aquí.

### 4.3 Migrar (con el código viejo todavía corriendo)

```bash
alembic upgrade head
alembic current     # debe decir: b7d2e9a41c03 (head)
```

Dura unos 3 segundos. La API sigue funcionando durante y después: está probado.

### 4.4 Variables de entorno de `api-eyesschool`

Antes de fusionar, en Azure → Settings → Environment variables:

| Variable | Qué verificar |
|---|---|
| `SECRET_KEY` | Debe existir y ser fuerte. Con `ENVIRONMENT=production` la API **no arranca** con la clave por defecto (`app/core/config.py`) |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | `postgresql+asyncpg://…?ssl=require`, host **externo** de Render |
| `REDIS_URL` | **Se puede borrar**: BE-17 retiró Redis del sistema |
| `FIREBASE_CREDENTIALS_JSON` | Opcional. Vacía = no se envían notificaciones, pero la API funciona igual (BE-18 registra el error y guarda la novedad) |

### 4.5 Fusionar el PR #21

Resolver el conflicto de `app/api/v1/dashboard.py` con **«Accept incoming change»** (el lado `developer`): corrige BE-03 igual que el hotfix y además trae BE-07.

El merge dispara `main_api-eyesschool.yml`.

### 4.6 Vigilar el primer arranque

Azure → `api-eyesschool` → **Log stream**, mientras el despliegue termina. Lo que no debe aparecer:

| Mensaje | Causa |
|---|---|
| `relation "sesiones_refresco" does not exist` | No se corrió el paso 4.3 |
| `SECRET_KEY` / falla al arrancar | Falta la variable (paso 4.4) |
| `The asyncio extension requires an async driver` | A `DATABASE_URL` le falta `+asyncpg` |

### 4.7 Prueba de humo (sin credenciales en el comando)

```bash
PROD=https://api-eyesschool-hrf2gsg7hyf9dacq.westus3-01.azurewebsites.net/api/v1
curl -s -o /dev/null -w "cursos:  %{http_code}\n" $PROD/cursos/            # 200
curl -s -o /dev/null -w "docs:    %{http_code}\n" ${PROD%/api/v1}/docs      # 200
curl -s -o /dev/null -w "login-:  %{http_code}\n" -X POST $PROD/auth/login \
     -H "Content-Type: application/json" \
     -d '{"correo":"noexiste@example.invalid","password":"x"}'              # 401, NO 500
```

Un **500** en el último es la señal de que la base no está migrada o mal configurada.

Después, un login real por rol (admin, docente, estudiante, acudiente) y que cada inicio cargue. **El inicio del estudiante es el que corrige BE-03**: es la verificación principal de esta versión.

### 4.8 Etiquetar

```bash
git checkout main && git pull
git tag -a v1.1.0 -m "Liberacion v1.1.0: BE-03 a BE-19, BE-17 y BE-INF-1 a BE-INF-4"
git push origin v1.1.0
```

El PR-06 y la UAT necesitan ese commit anotado.

## 5. Si producción no tiene `alembic_version`

Es el caso más peligroso y **se probó**. Si la base se creó desde `schema.sql` (el dump de Supabase) en vez de con Alembic, `alembic current` no devuelve nada y `alembic upgrade head` intenta crear todo desde cero:

```
asyncpg.exceptions.DuplicateTableError: relation "cursos" already exists
```

**No daña la base:** Alembic usa DDL transaccional y revierte el intento completo (comprobado: la base quedó igual). Pero tampoco migra. El arreglo, también comprobado:

```bash
alembic stamp a1b2c3d4e5f6   # declara en qué revisión está, sin tocar las tablas
alembic upgrade head         # ahora sí aplica solo la que falta
```

Antes de hacer `stamp`, confirme que la base tiene las 21 tablas y la columna `usuario.fotoPerfil` (que es lo que agregó `a1b2c3d4e5f6`). Si no tiene `fotoPerfil`, el stamp correcto es `7c1badcb31be`.

## 6. Rollback

### Disparadores (decididos antes, no durante)

- Cualquier 500 en login, refresh o en el inicio de cualquier rol.
- La API no arranca después de dos reintentos del despliegue.
- Errores en el Log stream que mencionen tablas o columnas inexistentes.

### Cómo volver atrás

1. **Primero el código, no la base.** En Azure → `api-eyesschool` → Deployment Center → Logs, elegir el despliegue anterior y *Redeploy*. O `git revert` del merge en `main`, que vuelve a desplegar la versión previa.
2. La base **puede quedarse migrada**: el código viejo funciona con ella (probado en la sección 2). No revierta la migración salvo que haga falta de verdad.
3. Si aun así hay que revertirla: `alembic downgrade a1b2c3d4e5f6`. Elimina `sesiones_refresco`, `dispositivos` y las tres columnas. **Se pierden las sesiones activas** (los usuarios vuelven a entrar) y los tokens de dispositivos registrados.
4. Si algo se corrompió: `pg_restore` del respaldo del paso 4.1.

## 7. Qué les cambia a los usuarios

- **Todas las sesiones activas se cierran.** BE-17 cambia dónde viven los refrescos, así que los tokens emitidos antes del despliegue dejan de servir. Todos vuelven a iniciar sesión una vez. Conviene avisar.
- **Las contraseñas nuevas deben cumplir 5 reglas** (BE-09): 8 caracteres, mayúscula, minúscula, número y carácter especial. Las existentes siguen funcionando.
- **5 intentos fallidos bloquean 15 minutos** (BE-16).
- **El inicio del estudiante y del acudiente vuelve a cargar** (BE-03), que es la razón principal de esta versión.
- Las notas quedan limitadas a 0.0–5.0 (BE-06) y no se aceptan dos entradas o dos salidas el mismo día (BE-08).

## 8. Lo que sigue abierto al momento de este despliegue

- **BE-01: la contraseña de la base de Render no se rotó.** El historial de git se reescribió el 09/11/2026 y gitleaks está en verde, pero las credenciales que estuvieron expuestas **siguen abriendo la base de producción**. Los clones antiguos, los forks y las refs `refs/pull/*/head` de GitHub las conservan. Ver la advertencia de `.gitleaksignore`.
- **El equipo debe volver a clonar** después de la reescritura: un `git pull` sobre un clon viejo falla o reintroduce los commits con el secreto.
- `FIREBASE_CREDENTIALS_JSON` sin configurar: BE-18 no enviará notificaciones.
- Los 21 defectos siguen sin registrar en Azure Boards (PR-07).
