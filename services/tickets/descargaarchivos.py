from pathlib import Path

from config.db import SessionLocal
from models.multimedia import Multimedia
from models.multimedia_tickets import MultimediaTickets
from services.tickets.crear import CARPETA_MULTIMEDIA


FIRMA_OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
FIRMA_ZIP = b"PK\x03\x04"

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".mp4": "video/mp4",
}


def _error(status_code: int, detail: str) -> dict:
    return {
        "success": False,
        "status_code": status_code,
        "detail": detail
    }


def _firma_valida(ruta: Path, extension: str) -> bool:
    with open(ruta, "rb") as f:
        cabecera = f.read(1024)

    if extension == ".pdf":
        return b"%PDF" in cabecera
    if extension == ".mp4":
        return cabecera[4:8] == b"ftyp"
    if extension in (".docx", ".xlsx"):
        return cabecera.startswith(FIRMA_ZIP)
    return cabecera.startswith(FIRMA_OLE2)


def validar_descarga_archivo(id_ticket: int, nombre_archivo: str) -> dict:
    """
    Valida que el archivo (PDF, Word, Excel o video) exista, esté asociado al ticket indicado
    y que su contenido coincida con su extensión.
    """
    nombre = (nombre_archivo or "").strip()

    if not nombre or ".." in nombre or "/" in nombre or "\\" in nombre:
        return _error(400, "Nombre de archivo inválido.")

    extension = Path(nombre).suffix.lower()

    if extension not in MEDIA_TYPES:
        return _error(400, "El tipo de archivo no es válido para descarga.")

    db = SessionLocal()
    try:
        vinculo = db.query(MultimediaTickets).join(
            Multimedia, Multimedia.id_multimedia == MultimediaTickets.id_multimedia
        ).filter(
            MultimediaTickets.id_ticket == id_ticket,
            Multimedia.nombre_archivo == nombre
        ).first()
    finally:
        db.close()

    if vinculo is None:
        return _error(404, "El archivo no existe o no está asociado al ticket indicado.")

    ruta = CARPETA_MULTIMEDIA / nombre

    if not ruta.is_file():
        return _error(404, "Archivo no encontrado en el servidor.")

    if not _firma_valida(ruta, extension):
        return _error(400, f"El contenido del archivo no coincide con la extensión {extension}.")

    return {
        "success": True,
        "ruta": str(ruta),
        "nombre_archivo": nombre,
        "media_type": MEDIA_TYPES[extension]
    }
