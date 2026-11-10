# Planeación del análisis estático — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** planeación de QA para el PR-03 (Informe de análisis estático de código). Describe qué se va a analizar, con qué herramientas y comandos, contra qué umbrales y dónde queda cada resultado. No contiene resultados: se llenan al ejecutar.
> **Pensado para:** cualquier integrante del equipo o una IA que no conoce el proyecto. Las rutas, la configuración y el CI se verificaron contra el repositorio el 02/11/2026.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Plazo:** preparación en S7 (hasta el 6 nov 2026) y ejecución en S8 (7 – 14 nov 2026), según el cronograma del PR-01.
> **Actualizado el 09/11/2026 (corrida E1 ejecutada):** la regla propia de gitleaks quedó **validada** y encontró **6 secretos**, no solo en `.env` sino también en **`create_admin.py`**, y con commits distintos a los que decía BE-01 (ver BE-SA-2 y la sección 7). `gitleaks` solo alcanzó 23 de los 41 commits de la rama en el clon local, así que la corrida que vale para el PR-03 es la del CI con `fetch-depth: 0`. Las herramientas y comandos de BE-SA-3 se dejaron automatizados en `scripts/qa/correr_estatico.sh`. Los resultados de la corrida están en [`../Resultados/corrida-2026-11-09.md`](../Resultados/corrida-2026-11-09.md), no en esta planeación.

---

## 1. Objetivo y alcance

El análisis estático revisa el código **sin ejecutarlo**: estilo y errores con ruff, seguridad con bandit, complejidad, duplicación, secretos, dependencias vulnerables y calidad general en SonarQube Cloud. Sus resultados alimentan el PR-03 y se comparan con los umbrales del MC-01.

| Entra | No entra |
|---|---|
| `app/` y `main.py` (código de producción) | `alembic/versions/` (migraciones generadas) y `static/` |
| `tests/` solo para ruff, como hace el CI | Escaneo dinámico con OWASP ZAP: va en el PR-06 (CP-NF-003) |
| `requirements.txt` (dependencias) | Pruebas unitarias e integración: PR-04 y PR-05 |
| Historial completo de git y los archivos `.sql` de la raíz (secretos) | |

## 2. Contexto técnico

| Dato | Valor |
|---|---|
| Repositorio | `github.com/AndresFelipeAceroLopez/backend-Eyes-School` (público) |
| Rama y commit a analizar | `chore/calidad-seguridad` · `0af4531` (25/10/2026). Si para el 7 nov ya existe `develop` con las correcciones de S7, se analiza `develop` y se anota el commit exacto en el PR-03 |
| Lenguaje | Python 3.11 (FastAPI, SQLAlchemy async, Pydantic v2) |
| Reglas de ruff del repositorio | `pyproject.toml`: `select = ["E", "F", "I", "N", "W"]`, `extend-ignore = ["E501"]` (164 líneas largas heredadas), `line-length = 100`, `target-version = "py311"` |
| CI actual | `.github/workflows/ci.yml`, job «Lint, pruebas y auditoria»: `ruff check app main.py tests` → `pytest -q --cov=app --cov-report=xml` → `pip-audit -r requirements.txt`. Corre en PR y en push a `developer` y `main` |
| Línea base (MC-01, 25/10/2026) | ruff: 0 hallazgos · pip-audit: 0 vulnerabilidades · cobertura de líneas 61 % · 4,2 KLOC |

## 3. Qué se mide

| # | Métrica | Herramienta | Umbral | Dónde va en el PR-03 |
|---|---|---|---|---|
| B1 | Hallazgos con las reglas del CI | `ruff check` (configuración del repositorio) | 0 (MC-01) | Tablas 1 y 2 |
| B2 | Hallazgos con un perfil ampliado (bugbear, seguridad, complejidad, simplificación, pylint) | `ruff check --select …` | Informativo: entra al plan de remediación | Tabla 2 |
| B3 | Problemas de seguridad en el código | `bandit` | 0 de severidad alta o media sin justificar | Tablas 1 y 4 |
| B4 | Calificaciones, bugs, vulnerabilidades, hotspots, code smells, complejidad cognitiva, deuda técnica | SonarQube Cloud | Métrica adicional del MC-01 (Quality Gate «Sonar way» como referencia) | Tablas 1, 2 y 3; captura en la sección 3 |
| B5 | Complejidad ciclomática por función | `lizard 1.25.0` (y `radon cc` como contraste) | Informativa: funciones con CCN > 15 | Tabla 2 |
| B6 | Duplicación | `jscpd 4.3.0` | ≤ 3 % (MC-01) | Tablas 1 y 2 |
| B7 | Líneas de código | `pygount` y líneas físicas de jscpd | — | Tablas 2 y 3 |
| B8 | Secretos en el código y en el historial | `gitleaks 8.24.2` con regla propia (ver BE-SA-2) | 0 secretos sin rotar y documentar | Tablas 1 y 4 |
| B9 | Dependencias vulnerables | `pip-audit` | 0 críticas o altas (MC-01) | Tabla 1 |
| B10 | Cobertura de líneas (dato de entrada para SonarQube) | `pytest --cov` | ≥ 60 % (MC-01) | Tablas 1 y 2 |

