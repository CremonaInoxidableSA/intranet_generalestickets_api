from typing import List

from sqlalchemy.exc import SQLAlchemyError

from config.db import SessionLocal
from models.representantes import Representantes
from models.ticket_involucrados import TicketInvolucrados
from models.ticket_resolutores import TicketResolutores
from models.tickets import Tickets
from schemas.tickets import EditarTicketRequest


ESTADOS_VALIDOS = {"FINALIZADO", "PENDIENTE", "EN PROCESO"}


def _sincronizar_involucrados(db, id_ticket: int, lista) -> None:
    """
    Deja en ticket_involucrados exactamente la lista recibida:
    actualiza los existentes, crea los nuevos y elimina los que ya no están.
    La clave de comparación es id_usuario_interviniente.
    """
    ids_recibidos = [inv.id_usuario_interviniente for inv in lista]
    if len(ids_recibidos) != len(set(ids_recibidos)):
        raise ValueError("La lista de involucrados contiene usuarios repetidos.")

    filas = db.query(TicketInvolucrados).filter(
        TicketInvolucrados.id_ticket == id_ticket
    ).all()
    existentes = {fila.id_usuario_interviniente: fila for fila in filas}

    for inv in lista:
        fila = existentes.get(inv.id_usuario_interviniente)
        if fila is None:
            db.add(TicketInvolucrados(
                id_ticket=id_ticket,
                id_usuario_interviniente=inv.id_usuario_interviniente,
                nombre_usuario_interviniente=inv.nombre_usuario_interviniente,
                apellido_usuario_interviniente=inv.apellido_usuario_interviniente,
                correo=inv.correo
            ))
        else:
            fila.nombre_usuario_interviniente = inv.nombre_usuario_interviniente
            fila.apellido_usuario_interviniente = inv.apellido_usuario_interviniente
            fila.correo = inv.correo

    for fila in filas:
        if fila.id_usuario_interviniente not in ids_recibidos:
            db.delete(fila)


def _sincronizar_resolutores(db, id_ticket: int, lista) -> None:
    """
    Deja en ticket_resolutores exactamente la lista recibida:
    actualiza los existentes, crea los nuevos y elimina los que ya no están.
    La clave de comparación es id_usuario_resolutor.
    """
    ids_recibidos = [res.id_usuario_resolutor for res in lista]
    if len(ids_recibidos) != len(set(ids_recibidos)):
        raise ValueError("La lista de resolutores contiene usuarios repetidos.")

    filas = db.query(TicketResolutores).filter(
        TicketResolutores.id_ticket == id_ticket
    ).all()
    existentes = {fila.id_usuario_resolutor: fila for fila in filas}

    for res in lista:
        fila = existentes.get(res.id_usuario_resolutor)
        if fila is None:
            db.add(TicketResolutores(
                id_ticket=id_ticket,
                id_usuario_resolutor=res.id_usuario_resolutor,
                nombre_usuario_resolutor=res.nombre_usuario_resolutor,
                apellido_usuario_resolutor=res.apellido_usuario_resolutor
            ))
        else:
            fila.nombre_usuario_resolutor = res.nombre_usuario_resolutor
            fila.apellido_usuario_resolutor = res.apellido_usuario_resolutor

    for fila in filas:
        if fila.id_usuario_resolutor not in ids_recibidos:
            db.delete(fila)


def editar_ticket_service(datos: EditarTicketRequest) -> dict:
    """
    Edita un ticket existente. Solo se modifican los campos enviados.
    Todas las validaciones y cambios se hacen en una sola transacción.
    """
    campos_enviados = datos.model_fields_set

    db = SessionLocal()
    try:
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == datos.id_ticket,
            Tickets.estado_ticket == True
        ).first()

        if not ticket:
            raise ValueError(f"Ticket con ID {datos.id_ticket} no encontrado o está inactivo.")

        if datos.id_representante is not None:
            representante = db.query(Representantes).filter(
                Representantes.id_representante == datos.id_representante,
                Representantes.id_cliente == ticket.id_cliente
            ).first()

            if not representante:
                raise ValueError(
                    f"El representante {datos.id_representante} no existe o no pertenece al cliente {ticket.id_cliente}."
                )

            ticket.id_representante = datos.id_representante

        if datos.nombre_proyecto is not None:
            ticket.nombre_proyecto = datos.nombre_proyecto

        if datos.fecha_ocurrencia is not None:
            ticket.fecha_ocurrencia = datos.fecha_ocurrencia

        if datos.descripcion is not None:
            ticket.descripcion = datos.descripcion

        if datos.estado is not None:
            if datos.estado not in ESTADOS_VALIDOS:
                raise ValueError("El estado debe ser 'FINALIZADO', 'PENDIENTE' o 'EN PROCESO'.")
            ticket.estado = datos.estado

        if "resolucion" in campos_enviados:
            ticket.resolucion = datos.resolucion

        if "fecha_resolucion" in campos_enviados:
            ticket.fecha_resolucion = datos.fecha_resolucion

        if "tiempo_empleado" in campos_enviados:
            ticket.tiempo_empleado = datos.tiempo_empleado

        if datos.involucrados is not None:
            _sincronizar_involucrados(db, datos.id_ticket, datos.involucrados)

        if datos.resolutores is not None:
            _sincronizar_resolutores(db, datos.id_ticket, datos.resolutores)

        db.commit()

        return {
            "success": True,
            "detail": f"Ticket {datos.id_ticket} editado correctamente.",
            "data": {
                "id_ticket": datos.id_ticket
            }
        }
    except ValueError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error en la base de datos: {str(e)}")
    finally:
        db.close()
