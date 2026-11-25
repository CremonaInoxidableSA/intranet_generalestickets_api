from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.permissions import require_role
from security.dependencies import get_current_user
from services.representantes.crear import crear_representante_service
from schemas.representantes import CrearRepresentanteRequest
from schemas.authenticated_user import AuthenticatedUser

router = APIRouter(
    prefix="/representantes",
    tags=["Representantes"]
)

security_scheme = HTTPBearer()


@router.post(
    "/crear",
    dependencies=[Depends(require_role("PERMISO_CREAR_REPRESENTANTE_POSTVENTA"))]
)
async def crear_representante(
    request_body: CrearRepresentanteRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    try:
        result = crear_representante_service(
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
