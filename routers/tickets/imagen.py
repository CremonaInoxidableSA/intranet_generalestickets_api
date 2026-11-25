from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse

from security.permissions import require_role
from services.tickets.imagen import validar_acceso_imagen

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.get(
    "/imagen",
    dependencies=[Depends(require_role("PERMISO_VER_TICKETS_POSTVENTA"))]
)
async def obtener_imagen(
    nombre_archivo: str = Query(..., description="Nombre del archivo multimedia"),
):
    """
    Requiere permiso: PERMISO_VER_TICKETS_POSTVENTA
    """
    validacion = validar_acceso_imagen(nombre_archivo=nombre_archivo)

    if not validacion["success"]:
        raise HTTPException(
            status_code=validacion["status_code"],
            detail=validacion["detail"]
        )

    return FileResponse(
        validacion["ruta"],
        media_type=validacion["media_type"],
        headers={"Content-Disposition": "inline"}
    )
