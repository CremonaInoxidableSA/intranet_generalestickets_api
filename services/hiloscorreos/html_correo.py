"""
Procesamiento del cuerpo HTML de correos (EML).

Responsabilidades:
  1. Incorporar las reglas de <style> como estilos en línea (así el HTML no depende de
     hojas de estilo globales ni "contamina" la página que lo muestre).
  2. Separar el hilo en correos individuales usando la estructura DOM (no texto plano).
  3. Quitar firmas, imágenes decorativas y bloques vacíos.
  4. Resolver imágenes cid: a data URI (base64).
  5. Sanitizar el resultado con una lista blanca (tags, atributos, URLs y propiedades CSS),
     de modo que el HTML sea seguro para renderizar en el frontend.
"""
import base64
import html as html_lib
import io
import re
from dataclasses import dataclass
from email.utils import getaddresses, parseaddr
from typing import Dict, List, Optional
from urllib.parse import unquote

import nh3
from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image


# ---------------------------------------------------------------------------
# Imágenes embebidas (cid:)
# ---------------------------------------------------------------------------

_MIMES_IMAGEN = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
    "image/gif": "image/gif",
    "image/webp": "image/webp",
    "image/bmp": "image/bmp",
}
_LADO_MAXIMO_ICONO = 48


@dataclass(frozen=True)
class ImagenEmbebida:
    mime: str
    contenido_base64: str
    ancho: Optional[int] = None
    alto: Optional[int] = None

    @property
    def data_uri(self) -> str:
        return f"data:{self.mime};base64,{self.contenido_base64}"

    @property
    def es_decorativa(self) -> bool:
        """Íconos, separadores y pixeles de seguimiento (muy pequeños)."""
        if self.ancho is None or self.alto is None:
            return False
        return min(self.ancho, self.alto) <= 2 or (
            self.ancho <= _LADO_MAXIMO_ICONO and self.alto <= _LADO_MAXIMO_ICONO
        )


def extraer_imagenes_embebidas(msg) -> Dict[str, ImagenEmbebida]:
    """
    Recorre el mensaje y devuelve las imágenes con Content-ID.
    La clave es el Content-ID (sin <>) en minúsculas.
    """
    imagenes: Dict[str, ImagenEmbebida] = {}

    for parte in msg.walk():
        mime = _MIMES_IMAGEN.get(parte.get_content_type())
        content_id = (parte.get("Content-ID") or "").strip().strip("<>").strip()
        if not mime or not content_id:
            continue

        try:
            datos = parte.get_payload(decode=True)
            if not datos:
                continue
            ancho = alto = None
            try:
                with Image.open(io.BytesIO(datos)) as imagen:
                    ancho, alto = imagen.size
            except Exception:
                pass
            imagenes[content_id.lower()] = ImagenEmbebida(
                mime=mime,
                contenido_base64=base64.b64encode(datos).decode("ascii"),
                ancho=ancho,
                alto=alto,
            )
        except Exception:
            continue

    return imagenes


# ---------------------------------------------------------------------------
# Cabeceras de respuesta (De / Enviado / Para / CC / Asunto)
# ---------------------------------------------------------------------------

_ETIQUETAS_CABECERA = {
    "de": "remitente", "from": "remitente",
    "enviado": "fecha", "enviada": "fecha", "sent": "fecha", "fecha": "fecha", "date": "fecha",
    "para": "destinatarios", "to": "destinatarios",
    "cc": "cc",
    "cco": "bcc", "bcc": "bcc",
    "asunto": "asunto", "subject": "asunto", "assunto": "asunto",
}
_RE_LINEA_CABECERA = re.compile(
    r"^\s*(" + "|".join(sorted(_ETIQUETAS_CABECERA, key=len, reverse=True)) + r")\s*:\s*(.*)$",
    re.IGNORECASE,
)
_RE_EMAIL_ENTRE_ANGULOS = re.compile(r"<\s*([^<>\s]+@[^<>\s]+)\s*>")
_RE_EMAIL = re.compile(r"[\w.+'-]+@[\w-]+(?:\.[\w-]+)+")


