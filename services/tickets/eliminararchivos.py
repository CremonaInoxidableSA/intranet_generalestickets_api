from sqlalchemy.exc import SQLAlchemyError

from config.db import SessionLocal
from models.multimedia import Multimedia
from models.multimedia_tickets import MultimediaTickets
from models.tickets import Tickets
from services.tickets.crear import CARPETA_MULTIMEDIA


def _error(status_code: int, detail: str) -> dict:
    return {
        "success": False,
        "status_code": status_code,
        "detail": detail
    }


def eliminar_archivo_ticket_service(id_ticket: int, nombre_archivo: str) -> dict:
    """
    Elimina un archivo multimedia asociado a un ticket.
    Quita el vínculo en multimedia_tickets y, si ningún otro ticket usa el archivo,
    elimina también el registro en multimedia y el archivo de la carpeta multimedia.
    """
    nombre = (nombre_archivo or "").strip()

    if not nombre or ".." in nombre or "/" in nombre or "\\" in nombre:
        return _error(400, "Nombre de archivo inválido.")

    db = SessionLocal()
    try:
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == id_ticket,
            Tickets.estado_ticket == True
        ).first()

        if not ticket:
            return _error(404, f"Ticket con ID {id_ticket} no encontrado o está inactivo.")

        vinculo = db.query(MultimediaTickets).join(
            Multimedia, Multimedia.id_multimedia == MultimediaTickets.id_multimedia
        ).filter(
            MultimediaTickets.id_ticket == id_ticket,
            Multimedia.nombre_archivo == nombre
        ).first()

        if vinculo is None:
            return _error(404, f"El archivo '{nombre}' no pertenece al ticket {id_ticket}.")

        multimedia = vinculo.multimedia
        db.delete(vinculo)
        db.flush()

        otros_vinculos = db.query(MultimediaTickets).filter(
            MultimediaTickets.id_multimedia == multimedia.id_multimedia
        ).count()

        eliminar_fisico = otros_vinculos == 0

        if eliminar_fisico:
            db.delete(multimedia)
            db.flush()
            (CARPETA_MULTIMEDIA / nombre).unlink(missing_ok=True)

        db.commit()

        return {
            "success": True,
            "detail": f"Archivo '{nombre}' eliminado del ticket {id_ticket}.",
        }
    except OSError as e:
        db.rollback()
        return _error(500, f"No se pudo eliminar el archivo del servidor: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        return _error(500, f"Error en la base de datos: {e}")
    finally:
        db.close()
