from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.hiloscorreos.listaticket import listar_hilos_por_ticket_service
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/hiloscorreos", 
    tags=["Hilos Correos"]
)

security_scheme = HTTPBearer()

@router.get(
    "/lista",
    dependencies=[Depends(require_role("PERMISO_CONSULTAR_TICKET_POSTVENTA"))]
)
async def listar_hilos_ticket(
    id_ticket: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    result = listar_hilos_por_ticket_service(id_ticket=id_ticket)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["detail"])
    
    return result
