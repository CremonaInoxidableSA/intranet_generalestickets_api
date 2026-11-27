from pathlib import Path
from typing import Dict
from email import message_from_binary_file, policy

from config.db import SessionLocal
from models.hilos import Hilos
from models.hilo_tickets import HiloTickets
from models.tickets import Tickets
from services.hiloscorreos.html_correo import (
    dividir_hilo_html,
    extraer_imagenes_embebidas,
    extraer_remitente,
    lista_direcciones,
    texto_plano_a_html,
)


CARPETA_HILOSCORREOS = Path("/app/archivos/hiloscorreos")


def _decodificar_payload(part) -> str:
    """
    Decodifica el payload de una parte del email intentando detectar
    la codificación correcta para preservar caracteres con tilde y especiales.
    """
    try:
        payload_bytes = part.get_payload(decode=True)
        if not payload_bytes:
            return ""
        
        charset = part.get_content_charset()
        
        encodings = []
        if charset:
            encodings.append(charset)
        encodings.extend(['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'ascii'])
        
        texto = None
        for encoding in encodings:
            try:
                texto = payload_bytes.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if texto is None:
            texto = payload_bytes.decode('latin-1', errors='replace')
        
        # Normalizar saltos de línea: convertir \r\n a \n
        texto = texto.replace('\r\n', '\n').replace('\r', '\n')
        
        return texto
    except Exception:
        return ""


def _cabecera_del_mensaje(msg) -> Dict:
    """Remitente, destinatarios, asunto y fecha tomados de los encabezados MIME del mensaje."""
    def valor(nombre: str) -> str:
        return ", ".join(str(h) for h in msg.get_all(nombre, []))

    return {
        "remitente": extraer_remitente(valor("From")),
        "asunto": str(msg.get("Subject", "") or ""),
        "destinatarios": lista_direcciones(valor("To")),
        "cc": lista_direcciones(valor("Cc")),
        "bcc": lista_direcciones(valor("Bcc")),
        "fecha": str(msg.get("Date", "") or ""),
    }


async def leer_archivo_eml_service(id_ticket: int, id_hilo: int) -> dict:
    """
    Lee un archivo EML y devuelve cada correo del hilo por separado con su cuerpo en HTML
    (sanitizado, con estilos, tablas, listas e imágenes de contenido embebidas en base64).
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
        if not ruta_archivo.exists():
            raise ValueError(f"El archivo EML no existe en el servidor.")

        with open(ruta_archivo, 'rb') as f:
            msg = message_from_binary_file(f, policy=policy.default)

        imagenes = extraer_imagenes_embebidas(msg)

        parte_html = msg.get_body(preferencelist=("html",))
        if parte_html is not None:
            segmentos = dividir_hilo_html(_decodificar_payload(parte_html), imagenes)
        else:
            # Correo sin parte HTML: se muestra como un único correo con el texto plano
            parte_texto = msg.get_body(preferencelist=("plain",))
            html_texto = texto_plano_a_html(_decodificar_payload(parte_texto)) if parte_texto is not None else ""
            segmentos = [{"cabecera": None, "cuerpo_html": html_texto}] if html_texto else []

        correos = []
        for indice, segmento in enumerate(segmentos):
            # El correo más reciente toma sus datos de los encabezados MIME;
            # los citados, del bloque "De / Enviado / Para / Asunto" del propio HTML.
            cabecera = _cabecera_del_mensaje(msg) if indice == 0 else segmento["cabecera"]
            correos.append({**cabecera, "cuerpo_html": segmento["cuerpo_html"]})

        return {
            "id_hilo": id_hilo,
            "id_ticket": id_ticket,
            "correos": correos
        }
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error al leer el archivo EML: {str(e)}")
    finally:
        db.close()
