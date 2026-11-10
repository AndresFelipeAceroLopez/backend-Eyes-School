"""Genera el CSV para importar en bloque los defectos conocidos en Azure Boards (PR-07).

Lee la tabla «Defectos ya conocidos» de la planeación de gestión de defectos y produce un CSV con
las columnas que Azure Boards espera en Boards > Work items > Import. Así el registro no se hace a
mano uno por uno, y el documento sigue siendo la única fuente de verdad: si cambia la tabla, se
vuelve a generar.

    python scripts/qa/generar_csv_azure_boards.py

Después de importar, Azure Boards asigna el `AB#` de cada bug: ese número se anota de vuelta en el
PR-07. El CSV no contiene credenciales ni valores secretos.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PLAN = RAIZ / "docs/test/GestionDefectos/planeacion-gestion-defectos-backend.md"
DESTINO = RAIZ / "evidencias/PR-07/defectos_azure_boards.csv"

# Severidad de QA -> campo Severity de Azure Boards; prioridad propuesta -> Priority (1 a 4).
SEVERIDAD = {"Crítica": "1 - Critical", "Alta": "2 - High", "Media": "3 - Medium", "Baja": "4 - Low"}


def filas_de_la_tabla() -> list[list[str]]:
    filas = []
    for linea in PLAN.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("| DEF-"):
            continue
        celdas = [c.strip() for c in linea.strip("|").split("|")]
        if len(celdas) >= 9:
            filas.append(celdas)
    return filas


def main() -> None:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    columnas = [
        "Work Item Type", "Title", "Severity", "Priority", "Assigned To", "Tags",
        "Repro Steps", "State",
    ]
    with DESTINO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        for id_qa, correccion, titulo, sev, prio, caso, asignado, fecha, _sprint in (
            fila[:9] for fila in filas_de_la_tabla()
        ):
            prioridad = re.sub(r"\D", "", prio) or "3"
            repro = (
                f"{id_qa}. Identificado el {fecha} en la revisión de código y las pruebas "
                f"de QA del backend.<br>"
                f"Corrección planeada: {correccion}.<br>"
                f"Caso que lo verifica: {caso}.<br>"
                f"Detalle y diseño de la corrección: docs/test/Especificaciones "
                f"(planeación de correcciones) y docs/test/Resultados "
                f"(corrida-2026-11-09.md e informe-pruebas-backend.md)."
            )
            w.writerow([
                "Bug", titulo, SEVERIDAD.get(sev, "3 - Medium"), prioridad, asignado,
                "api; revision-codigo", repro, "New",
            ])
    print(f"{len(filas_de_la_tabla())} defectos escritos en {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
