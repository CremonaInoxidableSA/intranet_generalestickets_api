from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from config.db import SessionLocal
from models.clientes import Clientes
from models.multimedia import Multimedia
from models.multimedia_tickets import MultimediaTickets
from models.representantes import Representantes
from models.ticket_involucrados import TicketInvolucrados
from models.ticket_resolutores import TicketResolutores
from models.tickets import Tickets
from schemas.authenticated_user import AuthenticatedUser
from schemas.tickets import InvolucradoCrear, ResolutorCrear


CARPETA_MULTIMEDIA = Path(__file__).resolve().parents[2] / "archivos" / "multimedia"
CARPETA_MULTIMEDIA.mkdir(parents=True, exist_ok=True)

MAX_ARCHIVOS = 5
MAX_BYTES_ARCHIVO = 10 * 1024 * 1024
LONGITUD_MAX_TEXTO = 255
LONGITUD_MAX_NOMBRE_ARCHIVO = 255

EXTENSIONES_PERMITIDAS = {
    ".mp4": ".mp4",
    ".png": ".png",
    ".jpeg": ".jpeg",
    ".jpg": ".jpg",
    ".pdf": ".pdf",
    ".doc": ".doc",
    ".docx": ".docx",
    ".xls": ".xls",
    ".xlsx": ".xlsx",
}


def _limpiar_texto(valor: Optional[str], campo: str, obligatorio: bool) -> Optional[str]:
    if valor is None or not valor.strip():
        if obligatorio:
            raise ValueError(f"El campo '{campo}' no puede estar vacío.")
        return None

    texto = valor.strip()

    if len(texto) > LONGITUD_MAX_TEXTO:
        raise ValueError(f"El campo '{campo}' no puede superar los {LONGITUD_MAX_TEXTO} caracteres.")

    return texto


async def _procesar_archivo(archivo: UploadFile) -> Tuple[str, str, bytes]:
    """
    Valida nombre, extensión y tamaño de un archivo y lo lee en memoria.
    Devuelve (nombre_original, tipo, contenido). No escribe nada en disco.
    """
    nombre = Path(archivo.filename or "").name

    if not nombre:
        raise ValueError("Uno de los archivos no tiene nombre.")

    if len(nombre) > LONGITUD_MAX_NOMBRE_ARCHIVO:
        raise ValueError(f"El nombre del archivo '{nombre}' supera los {LONGITUD_MAX_NOMBRE_ARCHIVO} caracteres.")

    extension = Path(nombre).suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        permitidas = ", ".join(EXTENSIONES_PERMITIDAS.keys())
        raise ValueError(
            f"El archivo '{nombre}' no se cargó, extensión no permitida. Extensiones permitidas: {permitidas}."
        )

    contenido = await archivo.read()

    if len(contenido) == 0:
        raise ValueError(f"El archivo '{nombre}' está vacío.")

    if len(contenido) > MAX_BYTES_ARCHIVO:
        raise ValueError(f"El archivo '{nombre}' supera el tamaño máximo de 10 MB.")

    return nombre, EXTENSIONES_PERMITIDAS[extension], contenido


def _nombre_disponible(nombre: str) -> str:
    """
    Devuelve el nombre original si está libre en la carpeta multimedia.
    Si ya existe, agrega un sufijo: 'archivo (1).pdf', 'archivo (2).pdf', etc.
    """
    base = Path(nombre).stem
    extension = Path(nombre).suffix
    candidato = nombre
    contador = 1

    while (CARPETA_MULTIMEDIA / candidato).exists():
        candidato = f"{base} ({contador}){extension}"
        contador += 1

    return candidato


def _eliminar_archivos(rutas: List[Path]):
    for ruta in rutas:
        try:
            ruta.unlink(missing_ok=True)
        except OSError:
            pass


