#!/usr/bin/env bash
# PR-03 · Análisis estático. Uso: scripts/qa/correr_estatico.sh E1   (o E2)
# Requiere: pip install ruff bandit pip-audit lizard==1.25.0 radon pygount pytest-cov
#           y, para duplicación y secretos, Node.js (npx jscpd@4.3.0) y el binario gitleaks 8.24.2.
# Las evidencias no deben contener valores secretos (gitleaks usa --redact).
set -uo pipefail
CORRIDA="${1:?Indique la corrida: E1 o E2}"
OUT="evidencias/PR-03/api"
mkdir -p "$OUT"
PERFIL="E,F,W,I,N,B,S,C90,SIM,UP,PL,RET,ARG,BLE,TRY"

git rev-parse --short HEAD > "$OUT/${CORRIDA}_commit.txt"
{ python --version; ruff --version; bandit --version; pip-audit --version; } > "$OUT/${CORRIDA}_versiones.txt" 2>&1

# B1 · reglas del CI
ruff check app main.py tests scripts > "$OUT/${CORRIDA}_ruff_ci.txt"
# B2 · perfil ampliado (informativo)
ruff check app main.py --select "$PERFIL" --ignore E501 --output-format json > "$OUT/${CORRIDA}_ruff_ampliado.json"
ruff check app main.py --select "$PERFIL" --ignore E501 --statistics > "$OUT/${CORRIDA}_ruff_ampliado_resumen.txt"
# B3 · seguridad del código
bandit -r app main.py -f json -o "$OUT/${CORRIDA}_bandit.json"
bandit -r app main.py > "$OUT/${CORRIDA}_bandit.txt"
# B5, B7 · complejidad y tamaño
lizard app main.py -l python --csv > "$OUT/${CORRIDA}_lizard.csv"
lizard app main.py -l python -C 15 -w > "$OUT/${CORRIDA}_lizard_ccn15.txt"
radon cc -s -a app main.py > "$OUT/${CORRIDA}_radon_cc.txt"
pygount --format=summary app main.py > "$OUT/${CORRIDA}_loc.txt"
# B6 · duplicación
npx jscpd@4.3.0 app --min-lines 5 --min-tokens 50 --reporters json,console --output "$OUT/${CORRIDA}_jscpd"
# B8 · secretos en todo el historial
gitleaks git . --redact --config .gitleaks.toml --report-format json --report-path "$OUT/${CORRIDA}_gitleaks.json"
# B9 · dependencias
pip-audit -r requirements.txt -f json -o "$OUT/${CORRIDA}_pip_audit.json"
# B10 · cobertura
pytest -q -m "not integration" --cov=app --cov-report=term --cov-report=xml > "$OUT/${CORRIDA}_cobertura.txt"

# Revisión manual H-08: solo se registra si el seed todavía trae contraseñas en comentarios.
if grep -nE '^--.*(->|→).*[A-Za-z]+[0-9]{4}[*#!]' seed_data.sql > /dev/null; then
  echo "H-08: seed_data.sql todavía trae contraseñas en un comentario" | tee "$OUT/${CORRIDA}_H08.txt"
else
  echo "H-08: seed_data.sql ya no trae contraseñas en comentarios" | tee "$OUT/${CORRIDA}_H08.txt"
fi
echo "Listo. Falta SonarQube Cloud (B4): capturas del Overview, Issues Blocker/Critical y Hotspots."