def _parsear_texto_cabecera(texto: str) -> Dict[str, str]:
    """Convierte el texto de un bloque 'De: ... Enviado: ...' en un dict por campo."""
    campos: Dict[str, str] = {}
    actual: Optional[str] = None

    for linea in texto.replace("\xa0", " ").splitlines():
        coincidencia = _RE_LINEA_CABECERA.match(linea)
        if coincidencia and _ETIQUETAS_CABECERA[coincidencia.group(1).lower()] not in campos:
            actual = _ETIQUETAS_CABECERA[coincidencia.group(1).lower()]
            campos[actual] = coincidencia.group(2).strip()
        elif actual and linea.strip():
            # Valor partido en varias líneas (p. ej. la dirección dentro de un <a>)
            campos[actual] = f"{campos[actual]} {linea.strip()}".strip()

    for clave, valor in campos.items():
        valor = re.sub(r"<\s+", "<", valor)
        valor = re.sub(r"\s+>", ">", valor)
        campos[clave] = re.sub(r"\s+", " ", valor).strip()
    return campos


def extraer_remitente(valor: str) -> str:
    """Devuelve solo la dirección de correo de un 'Nombre <correo>' (o el texto original)."""
    if not valor:
        return ""
    coincidencia = _RE_EMAIL_ENTRE_ANGULOS.search(valor) or _RE_EMAIL.search(valor)
    if coincidencia:
        return coincidencia.group(1) if coincidencia.lastindex else coincidencia.group(0)
    return valor.strip()


def lista_direcciones(valor: str) -> List[str]:
    """
    Convierte una lista de destinatarios en ['Nombre <correo>', ...].
    Outlook separa con ';' y los encabezados MIME con ','.
    """
    if not valor or not valor.strip():
        return []

    if ";" in valor:
        pares = [parseaddr(parte) for parte in valor.split(";") if parte.strip()]
    else:
        pares = getaddresses([valor])

    resultado = []
    for nombre, direccion in pares:
        if not direccion:
            continue
        resultado.append(f"{nombre.strip()} <{direccion}>" if nombre.strip() else direccion)
    return resultado


def _normalizar_cabecera(campos: Dict[str, str]) -> Dict:
    return {
        "remitente": extraer_remitente(campos.get("remitente", "")),
        "asunto": campos.get("asunto", ""),
        "destinatarios": lista_direcciones(campos.get("destinatarios", "")),
        "cc": lista_direcciones(campos.get("cc", "")),
        "bcc": lista_direcciones(campos.get("bcc", "")),
        "fecha": campos.get("fecha", ""),
    }


# ---------------------------------------------------------------------------
# Estilos: <style> -> estilos en línea
# ---------------------------------------------------------------------------

_RE_COMENTARIO_CSS = re.compile(r"/\*.*?\*/", re.DOTALL)
_RE_SENTENCIA_AT = re.compile(r"@(?:import|charset|namespace)\b[^;{}]*;", re.IGNORECASE)
_MAX_CARACTERES_CSS = 300_000
_MAX_REGLAS_CSS = 1_500


def _parsear_reglas_css(css: str) -> List[tuple]:
    """Devuelve [(selector, declaraciones)] ignorando reglas @ (@media, @font-face, @page...)."""
    css = _RE_COMENTARIO_CSS.sub("", css).replace("<!--", "").replace("-->", "")
    css = _RE_SENTENCIA_AT.sub("", css)

    reglas = []
    posicion = 0
    largo = len(css)
    while posicion < largo:
        apertura = css.find("{", posicion)
        if apertura == -1:
            break
        profundidad = 1
        cursor = apertura + 1
        while cursor < largo and profundidad:
            if css[cursor] == "{":
                profundidad += 1
            elif css[cursor] == "}":
                profundidad -= 1
            cursor += 1

        selector = css[posicion:apertura].strip()
        declaraciones = css[apertura + 1:cursor - 1 if profundidad == 0 else cursor]
        posicion = cursor
        if selector and not selector.startswith("@"):
            reglas.append((selector, declaraciones))
    return reglas


