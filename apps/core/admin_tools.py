import io
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from apps.billing.models import DetalleFactura, Factura
from apps.clinical.models import ServicioDental

try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:
    openpyxl = None


class SoloSuperUser(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class LicenciaView(SoloSuperUser, TemplateView):
    template_name = "core/licencia_panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.core import licencias
        ctx.update({
            "estado": licencias.estado_licencia(),
            "dias": licencias.dias_restantes(),
            "huella": licencias.huella_maquina(),
        })
        return ctx


class EstadisticasView(SoloSuperUser, TemplateView):
    template_name = "reports/estadisticas.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "total_pacientes": __import__("apps.patients.models", fromlist=["Paciente"]).Paciente.objects.filter(activo=True).count(),
            "total_servicios": ServicioDental.objects.filter(activo=True).count(),
            "total_facturas": Factura.objects.count(),
            "ingresos_usd": Factura.objects.filter(estado="emitida").aggregate(t=models.Sum("total"))["t"] or Decimal("0"),
        })
        return ctx


class AjusteMasivoPreciosView(SoloSuperUser, View):
    """Ajuste masivo de precios de servicios en $ por porcentaje."""

    def get(self, request):
        return render(request, "clinical/ajuste_masivo.html", {
            "servicios": ServicioDental.objects.filter(activo=True),
        })

    def post(self, request):
        try:
            pct = Decimal(request.POST.get("porcentaje", "0"))
        except Exception:
            messages.error(request, "Porcentaje inválido.")
            return redirect("ajuste_masivo")
        if pct == 0:
            messages.error(request, "Indique un porcentaje distinto de 0.")
            return redirect("ajuste_masivo")
        factor = (Decimal("100") + pct) / Decimal("100")
        n = 0
        for s in ServicioDental.objects.filter(activo=True):
            s.precio_usd = (s.precio_usd * factor).quantize(Decimal("0.01"))
            s.save(update_fields=["precio_usd"])
            n += 1
        messages.success(request, f"{n} servicios ajustados en {pct}%.")
        return redirect("ajuste_masivo")


class FacturaExportarExcelView(SoloSuperUser, TemplateView):
    template_name = "reports/exportar_excel.html"

    def post(self, request, *args, **kwargs):
        if openpyxl is None:
            messages.error(request, "La exportacion a Excel no esta disponible en esta instalacion.")
            return redirect(request.path)
        desde = request.POST.get("desde") or None
        hasta = request.POST.get("hasta") or None

        qs = Factura.objects.select_related("cita__expediente__paciente").order_by("numero_control")
        if desde:
            qs = qs.filter(fecha_creacion__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_creacion__date__lte=hasta)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Facturas"
        fill = PatternFill("solid", fgColor="1E65C0")
        font = Font(bold=True, color="FFFFFF")

        ws.append(["N Control", "N Factura", "Fecha", "Paciente", "Estado", "Motivo anulacion", "Detalle motivo", "Metodo de pago", "Subtotal", "Descuento", "Total", "Tasa", "Total Bs"])
        for c in ws[1]:
            c.fill = fill
            c.font = font
            c.alignment = Alignment(horizontal="center")

        total_general = Decimal("0")
        total_general_bs = Decimal("0")
        for f in qs:
            tasa_f = f.tasa or Decimal("0")
            if f.estado != "anulada":
                total_general += f.total
                total_general_bs += f.total * tasa_f
            ws.append([
                f.numero_control,
                f.numero,
                f.fecha_creacion.strftime("%d/%m/%Y"),
                str(f.cita.expediente.paciente),
                f.get_estado_display(),
                f.get_motivo_anulacion_display() or "-",
                f.motivo_anulacion_otro or "-",
                f.get_metodo_pago_display() or "-",
                float(f.subtotal),
                float(f.descuento),
                float(f.total),
                float(tasa_f),
                float(f.total * tasa_f),
            ])

        ws.append([])
        ws.append(["", "", "", "", "", "", "", "", "", "", "TOTAL:", float(total_general), float(total_general_bs)])
        ws.cell(row=ws.max_row, column=11).font = Font(bold=True)
        ws.cell(row=ws.max_row, column=12).font = Font(bold=True)
        ws.cell(row=ws.max_row, column=13).font = Font(bold=True)

        wd = wb.create_sheet("Detalles")
        wd.append(["N Control", "N Factura", "Servicio", "Diente", "Cantidad", "Precio unit.", "Subtotal"])
        for c in wd[1]:
            c.fill = fill
            c.font = font
        for f in qs:
            for d in f.detalles.select_related("servicio").all():
                wd.append([
                    f.numero_control, f.numero, d.servicio.nombre,
                    d.diente_fdi or "-", d.cantidad,
                    float(d.precio_unitario), float(d.subtotal),
                ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="facturacion_odontoclin.xlsx"'
        return response
