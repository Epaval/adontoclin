import os
"""
Sistema de licencias con tipos:
  - prueba:   N dias desde la primera ejecucion
  - anual:    clave OPACA con fecha de vencimiento firmada e incrustada
  - perpetua: para siempre (CODIGO)

La clave anual no muestra la fecha en texto claro: va firmada (HMAC) y
ofuscada. Cambiar cualquier caracter invalida la firma. Al vencer, el
cliente necesita una clave NUEVA (renovacion pagada).
"""
import base64
import hashlib
import hmac
import platform
import re
import uuid
from datetime import datetime, timedelta

# SECRETO DEL VENDEDOR (cambialo y no lo compartas)
SECRET = b"AZMA1972JCPD1970#2005$1991"

PRUEBA_DIAS = int(os.environ.get("LABCLIN_TRIAL_DIAS", "7"))
MODO_DEV = os.environ.get("LABCLIN_DEV", "") == "1"
ANUAL_DIAS = 365

TIPOS_VALIDOS = ["anual", "perpetua"]


def huella_maquina() -> str:
    """Identificador unico de la PC"""
    base = f"{uuid.getnode()}|{platform.node().lower()}"
    return hashlib.sha256(base.encode()).hexdigest()[:16].upper()


def _hmac(mensaje: str) -> str:
    return hmac.new(SECRET, mensaje.encode(), hashlib.sha256).hexdigest()[:12].upper()


def _clave_xor() -> bytes:
    return hashlib.sha256(SECRET + b"OFUSCACION").digest()


def _ofuscar(texto: str) -> str:
    """Convierte 'FECHA+CODIGO' en un token opaco agrupado en bloques de 4"""
    key = _clave_xor()
    data = bytes(b ^ key[i % len(key)] for i, b in enumerate(texto.encode()))
    token = base64.b32encode(data).decode().rstrip("=")
    return "-".join(token[i:i + 4] for i in range(0, len(token), 4))


def _desofuscar(token: str) -> str:
    limpio = re.sub(r"[^A-Z2-7]", "", token.upper())
    data = base64.b32decode(limpio + "=" * (-len(limpio) % 8))
    key = _clave_xor()
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data)).decode()


def generar_clave(huella: str, tipo: str = "perpetua", hasta=None) -> str:
    """
    Genera clave de activacion.
    Anual: token opaco que contiene la fecha de vencimiento firmada.
    Perpetua: CODIGO de 12 caracteres.
    """
    huella = huella.strip().upper()
    if tipo == "anual":
        if hasta is None:
            hasta = datetime.now() + timedelta(days=ANUAL_DIAS)
        fecha_str = hasta.strftime("%Y%m%d")
        codigo = _hmac(f"{huella}|anual|{fecha_str}")
        return _ofuscar(fecha_str + codigo)
    return _hmac(f"{huella}|perpetua")


def _analizar_clave(clave):
    """Devuelve (forma, fecha_str, codigo)"""
    original = clave.strip().upper()

    # 1) Formato opaco actual (anual con fecha firmada y ofuscada)
    limpio = re.sub(r"[^A-Z2-7]", "", original)
    if len(limpio) == 32:
        try:
            interno = _desofuscar(limpio)
            if len(interno) == 20 and interno[:8].isdigit():
                return "anual_nueva", interno[:8], interno[8:]
        except Exception:
            pass

    # 2) Legado plano AAAAMMDD-CODIGO (tambien va firmado)
    if "-" in original:
        fecha_str, _, codigo = original.partition("-")
        if len(fecha_str) == 8 and fecha_str.isdigit() and codigo:
            return "anual_plana", fecha_str, codigo

    # 3) Formato simple de 12 caracteres (perpetua o anual muy viejo)
    if original and "-" not in original:
        return "simple", None, original

    return None, None, None


def clave_valida(clave: str, tipo: str = None) -> bool:
    """Valida la firma de la clave para esta maquina (y tipo si se indica)"""
    forma, fecha_str, codigo = _analizar_clave(clave)
    if forma is None:
        return False
    huella = huella_maquina()

    if forma in ("anual_nueva", "anual_plana"):
        if tipo is not None and tipo != "anual":
            return False
        return hmac.compare_digest(codigo, _hmac(f"{huella}|anual|{fecha_str}"))

    # Formato simple: perpetua actual o anual legado
    if tipo in (None, "perpetua") and hmac.compare_digest(codigo, _hmac(f"{huella}|perpetua")):
        return True
    if tipo in (None, "anual") and hmac.compare_digest(codigo, _hmac(f"{huella}|anual")):
        return True
    return False


