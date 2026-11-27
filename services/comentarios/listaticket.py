from config.db import SessionLocal
from models.comentarios import Comentarios
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc


def listar_comentarios_por_ticket_service(id_ticket: int):
    """
    Obtiene la lista de comentarios de un ticket específico.
    """
    db = SessionLocal()
    try:
        from models.tickets import Tickets
        
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == id_ticket,
            Tickets.estado_ticket == True
        ).first()
        
        if not ticket:
            return {
                "success": False,
                "detail": "El ticket no existe o está inactivo."
            }
        
        comentarios = db.query(Comentarios).filter(
            Comentarios.id_ticket == id_ticket
        ).order_by(desc(Comentarios.fecha_creacion)).all()
        
        if not comentarios:
            return {
                "success": True,
                "detail": "No hay comentarios disponibles para este ticket.",
                "data": []
            }
        
        comentarios_list = [
            {
                "nombre_usuario_creador": comentario.nombre_usuario_creador,
                "apellido_usuario_creador": comentario.apellido_usuario_creador,
                "comentario": comentario.comentario,
                "fecha_creacion": comentario.fecha_creacion
            }
            for comentario in comentarios
        ]
        
        return {
            "success": True,
            "detail": "Comentarios obtenidos correctamente.",
            "data": comentarios_list
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "detail": f"Error en la base de datos: {str(e)}"
        }
    finally:
        db.close()