## 4. Preparación (S7, hasta el 6 nov)

### BE-SA-1 · SonarQube Cloud (es parte de BE-INF-3 de la planeación de correcciones)

1. Importar `backend-Eyes-School` en la misma organización de SonarQube Cloud que la app y la web. Clave sugerida: `AndresFelipeAceroLopez_backend-Eyes-School`.
2. Desactivar «Automatic Analysis»; crear el secreto `SONAR_TOKEN` en GitHub.
3. `sonar-project.properties`:
   - `sonar.sources=app,main.py`
   - `sonar.tests=tests`
   - `sonar.python.version=3.11`
   - `sonar.python.coverage.reportPaths=coverage.xml` (el CI ya genera `coverage.xml`)
   - `sonar.exclusions=alembic/**,static/**`
4. En `ci.yml`, después de «Tests», el paso `SonarSource/sonarqube-scan-action` con `env: SONAR_TOKEN`.
5. Agregar `develop` a las ramas de `push` del CI: hoy solo están `developer` y `main`, y la estrategia de ramas usa `develop`.

### BE-SA-2 · gitleaks con regla propia

- Job en `ci.yml` con `gitleaks/gitleaks-action` y `fetch-depth: 0`.
- Archivo `.gitleaks.toml` que extiende las reglas por defecto (`[extend] useDefault = true`) y agrega una regla para **URLs de conexión con usuario y contraseña** (`postgresql://usuario:clave@host`, también con `+asyncpg`). Motivo: el incidente BE-01 es justamente un `DATABASE_URL` de Render en el historial y la herramienta debe detectarlo sí o sí.
- **Prueba de la regla:** correr `gitleaks git .` y confirmar que reporta el `.env` de los commits de junio de 2026 señalados en BE-01. Si no lo reporta, la regla está mal y se ajusta antes de confiar en el CI.
- **Resultado de la prueba de la regla (09/11/2026, gitleaks 8.24.2): la regla funciona.** Reportó 6 hallazgos, con dos correcciones a lo que decía BE-01:

| Regla | Archivo | Commit | Fecha | Autor |
|---|---|---|---|---|
| `url-conexion-con-credenciales` | `.env` | `6fdf2cc` | 12/06/2026 | NoaTakeshi |
| `secret-key-en-env` | `.env` | `ccaec1c` | 12/06/2026 | NoaTakeshi |
| `url-conexion-con-credenciales` | `.env` | `db5565c` | 22/06/2026 | NoaTakeshi |
| `url-conexion-con-credenciales` | `.env` | `e21775a` | 24/06/2026 | Zharick Rodriguez |
| `url-conexion-con-credenciales` | **`create_admin.py`** | `6fdf2cc` | 12/06/2026 | NoaTakeshi |
| `url-conexion-con-credenciales` | **`create_admin.py`** | `476c0de` | 02/07/2026 | NoaTakeshi |

  1. **El alcance de BE-01 es mayor:** `create_admin.py` también traía la `DATABASE_URL` con usuario y contraseña, y `476c0de` es el commit que está en `main`, es decir **en producción**. Una limpieza del historial con `git filter-repo --path .env` no basta: hay que incluir `create_admin.py`. En la rama de trabajo ese archivo ya lee la URL de `settings` (línea 17), así que el riesgo vivo es el historial y el archivo de `main`.
  2. **Los commits de BE-01 estaban mal:** no son `847a48c` ni `c5621f7`, sino `6fdf2cc`, `ccaec1c`, `db5565c`, `e21775a` y `476c0de`.
- **Cobertura del escaneo:** en el clon local `gitleaks git .` informó «23 commits scanned» aunque la rama tiene 41, incluso con `--log-opts="--all"`: el clon no tiene todas las ramas remotas. **La corrida válida para el PR-03 es la del CI**, con `fetch-depth: 0`; la local sirve solo para validar la regla.
- Una vez rotados los secretos (acciones de BE-01), los hallazgos históricos se agregan a la lista permitida por huella (`.gitleaksignore`), con la fecha de la rotación. Así el CI queda en verde sin ocultar hallazgos nuevos. **Mientras no se roten, el Quality Gate de la sección 6 está en rojo por B8** (es el único control de E1 que no pasó).

### BE-SA-3 · Herramientas locales de quien ejecuta

