from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from security.permissions import require_role
from services.tickets.agregararchivos import agregar_archivos_ticket_service

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post(
    "/agregar-archivos",
    dependencies=[Depends(require_role("PERMISO_EDITAR_TICKET_POSTVENTA"))]
)
async def agregar_archivos_ticket(
    id_ticket: int = Form(...),
    archivos: List[UploadFile] = File(
        ...,
        description="Archivos a agregar. Máximo 5 por ticket en total: mp4, png, jpeg, jpg, pdf, doc, docx, xls, xlsx (máx. 10 MB c/u)"
    ),
):
    """
    Requiere permiso: PERMISO_EDITAR_TICKET_POSTVENTA
    """
    try:
        result = await agregar_archivos_ticket_service(
            id_ticket=id_ticket,
            archivos=archivos
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
