from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.comentarios.listaticket import listar_comentarios_por_ticket_service
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/comentarios", 
    tags=["Comentarios"]
)

security_scheme = HTTPBearer()

@router.get(
    "/lista",
    dependencies=[Depends(require_role("PERMISO_CONSULTAR_TICKET_POSTVENTA"))]
)
async def listar_comentarios_ticket(
    id_ticket: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    result = listar_comentarios_por_ticket_service(id_ticket=id_ticket)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["detail"])
    
    return result
