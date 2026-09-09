"""Instala cloudflared como servicio de Windows."""
import os
import sys
import subprocess
from pathlib import Path


def descargar_cloudflared():
    """Descarga cloudflared.exe desde GitHub."""
    import requests
    
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    dest = Path(__file__).parent / "cloudflared.exe"
    
    if dest.exists():
        print(f"✓ cloudflared.exe ya existe en {dest}")
        return dest
    
    print(f"Descargando cloudflared.exe...")
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print(f"✓ Descargado en {dest}")
    return dest


def instalar_servicio(exe_path):
    """Instala cloudflared como servicio de Windows."""
    if sys.platform != "win32":
        print("⚠ Este script solo funciona en Windows")
        return False
    
    result = subprocess.run(
        ["sc", "query", "cloudflared"],
        capture_output=True, text=True
    )
    
    if "RUNNING" in result.stdout or "STOPPED" in result.stdout:
        print("✓ Servicio cloudflared ya está instalado")
        return True
    
    print("Instalando servicio cloudflared...")
    cmd = [str(exe_path), "service", "install", "--no-autoupdate"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Servicio instalado correctamente")
        return True
    else:
        print(f"✗ Error: {result.stderr}")
        return False


def configurar_url(tunnel_url):
    """Guarda la URL del túnel en .env"""
    env_path = Path(__file__).parent.parent / ".env"
    
    if env_path.exists():
        content = env_path.read_text()
        if "DJANGO_TUNNEL_URL" in content:
            lines = content.split("\n")
            lines = [l for l in lines if not l.startswith("DJANGO_TUNNEL_URL")]
            content = "\n".join(lines)
        content += f'\nDJANGO_TUNNEL_URL={tunnel_url}\n'
    else:
        content = f'DJANGO_TUNNEL_URL={tunnel_url}\n'
    
    env_path.write_text(content)
    print(f"✓ URL guardada en .env: {tunnel_url}")


def main():
    if sys.platform != "win32":
        print("Este script solo funciona en Windows")
        sys.exit(1)
    
    exe = descargar_cloudflared()
    
    if not instalar_servicio(exe):
        sys.exit(1)
    
    print("\n=== Configuración del túnel ===")
    print("Ingresa la URL pública de tu clínica (ej: https://clinica.facdin.com)")
    tunnel_url = input("URL: ").strip()
    
    if not tunnel_url.startswith("https://"):
        tunnel_url = f"https://{tunnel_url}"
    
    configurar_url(tunnel_url)
    
    print("\n✓ Instalación completa!")
    print("Para iniciar el servicio: net start cloudflared")


if __name__ == "__main__":
    main()