def fecha_vencimiento_clave(clave):
    """Fecha de vencimiento incrustada en una clave anual, o None"""
    forma, fecha_str, _ = _analizar_clave(clave)
    if forma in ("anual_nueva", "anual_plana"):
        try:
            return datetime.strptime(fecha_str, "%Y%m%d")
        except ValueError:
            return None
    return None


def clave_vencida(clave) -> bool:
    """True si la clave anual ya paso su fecha de vencimiento"""
    venc = fecha_vencimiento_clave(clave)
    return bool(venc and datetime.now() >= venc)


def fecha_vencimiento(tipo, clave, fecha_activacion):
    """Vencimiento efectivo de una licencia activada (None = perpetua)"""
    if tipo == "perpetua":
        return None
    venc = fecha_vencimiento_clave(clave)
    if venc:
        return venc
    if fecha_activacion:
        return fecha_activacion + timedelta(days=ANUAL_DIAS)
    return None


def leer_licencia():
    """Lee el archivo de licencia. Devuelve (tipo, clave, fecha_activacion) o None"""
    from django.conf import settings

    lic_file = settings.DATA_DIR / "licencia.key"
    if not lic_file.exists():
        return None

    try:
        contenido = lic_file.read_text().strip()
        partes = contenido.split("|")
        if len(partes) == 3:
            tipo, clave, fecha_iso = partes
            return tipo, clave, datetime.fromisoformat(fecha_iso)
        return "perpetua", contenido, None
    except Exception:
        return None


def guardar_licencia(tipo: str, clave: str):
    """Guarda la licencia activada"""
    from django.conf import settings

    lic_file = settings.DATA_DIR / "licencia.key"
    fecha = datetime.now().isoformat()
    lic_file.write_text(f"{tipo}|{clave.strip().upper()}|{fecha}")


def estado_licencia() -> str:
    """Devuelve: 'activada' | 'prueba' | 'vencida'"""
    from django.conf import settings

    licencia = leer_licencia()
    if licencia:
        tipo, clave, fecha_activacion = licencia
        if clave_valida(clave, tipo):
            if tipo == "perpetua":
                return "activada"
            venc = fecha_vencimiento(tipo, clave, fecha_activacion)
            if venc is None or datetime.now() < venc:
                return "activada"
            return "vencida"

    prueba_file = settings.DATA_DIR / "primera_ejecucion"
    if not prueba_file.exists():
        prueba_file.write_text(datetime.now().isoformat())

    inicio = datetime.fromisoformat(prueba_file.read_text().strip())
    if (datetime.now().date() - inicio.date()).days <= PRUEBA_DIAS:
        return "prueba"
    return "vencida"


def dias_restantes() -> int:
    """Dias restantes de licencia o prueba"""
    from django.conf import settings

    licencia = leer_licencia()
    if licencia:
        tipo, clave, fecha_activacion = licencia
        if clave_valida(clave, tipo):
            if tipo == "perpetua":
                return 99999
            venc = fecha_vencimiento(tipo, clave, fecha_activacion)
            if venc:
                return max((venc - datetime.now()).days, 0)

    prueba_file = settings.DATA_DIR / "primera_ejecucion"
    if not prueba_file.exists():
        return PRUEBA_DIAS
    inicio = datetime.fromisoformat(prueba_file.read_text().strip())
    return max(PRUEBA_DIAS - (datetime.now().date() - inicio.date()).days, 0)


def tipo_licencia_actual() -> str:
    """Devuelve: prueba | anual | perpetua | vencida"""
    estado = estado_licencia()
    if estado == "prueba":
        return "prueba"
    if estado == "vencida":
        return "vencida"

    licencia = leer_licencia()
    if licencia:
        return licencia[0]
    return "prueba"


def info_licencia() -> dict:
    """Resumen completo de la licencia para el panel de administracion."""
    lic = leer_licencia()
    tipo = tipo_licencia_actual()
    estado = estado_licencia()
    clave = None
    venc = None
    if lic:
        clave = lic[1]
        try:
            venc = fecha_vencimiento(*lic)
        except Exception:
            venc = None
    else:
        from django.conf import settings
        pf = settings.DATA_DIR / "primera_ejecucion"
        if pf.exists():
            try:
                inicio = datetime.fromisoformat(pf.read_text().strip())
                venc = inicio + timedelta(days=PRUEBA_DIAS)
            except Exception:
                venc = None
    return {
        "tipo": tipo, "estado": estado, "dias": dias_restantes(),
        "vencimiento": venc, "huella": huella_maquina(), "clave": clave,
        "dev": MODO_DEV, "prueba_dias": PRUEBA_DIAS,
    }
