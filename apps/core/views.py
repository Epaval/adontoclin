from django.db.models import Q
from django.views.generic import TemplateView
import sqlite3
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.shortcuts import redirect
from django.views import View


class BackupView(LoginRequiredMixin, View):
    """Respaldo de un clic: crea la copia y la descarga (solo escritorio)"""

    def get(self, request):
        if not settings.ESCRITORIO:
            messages.error(request, "El respaldo de un clic solo existe en modo escritorio")
            return redirect("dashboard")

        try:
            origen = settings.DATABASES["default"]["NAME"]

            dir_backups = settings.DATA_DIR / "backups"
            dir_backups.mkdir(parents=True, exist_ok=True)

            nombre = f"labclin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            destino = dir_backups / nombre

            src = sqlite3.connect(str(origen))
            dst = sqlite3.connect(str(destino))
            with dst:
                src.backup(dst)
            src.close()
            dst.close()

            messages.success(request, f"Respaldo {nombre} creado y descargado")
            return FileResponse(open(destino, "rb"), as_attachment=True, filename=nombre)

        except Exception as e:
            messages.error(request, f"Error al crear respaldo: {str(e)}")
            return redirect("dashboard")


class BusquedaGlobalView(LoginRequiredMixin, TemplateView):
    """Búsqueda unificada: pacientes, órdenes y exámenes."""
    template_name = "core/busqueda_global.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        ctx["q"] = q
        if q and len(q) >= 2:
            from apps.patients.models import Paciente
            from apps.clinical.models import CitaDental as _CitaDental
            from apps.clinical.models import ServicioDental
            from django.db.models import Q

            ctx["pacientes"] = Paciente.objects.filter(
                Q(nombres__icontains=q) | Q(apellidos__icontains=q) | Q(ci__icontains=q)
                | Q(representante__ci__icontains=q) | Q(telefono__icontains=q)
                | Q(representante__telefono__icontains=q)
            ).filter(activo=True).select_related("representante")[:10]

            ctx["ordenes"] = _CitaDental.objects.filter(
                Q(expediente__paciente__nombres__icontains=q)
                | Q(expediente__paciente__apellidos__icontains=q)
                | Q(expediente__paciente__ci__icontains=q)
            ).select_related("expediente__paciente").order_by("-fecha_creacion")[:10]

            ctx["examenes"] = ServicioDental.objects.filter(
                Q(nombre__icontains=q) | Q(codigo__icontains=q)
            ).filter(activo=True)[:10]
        return ctx


class RecordatoriosWhatsAppView(LoginRequiredMixin, TemplateView):
    """Citas del dia con boton de recordatorio WhatsApp por paciente."""
    template_name = "core/recordatorios_whatsapp.html"

    def get_context_data(self, **kwargs):
        from datetime import date, datetime
        from apps.clinical.models import CitaDental
        from .models import ConfiguracionClinica
        ctx = super().get_context_data(**kwargs)
        try:
            f = datetime.strptime(self.request.GET.get("fecha", ""), "%Y-%m-%d").date()
        except Exception:
            f = date.today()
        ctx["fecha"] = f
        ctx["citas"] = (CitaDental.objects.filter(fecha__date=f)
                        .select_related("expediente__paciente").order_by("fecha"))
        ctx["cfg"] = ConfiguracionClinica.cargar()
        return ctx


class ConfiguracionWhatsAppView(LoginRequiredMixin, View):
    """Plantilla WhatsApp editable por clinica con preview."""
    def get(self, request):
        from django.shortcuts import render
        from .models import ConfiguracionClinica
        from .whatsapp import renderizar_plantilla
        cfg = ConfiguracionClinica.cargar()
        preview = renderizar_plantilla(cfg.plantilla_whatsapp, nombre="María Pérez",
                                       clinica=cfg.nombre_clinica, servicio="Limpieza dental",
                                       fecha="15/09/2026", hora="10:30")
        return render(request, "core/config_whatsapp.html", {"cfg": cfg, "preview": preview})

    def post(self, request):
        from django.contrib import messages
        from django.shortcuts import redirect
        from .models import ConfiguracionClinica
        cfg = ConfiguracionClinica.cargar()
        cfg.nombre_clinica = request.POST.get("nombre_clinica", cfg.nombre_clinica)[:120]
        cfg.wa_prefijo = request.POST.get("wa_prefijo", cfg.wa_prefijo)[:5]
        tpl = request.POST.get("plantilla_whatsapp", "")
        if tpl.strip():
            cfg.plantilla_whatsapp = tpl
        cfg.save()
        messages.success(request, "Configuración de WhatsApp guardada.")
        return redirect("config_whatsapp")
