from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InvolucradoCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_usuario_interviniente: str = Field(
        min_length=1, max_length=255,
        description="ID del usuario involucrado"
    )
    nombre_usuario_interviniente: str = Field(
        min_length=1, max_length=255,
        description="Nombre del usuario involucrado"
    )
    apellido_usuario_interviniente: str = Field(
        min_length=1, max_length=255,
        description="Apellido del usuario involucrado"
    )
    correo: str = Field(
        min_length=1, max_length=255,
        description="Correo del usuario involucrado"
    )


class ResolutorCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_usuario_resolutor: str = Field(
        min_length=1, max_length=255,
        description="ID del usuario resolutor"
    )
    nombre_usuario_resolutor: str = Field(
        min_length=1, max_length=255,
        description="Nombre del usuario resolutor"
    )
    apellido_usuario_resolutor: str = Field(
        min_length=1, max_length=255,
        description="Apellido del usuario resolutor"
    )


class EditarTicketRequest(BaseModel):
    """
    Campos opcionales: si no se envían, no se modifican.
    - nombre_proyecto, descripcion, estado, fecha_ocurrencia, id_representante: null se ignora.
    - resolucion, fecha_resolucion, tiempo_empleado: null los limpia.
    - involucrados, resolutores: lista completa a dejar; [] elimina todos.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    id_ticket: int = Field(description="ID del ticket a editar")
    id_representante: Optional[int] = Field(default=None, description="Nuevo representante (debe pertenecer al cliente del ticket)")
    nombre_proyecto: Optional[str] = Field(default=None, min_length=1, max_length=255)
    fecha_ocurrencia: Optional[datetime] = None
    descripcion: Optional[str] = Field(default=None, min_length=1, max_length=255)
    estado: Optional[str] = None
    resolucion: Optional[str] = Field(default=None, max_length=255)
    fecha_resolucion: Optional[datetime] = None
    tiempo_empleado: Optional[int] = Field(default=None, ge=0)
    involucrados: Optional[List[InvolucradoCrear]] = None
    resolutores: Optional[List[ResolutorCrear]] = None


class EliminarArchivoTicketRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_ticket: int = Field(description="ID del ticket al que pertenece el archivo")
    nombre_archivo: str = Field(
        min_length=1, max_length=255,
        description="Nombre del archivo multimedia a eliminar"
    )


class DescargarArchivoTicketRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id_ticket: int = Field(description="ID del ticket al que debe pertenecer el archivo")
    nombre_archivo: str = Field(
        min_length=1, max_length=255,
        description="Nombre del archivo a descargar (PDF, Word, Excel o video)"
    )
