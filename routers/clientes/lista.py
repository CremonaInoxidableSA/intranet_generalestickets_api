from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.clientes.lista import listar_clientes_service
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

security_scheme = HTTPBearer()


@router.get(
    "/lista",
    dependencies=[Depends(require_role("PERMISO_CONSULTAR_CLIENTES_POSTVENTA"))]
)
async def listar_clientes(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    try:
        result = listar_clientes_service()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
