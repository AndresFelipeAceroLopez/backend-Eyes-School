from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class DispositivoModel(Base):
    """Token FCM de un teléfono, para enviar notificaciones push al acudiente."""

    __tablename__ = "dispositivos"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(
        "idUsuario", Integer, ForeignKey("public.usuario.idUsuario", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    token_fcm: Mapped[str] = mapped_column("tokenFcm", String(512), nullable=False, unique=True)
    plataforma: Mapped[str] = mapped_column("plataforma", String(20), nullable=False)
    actualizado: Mapped[datetime] = mapped_column(
        "actualizado", DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
