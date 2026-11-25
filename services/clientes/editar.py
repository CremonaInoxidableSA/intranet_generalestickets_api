from typing import Optional

from config.db import SessionLocal
from models.clientes import Clientes
from sqlalchemy.exc import SQLAlchemyError


def editar_cliente_service(
    id_cliente: int,
    nombre: str,
    pais: str,
):
    """
    Edita los datos de un cliente existente.
    """
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del cliente no puede estar vacío.")

    if not pais or not pais.strip():
        raise ValueError("El país del cliente no puede estar vacío.")

    db = SessionLocal()
    try:
        cliente = db.query(Clientes).filter(
            Clientes.id_cliente == id_cliente
        ).first()

        if not cliente:
            raise ValueError(f"Cliente con ID {id_cliente} no encontrado.")

        cliente.nombre = nombre.strip()
        cliente.pais = pais.strip()

        db.commit()
        db.refresh(cliente)

        return {
            "success": True,
            "detail": f"Cliente '{cliente.nombre}' editado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
