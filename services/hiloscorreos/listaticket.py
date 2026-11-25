from config.db import SessionLocal
from models.hilo_tickets import HiloTickets
from models.hilos import Hilos
from sqlalchemy.exc import SQLAlchemyError


def listar_hilos_por_ticket_service(id_ticket: int):
    """
    Obtiene la lista de hilos (archivos EML) de un ticket específico.
    """
    db = SessionLocal()
    try:
        hilos = db.query(Hilos).join(
            HiloTickets, Hilos.id_hilo == HiloTickets.id_hilo
        ).filter(
            HiloTickets.id_ticket == id_ticket
        ).all()
        
        if not hilos:
            return {
                "success": True,
                "detail": "No hay hilos disponibles para este ticket.",
                "data": []
            }
        
        hilos_list = [
            {
                "id_hilo": hilo.id_hilo,
                "nombre_archivo": hilo.nombre_archivo
            }
            for hilo in hilos
        ]
        
        return {
            "success": True,
            "detail": "Hilos obtenidos correctamente.",
            "data": hilos_list
        }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "detail": f"Error en la base de datos: {str(e)}"
        }
    finally:
        db.close()
