#!/usr/bin/env bash
# PR-05 · Pruebas de integración. Uso: scripts/qa/correr_integracion.sh I1   (o I2)
#
# Variables de entorno:
#   TEST_DATABASE_URL  base DESECHABLE para pytest (postgresql+asyncpg://postgres:test@localhost:5432/eyes_test)
#   QA_API             URL de la API de QA con /api/v1 (si no hay, se omiten Newman y schemathesis)
#   QA_PASSWORD        contraseña de QA (secreto; nunca se escribe en las evidencias)
#   TOKEN_ADMIN        access token de un admin, solo para schemathesis
set -uo pipefail
CORRIDA="${1:?Indique la corrida: I1 o I2}"
OUT="evidencias/PR-05/api"
mkdir -p "$OUT"
git rev-parse --short HEAD > "$OUT/${CORRIDA}_commit.txt"

# 1. pytest contra PostgreSQL
if [ -n "${TEST_DATABASE_URL:-}" ]; then
  pytest -m integration -v --junitxml="$OUT/${CORRIDA}_pytest_integracion.xml" \
    > "$OUT/${CORRIDA}_pytest_integracion.txt"
else
  echo "TEST_DATABASE_URL no definida: se omite pytest -m integration"
fi

# 2. Colección Newman contra QA
if [ -n "${QA_API:-}" ] && [ -n "${QA_PASSWORD:-}" ]; then
  BASE_HOST="${QA_API%/api/v1}"
  ( cd tests/newman && newman run eyes_school_api.postman_collection.json \
      -e qa.postman_environment.json \
      --env-var "base_url=$QA_API" --env-var "base_host=$BASE_HOST" \
      --env-var "QA_PASSWORD=$QA_PASSWORD" --working-dir . \
      -r cli,junit,htmlextra \
      --reporter-junit-export "../../$OUT/${CORRIDA}_newman.xml" \
      --reporter-htmlextra-export "../../$OUT/${CORRIDA}_newman.html" )
else
  echo "QA_API/QA_PASSWORD no definidas: se omite Newman"
fi

# 3. Contrato contra OpenAPI
if [ -n "${QA_API:-}" ] && [ -n "${TOKEN_ADMIN:-}" ]; then
  schemathesis run "$QA_API/openapi.json" -H "Authorization: Bearer $TOKEN_ADMIN" \
    --checks all --report > "$OUT/${CORRIDA}_schemathesis.txt"
fi
