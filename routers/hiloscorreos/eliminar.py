from fastapi import APIRouter, Depends, HTTPException

from security.permissions import require_role
from services.hiloscorreos.eliminar import eliminar_hilo_service

router = APIRouter(
    prefix="/hiloscorreos",
    tags=["Hilos Correos"]
)


@router.delete(
    "/eliminar",
    dependencies=[Depends(require_role("PERMISO_ELIMINAR_HILO_POSTVENTA"))]
)
async def eliminar_hilo(
    id_ticket: int,
    id_hilo: int,
):
    """
    Elimina un hilo completamente: registro en base de datos y archivo físico.
    
    Requiere permiso: PERMISO_ELIMINAR_HILO_POSTVENTA
    """
    try:
        result = await eliminar_hilo_service(id_ticket=id_ticket, id_hilo=id_hilo)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