def _inlinar_estilos(soup: BeautifulSoup) -> None:
    """Aplica las reglas de los <style> como atributo style de cada elemento y elimina los <style>."""
    estilos = soup.find_all("style")
    acumulado: Dict[int, list] = {}
    caracteres = 0
    reglas_totales = 0

    for estilo in estilos:
        css = "".join(str(nodo) for nodo in estilo.contents)
        caracteres += len(css)
        if caracteres > _MAX_CARACTERES_CSS:
            break
        medio = (estilo.get("media") or "").lower()
        if medio and "screen" not in medio and "all" not in medio:
            continue

        for selector, declaraciones in _parsear_reglas_css(css):
            reglas_totales += 1
            if reglas_totales > _MAX_REGLAS_CSS:
                break
            try:
                elementos = soup.select(selector)
            except Exception:
                continue  # selector no soportado (pseudo-elementos, sintaxis inválida...)
            for elemento in elementos:
                acumulado.setdefault(id(elemento), [elemento, []])[1].append(declaraciones.strip().strip(";"))

    for elemento, reglas in acumulado.values():
        propio = (elemento.get("style") or "").strip().strip(";")
        elemento["style"] = ";".join(reglas + ([propio] if propio else []))

    for estilo in estilos:
        estilo.decompose()


_RE_OCULTO = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden|mso-hide\s*:\s*all", re.IGNORECASE)


def _decomposed(nodo) -> bool:
    return getattr(nodo, "decomposed", False)


def _quitar_ocultos(soup: BeautifulSoup) -> None:
    for elemento in soup.find_all(style=_RE_OCULTO):
        if not _decomposed(elemento):
            elemento.decompose()


# ---------------------------------------------------------------------------
# Separación del hilo
# ---------------------------------------------------------------------------

# Outlook (web/nuevo): <hr> + <div id="[x_]*divRplyFwdMsg"> con "De / Enviado / Para / Asunto".
_RE_ID_CABECERA = re.compile(r"(?:^|_)divRplyFwdMsg$")
# Outlook de escritorio (Word): <div style="border:none;border-top:solid #E1E1E1 1.0pt;..."> con "De:".
_RE_BORDE_CABECERA = re.compile(r"border-top\s*:\s*solid\s*#(?:E1E1E1|B5C4DF)", re.IGNORECASE)
_RE_INICIA_CON_DE = re.compile(r"^\s*(?:De|From)\s*:", re.IGNORECASE)


def _localizar_cabeceras(soup: BeautifulSoup) -> List[Tag]:
    """Bloques de cabecera de cada correo citado, en orden de documento."""
    cabeceras = []
    for div in soup.find_all("div"):
        if _RE_ID_CABECERA.search(div.get("id") or ""):
            cabeceras.append(div)
        elif _RE_BORDE_CABECERA.search(div.get("style") or "") and _RE_INICIA_CON_DE.match(div.get_text()):
            cabeceras.append(div)
    return cabeceras


def _hermano_previo_significativo(nodo):
    previo = nodo.previous_sibling
    while isinstance(previo, NavigableString) and not str(previo).strip(" \t\r\n"):
        previo = previo.previous_sibling
    return previo


def _inicio_cabecera(cabecera: Tag) -> Tag:
    """Incluye el <hr> que Outlook coloca justo antes de la cabecera."""
    previo = _hermano_previo_significativo(cabecera)
    if isinstance(previo, Tag) and previo.name == "hr":
        return previo
    return cabecera


def _truncar_desde(nodo) -> None:
    """Elimina el nodo y todo lo que le sigue en orden de documento (conserva los ancestros)."""
    actual = nodo
    while actual is not None and actual.parent is not None:
        padre = actual.parent
        for hermano in list(actual.next_siblings):
            hermano.extract()
        if actual is nodo:
            actual.extract()
        actual = padre


def _truncar_hasta(nodo) -> None:
    """Elimina el nodo y todo lo que lo precede en orden de documento (conserva los ancestros)."""
    actual = nodo
    while actual is not None and actual.parent is not None:
        padre = actual.parent
        for hermano in list(actual.previous_siblings):
            hermano.extract()
        if actual is nodo:
            actual.extract()
        actual = padre


# ---------------------------------------------------------------------------
# Firmas
# ---------------------------------------------------------------------------

_RE_ID_FIRMA = re.compile(r"^(?:x_)*(?:signature|ms-outlook-[a-z]+-signature)$", re.IGNORECASE)
_RE_CLASE_FIRMA = re.compile(r"(?:^|_)(?:gmail_signature|moz-signature)$", re.IGNORECASE)

_RE_CONTACTO_TELEFONO = re.compile(
    r"\b(?:tel|tel[eé]fono|cel|celular|m[oó]vil|mobile|phone|fono|anexo|interno)\b\.?\s*:?\s*[+\d(]",
    re.IGNORECASE,
)
_RE_CONTACTO_WEB = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|net|org|cl|ar|es|com\.\w{2})\b", re.IGNORECASE)
_MAX_CARACTERES_TARJETA = 700
_MAX_FILAS_TARJETA = 6