async def crear_ticket_service(
    usuario: AuthenticatedUser,
    id_cliente: int,
    id_representante: Optional[int],
    nombre_proyecto: str,
    descripcion: str,
    estado: str,
    fecha_ocurrencia: datetime,
    resolucion: Optional[str],
    fecha_resolucion: Optional[datetime],
    tiempo_empleado: Optional[int],
    archivos: List[UploadFile],
    involucrados: Optional[List[InvolucradoCrear]] = None,
    resolutores: Optional[List[ResolutorCrear]] = None
):
    """
    Crea un ticket con sus archivos multimedia.
    Todas las validaciones se hacen antes de escribir en la base de datos o en disco.
    """
    nombre_creador = _limpiar_texto(usuario.first_name, "nombre del usuario creador", True)
    apellido_creador = _limpiar_texto(usuario.last_name, "apellido del usuario creador", True)
    proyecto = _limpiar_texto(nombre_proyecto, "nombre_proyecto", True)
    descripcion_limpia = _limpiar_texto(descripcion, "descripcion", True)
    resolucion_limpia = _limpiar_texto(resolucion, "resolucion", False)

    if tiempo_empleado is not None and tiempo_empleado < 0:
        raise ValueError("El tiempo_empleado no puede ser negativo.")

    if estado is None or (estado.strip() != "FINALIZADO" and estado.strip() != "PENDIENTE" and estado.strip() != "EN PROCESO"):
        raise ValueError("El estado no puede estar vacío y debe ser 'FINALIZADO', 'PENDIENTE' o 'EN PROCESO'.")

    if len(archivos) > MAX_ARCHIVOS:
        raise ValueError(f"Se permiten como máximo {MAX_ARCHIVOS} archivos por ticket.")

    archivos_validos: List[Tuple[str, str, bytes]] = []
    errores: List[str] = []

    for archivo in archivos:
        try:
            archivos_validos.append(await _procesar_archivo(archivo))
        except Exception as e:
            errores.append(str(e))

    db = SessionLocal()
    rutas_creadas: List[Path] = []
    nombres_guardados: List[str] = []
    try:
        cliente = db.query(Clientes).filter(
            Clientes.id_cliente == id_cliente
        ).first()

        if not cliente:
            raise ValueError(f"Cliente con ID {id_cliente} no encontrado.")

        representante = db.query(Representantes).filter(
            Representantes.id_representante == id_representante,
            Representantes.id_cliente == id_cliente
        ).first()

        if not representante:
            raise ValueError(
                f"El representante {id_representante} no existe o no pertenece al cliente {id_cliente}."
            )

        nuevo_ticket = Tickets(
            id_usuario_creador=usuario.id,
            nombre_usuario_creador=nombre_creador,
            apellido_usuario_creador=apellido_creador,
            fecha_creacion=datetime.now(),
            id_cliente=id_cliente,
            id_representante=id_representante,
            nombre_proyecto=proyecto,
            descripcion=descripcion_limpia,
            fecha_ocurrencia=fecha_ocurrencia,
            estado=estado,
            resolucion=resolucion_limpia,
            fecha_resolucion=fecha_resolucion,
            tiempo_empleado=tiempo_empleado
        )

        db.add(nuevo_ticket)
        db.flush()
        id_ticket = nuevo_ticket.id_ticket

        for inv in involucrados or []:
            db.add(TicketInvolucrados(
                id_ticket=id_ticket,
                id_usuario_interviniente=inv.id_usuario_interviniente,
                nombre_usuario_interviniente=inv.nombre_usuario_interviniente,
                apellido_usuario_interviniente=inv.apellido_usuario_interviniente,
                correo=inv.correo
            ))

        for res in resolutores or []:
            db.add(TicketResolutores(
                id_ticket=id_ticket,
                id_usuario_resolutor=res.id_usuario_resolutor,
                nombre_usuario_resolutor=res.nombre_usuario_resolutor,
                apellido_usuario_resolutor=res.apellido_usuario_resolutor
            ))

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
            "detail": f"Ticket {id_ticket} creado correctamente.",
            "data": {
                "id_ticket": id_ticket,
                "archivos": nombres_guardados
            }
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
