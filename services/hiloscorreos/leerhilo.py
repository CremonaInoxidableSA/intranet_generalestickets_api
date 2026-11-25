from pathlib import Path
from typing import Optional, List, Dict
from email import message_from_binary_file
import base64
import re

from config.db import SessionLocal
from models.hilos import Hilos
from models.hilo_tickets import HiloTickets
from models.tickets import Tickets


CARPETA_HILOSCORREOS = Path(__file__).resolve().parents[2] / "archivos" / "hiloscorreos"


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
                texto = payload_bytes.decode(encoding, errors='replace')
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


def _extraer_imagenes_embebidas(msg) -> Dict[str, str]:
    """
    Extrae imágenes embebidas del email y las convierte a base64.
    Devuelve un diccionario con cid como clave y URL base64 como valor.
    """
    imagenes = {}
    
    for part in msg.walk():
        if part.get_content_disposition() == "inline":
            content_type = part.get_content_type()
            if content_type.startswith("image/"):
                content_id = part.get("Content-ID", "").strip("<>")
                if content_id:
                    try:
                        imagen_data = part.get_payload(decode=True)
                        b64_imagen = base64.b64encode(imagen_data).decode('utf-8')
                        imagenes[content_id] = f"data:{content_type};base64,{b64_imagen}"
                    except Exception:
                        pass
    
    return imagenes


def _reemplazar_cid_en_html(html: str, imagenes: Dict[str, str]) -> str:
    """
    Reemplaza referencias cid: en el HTML por URLs base64.
    """
    if not html or not imagenes:
        return html
    
    for cid, url_base64 in imagenes.items():
        html = html.replace(f"cid:{cid}", url_base64)
    
    return html


def _limpiar_referencias_cid(texto: str) -> str:
    """
    Elimina referencias [cid:...] del texto plano.
    También elimina saltos de línea después de las referencias.
    """
    if not texto:
        return texto
    
    texto = re.sub(r'\[\s*cid:[^\]]*\s*\]\s*\n', '', texto)

    texto = re.sub(r'\[\s*cid:[^\]]*\s*\]', '', texto)
    
    return texto


def _normalizar_viñetas(texto: str) -> str:
    """
    Normaliza viñetas cuando están separadas del contenido por saltos de línea.
    Convierte:
        *
        Hola
    En:
        * Hola
    """
    if not texto:
        return texto
    
    lineas = texto.split('\n')
    lineas_normalizadas = []
    i = 0
    
    while i < len(lineas):
        linea = lineas[i]
        linea_stripped = linea.strip()
        
        if linea_stripped in ('*', '-', '•', '◦', '+'):
            if i + 1 < len(lineas) and lineas[i + 1].strip():
                lineas_normalizadas.append(linea_stripped + ' ' + lineas[i + 1].strip())
                i += 2
                continue
        
        lineas_normalizadas.append(linea)
        i += 1
    
    return '\n'.join(lineas_normalizadas)


def _eliminar_saltos_linea_multiples(texto: str) -> str:
    """
    Elimina saltos de línea múltiples consecutivos, dejando solo uno.
    """
    if not texto:
        return texto
    
    texto = re.sub(r'\n{2,}', '\n\n', texto)
    
    return texto.strip()


def _parsear_correos_del_hilo(cuerpo_texto: str) -> List[Dict]:
    """
    Separa y parsea cada correo individual del hilo.
    El primer correo puede no tener "De:" (es el remitente principal).
    Los siguientes correos están separados por líneas de guiones/subrayos y contienen "De:".
    """
    if not cuerpo_texto:
        return []
    
    correos = []
    
    patron_separador = r'^_{5,}|-{5,}={5,}'
    patron_inicio_de = r"^De:\s+(.+?)\s*<(.+?)>\s*$"
    
    lineas = cuerpo_texto.split('\n')
    
    indices_separadores = []
    for i, linea in enumerate(lineas):
        if re.match(patron_separador, linea.strip()):
            indices_separadores.append(i)
    
    # Si no hay separadores, asumir que todo es un solo correo
    if not indices_separadores:
        correo_parseado = _parsear_correo_individual(cuerpo_texto)
        if correo_parseado:
            correos.append(correo_parseado)
        return correos
    
    # Primer correo: desde el inicio hasta el primer separador
    primer_correo_text = '\n'.join(lineas[:indices_separadores[0]])
    if primer_correo_text.strip():
        correo_parseado = _parsear_correo_individual(primer_correo_text)
        if correo_parseado:
            correos.append(correo_parseado)
    
    # Correos siguientes: entre separadores
    for i in range(len(indices_separadores)):
        inicio = indices_separadores[i] + 1
        fin = indices_separadores[i + 1] if i + 1 < len(indices_separadores) else len(lineas)
        
        correo_text = '\n'.join(lineas[inicio:fin])
        if correo_text.strip():
            correo_parseado = _parsear_correo_individual(correo_text)
            if correo_parseado:
                correos.append(correo_parseado)
    
    return correos

