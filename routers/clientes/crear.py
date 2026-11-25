from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.clientes.crear import crear_cliente_service
from schemas.clientes import CrearClienteRequest
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

security_scheme = HTTPBearer()


@router.post(
    "/crear",
    dependencies=[Depends(require_role("PERMISO_CREAR_CLIENTE_POSTVENTA"))]
)
async def crear_cliente(
    request_body: CrearClienteRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    try:
        result = crear_cliente_service(nombre=request_body.nombre, pais=request_body.pais)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
