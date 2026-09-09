"""Vistas del panel SaaS."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from django.conf import settings
from django.http import Http404

from .models import Clinica
from .forms import ClinicaForm
from .cloudflare_service import CloudflareService


class ProveedorRequired(LoginRequiredMixin):
    """Solo accesible cuando LABCLIN_ROL == proveedor."""
    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "LABCLIN_ROL", "clinica") != "proveedor":
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class ClinicaListView(ProveedorRequired, ListView):
    """Dashboard: lista de todas las clínicas."""
    model = Clinica
    template_name = "saas/clinica_list.html"
    context_object_name = "clinicas"


class ClinicaCreateView(ProveedorRequired, CreateView):
    """Formulario para crear una nueva clínica."""
    model = Clinica
    form_class = ClinicaForm
    template_name = "saas/clinica_form.html"
    success_url = reverse_lazy("saas:clinica_list")

    def form_valid(self, form):
        clinica = form.save(commit=False)
        clinica.estado = "creando"
        clinica.save()

        # Crear túnel en Cloudflare
        try:
            cf = CloudflareService()
            result = cf.crear_tunnel(clinica.slug)
            
            clinica.tunnel_id = result["tunnel_id"]
            clinica.token = result["token"]
            
            # Crear DNS
            cf.crear_dns_cname(clinica.slug, result["tunnel_id"])
            
            # Configurar ingress en el túnel
            cf.configurar_ingress(result["tunnel_id"], f"{clinica.slug}.facdin.com")
            
            clinica.estado = "activo"
            clinica.fecha_activacion = timezone.now()
            clinica.save()
            
            messages.success(self.request, f"✓ Clínica {clinica.nombre} creada exitosamente")
        except Exception as e:
            clinica.estado = "error"
            clinica.save()
            messages.error(self.request, f"Error creando túnel: {str(e)}")
            return redirect("saas:clinica_list")

        return super().form_valid(form)


class ClinicaDetailView(ProveedorRequired, DetailView):
    """Detalle de una clínica con token e instrucciones."""
    model = Clinica
    template_name = "saas/clinica_detail.html"
    context_object_name = "clinica"


class ClinicaVerificarView(ProveedorRequired, View):
    """Verifica si el túnel de una clínica está activo."""
    
    def get(self, request, pk):
        clinica = get_object_or_404(Clinica, pk=pk)
        
        try:
            cf = CloudflareService()
            activo = cf.verificar_tunel_activo(clinica.tunnel_id)
            clinica.fecha_ultimo_check = timezone.now()
            clinica.estado = "activo" if activo else "suspendido"
            clinica.save()
            
            return JsonResponse({
                "success": True,
                "activo": activo,
                "estado": clinica.estado
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class ClinicaDescargarZipView(ProveedorRequired, View):
    """Genera un ZIP con .env + 2 .bat + LEEME.txt para el cliente."""

    def get(self, request, pk):
        import io
        import zipfile
        import re
        from django.http import HttpResponse
        from django.conf import settings

        clinica = get_object_or_404(Clinica, pk=pk)
        token = clinica.token or ""
        url_pub = clinica.url_publica
        nombre = clinica.nombre

        # --- .env personalizado ---
        env_contenido = f"""# Configuracion OdontoClin para {nombre}
# Generado automaticamente por el panel SaaS

DJANGO_LABCLIN_ROL=clinica
DJANGO_TUNNEL_URL={url_pub}
DJANGO_CSRF_TRUSTED_ORIGINS=https://{clinica.slug}.facdin.com,https://*.facdin.com
LABCLIN_PUERTO=8000
LABCLIN_MODO=escritorio
"""

        # --- descargar_app.bat (descarga el exe desde GitHub y lo lanza) ---
        releases_url = getattr(settings, "LABCLIN_RELEASES_URL", "")
        descargar_bat = f"""@echo off
chcp 65001 >nul
title Instalador OdontoClin - {nombre}
echo ================================================
echo   Instalando OdontoClin - {nombre}
echo ================================================
echo.

cd /d "%~dp0"

echo [1/2] Descargando aplicacion desde GitHub...
powershell -Command "try {{ Invoke-WebRequest -Uri '{releases_url}' -OutFile 'OdontoClin.exe' -ErrorAction Stop; Write-Host 'OK' }} catch {{ Write-Host 'Fallo la descarga manual: {releases_url}'; exit 1 }}"

if not exist OdontoClin.exe (
    echo.
    echo No se pudo descargar OdontoClin.exe.
    echo Descarguelo manualmente de:
    echo   {releases_url}
    echo y coloquelo en esta carpeta.
    pause
    exit /b 1
)

