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
            from apps.patients.models import Paciente, Expediente
            from apps.exams.models import Examen
            from django.db.models import Q

            ctx["pacientes"] = Paciente.objects.filter(
                Q(nombres__icontains=q) | Q(apellidos__icontains=q) | Q(ci__icontains=q)
                | Q(representante__ci__icontains=q) | Q(telefono__icontains=q)
                | Q(representante__telefono__icontains=q)
            ).filter(activo=True).select_related("representante")[:10]

            ctx["ordenes"] = Expediente.objects.filter(
                Q(paciente__nombres__icontains=q) | Q(paciente__apellidos__icontains=q) | Q(paciente__ci__icontains=q)
            ).select_related("paciente").order_by("-fecha_creacion")[:10]

            ctx["examenes"] = Examen.objects.filter(
                Q(nombre_completo__icontains=q) | Q(perfil__icontains=q)
            ).filter(activo=True)[:10]
        return ctx