# Pies que agregan automáticamente los gateways de correo (no son parte del mensaje).
_RE_PIE_GATEWAY = re.compile(
    r"scanned\s+for\s+(?:malware|viruses)\s+by\s+\w+|"
    r"click\s+here\s+to\s+report\s+this\s+email\s+as\s+spam|"
    r"(?:analizado|escaneado)\s+(?:en\s+busca\s+de|contra)\s+(?:malware|virus)",
    re.IGNORECASE,
)
_MAX_CARACTERES_PIE = 300


def _quitar_firmas_declaradas(raiz: Tag) -> None:
    """Firmas marcadas por el cliente de correo (OWA, Gmail, Thunderbird)."""
    candidatos = list(raiz.find_all(id=_RE_ID_FIRMA))
    candidatos += list(raiz.find_all(class_=_RE_CLASE_FIRMA))
    for elemento in candidatos:
        if not _decomposed(elemento):
            elemento.decompose()


def _quitar_pies_gateway(raiz: Tag) -> None:
    """Elimina el bloque más pequeño que contiene un pie automático del gateway de correo."""
    for bloque in reversed(raiz.find_all(["p", "div"])):
        if _decomposed(bloque) or bloque.find(_MEDIA):
            continue
        texto = " ".join(bloque.get_text(" ").split())
        if texto and len(texto) <= _MAX_CARACTERES_PIE and _RE_PIE_GATEWAY.search(texto):
            bloque.decompose()


def _hay_contenido_posterior(nodo) -> bool:
    """¿Existe texto o contenido visual después del nodo (en orden de documento)?"""
    actual = nodo
    while actual is not None and actual.parent is not None:
        for hermano in actual.next_siblings:
            if isinstance(hermano, Tag):
                if _tiene_media(hermano) or _texto_visible(hermano):
                    return True
            elif str(hermano).strip():
                return True
        actual = actual.parent
    return False


def _parece_tarjeta_contacto(tabla: Tag) -> bool:
    """
    Heurística conservadora para firmas hechas con tablas: pocas filas, poco texto,
    al menos dos tipos de dato de contacto (teléfono / correo / web) y algún enlace o imagen.
    """
    texto = " ".join(tabla.get_text(" ").split())
    if not texto or len(texto) > _MAX_CARACTERES_TARJETA:
        return False
    if len(tabla.find_all("tr")) > _MAX_FILAS_TARJETA or tabla.find("th"):
        return False
    if not tabla.find(["a", "img"]):
        return False

    sin_correos = _RE_EMAIL.sub(" ", texto)  # el dominio de un correo no cuenta como sitio web
    tipos = sum([
        bool(_RE_CONTACTO_TELEFONO.search(texto)),
        bool(_RE_EMAIL.search(texto)),
        bool(_RE_CONTACTO_WEB.search(sin_correos)),
    ])
    return tipos >= 2


def _quitar_tarjeta_contacto_final(raiz: Tag) -> None:
    """Quita la última tabla del correo si parece una firma de contacto y no hay nada después."""
    while True:
        tablas = [t for t in raiz.find_all("table") if t.find_parent("table") is None]
        if not tablas:
            return
        ultima = tablas[-1]
        if _hay_contenido_posterior(ultima) or not _parece_tarjeta_contacto(ultima):
            return
        ultima.decompose()
        _podar_vacios(raiz)


# ---------------------------------------------------------------------------
# Imágenes y tablas
# ---------------------------------------------------------------------------

_RE_CID = re.compile(r"^cid:(.+)$", re.IGNORECASE)
_RE_DATA_IMAGEN = re.compile(r"^data:image/(?:png|jpe?g|gif|webp|bmp);base64,[A-Za-z0-9+/=\s]+$", re.IGNORECASE)


def _dimension_declarada(imagen: Tag, atributo: str) -> Optional[int]:
    valor = (imagen.get(atributo) or "").strip().lower().removesuffix("px")
    return int(valor) if valor.isdigit() else None


