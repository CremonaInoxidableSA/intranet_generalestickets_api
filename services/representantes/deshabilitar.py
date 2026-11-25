from config.db import SessionLocal
from models.representantes import Representantes
from sqlalchemy.exc import SQLAlchemyError


def deshabilitar_representante_service(id_representante: int):
    """
    Deshabilita un representante actualizando su estado a False.
    Solo es posible deshabilitar representantes que están habilitados (estado=True).
    """
    db = SessionLocal()
    try:
        representante = db.query(Representantes).filter(
            Representantes.id_representante == id_representante
        ).first()

        if not representante:
            raise Exception(f"Representante con ID {id_representante} no encontrado")

        if not representante.estado:
            return {
                "success": False,
                "detail": "El representante ya se encuentra deshabilitado."
            }

        representante.estado = False

        db.commit()
        db.refresh(representante)

        return {
            "success": True,
            "detail": f"El representante '{representante.nombre} {representante.apellido}' fue deshabilitado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
