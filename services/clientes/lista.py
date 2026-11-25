from config.db import SessionLocal
from models.clientes import Clientes
from sqlalchemy.exc import SQLAlchemyError


def listar_clientes_service():
    """
    Obtiene la lista de todos los clientes de la base de datos.
    """
    db = SessionLocal()
    try:
        clientes = db.query(Clientes).all()

        if not clientes:
            return {
                "success": True,
                "detail": "No hay clientes disponibles.",
                "data": []
            }

        clientes_list = [
            {
                "id_cliente": cliente.id_cliente,
                "nombre": cliente.nombre,
                "pais": cliente.pais,
                "estado": cliente.estado
            }
            for cliente in clientes
        ]

        return {
            "success": True,
            "detail": "Clientes obtenidos correctamente.",
            "data": clientes_list
        }
    except SQLAlchemyError as e:
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
