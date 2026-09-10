"""Monitor del túnel Cloudflare: estado con cache de 5 min."""
import subprocess
import sys
import time

from django.conf import settings
from django.core.cache import cache


def _proceso_corriendo():
    try:
        if sys.platform == "win32":
            out = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq cloudflared.exe"],
                capture_output=True, text=True, timeout=5,
                creationflags=0x08000000,  # CREATE_NO_WINDOW: sin parpadeo de consola
            ).stdout
            return "cloudflared.exe" in out
        return subprocess.run(["pgrep", "-f", "cloudflared"],
                              capture_output=True, timeout=5).returncode == 0
    except Exception:
        return False


def tunnel_status(force=False):
    from urllib.request import urlopen
    from urllib.error import URLError
    
    url = getattr(settings, "TUNNEL_URL", None)
    if not url:
        return {"estado": "desactivado", "url": "", "proc": False, "remoto": False, "ts": 0}
    data = cache.get("tunnel_status")
    if data and not force and time.time() - data.get("ts", 0) < 300:
        return data
    proc = _proceso_corriendo()
    remoto = False
    try:
        import requests as _rq
        r = _rq.get(url + "/accounts/login/", timeout=8, allow_redirects=True)
        remoto = 200 <= r.status_code < 400
    except Exception:
        remoto = False
    if proc and remoto:
        estado = "activo"
    elif not proc:
        estado = "proceso_caido"
    else:
        estado = "sin_respuesta"
    data = {"estado": estado, "url": url, "proc": proc, "remoto": remoto, "ts": time.time()}
    cache.set("tunnel_status", data, 300)
    return data
