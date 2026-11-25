from config.db import SessionLocal
from models.representantes import Representantes
from models.tickets import Tickets


def _error(status_code: int, detail: str) -> dict:
    return {
        "success": False,
        "status_code": status_code,
        "detail": detail
    }


def obtener_detalle_ticket_service(id_ticket: int) -> dict:
    """
    Obtiene el detalle de un ticket, incluyendo cliente, representante
    y nombres de los archivos multimedia asociados.
    """
    db = SessionLocal()
    try:
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == id_ticket
        ).first()

        if ticket is None:
            return _error(404, "El ticket no existe.")

        representante = db.query(Representantes).filter(
            Representantes.id_representante == ticket.id_representante
        ).first()

        archivos = [
            vinculo.multimedia.nombre_archivo
            for vinculo in ticket.multimedia_tickets
            if vinculo.multimedia is not None
        ]

        involucrados = [
            {
                "id_usuario_interviniente": involucrado.id_usuario_interviniente,
                "nombre_usuario_interviniente": involucrado.nombre_usuario_interviniente,
                "apellido_usuario_interviniente": involucrado.apellido_usuario_interviniente,
                "correo": involucrado.correo
            }
            for involucrado in ticket.ticket_involucrados
        ]

        resolutores = [
            {
                "id_usuario_resolutor": resolutor.id_usuario_resolutor,
                "nombre_usuario_resolutor": resolutor.nombre_usuario_resolutor,
                "apellido_usuario_resolutor": resolutor.apellido_usuario_resolutor
            }
            for resolutor in ticket.ticket_resolutores
        ]

        return {
            "success": True,
            "detail": "Detalle del ticket obtenido correctamente.",
            "data": {
                "id_ticket": ticket.id_ticket,
                "nombre_usuario_creador": ticket.nombre_usuario_creador,
                "apellido_usuario_creador": ticket.apellido_usuario_creador,
                "nombre_cliente": ticket.clientes.nombre if ticket.clientes else None,
                "nombre_representante": representante.nombre if representante else None,
                "apellido_representante": representante.apellido if representante else None,
                "nombre_proyecto": ticket.nombre_proyecto,
                "fecha_ocurrencia": ticket.fecha_ocurrencia,
                "descripcion": ticket.descripcion,
                "estado": ticket.estado,
                "fecha_resolucion": ticket.fecha_resolucion,
                "tiempo_empleado": ticket.tiempo_empleado,
                "resolucion": ticket.resolucion,
                "archivos": archivos,
                "involucrados": involucrados,
                "resolutores": resolutores
            }
        }
    finally:
        db.close()