- Python 3.11 en un entorno virtual con `pip install -r requirements.txt pytest pytest-asyncio pytest-cov ruff bandit pip-audit lizard==1.25.0 radon pygount`.
- VS Code con las extensiones Python y Ruff; Node.js para `npx jscpd@4.3.0`; binario `gitleaks` 8.24.2 desde GitHub Releases.
- Carpeta de evidencias: `evidencias/PR-03/api/` (unidad compartida del equipo, no en el repositorio).

**Instalación verificada en Windows el 09/11/2026.** Los 10 pasos de la sección 5 están automatizados en `scripts/qa/correr_estatico.sh` (`bash scripts/qa/correr_estatico.sh E1`), que usa `set -uo pipefail` y por eso **no se detiene si falta una herramienta**: hay que leer su salida para confirmar que ninguna se saltó.

| Herramienta | Cómo se instaló | Versión usada en E1 |
|---|---|---|
| ruff, bandit, pip-audit | Ya estaban en el `venv` del proyecto | Python 3.11.9 · ruff 0.17.3 · bandit 1.9.4 · pip-audit 2.10.1 |
| lizard, radon, pygount | `venv/Scripts/python -m pip install "lizard==1.25.0" radon pygount` (faltaban) | lizard 1.25.0 |
| jscpd | `npx jscpd@4.3.0` (lo descarga Node.js al correr) | 4.3.0 |
| **gitleaks** | `winget install Gitleaks.Gitleaks --version 8.24.2` (más simple que bajar el zip de GitHub Releases) | 8.24.2 |

En Windows, `winget` deja `gitleaks.exe` en `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gitleaks.Gitleaks_Microsoft.Winget.Source_8wekyb3d8bbwe\` y **no** en los *Links* del PATH, así que hay que agregar esa carpeta al PATH de la terminal antes de correr el script, o `gitleaks` se salta sin fallar la corrida (fue lo que pasó en el primer intento de E1).

## 5. Ejecución (S8)

| Corrida | Fecha | Qué mide |
|---|---|---|
| E1 · línea base del PR-03 | 7 nov 2026 | El estado al empezar S8 (commit anotado) |
| E2 · después de correcciones | 13 nov 2026 | Con BE-01 a BE-18 de S7 y S8 fusionadas; alimenta la sección 8 (evolución) del PR-03 |

Pasos de cada corrida, desde la raíz del repositorio con el entorno virtual activo:

```bash
# 0. Commit y versiones
git rev-parse --short HEAD                > evidencias/PR-03/api/E1_commit.txt
python --version; ruff --version; bandit --version; pip-audit --version > evidencias/PR-03/api/E1_versiones.txt

# 1. Reglas del CI (B1)
ruff check app main.py tests              > evidencias/PR-03/api/E1_ruff_ci.txt

# 2. Perfil ampliado, informativo (B2)
ruff check app main.py --select E,F,W,I,N,B,S,C90,SIM,UP,PL,RET,ARG,BLE,TRY --ignore E501 \
     --output-format json                 > evidencias/PR-03/api/E1_ruff_ampliado.json
ruff check app main.py --select E,F,W,I,N,B,S,C90,SIM,UP,PL,RET,ARG,BLE,TRY --ignore E501 --statistics \
                                          > evidencias/PR-03/api/E1_ruff_ampliado_resumen.txt

# 3. Seguridad del código (B3)
bandit -r app main.py -f json -o evidencias/PR-03/api/E1_bandit.json
bandit -r app main.py                     > evidencias/PR-03/api/E1_bandit.txt

# 4. Complejidad y tamaño (B5, B7)
lizard app main.py -l python --csv        > evidencias/PR-03/api/E1_lizard.csv
lizard app main.py -l python -C 15 -w     > evidencias/PR-03/api/E1_lizard_ccn15.txt
radon cc -s -a app main.py                > evidencias/PR-03/api/E1_radon_cc.txt
pygount --format=summary app main.py      > evidencias/PR-03/api/E1_loc.txt

# 5. Duplicación (B6)
npx jscpd@4.3.0 app --min-lines 5 --min-tokens 50 --reporters json,console --output evidencias/PR-03/api/E1_jscpd

# 6. Secretos en todo el historial (B8); --redact evita mostrar valores
gitleaks git . --redact --config .gitleaks.toml --report-format json --report-path evidencias/PR-03/api/E1_gitleaks.json

# 7. Dependencias (B9)
pip-audit -r requirements.txt -f json -o evidencias/PR-03/api/E1_pip_audit.json

