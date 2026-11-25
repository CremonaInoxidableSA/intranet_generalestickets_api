import importlib

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from security.permissions import require_role

from services.tickets.descargaarchivos import validar_descarga_archivo
from schemas.tickets import DescargarArchivoTicketRequest

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post(
    "/descarga-archivos",
    dependencies=[Depends(require_role("PERMISO_VER_TICKETS_POSTVENTA"))]
)
async def descargar_archivo(
    request_body: DescargarArchivoTicketRequest
):
    """
    Requiere permiso: PERMISO_VER_TICKETS_POSTVENTA
    """
    validacion = validar_descarga_archivo(
        id_ticket=request_body.id_ticket,
        nombre_archivo=request_body.nombre_archivo
    )

    if not validacion["success"]:
        raise HTTPException(
            status_code=validacion["status_code"],
            detail=validacion["detail"]
        )

    return FileResponse(
        path=validacion["ruta"],
        media_type=validacion["media_type"],
        filename=validacion["nombre_archivo"]
    )
