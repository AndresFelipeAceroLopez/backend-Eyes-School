from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base


class SesionRefrescoModel(Base):
    """Refresh token emitido: permite revocarlo (cierre de sesión, cuenta desactivada)."""

    __tablename__ = "sesiones_refresco"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column("id", Integer, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column("jti", String(64), nullable=False, unique=True)
    id_usuario: Mapped[int] = mapped_column(
        "idUsuario", Integer, ForeignKey("public.usuario.idUsuario", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    emitido: Mapped[datetime] = mapped_column("emitido", DateTime, nullable=False, default=func.now())
    expira: Mapped[datetime] = mapped_column("expira", DateTime, nullable=False)
    revocado: Mapped[bool] = mapped_column(
        "revocado", Boolean, nullable=False, default=False, server_default="false"
    )
