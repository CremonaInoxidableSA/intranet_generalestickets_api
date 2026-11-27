from fastapi import APIRouter, HTTPException, Depends

from security.permissions import require_role
from security.dependencies import get_current_user
from services.tickets.eliminar import eliminar_ticket_service
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.delete(
    "/{id_ticket}",
    dependencies=[Depends(require_role("PERMISO_ELIMINAR_TICKET_POSTVENTA"))]
)
async def eliminar_ticket(
    id_ticket: int,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Desactiva un ticket seteando estado_ticket = False.
    Requiere permiso: PERMISO_ELIMINAR_TICKET_POSTVENTA
    """
    try:
        return eliminar_ticket_service(id_ticket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