def _resolver_imagenes(raiz: Tag, imagenes: Dict[str, ImagenEmbebida]) -> None:
    """
    - cid:xxx           -> data URI (si existe y no es decorativa)
    - data:image/...    -> se conserva (el sanitizador valida el formato)
    - cualquier otra    -> se elimina (no se cargan recursos remotos: privacidad y seguimiento)
    """
    for imagen in list(raiz.find_all("img")):
        if _decomposed(imagen):
            continue
        origen = (imagen.get("src") or "").strip()

        ancho = _dimension_declarada(imagen, "width")
        alto = _dimension_declarada(imagen, "height")
        if ancho is not None and alto is not None and (
            min(ancho, alto) <= 2 or (ancho <= _LADO_MAXIMO_ICONO and alto <= _LADO_MAXIMO_ICONO)
        ):
            imagen.decompose()
            continue

        if origen.lower().startswith("data:image/"):
            pass
        else:
            coincidencia = _RE_CID.match(origen)
            embebida = None
            if coincidencia:
                clave = unquote(coincidencia.group(1)).strip().strip("<>").lower()
                embebida = imagenes.get(clave)
            if embebida is None or embebida.es_decorativa:
                imagen.decompose()
                continue
            imagen["src"] = embebida.data_uri

        # Responsive: nunca más ancha que el contenedor y conservando la proporción
        estilo = (imagen.get("style") or "").strip().rstrip(";")
        imagen["style"] = f"{estilo};max-width:100%;height:auto" if estilo else "max-width:100%;height:auto"


def _envolver_tablas(soup: BeautifulSoup, raiz: Tag) -> None:
    """Las tablas anchas hacen scroll horizontal en lugar de desbordar el contenedor."""
    for tabla in raiz.find_all("table"):
        if tabla.find_parent("table") is None:
            tabla.wrap(soup.new_tag("div", style="overflow-x:auto;max-width:100%"))


# ---------------------------------------------------------------------------
# Poda de bloques vacíos / saltos de línea excesivos
# ---------------------------------------------------------------------------

_MEDIA = ["img", "table", "hr", "ul", "ol", "iframe"]
_PODABLES = ["div", "p", "span", "font", "center", "b", "i", "u", "strong", "em", "a", "blockquote"]
_TRANSPARENTES = set(_PODABLES)


def _texto_visible(nodo: Tag) -> str:
    return nodo.get_text().replace("\xa0", "").strip()


def _tiene_media(nodo: Tag) -> bool:
    return nodo.name in _MEDIA or nodo.find(_MEDIA) is not None


def _es_vacio_visual(nodo: Tag) -> bool:
    """Sin texto ni contenido visual (puede contener <br> o &nbsp;)."""
    return not _tiene_media(nodo) and not _texto_visible(nodo)


def _es_estrictamente_vacio(nodo: Tag) -> bool:
    """Sin texto, &nbsp;, <br> ni media: no aporta ningún espacio visual."""
    return (
        not _tiene_media(nodo)
        and nodo.find("br") is None
        and not nodo.get_text().strip(" \t\r\n")
    )


def _recortar_extremo(contenedor: Tag, al_final: bool) -> None:
    """Quita bloques en blanco al inicio (o final) del contenedor, descendiendo por envoltorios."""
    while True:
        hijos = [
            h for h in contenedor.contents
            if not (isinstance(h, NavigableString) and not str(h).strip(" \t\r\n"))
        ]
        if not hijos:
            return
        extremo = hijos[-1] if al_final else hijos[0]

        if isinstance(extremo, NavigableString):
            if not str(extremo).strip():  # solo &nbsp;
                extremo.extract()
                continue
            return
        if _es_vacio_visual(extremo):
            extremo.decompose()
            continue
        if extremo.name in _TRANSPARENTES:
            _recortar_extremo(extremo, al_final)
        return


def _podar_vacios(raiz: Tag) -> None:
    """
    - Elimina contenedores totalmente vacíos.
    - Colapsa líneas en blanco consecutivas (<div><br></div>, <p>&nbsp;</p>, <br><br><br>) en una sola.
    - Elimina líneas en blanco al inicio y al final.
    """
    for elemento in reversed(raiz.find_all(_PODABLES)):
        if not _decomposed(elemento) and _es_estrictamente_vacio(elemento):
            elemento.decompose()

    for elemento in raiz.find_all(["div", "p"]):
        if _decomposed(elemento) or not _es_vacio_visual(elemento):
            continue
        previo = _hermano_previo_significativo(elemento)
        if isinstance(previo, Tag) and previo.name in ("div", "p") and _es_vacio_visual(previo):
            elemento.decompose()

    for salto in raiz.find_all("br"):
        if _decomposed(salto):
            continue
        previo = _hermano_previo_significativo(salto)
        if isinstance(previo, Tag) and previo.name == "br":
            antes = _hermano_previo_significativo(previo)
            if isinstance(antes, Tag) and antes.name == "br":
                salto.decompose()

    _recortar_extremo(raiz, al_final=False)
    _recortar_extremo(raiz, al_final=True)


