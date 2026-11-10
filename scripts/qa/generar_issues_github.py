"""Genera los issues de GitHub de los defectos conocidos del backend (PR-07).

El catálogo de defectos vive en la tabla de `docs/test/GestionDefectos/...`, que es la única
fuente de verdad: este script la lee y produce un CSV y un script de `gh` para crearlos sin
escribirlos a mano. Si la tabla cambia, se vuelve a generar.

    python scripts/qa/generar_issues_github.py

Produce en `evidencias/PR-07/`:
  * `defectos_github_issues.csv`  — para revisar, o para importar con cualquier herramienta.
  * `crear_issues_github.sh`      — los comandos `gh issue create`, uno por defecto.

Para crearlos (una sola vez, desde la raíz del repositorio y con `gh auth login` hecho):

    bash evidencias/PR-07/crear_issues_github.sh

`gh` imprime la URL de cada issue; ese número `#n` se anota en la tabla del documento.
El CSV no contiene credenciales ni valores secretos.

Nota: el equipo usa Azure DevOps solo para el componente móvil, por eso los defectos del
backend van a GitHub Issues y no a Azure Boards (ver la sección 1 de la planeación).
"""

from __future__ import annotations

import csv
import re
import shlex
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PLAN = RAIZ / "docs/test/GestionDefectos/planeacion-gestion-defectos-backend.md"
SALIDA = RAIZ / "evidencias/PR-07"

ETIQUETA_SEVERIDAD = {"Crítica": "critica", "Alta": "alta", "Media": "media", "Baja": "baja"}


def filas_de_la_tabla() -> list[list[str]]:
    filas = []
    for linea in PLAN.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("| DEF-"):
            continue
        celdas = [c.strip() for c in linea.strip("|").split("|")]
        # La tabla tiene una columna «Issue» que se rellena DESPUÉS de crearlos; se descarta aquí
        # para que el script siga leyendo las mismas nueve columnas de siempre.
        if len(celdas) >= 10 and celdas[1].startswith("[#"):
            celdas = [celdas[0]] + celdas[2:]
        if len(celdas) >= 9:
            filas.append(celdas[:9])
    return filas


def cuerpo(id_qa, correccion, caso, fecha, sprint) -> str:
    return (
        f"**Identificado:** {fecha} · **Sprint previsto:** {sprint}\n\n"
        f"**Corrección planeada:** {correccion}\n"
        f"**Caso que lo verifica:** {caso}\n\n"
        "El diseño de la corrección y los pasos para reproducirlo están en "
        "`docs/test/Especificaciones` (planeación de correcciones). Los resultados medidos, en "
        "`docs/test/Resultados/corrida-2026-11-09.md` y `informe-pruebas-backend.md`.\n\n"
        f"Catálogo completo: `docs/test/GestionDefectos` ({id_qa}).\n\n"
        "Al cerrar: anotar la causa raíz (Requisitos, Diseño, Codificación, Datos o Entorno). "
        "El pull request de la corrección debe decir `Closes #<n>` para que quede enlazado el commit."
    )


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    filas = filas_de_la_tabla()

    csv_destino = SALIDA / "defectos_github_issues.csv"
    sh_destino = SALIDA / "crear_issues_github.sh"

    with csv_destino.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["title", "body", "labels", "assignee", "milestone"])
        comandos = [
            "#!/usr/bin/env bash",
            "# Generado por scripts/qa/generar_issues_github.py · no editar a mano.",
            "# Requiere `gh auth login`. Se corre UNA sola vez desde la raíz del repositorio.",
            "set -euo pipefail",
            "",
        ]
        for id_qa, correccion, titulo, sev, prio, caso, asignado, fecha, sprint in filas:
            etiquetas = ["defecto", ETIQUETA_SEVERIDAD.get(sev, "media")]
            p = re.sub(r"\D", "", prio)
            if p:
                etiquetas.append(f"P{p}")
            etiquetas.append("revision-codigo")
            titulo_issue = f"{id_qa} · {titulo}"
            texto = cuerpo(id_qa, correccion, caso, fecha, sprint)
            w.writerow([titulo_issue, texto, ",".join(etiquetas), asignado, sprint])
            comandos.append(
                "gh issue create "
                f"--title {shlex.quote(titulo_issue)} "
                f"--body {shlex.quote(texto)} "
                f"--label {shlex.quote(','.join(etiquetas))}"
            )
        comandos.append("")
        sh_destino.write_text("\n".join(comandos), encoding="utf-8")

    print(f"{len(filas)} defectos")
    print(f"  CSV     : {csv_destino.relative_to(RAIZ)}")
    print(f"  comandos: {sh_destino.relative_to(RAIZ)}")
    print("\nEtiquetas que deben existir antes (una sola vez):")
    print("  gh label create defecto --color d73a4a --description 'Defecto del backend (PR-07)'")
    for et, color in [("critica", "b60205"), ("alta", "d93f0b"), ("media", "fbca04"), ("baja", "0e8a16")]:
        print(f"  gh label create {et} --color {color}")
    for p in ("P1", "P2", "P3", "P4"):
        print(f"  gh label create {p} --color ededed")
    print("  gh label create revision-codigo --color c5def5")


if __name__ == "__main__":
    main()