# 8. Cobertura (B10)
pytest -q --cov=app --cov-report=term --cov-report=xml > evidencias/PR-03/api/E1_cobertura.txt
```

9. **SonarQube Cloud (B4):** con el CI ya corrido sobre la rama analizada, guardar la captura del Overview, la lista de Issues Blocker y Critical, la lista de Security Hotspots y los valores de Technical Debt y Debt Ratio (Measures → Maintainability).
10. **Revisión de secretos fuera de los patrones:** abrir `seed_data.sql` y revisar el comentario de las líneas 29–33 (hallazgo H-08). No se copia ninguna contraseña a las evidencias: solo se registra si sigue o no en el archivo.

En E2 se repiten los pasos con el prefijo `E2_`.

## 6. Criterio de aprobación (Quality Gate de la API)

| Condición | Umbral | Origen |
|---|---|---|
| Hallazgos de ruff con las reglas del CI | 0 | MC-01 / QG3 |
| Vulnerabilidades críticas o altas en código y dependencias (incluye secretos sin rotar) | 0 | MC-01 |
| Hallazgos de bandit de severidad alta | 0 | Este plan (refuerza el umbral de seguridad del MC-01) |
| Duplicación | ≤ 3 % | MC-01 |
| Cobertura de líneas | ≥ 60 % | MC-01 |
| Quality Gate de SonarQube Cloud | Aprobado (métrica adicional) | MC-01, sección de instrumentos |

El perfil ampliado de ruff y las funciones con CCN > 15 no bloquean: entran al plan de remediación del PR-03.

## 7. Revisión dirigida (hallazgos ya conocidos que el análisis debe confirmar)

| Ref. | Qué revisar | Dónde | Herramienta que debería detectarlo |
|---|---|---|---|
| BE-01 | `.env` con `DATABASE_URL` de Render y `SECRET_KEY` en el historial | Commits `6fdf2cc`, `ccaec1c`, `db5565c` y `e21775a` (jun 2026) | gitleaks con la regla propia de BE-SA-2. **Confirmado el 09/11/2026: 4 hallazgos** |
| BE-01 (ampliado) | `DATABASE_URL` con usuario y contraseña **embebida en `create_admin.py`** | Commits `6fdf2cc` y `476c0de`; `476c0de` está en `main`, o sea en producción | gitleaks. **Hallazgo nuevo del 09/11/2026**: no estaba en BE-01 y cambia el alcance de la limpieza del historial |
| H-08 | Contraseñas de usuarios de prueba en un comentario | `seed_data.sql`, líneas 29–33 | Revisión manual (no tiene un patrón fijo). **Verificado el 09/11/2026: ya no están** |
| BE-17 / BE-13 | `try/except Exception: pass` alrededor de Redis: si Redis falla, la revocación de sesiones se desactiva sin aviso | `app/application/auth/service.py`, bloques de `login`, `refresh` y `logout` | bandit (B110) y ruff (S110, BLE001) |
| BE-14 | Avatares sin validar tipo ni tamaño | `AuthService.upload_avatar` | SonarQube Cloud (hotspot) o revisión manual |
| BE-15 | `/static` montado completo como público | `main.py` | Revisión manual |
| BE-01 | Clave por defecto `change-me-in-production` | `app/core/config.py` | bandit (B105) y ruff (S105). Es esperado: la API no arranca en producción con ella (`tests/test_config.py`) |

## 8. Registro de hallazgos

- Todo secreto, toda vulnerabilidad alta o crítica (bandit, pip-audit o SonarQube) y todo issue Blocker o Critical de SonarQube se registra como **Bug en Azure Boards** con la etiqueta `analisis-estatico`, y va en la Tabla 4 del PR-03 y luego en el PR-07.
- Si el hallazgo ya tiene corrección en la planeación (BE-xx), el bug se enlaza a esa corrección; no se crea otra.
- Los hallazgos del perfil ampliado y la complejidad entran al plan de remediación (sección 7 del PR-03).
- Los falsos positivos se marcan en SonarQube, con `# nosec` (bandit) o `# noqa: <regla>` (ruff), siempre con un comentario que explique el motivo.

## 9. Responsables y calendario

| Actividad | Fecha | Responsable |
|---|---|---|
| BE-SA-1 y BE-SA-2 (preparación) | 3 – 6 nov | Samuel Sierra · Andrés Acero (regla de gitleaks y ramas del CI) |
| E1 | 7 nov | Mariana Cortés |
| Registro de bugs y plan de remediación | 7 – 8 nov | Mariana Cortés |
| E2 | 13 nov | Mariana Cortés |
| Llenar la columna API del PR-03 | 13 – 14 nov | Mariana Cortés · revisa Samuel Sierra |

## 10. Definición de terminado

- [ ] SonarQube Cloud muestra el proyecto con la cobertura de `coverage.xml`.
- [ ] La regla propia de gitleaks detecta el `.env` histórico de BE-01 (prueba de la regla).
- [ ] E1 y E2 ejecutadas, con evidencias en `evidencias/PR-03/api/` y sin ningún valor secreto copiado.
- [ ] Bugs registrados en Azure Boards y enlazados a su corrección BE-xx cuando existe.
- [ ] Columna API del PR-03 diligenciada y revisada por el líder de pruebas.
