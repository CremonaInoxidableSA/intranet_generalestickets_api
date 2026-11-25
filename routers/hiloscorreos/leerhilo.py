from fastapi import APIRouter, Depends, HTTPException

from security.permissions import require_role
from services.hiloscorreos.leerhilo import leer_archivo_eml_service

router = APIRouter(
    prefix="/hiloscorreos",
    tags=["Hilos Correos"]
)


@router.get(
    "/leer",
    dependencies=[Depends(require_role("PERMISO_VER_TICKETS_POSTVENTA"))]
)
async def leer_archivo_eml(
    id_ticket: int,
    id_hilo: int,
):
    """
    Lee el contenido de un archivo EML vinculado a un ticket.
    Retorna cada correo del hilo (del más reciente al más antiguo) con remitente, destinatarios,
    asunto, fecha y `cuerpo_html` sanitizado (listo para renderizar).
    
    Requiere permiso: PERMISO_VER_TICKETS_POSTVENTA
    """
    try:
        result = await leer_archivo_eml_service(id_ticket=id_ticket, id_hilo=id_hilo)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
