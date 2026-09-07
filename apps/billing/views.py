from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from apps.clinical.models import CitaDental

from .models import Factura
from .services import generar_factura, generar_pdf_factura


class FacturaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Factura
    permission_required = "billing.view_factura"
    template_name = "billing/factura_list.html"
    context_object_name = "object_list"
    paginate_by = 6

    def get_queryset(self):
        qs = Factura.objects.select_related("cita__expediente__paciente", "creado_por")
        q = self.request.GET.get("q", "").strip()
        if q:
            for term in q.split():
                qs = qs.filter(
                    Q(numero__icontains=term)
                    | Q(expediente__paciente__nombres__unaccent__icontains=term)
                    | Q(expediente__paciente__apellidos__unaccent__icontains=term)
                    | Q(expediente__paciente__ci__unaccent__icontains=term)
                )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class FacturaDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Factura
    permission_required = "billing.view_factura"
    template_name = "billing/factura_detail.html"
    context_object_name = "factura"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["detalles"] = self.object.detalles.select_related("servicio")
        context["metodos_pago"] = Factura.METODO_PAGO
        return context


class FacturaCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genera factura en $ desde una orden dental."""
    permission_required = "billing.add_factura"

    def post(self, request, cita_pk):
        cita = get_object_or_404(CitaDental, pk=cita_pk)
        try:
            factura = generar_factura(cita, request.user)
            messages.success(request, f"Factura {factura.numero} generada por ${factura.total}")
            return redirect("billing:detail", pk=factura.pk)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("patients:historial", pk=cita.expediente.paciente.pk)


class FacturaPagarView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "billing.change_factura"

    def post(self, request, pk):
        factura = get_object_or_404(Factura, pk=pk)

        if factura.estado == "anulada":
            messages.error(request, "No se puede pagar una factura anulada")
        else:
            metodo = request.POST.get("metodo_pago", "")
            if metodo in dict(Factura.METODO_PAGO):
                factura.metodo_pago = metodo
            factura.estado = "pagada"
            factura.save(update_fields=["estado", "metodo_pago", "ultima_fecha_act"])
            messages.success(request, f"Factura {factura.numero} marcada como pagada")

        return redirect("billing:detail", pk=factura.pk)


class FacturaAnularView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "billing.change_factura"

    def post(self, request, pk):
        factura = get_object_or_404(Factura, pk=pk)

        if factura.estado == "pagada":
            messages.error(request, "No se puede anular una factura pagada")
        else:
            motivo = request.POST.get("motivo_anulacion", "").strip()
            motivo_otro = request.POST.get("motivo_anulacion_otro", "").strip()
            
            if not motivo:
                messages.error(request, "Debe seleccionar un motivo de anulación")
                return redirect("billing:detail", pk=factura.pk)
            
            if motivo == "otros" and not motivo_otro:
                messages.error(request, "Debe especificar el motivo cuando selecciona 'Otros'")
                return redirect("billing:detail", pk=factura.pk)
            
            factura.estado = "anulada"
            factura.motivo_anulacion = motivo
            factura.motivo_anulacion_otro = motivo_otro if motivo == "otros" else ""
            factura.save(update_fields=["estado", "motivo_anulacion", "motivo_anulacion_otro", "ultima_fecha_act"])
            messages.success(request, f"Factura {factura.numero} anulada. Motivo: {factura.get_motivo_anulacion_display()}")

        return redirect("billing:detail", pk=factura.pk)


class FacturaPDFView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Descarga el PDF de una factura con el encabezado del laboratorio"""
    permission_required = "billing.view_factura"

    def get(self, request, pk):
        factura = get_object_or_404(Factura, pk=pk)
        pdf = generar_pdf_factura(factura)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="factura_{factura.numero}.pdf"'
        return response
