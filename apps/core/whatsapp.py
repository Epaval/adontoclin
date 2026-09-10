"""Utilidades WhatsApp Ruta A: links wa.me con plantilla por clinica."""
import re
from urllib.parse import quote


def normalizar_telefono(telefono, prefijo="58"):
    d = re.sub(r"\D", "", telefono or "")
    if not d:
        return None
    if d.startswith("0"):
        d = prefijo + d[1:]
    elif not d.startswith(prefijo):
        d = prefijo + d
    return d


def renderizar_plantilla(plantilla, nombre="", clinica="", servicio="", fecha="", hora=""):
    return (plantilla.replace("{nombre}", nombre).replace("{clinica}", clinica)
            .replace("{servicio}", servicio).replace("{fecha}", fecha).replace("{hora}", hora))


def armar_link_wa(telefono, mensaje, prefijo="58"):
    d = normalizar_telefono(telefono, prefijo)
    if not d:
        return None
    return f"https://wa.me/{d}?text={quote(mensaje)}"