def _eliminar_firma(texto: str) -> str:
    """
    Elimina la firma del correo detectando patrones comunes.
    Solo elimina si hay separadores claros (===, ---, ___) o múltiples patrones de firma juntos.
    """
    if not texto:
        return texto
    
    lineas = texto.split('\n')
    lineas_sin_firma = []
    
    # Patrones de separadores de firma (más confiables)
    patrones_separador = [
        r'^={5,}',
        r'^-{5,}',
        r'^_{5,}',
    ]
    
    # Patrones que indican firma (títulos y contacto específicos)
    patrones_titulo = [
        r'Software Developer',
        r'Ingeniero de Sistemas',
        r'Coordinador de Sistemas',
        r'Jefe de',
        r'Director de',
        r'Manager',
    ]
    
    for i, linea in enumerate(lineas):
        linea_lower = linea.lower().strip()
        
        # Buscar separadores claros
        hay_separador = any(re.search(patron, linea, re.IGNORECASE) for patron in patrones_separador)
        
        if hay_separador:
            # Eliminar esta línea y todo lo que sigue
            break
        
        # Buscar líneas con patrones de firma fuerte
        hay_patron_firma = any(re.search(patron, linea, re.IGNORECASE) for patron in patrones_titulo)
        
        # Si encontramos un patrón de firma fuerte, revisar si tiene contacto también
        if hay_patron_firma:
            # Buscar patrones de contacto en las próximas líneas
            lineas_proximas = '\n'.join(lineas[i:i+5]).lower()
            tiene_contacto = any([
                re.search(r'cel:?\s*\+?[\d\s]+', lineas_proximas),
                re.search(r'teléfono:?\s*\+?[\d\s]+', lineas_proximas),
                re.search(r'(creminox|empresa|company)\.com', lineas_proximas),
                re.search(r'\[cid:', '\n'.join(lineas[i:i+3]))
            ])
            
            if tiene_contacto:
                break
        
        lineas_sin_firma.append(linea)
    
    # Limpiar líneas en blanco al final
    while lineas_sin_firma and lineas_sin_firma[-1].strip() == '':
        lineas_sin_firma.pop()
    
    return '\n'.join(lineas_sin_firma).strip()