# ---------------------------------------------------------------------------
# Sanitización (lista blanca)
# ---------------------------------------------------------------------------

_TAGS_PERMITIDOS = {
    "a", "abbr", "address", "b", "bdi", "bdo", "big", "blockquote", "br", "caption", "center",
    "cite", "code", "col", "colgroup", "dd", "del", "dfn", "div", "dl", "dt", "em", "font",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd", "li", "mark", "ol", "p",
    "pre", "q", "s", "samp", "small", "span", "strike", "strong", "sub", "sup", "table",
    "tbody", "td", "tfoot", "th", "thead", "tr", "tt", "u", "ul", "var", "wbr",
}
_ATRIBUTOS_PERMITIDOS = {
    "*": {"style", "dir", "lang", "title", "align"},
    "a": {"href"},
    "img": {"src", "alt", "width", "height"},
    "table": {"border", "cellpadding", "cellspacing", "width", "bgcolor"},
    "tr": {"bgcolor", "valign"},
    "td": {"colspan", "rowspan", "width", "height", "bgcolor", "valign", "nowrap"},
    "th": {"colspan", "rowspan", "width", "height", "bgcolor", "valign", "nowrap", "scope"},
    "col": {"span", "width"},
    "colgroup": {"span", "width"},
    "ol": {"start", "type", "reversed"},
    "ul": {"type"},
    "li": {"value", "type"},
    "font": {"face", "color", "size"},
}

_LADOS = ("top", "right", "bottom", "left")
_PROPIEDADES_CSS = {
    "color", "background", "background-color",
    "font", "font-family", "font-size", "font-style", "font-weight", "font-variant",
    "line-height", "letter-spacing", "word-spacing",
    "text-align", "text-decoration", "text-indent", "text-transform",
    "white-space", "word-break", "word-wrap", "overflow-wrap", "vertical-align",
    "direction", "unicode-bidi",
    "width", "height", "min-width", "min-height", "max-width", "max-height",
    "display", "table-layout", "box-sizing", "empty-cells", "caption-side",
    "border", "border-collapse", "border-spacing", "border-color", "border-style",
    "border-width", "border-radius",
    "margin", "padding",
    "list-style", "list-style-type", "list-style-position",
    "overflow", "overflow-x", "overflow-y",
}
for _lado in _LADOS:
    _PROPIEDADES_CSS.update({
        f"margin-{_lado}", f"padding-{_lado}",
        f"border-{_lado}", f"border-{_lado}-color", f"border-{_lado}-style", f"border-{_lado}-width",
    })

_DISPLAY_PERMITIDO = {
    "block", "inline", "inline-block", "table", "inline-table", "table-row", "table-cell",
    "table-row-group", "table-header-group", "table-footer-group", "list-item",
}
_FUNCIONES_CSS_PERMITIDAS = {"rgb", "rgba", "hsl", "hsla", "calc", "min", "max", "clamp"}
_RE_FUNCION_CSS = re.compile(r"([a-zA-Z_-][\w-]*)\s*\(")
_RE_CARACTERES_CSS_PROHIBIDOS = re.compile(r"[\\<>{}@]")
_RE_ENLACE_SEGURO = re.compile(r"^(?:https?://|mailto:|tel:)", re.IGNORECASE)
_RE_DIMENSION = re.compile(r"^\d{1,4}(?:px|%)?$", re.IGNORECASE)
_RE_COLOR_ATRIBUTO = re.compile(r"^[#\w(),.%\s-]{1,40}$")


def _valor_css_seguro(valor: str) -> bool:
    """Rechaza url(), expression(), image-set(), escapes y cualquier función fuera de la lista blanca."""
    if len(valor) > 300 or _RE_CARACTERES_CSS_PROHIBIDOS.search(valor):
        return False
    return all(nombre.lower() in _FUNCIONES_CSS_PERMITIDAS for nombre in _RE_FUNCION_CSS.findall(valor))


