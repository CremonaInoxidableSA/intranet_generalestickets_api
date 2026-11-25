from config.db import SessionLocal
from models.representantes import Representantes
from sqlalchemy.exc import SQLAlchemyError


def listar_representantes_service():
    """
    Obtiene la lista de todos los representantes de la base de datos.
    """
    db = SessionLocal()
    try:
        representantes = db.query(Representantes).all()

        if not representantes:
            return {
                "success": True,
                "detail": "No hay representantes disponibles.",
                "data": []
            }

        representantes_list = [
            {
                "id_representante": representante.id_representante,
                "id_cliente": representante.id_cliente,
                "nombre": representante.nombre,
                "apellido": representante.apellido,
                "correo": representante.correo,
                "telefono": representante.telefono,
                "area": representante.area,
                "estado": representante.estado
            }
            for representante in representantes
        ]

        return {
            "success": True,
            "detail": "Representantes obtenidos correctamente.",
            "data": representantes_list
        }
    except SQLAlchemyError as e:
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
