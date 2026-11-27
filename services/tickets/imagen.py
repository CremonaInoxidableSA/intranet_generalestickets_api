from pathlib import Path

from config.db import SessionLocal
from models.multimedia import Multimedia
from models.multimedia_tickets import MultimediaTickets
from models.tickets import Tickets
from services.tickets.crear import CARPETA_MULTIMEDIA, EXTENSIONES_PERMITIDAS


CARPETA_ICONOS = Path(__file__).resolve().parents[2] / "archivos" / "utils"

MEDIA_TYPES_IMAGEN = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

ICONOS = {
    ".pdf": "PDF.png",
    ".doc": "WORD.png",
    ".docx": "WORD.png",
    ".xls": "XLSX.png",
    ".xlsx": "XLSX.png",
    ".mp4": "MP4.png",
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
    if extension == ".png":
        return cabecera.startswith(b"\x89PNG\r\n\x1a\n")
    return cabecera.startswith(b"\xff\xd8\xff")


def validar_acceso_imagen(nombre_archivo: str) -> dict:
    """
    Devuelve la ruta a mostrar para un archivo consultado por nombre:
    - Imágenes (png, jpg, jpeg): el propio archivo, validando su contenido.
    - Otros tipos: el ícono correspondiente.
    """
    nombre = (nombre_archivo or "").strip()

    if not nombre or ".." in nombre or "/" in nombre or "\\" in nombre:
        return _error(400, "Nombre de archivo inválido.")

    extension = Path(nombre).suffix.lower()

    if extension not in EXTENSIONES_PERMITIDAS:
        return _error(400, "El archivo no es un archivo válido.")

    db = SessionLocal()
    try:
        vinculo = db.query(MultimediaTickets).join(
            Multimedia, Multimedia.id_multimedia == MultimediaTickets.id_multimedia
        ).join(
            Tickets, Tickets.id_ticket == MultimediaTickets.id_ticket
        ).filter(
            Multimedia.nombre_archivo == nombre,
            Tickets.estado_ticket == True
        ).first()
    finally:
        db.close()

    if vinculo is None:
        return _error(404, "El archivo no existe, no está asociado a ningún ticket o el ticket está inactivo.")

    ruta = CARPETA_MULTIMEDIA / nombre

    if not ruta.is_file():
        return _error(404, "Archivo no encontrado en el servidor.")

    if extension in MEDIA_TYPES_IMAGEN:
        if not _firma_valida(ruta, extension):
            return _error(400, f"El contenido del archivo no coincide con la extensión {extension}.")

        return {
            "success": True,
            "ruta": str(ruta),
            "nombre_archivo": nombre,
            "media_type": MEDIA_TYPES_IMAGEN[extension]
        }

    nombre_icono = ICONOS.get(extension)

    if nombre_icono is None or not (CARPETA_ICONOS / nombre_icono).is_file():
        return _error(404, f"Ícono no encontrado para la extensión {extension}.")

    return {
        "success": True,
        "ruta": str(CARPETA_ICONOS / nombre_icono),
        "nombre_archivo": nombre,
        "media_type": "image/png"
    }
