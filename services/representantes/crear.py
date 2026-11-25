from config.db import SessionLocal
from models.clientes import Clientes
from models.representantes import Representantes
from sqlalchemy.exc import SQLAlchemyError


def crear_representante_service(
    id_cliente: int,
    nombre: str,
    apellido: str,
    correo: str,
    telefono: str,
    area: str
):
    """
    Crea un nuevo representante asociado a un cliente existente.
    """
    if not nombre or not nombre.strip():
        raise ValueError("El nombre del representante no puede estar vacío.")

    if not apellido or not apellido.strip():
        raise ValueError("El apellido del representante no puede estar vacío.")

    if not correo or not correo.strip():
        raise ValueError("El correo del representante no puede estar vacío.")

    if not area or not area.strip():
        raise ValueError("El área del representante no puede estar vacía.")

    db = SessionLocal()
    try:
        cliente = db.query(Clientes).filter(
            Clientes.id_cliente == id_cliente
        ).first()

        if not cliente:
            raise ValueError(f"Cliente con ID {id_cliente} no encontrado.")

        nuevo_representante = Representantes(
            id_cliente=id_cliente,
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            correo=correo.strip(),
            telefono=telefono.strip(),
            area=area.strip(),
            estado=True
        )

        db.add(nuevo_representante)
        db.commit()
        db.refresh(nuevo_representante)

        return {
            "success": True,
            "detail": f"Representante '{nombre} {apellido}' creado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
