#!/usr/bin/env bash
# PR-04 · Pruebas unitarias y cobertura. Uso: scripts/qa/correr_unitarias.sh U1   (o U2)
# Deja las evidencias en evidencias/PR-04/api/ (carpeta ignorada por git).
set -euo pipefail
CORRIDA="${1:?Indique la corrida: U1 o U2}"
OUT="evidencias/PR-04/api"
mkdir -p "$OUT"

git rev-parse --short HEAD > "$OUT/${CORRIDA}_commit.txt"

# 1. Inventario
pytest --collect-only -q -m "not integration" > "$OUT/${CORRIDA}_inventario.txt"

# 2. Ejecución con cobertura de líneas y ramas, y reporte JUnit para contar resultados
pytest -m "not integration" -q --durations=10 \
  --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html \
  --junitxml="$OUT/${CORRIDA}_junit.xml" > "$OUT/${CORRIDA}_pytest.txt" || true
cp coverage.xml "$OUT/${CORRIDA}_coverage.xml"
rm -rf "$OUT/${CORRIDA}_htmlcov" && cp -r htmlcov "$OUT/${CORRIDA}_htmlcov"

# 3. Cobertura por capa para la Tabla 3
coverage report --include="app/api/*"            > "$OUT/${CORRIDA}_cov_presentacion.txt"
coverage report --include="app/application/*"    > "$OUT/${CORRIDA}_cov_aplicacion.txt"
coverage report --include="app/infrastructure/*" > "$OUT/${CORRIDA}_cov_infraestructura.txt"
coverage report --include="app/core/*"           > "$OUT/${CORRIDA}_cov_nucleo.txt"

tail -n 5 "$OUT/${CORRIDA}_pytest.txt"