def _sanear_estilo(valor: str) -> str:
    """Conserva solo propiedades CSS permitidas con valores seguros."""
    valor = _RE_COMENTARIO_CSS.sub("", valor)
    declaraciones = []
    for declaracion in re.split(r";(?![^()]*\))", valor):
        if ":" not in declaracion:
            continue
        propiedad, contenido = declaracion.split(":", 1)
        propiedad = propiedad.strip().lower()
        contenido = re.sub(r"\s*!\s*important\s*$", "", contenido.strip(), flags=re.IGNORECASE).strip()
        if not contenido or propiedad not in _PROPIEDADES_CSS:
            continue
        if propiedad == "display" and contenido.lower() not in _DISPLAY_PERMITIDO:
            continue
        if not _valor_css_seguro(contenido):
            continue
        declaraciones.append(f"{propiedad}:{contenido}")
    return ";".join(declaraciones)


def _filtrar_atributo(tag: str, atributo: str, valor: str) -> Optional[str]:
    """Última barrera de validación de atributos (se ejecuta dentro de nh3)."""
    if atributo == "style":
        return _sanear_estilo(valor) or None
    if tag == "a" and atributo == "href":
        valor = valor.strip()
        return valor if _RE_ENLACE_SEGURO.match(valor) else None
    if tag == "img" and atributo == "src":
        return valor if _RE_DATA_IMAGEN.match(valor.strip()) else None
    if atributo in ("width", "height"):
        return valor.strip() if _RE_DIMENSION.match(valor.strip()) else None
    if atributo in ("color", "bgcolor"):
        return valor.strip() if _RE_COLOR_ATRIBUTO.match(valor) else None
    return valor


def _sanitizar(html: str) -> str:
    return nh3.clean(
        html,
        tags=_TAGS_PERMITIDOS,
        clean_content_tags={"script", "style"},
        attributes=_ATRIBUTOS_PERMITIDOS,
        attribute_filter=_filtrar_atributo,
        url_schemes={"http", "https", "mailto", "tel", "data"},
        url_relative="deny",
        link_rel="noopener noreferrer nofollow",
        set_tag_attribute_values={"a": {"target": "_blank"}},
        strip_comments=True,
    )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def _extraer_segmento(html_base: str, indice: int, imagenes: Dict[str, ImagenEmbebida]) -> Dict:
    """
    Segmento 0  : correo más reciente (antes de la primera cabecera de respuesta).
    Segmento k>0: correo descrito por la cabecera k-1 (hasta la cabecera k).
    """
    soup = BeautifulSoup(html_base, "lxml")
    cabeceras = _localizar_cabeceras(soup)

    cabecera = None
    if indice > 0:
        cabecera = _normalizar_cabecera(_parsear_texto_cabecera(cabeceras[indice - 1].get_text("\n")))

    if indice < len(cabeceras):
        _truncar_desde(_inicio_cabecera(cabeceras[indice]))
    if indice > 0:
        _truncar_hasta(cabeceras[indice - 1])

    raiz = soup.body or soup
    _quitar_firmas_declaradas(raiz)
    _quitar_pies_gateway(raiz)
    _resolver_imagenes(raiz, imagenes)
    _podar_vacios(raiz)
    _quitar_tarjeta_contacto_final(raiz)
    _envolver_tablas(soup, raiz)

    cuerpo_html = _sanitizar(raiz.decode_contents()).strip()
    return {"cabecera": cabecera, "cuerpo_html": cuerpo_html}


def dividir_hilo_html(html: str, imagenes: Dict[str, ImagenEmbebida]) -> List[Dict]:
    """
    Separa un cuerpo HTML en los correos que lo componen (del más reciente al más antiguo).
    Devuelve [{"cabecera": dict | None, "cuerpo_html": str}, ...]; la cabecera del primero es None
    porque corresponde a los encabezados del propio mensaje MIME.
    """
    soup = BeautifulSoup(html, "lxml")
    _inlinar_estilos(soup)
    _quitar_ocultos(soup)

    cantidad_cabeceras = len(_localizar_cabeceras(soup))
    html_base = str(soup)
    return [_extraer_segmento(html_base, i, imagenes) for i in range(cantidad_cabeceras + 1)]


def texto_plano_a_html(texto: str) -> str:
    """Respaldo para correos sin parte HTML: conserva saltos de línea y espacios."""
    if not texto or not texto.strip():
        return ""
    return f'<div style="white-space:pre-wrap">{html_lib.escape(texto.strip())}</div>'
