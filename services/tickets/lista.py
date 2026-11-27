from config.db import SessionLocal
from models.tickets import Tickets


def _serializar_ticket(ticket: Tickets) -> dict:
    return {
        "id_ticket": ticket.id_ticket,
        "nombre_cliente": ticket.clientes.nombre if ticket.clientes else None,
        "nombre_proyecto": ticket.nombre_proyecto,
        "fecha_ocurrencia": ticket.fecha_ocurrencia,
        "descripcion": ticket.descripcion,
        "estado": ticket.estado
    }


def listar_tickets_service() -> dict:
    db = SessionLocal()
    try:
        tickets = db.query(Tickets).filter(Tickets.estado_ticket == True).order_by(Tickets.fecha_creacion.desc()).all()
        data = [_serializar_ticket(ticket) for ticket in tickets]

        return {
            "success": True,
            "detail": f"Se encontraron {len(data)} ticket(s).",
            "data": data
        }

    finally:
        db.close()
