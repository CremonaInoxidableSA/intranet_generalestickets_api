from typing import Optional

from pydantic import BaseModel, Field


class CrearRepresentanteRequest(BaseModel):
    id_cliente: int = Field(
        description="ID del cliente al que pertenece el representante"
    )
    nombre: str = Field(
        description="Nombre del representante"
    )
    apellido: str = Field(
        description="Apellido del representante"
    )
    correo: str = Field(
        description="Correo electrónico del representante"
    )
    telefono: str = Field(
        description="Teléfono del representante"
    )
    area: str = Field(
        description="Área del representante"
    )


class HabilitarRepresentanteRequest(BaseModel):
    id_representante: int = Field(
        description="ID del representante a habilitar"
    )


class DeshabilitarRepresentanteRequest(BaseModel):
    id_representante: int = Field(
        description="ID del representante a deshabilitar"
    )


class EditarRepresentanteRequest(BaseModel):
    id_representante: int = Field(
        description="ID del representante a editar"
    )
    id_cliente: int = Field(
        description="ID del cliente al que pertenece el representante (debe existir)"
    )
    nombre: str = Field(
        description="Nuevo nombre del representante"
    )
    apellido: str = Field(
        description="Nuevo apellido del representante"
    )
    correo: str = Field(
        description="Nuevo correo electrónico del representante"
    )
    telefono: str = Field(
        description="Nuevo teléfono del representante"
    )
    area: str = Field(
        description="Nueva área del representante"
    )
    estado: Optional[bool] = Field(
        default=None,
        description="Nuevo estado del representante. Si no se envía, se mantiene el actual"
    )
