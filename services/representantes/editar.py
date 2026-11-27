from typing import Optional

from config.db import SessionLocal
from models.clientes import Clientes
from models.representantes import Representantes
from sqlalchemy.exc import SQLAlchemyError


def editar_representante_service(
    id_representante: int,
    id_cliente: int,
    nombre: str,
    apellido: str,
    correo: str,
    telefono: str,
    area: str
):
    """
    Edita los datos de un representante existente.
    Valida que el cliente indicado exista.
    """
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del representante no puede estar vacío.")

    if not apellido or not apellido.strip():
        raise ValueError("El apellido del representante no puede estar vacío.")

    db = SessionLocal()
    try:
        representante = db.query(Representantes).filter(
            Representantes.id_representante == id_representante
        ).first()

        if not representante:
            raise ValueError(f"Representante con ID {id_representante} no encontrado.")

        cliente = db.query(Clientes).filter(
            Clientes.id_cliente == id_cliente
        ).first()

        if not cliente:
            raise ValueError(f"Cliente con ID {id_cliente} no encontrado.")

        representante.id_cliente = id_cliente
        representante.nombre = nombre.strip()
        representante.apellido = apellido.strip()
        representante.correo = correo.strip() if correo else None
        representante.telefono = telefono.strip() if telefono else None
        representante.area = area.strip() if area else None

        db.commit()
        db.refresh(representante)

        return {
            "success": True,
            "detail": f"Representante '{representante.nombre} {representante.apellido}' editado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
