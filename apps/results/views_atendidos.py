from datetime import date, datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Max, Q
from django.views.generic import DetailView, ListView

from apps.patients.models import Expediente, Paciente


class PacientesAtendidosView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Pacientes atendidos por dia (por defecto hoy) con filtros"""
    model = Paciente
    permission_required = "results.view_resultado"
    template_name = "results/pacientes_atendidos.html"
    context_object_name = "pacientes"
    paginate_by = 20

    def get_queryset(self):
        fecha_str = self.request.GET.get("fecha", "").strip()
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            except ValueError:
                fecha = date.today()
        else:
            fecha = date.today()

        self.fecha_filtro = fecha

        qs = Paciente.objects.filter(
            expedientes__fecha_creacion__date=fecha,
            activo=True,
        ).annotate(
            total_ordenes=Count("expedientes", distinct=True),
            ultimo_atendido=Max("expedientes__fecha_creacion"),
        ).distinct().order_by("-ultimo_atendido")

        nombre = self.request.GET.get("nombre", "").strip()
        if nombre:
            for term in nombre.split():
                qs = qs.filter(
                    Q(nombres__unaccent__icontains=term)
                    | Q(apellidos__unaccent__icontains=term)
                )

        ci = self.request.GET.get("ci", "").strip()
        if ci:
            qs = qs.filter(ci__icontains=ci)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fecha_filtro"] = self.fecha_filtro
        context["nombre_filtro"] = self.request.GET.get("nombre", "")
        context["ci_filtro"] = self.request.GET.get("ci", "")
        context["hoy"] = date.today()
        return context


class HistoriaPacienteView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Historia completa: todas las visitas y resultados del paciente"""
    model = Paciente
    permission_required = "results.view_resultado"
    template_name = "results/historia_paciente.html"
    context_object_name = "paciente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expedientes = Expediente.objects.filter(
            paciente=self.object
        ).prefetch_related(
            "resultados__examen",
            "expedientes_medicos__medico",
        ).order_by("-fecha_creacion")

        context["expedientes"] = expedientes
        context["total_examenes"] = sum(
            exp.resultados.count() for exp in expedientes
        )
        return context
