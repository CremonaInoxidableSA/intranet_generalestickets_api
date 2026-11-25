from fastapi import APIRouter, Depends, HTTPException

from security.permissions import require_role
from security.dependencies import get_current_user
from services.tickets.editar import editar_ticket_service
from schemas.authenticated_user import AuthenticatedUser
from schemas.tickets import EditarTicketRequest

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post(
    "/editar",
    dependencies=[Depends(require_role("PERMISO_EDITAR_TICKET_POSTVENTA"))]
)
async def editar_ticket(
    request_body: EditarTicketRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Requiere permiso: PERMISO_EDITAR_TICKET_POSTVENTA
    """
    try:
        result = editar_ticket_service(datos=request_body)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
