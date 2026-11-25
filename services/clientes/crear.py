from config.db import SessionLocal
from models.clientes import Clientes
from sqlalchemy.exc import SQLAlchemyError


def crear_cliente_service(nombre: str, pais: str):
    """
    Crea un nuevo cliente en la base de datos.
    """
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del cliente no puede estar vacío.")

    if not pais or not pais.strip():
        raise ValueError("El país del cliente no puede estar vacío.")

    db = SessionLocal()
    try:
        cliente_existente = db.query(Clientes).filter(
            Clientes.nombre == nombre.strip()
        ).first()

        if cliente_existente:
            raise ValueError(f"Ya existe un cliente con el nombre '{nombre.strip()}'.")

        nuevo_cliente = Clientes(
            nombre=nombre.strip(),
            pais=pais.strip(),
            estado=True
        )

        db.add(nuevo_cliente)
        db.commit()
        db.refresh(nuevo_cliente)

        return {
            "success": True,
            "detail": f"Cliente '{nombre}' creado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
