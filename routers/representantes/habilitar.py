from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.representantes.habilitar import habilitar_representante_service
from schemas.authenticated_user import AuthenticatedUser
from schemas.representantes import HabilitarRepresentanteRequest

router = APIRouter(
    prefix="/representantes",
    tags=["Representantes"]
)

security_scheme = HTTPBearer()


@router.post(
    "/habilitar",
    dependencies=[Depends(require_role("PERMISO_ESTADOS_REPRESENTANTES_POSTVENTA"))]
)
async def habilitar_representante(
    request_body: HabilitarRepresentanteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Habilita un representante.
    Requiere permiso: PERMISO_ESTADOS_REPRESENTANTES_POSTVENTA
    """
    try:
        resultado = habilitar_representante_service(request_body.id_representante)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