def _parsear_correo_individual(texto_correo: str) -> dict:
    """
    Parsea un correo individual y extrae sus campos.
    """
    correo = {
        "remitente": "",
        "asunto": "",
        "destinatarios": [],
        "cc": [],
        "bcc": [],
        "fecha": "",
        "cuerpo_texto": ""
    }
    
    lineas = texto_correo.split('\n')
    cuerpo_inicio = -1
    
    for i, linea in enumerate(lineas):
        linea_lower = linea.lower()
        
        if linea_lower.startswith('de:'):
            match = re.search(r'<(.+?)>', linea)
            if match:
                correo["remitente"] = match.group(1)
            else:
                correo["remitente"] = linea.replace('De:', '').strip()
        
        elif linea_lower.startswith('asunto:'):
            correo["asunto"] = linea.replace('Asunto:', '').replace('asunto:', '').strip()
        
        elif linea_lower.startswith('enviado:') or linea_lower.startswith('date:'):
            correo["fecha"] = linea.split(':', 1)[1].strip() if ':' in linea else linea
        
        elif linea_lower.startswith('para:'):
            destinatarios_str = linea.replace('Para:', '').replace('para:', '').strip()
            correo["destinatarios"] = [addr.strip() for addr in destinatarios_str.split(',') if addr.strip()]
        
        elif linea_lower.startswith('cc:'):
            cc_str = linea.replace('CC:', '').replace('Cc:', '').replace('cc:', '').strip()
            correo["cc"] = [addr.strip() for addr in cc_str.split(',') if addr.strip()]
        
        elif linea_lower.startswith('bcc:'):
            bcc_str = linea.replace('BCC:', '').replace('Bcc:', '').replace('bcc:', '').strip()
            correo["bcc"] = [addr.strip() for addr in bcc_str.split(',') if addr.strip()]
        
        elif cuerpo_inicio == -1 and linea.strip() == '' and i > 0:
            if correo["remitente"]:
                cuerpo_inicio = i + 1
                break
    
    if cuerpo_inicio != -1:
        cuerpo_lineas = lineas[cuerpo_inicio:]
        correo["cuerpo_texto"] = '\n'.join(cuerpo_lineas).strip()
        
        correo["cuerpo_texto"] = _eliminar_firma(correo["cuerpo_texto"])
        correo["cuerpo_texto"] = _limpiar_referencias_cid(correo["cuerpo_texto"])
        correo["cuerpo_texto"] = _normalizar_viñetas(correo["cuerpo_texto"])
        correo["cuerpo_texto"] = _eliminar_saltos_linea_multiples(correo["cuerpo_texto"])
    
    return correo if correo["remitente"] else None


async def leer_archivo_eml_service(id_ticket: int, id_hilo: int) -> dict:
    """
    Lee el contenido de un archivo EML y extrae cada correo del hilo por separado.
    Retorna un array de correos, cada uno con su estructura completa.
    """
    if not id_ticket or not id_hilo:
        raise ValueError("Debe proporcionar id_ticket e id_hilo.")

    db = SessionLocal()
    try:
        ticket = db.query(Tickets).filter(Tickets.id_ticket == id_ticket).first()
        if not ticket:
            raise ValueError(f"Ticket con ID {id_ticket} no encontrado.")

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
            msg = message_from_binary_file(f)

        imagenes = _extraer_imagenes_embebidas(msg)

        cuerpo_html: Optional[str] = None
        cuerpo_texto: Optional[str] = None

        for part in msg.walk():
            content_type = part.get_content_type()
            
            if content_type == "text/html":
                try:
                    cuerpo_html = _decodificar_payload(part)
                    cuerpo_html = _reemplazar_cid_en_html(cuerpo_html, imagenes)
                except Exception:
                    pass
            elif content_type == "text/plain" and not cuerpo_texto:
                try:
                    cuerpo_texto = _decodificar_payload(part)
                except Exception:
                    pass

        # Parsear los correos del hilo
        correos_hilo = _parsear_correos_del_hilo(cuerpo_texto)
        
        # Si hay correos en el hilo, el primero puede no tener remitente (es el principal)
        # En ese caso, usar los headers del mensaje principal
        if correos_hilo:
            primer_correo = correos_hilo[0]
            if not primer_correo.get("remitente"):
                # Extraer info del header principal
                from_header = msg.get("From", "")
                match_from = re.search(r'<(.+?)>', from_header)
                if match_from:
                    primer_correo["remitente"] = match_from.group(1)
                else:
                    primer_correo["remitente"] = from_header.strip()
                
                # Extraer remitentes múltiples
                to_header = msg.get("To", "")
                if to_header:
                    primer_correo["destinatarios"] = [addr.strip() for addr in to_header.split(',')]
                
                cc_header = msg.get("CC", "")
                if cc_header:
                    primer_correo["cc"] = [addr.strip() for addr in cc_header.split(',')]
                
                subject = msg.get("Subject", "")
                if subject:
                    primer_correo["asunto"] = subject
                
                date = msg.get("Date", "")
                if date:
                    primer_correo["fecha"] = date

        return {
            "id_hilo": id_hilo,
            "id_ticket": id_ticket,
            "correos": correos_hilo if correos_hilo else []
        }
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Error al leer el archivo EML: {str(e)}")
    finally:
        db.close()