echo.
echo [2/2] Iniciando OdontoClin...
start "" "OdontoClin.exe"
echo.
echo La aplicacion se abrio. Complete el asistente inicial.
echo Despues ejecute "instalar_acceso_remoto.bat" como administrador.
echo.
pause
"""

        # --- instalar_acceso_remoto.bat (instala cloudflared + servicio) ---
        acceso_bat = f"""@echo off
chcp 65001 >nul
title Acceso Remoto - {nombre}
echo ================================================
echo   Instalando acceso remoto para {nombre}
echo ================================================
echo.

:: Verificar permisos de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ejecute este archivo como ADMINISTRADOR
    echo (clic derecho ^> Ejecutar como administrador)
    pause
    exit /b 1
)

cd /d "%~dp0"

echo [1/4] Descargando cloudflared desde Cloudflare...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi' -OutFile '%%TEMP%%\\cloudflared.msi'"

if not exist "%TEMP%\\cloudflared.msi" (
    echo [ERROR] No se pudo descargar cloudflared
    pause
    exit /b 1
)

echo [2/4] Instalando cloudflared (silencioso)...
msiexec /i "%TEMP%\\cloudflared.msi" /quiet /norestart

echo [3/4] Registrando tunel con su token...
set TOKEN={token}
"C:\\Program Files (x86)\\cloudflared\\cloudflared.exe" service install %TOKEN%
if %errorlevel% neq 0 (
    "C:\\Program Files\\cloudflared\\cloudflared.exe" service install %TOKEN%
)

echo [4/4] Iniciando servicio...
net start cloudflared

echo.
echo ================================================
echo   Instalacion completada
echo ================================================
echo.
echo   URL publica: {url_pub}
echo.
echo   Para detener:  net stop cloudflared
echo   Para iniciar:  net start cloudflared
echo.
echo   La clinica "{nombre}" ya es accesible desde internet.
echo.
pause
"""

        # --- LEEME.txt (guia para videollamada) ---
        leeme = f"""OdontoClin - Instalacion para {nombre}
======================================

CONTENIDO DEL PAQUETE
---------------------
1. descargar_app.bat       - Descarga e inicia la aplicacion
2. instalar_acceso_remoto.bat - Instala el acceso remoto (internet)
3. .env                    - Configuracion personalizada
4. LEEME.txt               - Este archivo

PASO 1: INSTALAR LA APLICACION
-------------------------------
1. Doble clic en "descargar_app.bat"
   - Se descargara OdontoClin.exe (~100 MB)
   - La aplicacion se abrira automaticamente
2. Complete el asistente inicial:
   - Crear usuario administrador
   - Datos de la clinica
   - Logo (opcional)

VERIFICACION PASO 1:
- Desde ESTE PC, abra http://localhost:8000 en el navegador
- Debe ver el login de OdontoClin con sus credenciales

PASO 2: INSTALAR ACCESO REMOTO
-------------------------------
1. Cierre OdontoClin.exe
2. Clic derecho en "instalar_acceso_remoto.bat"
   > Ejecutar como administrador
3. Espere los 4 pasos (descarga + instalacion + registro + inicio)
4. Reabra OdontoClin.exe (doble clic)

VERIFICACION PASO 2 (desdeel celular con DATOS MOVILES):
- Abra el navegador del celular (apague WiFi)
- Vaya a: {url_pub}
- Debe ver el login con candado (HTTPS)

OTROS PCS DE LA CLINICA (red local)
-----------------------------------
No instalan nada. Solo abren el navegador y van a:
   http://DIRECCION_IP_DE_ESTE_PC:8000

Para saber la IP de este PC:
   Abra cmd y ejecute: ipconfig
   Busque "Direccion IPv4": 192.168.x.x

SOPORTE
-------
Si algo falla, envie esta informacion a su proveedor:
- Captura de pantalla del error
- Que paso estaba ejecutando
- Modelo de Windows (inicio > configuracion > sistema > acerca de)

Clinica: {nombre}
URL publica: {url_pub}
"""

        # --- Armar el ZIP en memoria ---
        buf = io.BytesIO()
        slug_safe = re.sub(r"[^a-zA-Z0-9]", "_", clinica.slug)
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"OdontoClin_{slug_safe}/descargar_app.bat", descargar_bat)
            zf.writestr(f"OdontoClin_{slug_safe}/instalar_acceso_remoto.bat", acceso_bat)
            zf.writestr(f"OdontoClin_{slug_safe}/.env", env_contenido)
            zf.writestr(f"OdontoClin_{slug_safe}/LEEME.txt", leeme)

        buf.seek(0)
        nombre_zip = f"OdontoClin_{slug_safe}.zip"

        resp = HttpResponse(buf.read(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="{nombre_zip}"'
        resp["Content-Length"] = buf.getbuffer().nbytes
        return resp
