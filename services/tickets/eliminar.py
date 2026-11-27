from config.db import SessionLocal
from models.tickets import Tickets


def eliminar_ticket_service(id_ticket: int) -> dict:
    """
    Desactiva un ticket seteando estado_ticket = False.
    """
    db = SessionLocal()
    try:
        ticket = db.query(Tickets).filter(Tickets.id_ticket == id_ticket).first()

        if not ticket:
            raise ValueError(f"Ticket con ID {id_ticket} no encontrado.")

        if not ticket.estado_ticket:
            raise ValueError(f"El ticket {id_ticket} ya está desactivado.")

        ticket.estado_ticket = False
        db.commit()

        return {
            "success": True,
            "detail": f"Ticket {id_ticket} eliminado correctamente.",
            "data": {
                "id_ticket": id_ticket
            }
        }

    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
