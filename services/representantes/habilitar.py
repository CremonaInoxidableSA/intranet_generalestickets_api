from config.db import SessionLocal
from models.representantes import Representantes
from sqlalchemy.exc import SQLAlchemyError


def habilitar_representante_service(id_representante: int):
    """
    Habilita un representante actualizando su estado a True.
    Solo es posible habilitar representantes que están deshabilitados (estado=False).
    """
    db = SessionLocal()
    try:
        representante = db.query(Representantes).filter(
            Representantes.id_representante == id_representante
        ).first()

        if not representante:
            raise Exception(f"Representante con ID {id_representante} no encontrado")

        if representante.estado:
            return {
                "success": False,
                "detail": "El representante ya se encuentra habilitado."
            }

        representante.estado = True

        db.commit()
        db.refresh(representante)

        return {
            "success": True,
            "detail": f"El representante '{representante.nombre} {representante.apellido}' fue habilitado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
