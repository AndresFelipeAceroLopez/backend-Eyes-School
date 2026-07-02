"""
Script para crear el primer usuario administrador en la base de datos.
Úsalo una sola vez para arrancar el sistema.

Uso:
    python create_admin.py
"""
import asyncio
import sys
import uuid
from datetime import date

import asyncpg


DATABASE_URL = "postgresql://eyesschool_zia0_user:13ZI07GWMlG2EI0MSJyhFSWMgzrXh99v@dpg-d92jl71kh4rs73cllun0-a.oregon-postgres.render.com/eyesschool_zia0"



def hash_password(password: str) -> str:
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def crear_admin():
    print("=== Crear usuario administrador ===\n")

    primer_nombre    = input("Primer nombre:        ").strip()
    primer_apellido  = input("Primer apellido:      ").strip()
    tipo_documento   = input("Tipo documento (CC/TI/CE): ").strip() or "CC"
    numero_documento = input("Número de documento:  ").strip()
    correo           = input("Correo electrónico:   ").strip()
    password         = input("Contraseña:           ").strip()
    cargo            = input("Cargo (Enter = Rector): ").strip() or "Rector"

    if not all([primer_nombre, primer_apellido, numero_documento, correo, password]):
        print("\nError: todos los campos son obligatorios.")
        sys.exit(1)

    pw_hash = hash_password(password)
    uid     = uuid.uuid4()

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Verificar que no exista ya ese correo
        existing = await conn.fetchval(
            'SELECT "idUsuario" FROM public.usuario WHERE correo = $1', correo
        )
        if existing:
            print(f"\nError: ya existe un usuario con el correo {correo} (id={existing}).")
            return

        # Insertar usuario con id_rol = 3 (admin)
        id_usuario = await conn.fetchval(
            """
            INSERT INTO public.usuario
              ("tipoDocumento", "numeroDocumento", "primerNombre", "primerApellido",
               "correo", "password", "estado", "fechaRegistro", "idRol", "idUsuario_uuid")
            VALUES ($1, $2, $3, $4, $5, $6, true, NOW(), 3, $7)
            RETURNING "idUsuario"
            """,
            tipo_documento, numero_documento, primer_nombre, primer_apellido,
            correo, pw_hash, uid,
        )

        # Insertar administrador
        id_admin = await conn.fetchval(
            """
            INSERT INTO public.administrador
              ("idUsuario", "cargo", "nivelAcceso", "estado", "fechaAsignacion")
            VALUES ($1, $2, 'Total', 'Activo', $3)
            RETURNING "idAdministrador"
            """,
            id_usuario, cargo, date.today(),
        )

        print(f"\nAdministrador creado exitosamente.")
        print(f"  idUsuario:      {id_usuario}")
        print(f"  idAdministrador:{id_admin}")
        print(f"  Correo:         {correo}")
        print(f"\nAhora puedes iniciar sesión en la interfaz con esas credenciales.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(crear_admin())