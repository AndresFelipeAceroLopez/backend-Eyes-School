from typing import Literal

from pydantic import BaseModel, Field


class DispositivoCreate(BaseModel):
    token_fcm: str = Field(min_length=10, max_length=512)
    plataforma: Literal["android", "ios", "web"]


class DispositivoOut(BaseModel):
    id: int
    token_fcm: str
    plataforma: str
    model_config = {"from_attributes": True}
