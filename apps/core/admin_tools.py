import os
from pathlib import Path
from django.conf import settings
"""Herramientas de administracion: exclusivas del superusuario"""
import json
from datetime import date as hoy_date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:  # ejecutables empaquetados sin openpyxl
    openpyxl = None
    Alignment = Font = PatternFill = None

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from apps.billing.models import Factura
from apps.exams.models import CostoExamen, Examen
from apps.results.models import Resultado


class SoloSuperUser(UserPassesTestMixin):
    """Vistas exclusivas del administrador"""

    def test_func(self):
        return self.request.user.is_superuser


class AjusteMasivoPreciosView(SoloSuperUser, TemplateView):
    template_name = "exams/ajuste_masivo.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("preview", [])
        ctx.setdefault("porcentaje", "")
        ctx["total_examenes"] = Examen.objects.filter(activo=True).count()
        return ctx

    def post(self, request, *args, **kwargs):
        try:
            pct = Decimal(request.POST.get("porcentaje", "0").replace(",", "."))
        except (InvalidOperation, ValueError):
            messages.error(request, "Porcentaje invalido.")
            return redirect("ajuste_masivo")

        if pct <= Decimal("-100"):
            messages.error(request, "El ajuste no puede dejar precios en cero o negativo.")
            return redirect("ajuste_masivo")

        factor = (Decimal("100") + pct) / Decimal("100")
        filas = []
        for ex in Examen.objects.filter(activo=True).order_by("nombre_completo"):
            costo = ex.costo_actual
            if costo:
                nuevo = (costo.precio * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                filas.append({"examen": ex, "actual": costo.precio, "nuevo": nuevo})

        if "aplicar" in request.POST:
            with transaction.atomic():
                for fila in filas:
                    CostoExamen.objects.create(examen=fila["examen"], precio=fila["nuevo"], activo=True)
            messages.success(request, f"{len(filas)} precios actualizados con ajuste de {pct:+.2f}%.")
            return redirect("exams:list")

        ctx = self.get_context_data()
        ctx["preview"] = filas
        ctx["porcentaje"] = str(pct)
        return self.render_to_response(ctx)


class FacturaExportarExcelView(SoloSuperUser, TemplateView):
    template_name = "reports/exportar_excel.html"

    def post(self, request, *args, **kwargs):
        if openpyxl is None:
            messages.error(request, "La exportacion a Excel no esta disponible en esta instalacion.")
            return redirect(request.path)
        desde = request.POST.get("desde") or None
        hasta = request.POST.get("hasta") or None

        qs = Factura.objects.select_related("expediente__paciente").order_by("numero_control")
        if desde:
            qs = qs.filter(fecha_creacion__date__gte=desde)
        if hasta:
            qs = qs.filter(fecha_creacion__date__lte=hasta)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Facturas"

        fill = PatternFill("solid", fgColor="1E65C0")
        font = Font(bold=True, color="FFFFFF")

        ws.append(["N Control", "N Factura", "Fecha", "Paciente", "Estado", "Motivo anulación", "Detalle motivo", "Metodo de pago", "Subtotal", "Descuento", "Total", "Tasa", "Total Bs"])
        for c in ws[1]:
            c.fill = fill
            c.font = font
            c.alignment = Alignment(horizontal="center")

        from apps.core.models import TasaCambio
        _t = TasaCambio.actual()
        tasa_hoy = _t.valor if _t else Decimal("0")
        total_general = Decimal("0")
        total_general_bs = Decimal("0")
        for f in qs:
            tasa_f = f.tasa or tasa_hoy
            if f.estado != "anulada":
                total_general += f.total
                total_general_bs += f.total * tasa_f
            ws.append([
                f.numero_control,
                f.numero,
                f.fecha_creacion.strftime("%d/%m/%Y"),
                str(f.expediente.paciente),
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

        for i, ancho in enumerate([12, 12, 12, 40, 10, 18, 30, 18, 12, 12, 12, 12, 14], start=1):
            ws.column_dimensions[chr(64 + i)].width = ancho

        wd = wb.create_sheet("Detalles")
        wd.append(["N Control", "N Factura", "Examen", "Cantidad", "Precio unit.", "Subtotal"])
        for c in wd[1]:
            c.fill = fill
            c.font = font
        for f in qs:
            for d in f.detalles.select_related("examen"):
                wd.append([f.numero_control, f.numero, d.examen.nombre_completo, d.cantidad, float(d.precio_unitario), float(d.subtotal)])

        nombre = f"facturacion_{desde or 'inicio'}_{hasta or 'hoy'}.xlsx"
        
        if getattr(settings, 'ESCRITORIO', False):
            # Modo escritorio: guardar en disco y abrir en Excel
            export_dir = Path(settings.DATA_DIR) / "exportaciones"
            export_dir.mkdir(parents=True, exist_ok=True)
            ruta = export_dir / nombre
            wb.save(str(ruta))
            messages.success(request, f"Archivo guardado en: {ruta}")
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(ruta)
                else:  # Linux/Mac
                    import subprocess
                    subprocess.run(['xdg-open', str(ruta)])
            except Exception as e:
                messages.warning(request, f"No se pudo abrir automáticamente. Ruta: {ruta}")
            return redirect(request.path)
        else:
            # Modo web: descarga HTTP normal
            response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = f'attachment; filename="{nombre}"'
            wb.save(response)
            return response


class EstadisticasView(SoloSuperUser, TemplateView):
    template_name = "reports/estadisticas.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            dias = int(self.request.GET.get("dias", 365))
        except ValueError:
            dias = 365
        desde = timezone.now() - timedelta(days=dias)
        ctx["dias"] = dias

        base = Resultado.objects.exclude(estado="anulado").filter(fecha_creacion__gte=desde)

        top = list(
            base.values("examen__nombre_completo")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        por_mes = list(
            base.annotate(mes=TruncMonth("fecha_creacion"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")
        )
        por_sexo = list(
            base.values("expediente__paciente__sexo").annotate(total=Count("id"))
        )

        rangos = {"0-12": 0, "13-25": 0, "26-40": 0, "41-60": 0, "61+": 0}
        hoy = hoy_date.today()
        for fn in base.values_list("expediente__paciente__fecha_nac", flat=True):
            if not fn:
                continue
            edad = (hoy - fn).days // 365
            if edad <= 12:
                rangos["0-12"] += 1
            elif edad <= 25:
                rangos["13-25"] += 1
            elif edad <= 40:
                rangos["26-40"] += 1
            elif edad <= 60:
                rangos["41-60"] += 1
            else:
                rangos["61+"] += 1

        facturas = Factura.objects.exclude(estado="anulada").filter(fecha_creacion__gte=desde)
        ingresos = list(
            facturas.annotate(mes=TruncMonth("fecha_creacion"))
            .values("mes")
            .annotate(total=Sum("total"))
            .order_by("mes")
        )

        ctx.update({
            "top_examenes": top,
            "total_resultados": base.count(),
            "total_facturas": facturas.count(),
            "total_ingresos": sum((f.total for f in facturas), Decimal("0")),
            "chart_top_labels": json.dumps([t["examen__nombre_completo"] for t in top]),
            "chart_top_data": json.dumps([t["total"] for t in top]),
            "chart_mes_labels": json.dumps([m["mes"].strftime("%b %y") if m["mes"] else "-" for m in por_mes]),
            "chart_mes_data": json.dumps([m["total"] for m in por_mes]),
            "chart_sexo_labels": json.dumps(["Femenino", "Masculino", "Otro"]),
            "chart_sexo_data": json.dumps([
                sum(s["total"] for s in por_sexo if s["expediente__paciente__sexo"] == "F"),
                sum(s["total"] for s in por_sexo if s["expediente__paciente__sexo"] == "M"),
                sum(s["total"] for s in por_sexo if s["expediente__paciente__sexo"] not in ("F", "M")),
            ]),
            "chart_edad_labels": json.dumps(list(rangos.keys())),
            "chart_edad_data": json.dumps(list(rangos.values())),
            "chart_ing_labels": json.dumps([m["mes"].strftime("%b %y") if m["mes"] else "-" for m in ingresos]),
            "chart_ing_data": json.dumps([float(m["total"] or 0) for m in ingresos]),
        })
        return ctx


class LicenciaView(SoloSuperUser, TemplateView):
    """Panel de licencia: tipo, vencimiento, dias, huella y modo dev."""
    template_name = "core/licencia_panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.core.licencias import info_licencia
        ctx["lic"] = info_licencia()
        return ctx
