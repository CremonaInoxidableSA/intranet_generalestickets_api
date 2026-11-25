from pydantic import BaseModel


class CrearComentarioRequest(BaseModel):
    id_ticket: int
    comentario: str
