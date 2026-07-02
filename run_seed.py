"""
Ejecuta cualquier archivo .sql contra la base de datos configurada en .env
Uso:
  python run_seed.py                          -> ejecuta seed_data.sql (por defecto)
  python run_seed.py seed_estudiantes_sinteticos.sql
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Convertir URL asyncpg → psycopg2 síncrono
raw_url = os.getenv("DATABASE_URL", "")
db_url = raw_url.replace("postgresql+asyncpg://", "postgresql://")

sql_file = sys.argv[1] if len(sys.argv) > 1 else "seed_data.sql"

print(f"[INFO] Conectando a la base de datos...")

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    with open(sql_file, "r", encoding="utf-8-sig") as f:
        sql = f.read()

    print(f"[INFO] Ejecutando {sql_file} ...")
    cur.execute(sql)
    conn.commit()

    print("[OK] Seed ejecutado correctamente.")
    cur.close()
    conn.close()

except psycopg2.Error as e:
    msg = str(e).encode('ascii', errors='replace').decode('ascii')
    print(f"[ERROR] Error en la base de datos: {msg}")
    if conn:
        conn.rollback()
        conn.close()
except FileNotFoundError:
    print(f"[ERROR] No se encontro '{sql_file}' en el directorio actual.")
