from datetime import datetime
from config.db import SessionLocal
from models.comentarios import Comentarios
from models.tickets import Tickets
from sqlalchemy.exc import SQLAlchemyError


def crear_comentario_service(
    id_ticket: int,
    id_usuario_creador: str,
    nombre_usuario_creador: str,
    apellido_usuario_creador: str,
    comentario: str
):
    """
    Crea un nuevo comentario en la base de datos.
    """
    if not comentario or not comentario.strip():
        return {
            "success": False,
            "detail": "El comentario no puede estar vacío."
        }
    
    db = SessionLocal()

    try:
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == id_ticket,
            Tickets.estado_ticket == True
        ).first()

        if not ticket:
            return {
                "success": False,
                "detail": "El ticket no existe o está inactivo."
            }

        nuevo_comentario = Comentarios(
            id_ticket=id_ticket,
            id_usuario_creador=id_usuario_creador,
            nombre_usuario_creador=nombre_usuario_creador,
            apellido_usuario_creador=apellido_usuario_creador,
            fecha_creacion=datetime.now(),
            comentario=comentario.strip()
        )
        
        db.add(nuevo_comentario)
        db.commit()
        db.refresh(nuevo_comentario)
        
        return {
            "success": True,
            "detail": "Comentario creado correctamente."
        }
    except SQLAlchemyError as e:
        db.rollback()
        return {
            "success": False,
            "detail": f"Error en la base de datos: {str(e)}"
        }
    finally:
        db.close()
