from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import PacienteForm
from .models import Paciente


class PacienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Paciente
    permission_required = "patients.view_paciente"
    template_name = "patients/paciente_list.html"
    context_object_name = "object_list"
    paginate_by = 6

    def get_queryset(self):
        qs = Paciente.objects.filter(activo=True).order_by("apellidos", "nombres")
        q = self.request.GET.get("q", "").strip()
        if q:
            for term in q.split():
                qs = qs.filter(
                    Q(nombres__unaccent__icontains=term)
                    | Q(apellidos__unaccent__icontains=term)
                    | Q(ci__unaccent__icontains=term)
                    | Q(telefono__unaccent__icontains=term)
                    | Q(email__unaccent__icontains=term)
                    | Q(representante__ci__unaccent__icontains=term)
                )
        return qs.select_related("representante")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class PacienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Paciente
    form_class = PacienteForm
    permission_required = "patients.crear_paciente"
    template_name = "form.html"
    success_url = reverse_lazy("patients:list")
    extra_context = {"title": "Nuevo paciente", "es_paciente": True}


class PacienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Paciente
    form_class = PacienteForm
    permission_required = "patients.change_paciente"
    template_name = "form.html"
    success_url = reverse_lazy("patients:list")
    extra_context = {"title": "Editar paciente", "es_paciente": True}

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["fecha_nac"].disabled = True
        return form


class PacienteHistorialView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Paciente
    permission_required = "patients.view_paciente"
    template_name = "patients/paciente_historial.html"
    context_object_name = "paciente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            expediente = self.object.expediente_dental
            context["expediente"] = expediente
            context["citas"] = expediente.citas.prefetch_related(
                "dientes", "items__servicio"
            ).order_by("-fecha")
        except Exception:
            context["expediente"] = None
            context["citas"] = []
        from apps.billing.models import Factura
        from apps.clinical.models import HistorialDiente
        context["stats_historial"] = {
            "citas": len(context["citas"]),
            "dientes": HistorialDiente.objects.filter(paciente=self.object).values("diente_fdi").distinct().count(),
            "facturado": Factura.objects.filter(
                cita__expediente__paciente=self.object, estado="emitida"
            ).aggregate(t=__import__("django.db.models", fromlist=["Sum"]).Sum("total"))["t"] or 0,
        }
        return context
