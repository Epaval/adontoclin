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
    """Genera un ZIP con INSTALAR.bat + .env + LEEME.txt para el cliente."""

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
        slug_safe = re.sub(r"[^a-zA-Z0-9]", "_", clinica.slug)

        # --- .env personalizado ---
        env_contenido = f"""# Configuracion OdontoClin para {nombre}
# Generado automaticamente por el panel SaaS

DJANGO_LABCLIN_ROL=clinica
DJANGO_TUNNEL_URL={url_pub}
DJANGO_CSRF_TRUSTED_ORIGINS=https://{clinica.slug}.facdin.com,https://*.facdin.com
LABCLIN_PUERTO=8000
LABCLIN_MODO=escritorio
"""

        # --- INSTALAR.bat unico: se auto-eleva y hace todo ---
        instalar_bat = f"""@echo off
chcp 65001 >nul
title Instalacion OdontoClin - {nombre}
cd /d "%~dp0"

:: Auto-elevar a administrador si no lo somos
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

echo ================================================
echo   Instalacion automatica - {nombre}
echo ================================================
echo.

echo [1/6] Descargando instalador oficial...
powershell -Command "try {{ $r = Invoke-RestMethod -Uri 'https://api.github.com/repos/Epaval/adontoclin/releases/latest' -UseBasicParsing; $a = $r.assets | Select-Object -First 1; Invoke-WebRequest -Uri $a.browser_download_url -OutFile '%TEMP%\OdontoClin-Setup.exe' -UseBasicParsing }} catch {{ exit 1 }}"
if not exist "%TEMP%\OdontoClin-Setup.exe" (
    echo ERROR: no se pudo descargar el instalador.
    echo Verifique internet o descargue manualmente desde:
    echo   https://github.com/Epaval/adontoclin/releases/latest
    pause
    exit /b 1
)

echo [2/6] Instalando OdontoClin (silencioso, ~1 min)...
start /wait "" "%TEMP%\OdontoClin-Setup.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART

echo [3/6] Copiando configuracion de {nombre}...
set DEST=
for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "$p=[Environment]::GetFolderPath('Desktop'); $l=Join-Path $p 'OdontoClin.lnk'; if(Test-Path $l){{(New-Object -ComObject WScript.Shell).CreateShortcut($l).TargetPath}}" 2^>nul`) do for %%f in ("%%i") do set "DEST=%%~dpf"
if not defined DEST if exist "C:\Program Files\OdontoClin\OdontoClin.exe" set DEST=C:\Program Files\OdontoClin
if not defined DEST if exist "C:\Program Files (x86)\OdontoClin\OdontoClin.exe" set DEST=C:\Program Files (x86)\OdontoClin
if defined DEST if "%DEST:~-1%"=="\\" set "DEST=%DEST:~0,-1%"
if defined DEST (
    copy /Y "%~dp0.env" "%DEST%\.env" >nul
    echo      Config aplicada en %DEST%
) else (
    echo      No se encontro la carpeta de instalacion.
)

echo [4/6] Instalando acceso remoto (cloudflared)...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi' -OutFile '%TEMP%\cf.msi' -UseBasicParsing"
msiexec /i "%TEMP%\cf.msi" /quiet /norestart

echo [5/6] Registrando tunel de {nombre}...
net stop cloudflared >nul 2>&1
sc delete cloudflared >nul 2>&1
set TOKEN={token}
if exist "C:\Program Files (x86)\cloudflared\cloudflared.exe" (
    "C:\Program Files (x86)\cloudflared\cloudflared.exe" service install %TOKEN%
) else (
    "C:\Program Files\cloudflared\cloudflared.exe" service install %TOKEN%
)
net start cloudflared >nul 2>&1

echo [6/6] Iniciando OdontoClin...
if defined DEST start "" "%DEST%\OdontoClin.exe"

echo.
echo ================================================
echo   INSTALACION COMPLETADA - {nombre}
echo.
echo   Internet:  {url_pub}
echo   Red local: http://localhost:8000
echo ================================================
echo.
pause
"""

        # --- LEEME.txt ---
        leeme = f"""OdontoClin - Instalacion para {nombre}
======================================

INSTALACION (2 clics)
---------------------
1. Extraiga este ZIP en el Escritorio
2. Doble clic en "INSTALAR_{slug_safe}.bat"
3. Acepte el permiso de administrador ("Si")
4. Espere los 6 pasos y listo

QUE PASA SOLO
-------------
- Se descarga e instala OdontoClin
- Se copia la configuracion de {nombre}
- Se instala el acceso remoto a internet
- Se abre OdontoClin para crear su usuario admin

VERIFICAR (celular con DATOS, WiFi apagado)
-------------------------------------------
   {url_pub}
Debe ver el login con candado HTTPS.

OTROS PCS DE LA CLINICA
-----------------------
Sin instalar nada, abren el navegador en:
   http://IP_DE_ESTE_PC:8000
(IP: cmd > ipconfig > Direccion IPv4)

SOPORTE: envie captura del error indicando en que paso estaba.
Clinica: {nombre} | URL: {url_pub}
"""

        # --- Armar el ZIP en memoria ---
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"OdontoClin_{slug_safe}/INSTALAR_{slug_safe}.bat", instalar_bat)
            zf.writestr(f"OdontoClin_{slug_safe}/.env", env_contenido)
            zf.writestr(f"OdontoClin_{slug_safe}/LEEME.txt", leeme)

        buf.seek(0)
        nombre_zip = f"OdontoClin_{slug_safe}.zip"

        resp = HttpResponse(buf.read(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="{nombre_zip}"'
        resp["Content-Length"] = buf.getbuffer().nbytes
        return resp
