from fastapi import APIRouter

from app.application.dispositivos.schemas import DispositivoCreate, DispositivoOut
from app.core.dependencies import AuthUser, DbSession
from app.infrastructure.repositories.dispositivo_repository import DispositivoRepository

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos"])


# Cualquier usuario autenticado registra su teléfono para recibir notificaciones push.
# Si el token ya existía (el teléfono cambió de cuenta) se reasigna al usuario actual.
@router.post("", response_model=DispositivoOut, status_code=201)
async def registrar_dispositivo(data: DispositivoCreate, db: DbSession, current_user: AuthUser):
    item = await DispositivoRepository(db).registrar(
        current_user.id_usuario, data.token_fcm, data.plataforma
    )
    return DispositivoOut.model_validate(item)


# Al cerrar sesión la app borra su token para no seguir recibiendo avisos de esa cuenta.
@router.delete("/{token_fcm}", status_code=204)
async def eliminar_dispositivo(token_fcm: str, db: DbSession, current_user: AuthUser):
    await DispositivoRepository(db).eliminar_token(token_fcm, current_user.id_usuario)
