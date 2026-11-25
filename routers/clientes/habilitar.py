from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.clientes.habilitar import habilitar_cliente_service
from schemas.authenticated_user import AuthenticatedUser
from schemas.clientes import HabilitarClienteRequest

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

security_scheme = HTTPBearer()


@router.post(
    "/habilitar",
    dependencies=[Depends(require_role("PERMISO_ESTADOS_CLIENTES_POSTVENTA"))]
)
async def habilitar_cliente(
    request_body: HabilitarClienteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Habilita un cliente.
    Requiere permiso: PERMISO_ESTADOS_CLIENTES_POSTVENTA
    """
    try:
        resultado = habilitar_cliente_service(request_body.id_cliente)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
