from config.db import SessionLocal
from models.clientes import Clientes
from sqlalchemy.exc import SQLAlchemyError


def habilitar_cliente_service(id_cliente: int):
    """
    Habilita un cliente actualizando su estado a True.
    Solo es posible habilitar clientes que están deshabilitados (estado=False).
    """
    db = SessionLocal()
    try:
        cliente = db.query(Clientes).filter(
            Clientes.id_cliente == id_cliente
        ).first()

        if not cliente:
            raise Exception(f"Cliente con ID {id_cliente} no encontrado")

        if cliente.estado:
            return {
                "success": False,
                "detail": "El cliente ya se encuentra habilitado."
            }

        cliente.estado = True

        db.commit()
        db.refresh(cliente)

        return {
            "success": True,
            "detail": f"El cliente '{cliente.nombre}' fue habilitado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
