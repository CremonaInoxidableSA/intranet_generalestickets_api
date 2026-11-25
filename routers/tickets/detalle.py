from fastapi import APIRouter, HTTPException, Depends, Query

from security.permissions import require_role
from services.tickets.detalle import obtener_detalle_ticket_service

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.get(
    "/detalle",
    dependencies=[Depends(require_role("PERMISO_VER_TICKETS_POSTVENTA"))]
)
async def obtener_detalle_ticket(
    id_ticket: int = Query(..., description="ID del ticket")
):
    """
    Requiere permiso: PERMISO_VER_TICKETS_POSTVENTA
    """
    try:
        resultado = obtener_detalle_ticket_service(id_ticket=id_ticket)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not resultado["success"]:
        raise HTTPException(
            status_code=resultado["status_code"],
            detail=resultado["detail"]
        )

    return resultado
