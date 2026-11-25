from fastapi import APIRouter, HTTPException, Depends

from security.permissions import require_role
from services.tickets.lista import listar_tickets_service

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.get(
    "/lista",
    dependencies=[Depends(require_role("PERMISO_VER_TICKETS_POSTVENTA"))]
)
async def listar_tickets():
    """
    Requiere permiso: PERMISO_VER_TICKETS_POSTVENTA
    """
    try:
        return listar_tickets_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
