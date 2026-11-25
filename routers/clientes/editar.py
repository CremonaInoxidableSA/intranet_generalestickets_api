from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.clientes.editar import editar_cliente_service
from schemas.clientes import EditarClienteRequest
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

security_scheme = HTTPBearer()


@router.post(
    "/editar",
    dependencies=[Depends(require_role("PERMISO_EDITAR_CLIENTE_POSTVENTA"))]
)
async def editar_cliente(
    request_body: EditarClienteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Edita un cliente.
    """
    try:
        result = editar_cliente_service(
            id_cliente=request_body.id_cliente,
            nombre=request_body.nombre,
            pais=request_body.pais
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
