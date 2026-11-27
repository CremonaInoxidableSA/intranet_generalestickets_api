from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from config.db import SessionLocal
from models.hilos import Hilos
from models.hilo_tickets import HiloTickets
from models.tickets import Tickets


CARPETA_HILOSCORREOS = Path("/app/archivos/hiloscorreos")


def _eliminar_archivo(ruta: Path) -> None:
    """
    Elimina un archivo del disco. Ignora errores individuales.
    """
    try:
        if ruta.exists():
            ruta.unlink()
    except Exception:
        pass


async def eliminar_hilo_service(id_ticket: int, id_hilo: int) -> dict:
    """
    Elimina un hilo completamente: registro en hilo_tickets, hilos y archivo físico.
    """
    if not id_ticket or not id_hilo:
        raise ValueError("Debe proporcionar id_ticket e id_hilo.")

    db = SessionLocal()
    try:
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == id_ticket,
            Tickets.estado_ticket == True
        ).first()
        if not ticket:
            raise ValueError(f"Ticket con ID {id_ticket} no encontrado o está inactivo.")

        hilo = db.query(Hilos).filter(Hilos.id_hilo == id_hilo).first()
        if not hilo:
            raise ValueError(f"Hilo con ID {id_hilo} no encontrado.")

        hilo_ticket = db.query(HiloTickets).filter(
            HiloTickets.id_ticket == id_ticket,
            HiloTickets.id_hilo == id_hilo
        ).first()
        if not hilo_ticket:
            raise ValueError(f"El hilo {id_hilo} no está vinculado al ticket {id_ticket}.")

        ruta_archivo = CARPETA_HILOSCORREOS / hilo.nombre_archivo

        db.delete(hilo_ticket)
        db.delete(hilo)
        db.commit()

        _eliminar_archivo(ruta_archivo)

        return {
            "success": True,
            "detail": f"Hilo {id_hilo} eliminado correctamente.",
            "id_hilo": id_hilo,
            "id_ticket": id_ticket,
        }
    except ValueError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        if isinstance(e, SQLAlchemyError):
            raise Exception(f"Error en la base de datos: {str(e)}") from e
        raise
    finally:
        db.close()
