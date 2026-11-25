from typing import Optional

from pydantic import BaseModel, Field


class CrearClienteRequest(BaseModel):
    nombre: str = Field(
        description="Nombre del cliente"
    )
    pais: str = Field(
        description="País del cliente"
    )


class HabilitarClienteRequest(BaseModel):
    id_cliente: int = Field(
        description="ID del cliente a habilitar"
    )


class DeshabilitarClienteRequest(BaseModel):
    id_cliente: int = Field(
        description="ID del cliente a deshabilitar"
    )


class EditarClienteRequest(BaseModel):
    id_cliente: int = Field(
        description="ID del cliente a editar"
    )
    nombre: str = Field(
        description="Nuevo nombre del cliente"
    )
    pais: str = Field(
        description="Nuevo país del cliente"
    )
    estado: Optional[bool] = Field(
        default=None,
        description="Nuevo estado del cliente. Si no se envía, se mantiene el actual"
    )
