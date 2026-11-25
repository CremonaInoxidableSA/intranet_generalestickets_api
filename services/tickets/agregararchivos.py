from pathlib import Path
from typing import List, Tuple

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from config.db import SessionLocal
from models.multimedia import Multimedia
from models.multimedia_tickets import MultimediaTickets
from models.tickets import Tickets
from services.tickets.crear import (
    CARPETA_MULTIMEDIA,
    MAX_ARCHIVOS,
    _eliminar_archivos,
    _nombre_disponible,
    _procesar_archivo,
)


async def agregar_archivos_ticket_service(id_ticket: int, archivos: List[UploadFile]) -> dict:
    """
    Agrega archivos multimedia a un ticket existente.
    Valida extensión y tamaño, controla el máximo de archivos por ticket y evita
    colisiones de nombre igual que el servicio de creación.
    Todas las validaciones se hacen antes de escribir en la base de datos o en disco.
    """
    if not archivos:
        raise ValueError("Debe enviar al menos un archivo.")

    archivos_validos: List[Tuple[str, str, bytes]] = []
    errores: List[str] = []

    for archivo in archivos:
        try:
            archivos_validos.append(await _procesar_archivo(archivo))
        except Exception as e:
            errores.append(str(e))

    if not archivos_validos:
        raise ValueError("; ".join(errores))

    db = SessionLocal()
    rutas_creadas: List[Path] = []
    nombres_guardados: List[str] = []
    try:
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == id_ticket
        ).first()

        if not ticket:
            raise ValueError(f"Ticket con ID {id_ticket} no encontrado.")

        total_actual = db.query(MultimediaTickets).filter(
            MultimediaTickets.id_ticket == id_ticket
        ).count()

        if total_actual + len(archivos_validos) > MAX_ARCHIVOS:
            disponibles = max(0, MAX_ARCHIVOS - total_actual)
            raise ValueError(
                f"El ticket {id_ticket} tiene {total_actual} archivo(s). "
                f"Solo se pueden agregar {disponibles} archivo(s) más (máximo {MAX_ARCHIVOS} por ticket)."
            )

        for nombre_original, tipo, contenido in archivos_validos:
            nombre_final = _nombre_disponible(nombre_original)
            ruta = CARPETA_MULTIMEDIA / nombre_final

            rutas_creadas.append(ruta)
            try:
                with open(ruta, "wb") as destino:
                    destino.write(contenido)
            except OSError as e:
                _eliminar_archivos([ruta])
                errores.append(f"El archivo '{nombre_original}' no se pudo guardar: {e}")
                continue

            nombres_guardados.append(nombre_final)
            multimedia = Multimedia(nombre_archivo=nombre_final)
            db.add(multimedia)
            db.flush()

            db.add(MultimediaTickets(
                id_ticket=id_ticket,
                id_multimedia=multimedia.id_multimedia,
                tipo=tipo
            ))

        db.commit()

        respuesta = {
            "success": True,
            "detail": f"Se agregaron {len(nombres_guardados)} archivo(s) al ticket {id_ticket}.",
        }

        if errores:
            respuesta["errores"] = errores

        return respuesta
    except Exception as e:
        db.rollback()
        _eliminar_archivos(rutas_creadas)

        if isinstance(e, SQLAlchemyError):
            raise Exception(f"Error en la base de datos: {str(e)}") from e

        raise
    finally:
        db.close()
