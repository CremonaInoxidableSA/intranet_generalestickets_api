from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.representantes.deshabilitar import deshabilitar_representante_service
from schemas.authenticated_user import AuthenticatedUser
from schemas.representantes import DeshabilitarRepresentanteRequest

router = APIRouter(
    prefix="/representantes",
    tags=["Representantes"]
)

security_scheme = HTTPBearer()

@router.post(
    "/deshabilitar",
    dependencies=[Depends(require_role("PERMISO_ESTADOS_REPRESENTANTES_POSTVENTA"))]
)
async def deshabilitar_representante(
    request_body: DeshabilitarRepresentanteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Deshabilita un representante.
    Requiere permiso: PERMISO_ESTADOS_REPRESENTANTES_POSTVENTA
    """
    try:
        resultado = deshabilitar_representante_service(request_body.id_representante)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
