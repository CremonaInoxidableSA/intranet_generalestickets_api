from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import TypeAdapter

from security.permissions import require_role
from security.dependencies import get_current_user
from services.tickets.crear import crear_ticket_service
from schemas.authenticated_user import AuthenticatedUser
from schemas.tickets import InvolucradoCrear, ResolutorCrear

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


def _parsear_lista(valor: Optional[str], modelo):
    """
    Convierte un JSON enviado en un campo de formulario en una lista validada.
    Un valor vacío o ausente devuelve una lista vacía.
    """
    if valor is None or not valor.strip():
        return []
    return TypeAdapter(List[modelo]).validate_json(valor)


@router.post(
    "/crear",
    dependencies=[Depends(require_role("PERMISO_CREAR_TICKET_POSTVENTA"))]
)
async def crear_ticket(
    id_cliente: int = Form(...),
    nombre_proyecto: str = Form(...),
    descripcion: str = Form(...),
    estado: str = Form(...),
    fecha_ocurrencia: datetime = Form(...),
    id_representante: Optional[int] = Form(default=None),
    resolucion: Optional[str] = Form(default=None),
    fecha_resolucion: Optional[datetime] = Form(default=None),
    tiempo_empleado: Optional[int] = Form(default=None),
    involucrados: Optional[str] = Form(
        default=None,
        description='[{"id_usuario_interviniente": "...", "nombre_usuario_interviniente": "...", "apellido_usuario_interviniente": "...", "correo": "..."}]'
    ),
    resolutores: Optional[str] = Form(
        default=None,
        description='[{"id_usuario_resolutor": "...", "nombre_usuario_resolutor": "...", "apellido_usuario_resolutor": "..."}]'
    ),
    archivos: List[UploadFile] = File(default=[], description="Hasta 5 archivos: mp4, png, jpeg, jpg, pdf, doc, docx, xls, xlsx (máx. 10 MB c/u)"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Requiere permiso: PERMISO_CREAR_TICKET_POSTVENTA
    """
    try:
        lista_involucrados = _parsear_lista(involucrados, InvolucradoCrear)
        lista_resolutores = _parsear_lista(resolutores, ResolutorCrear)

        result = await crear_ticket_service(
            usuario=current_user,
            id_cliente=id_cliente,
            id_representante=id_representante,
            nombre_proyecto=nombre_proyecto,
            descripcion=descripcion,
            estado=estado,
            fecha_ocurrencia=fecha_ocurrencia,
            resolucion=resolucion,
            fecha_resolucion=fecha_resolucion,
            tiempo_empleado=tiempo_empleado,
            archivos=archivos,
            involucrados=lista_involucrados,
            resolutores=lista_resolutores
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
