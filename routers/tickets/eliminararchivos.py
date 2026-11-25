import importlib

from fastapi import APIRouter, Depends, HTTPException

from security.permissions import require_role
from schemas.tickets import EliminarArchivoTicketRequest

from services.tickets.eliminararchivos import eliminar_archivo_ticket_service

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post(
    "/eliminar-archivos",
    dependencies=[Depends(require_role("PERMISO_EDITAR_TICKET_POSTVENTA"))]
)
async def eliminar_archivo_ticket(request_body: EliminarArchivoTicketRequest):
    """
    Requiere permiso: PERMISO_EDITAR_TICKET_POSTVENTA
    """
    resultado = eliminar_archivo_ticket_service(
        id_ticket=request_body.id_ticket,
        nombre_archivo=request_body.nombre_archivo
    )

    if not resultado["success"]:
        raise HTTPException(
            status_code=resultado["status_code"],
            detail=resultado["detail"]
        )

    return resultado
