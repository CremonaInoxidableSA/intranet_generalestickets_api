from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.representantes.editar import editar_representante_service
from schemas.representantes import EditarRepresentanteRequest
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/representantes",
    tags=["Representantes"]
)

security_scheme = HTTPBearer()


@router.post(
    "/editar",
    dependencies=[Depends(require_role("PERMISO_EDITAR_REPRESENTANTE_POSTVENTA"))]
)
async def editar_representante(
    request_body: EditarRepresentanteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Edita un representante.
    """
    try:
        result = editar_representante_service(
            id_representante=request_body.id_representante,
            id_cliente=request_body.id_cliente,
            nombre=request_body.nombre,
            apellido=request_body.apellido,
            correo=request_body.correo,
            telefono=request_body.telefono,
            area=request_body.area
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
