from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from security.permissions import require_role
from services.hiloscorreos.guardar import guardar_archivo_eml_service

router = APIRouter(
    prefix="/hiloscorreos",
    tags=["Hilos Correos"]
)


@router.post(
    "/guardar",
    dependencies=[Depends(require_role("PERMISO_GUARDAR_HILO_POSTVENTA"))]
)
async def guardar_archivo_eml(
    id_ticket: int = Form(...),
    archivo: UploadFile = File(
        ...,
        description="Archivo EML a guardar (máx. 50 MB)"
    ),
):
    """ 
    Recibe un archivo EML y lo vincula a un ticket.
    
    Requiere permiso: PERMISO_GUARDAR_HILO_POSTVENTA
    """
    try:
        result = await guardar_archivo_eml_service(id_ticket=id_ticket, archivo=archivo)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

