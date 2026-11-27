from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from config.db import SessionLocal
from models.hilos import Hilos
from models.hilo_tickets import HiloTickets
from models.tickets import Tickets


CARPETA_HILOSCORREOS = Path("/app/archivos/hiloscorreos")
CARPETA_HILOSCORREOS.mkdir(parents=True, exist_ok=True)

MAX_BYTES_ARCHIVO = 50 * 1024 * 1024
LONGITUD_MAX_NOMBRE_ARCHIVO = 255

EXTENSIONES_PERMITIDAS = {
    ".eml": ".eml",
}


async def _procesar_archivo_eml(archivo: UploadFile) -> Tuple[str, bytes]:
    """
    Valida nombre, extensión y tamaño de un archivo EML y lo lee en memoria.
    Devuelve (nombre_original, contenido). No escribe nada en disco.
    """
    nombre = Path(archivo.filename or "").name

    if not nombre:
        raise ValueError("El archivo no tiene nombre.")

    if len(nombre) > LONGITUD_MAX_NOMBRE_ARCHIVO:
        raise ValueError(f"El nombre del archivo '{nombre}' supera los {LONGITUD_MAX_NOMBRE_ARCHIVO} caracteres.")

    extension = Path(nombre).suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError(
            f"El archivo '{nombre}' no se cargó. Solo se permiten archivos .eml"
        )

    contenido = await archivo.read()

    if len(contenido) == 0:
        raise ValueError(f"El archivo '{nombre}' está vacío.")

    if len(contenido) > MAX_BYTES_ARCHIVO:
        raise ValueError(f"El archivo '{nombre}' supera el tamaño máximo de 50 MB.")

    return nombre, contenido


def _nombre_disponible(nombre: str) -> str:
    """
    Devuelve el nombre original si está libre en la carpeta hiloscorreos.
    Si ya existe, agrega un sufijo: 'archivo (1).eml', 'archivo (2).eml', etc.
    """
    base = Path(nombre).stem
    extension = Path(nombre).suffix
    candidato = nombre
    contador = 1

    while (CARPETA_HILOSCORREOS / candidato).exists():
        candidato = f"{base} ({contador}){extension}"
        contador += 1

    return candidato


def _eliminar_archivos(rutas: list) -> None:
    """
    Elimina archivos del disco. Ignora errores individuales.
    """
    for ruta in rutas:
        try:
            if ruta.exists():
                ruta.unlink()
        except Exception:
            pass


async def guardar_archivo_eml_service(id_ticket: int, archivo: UploadFile) -> dict:
    """
    Recibe un archivo EML, lo valida, lo guarda en disco y crea registros en la base de datos.
    Vincula el archivo al ticket mediante la tabla hilo_tickets.
    """
    if not archivo:
        raise ValueError("Debe enviar un archivo EML.")

    if not id_ticket:
        raise ValueError("Debe proporcionar un id_ticket.")

    try:
        nombre_original, contenido = await _procesar_archivo_eml(archivo)
    except Exception as e:
        raise ValueError(str(e))

    db = SessionLocal()
    ruta_creada: Path = None
    try:
        ticket = db.query(Tickets).filter(
            Tickets.id_ticket == id_ticket,
            Tickets.estado_ticket == True
        ).first()
        if not ticket:
            raise ValueError(f"Ticket con ID {id_ticket} no encontrado o está inactivo.")

        # Validar que no existan 3 o más hilos para este ticket
        cantidad_hilos = db.query(HiloTickets).filter(
            HiloTickets.id_ticket == id_ticket
        ).count()
        
        if cantidad_hilos >= 3:
            raise ValueError(f"El ticket {id_ticket} ya tiene 3 hilos. No se pueden agregar más.")

        nombre_final = _nombre_disponible(nombre_original)
        ruta = CARPETA_HILOSCORREOS / nombre_final

        ruta_creada = ruta
        try:
            with open(ruta, "wb") as destino:
                destino.write(contenido)
        except OSError as e:
            _eliminar_archivos([ruta])
            raise Exception(f"El archivo '{nombre_original}' no se pudo guardar: {e}")

        hilo = Hilos(nombre_archivo=nombre_final)
        db.add(hilo)
        db.flush()

        hilo_ticket = HiloTickets(
            id_ticket=id_ticket,
            id_hilo=hilo.id_hilo
        )
        db.add(hilo_ticket)
        db.commit()

        return {
            "success": True,
            "detail": f"Archivo EML '{nombre_original}' guardado correctamente y vinculado al ticket."
        }
    except Exception as e:
        db.rollback()
        if ruta_creada:
            _eliminar_archivos([ruta_creada])

        if isinstance(e, SQLAlchemyError):
            raise Exception(f"Error en la base de datos: {str(e)}") from e

        raise
    finally:
        db.close()

