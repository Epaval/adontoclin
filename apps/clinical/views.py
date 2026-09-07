from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, DetailView, CreateView, ListView
from django.urls import reverse_lazy

from .models import (
    TIPO_TRATAMIENTO,
    ExpedienteDental, HistorialDiente, ServicioDental,
    OrdenDental, DIENTE_FDI, COLOR_DIENTE,
)
from apps.patients.models import Paciente


# ===== Arcada fija para el SVG =====
DIENTE_NUMS_SUPERIOR = ["18","17","16","15","14","13","12","11",
                         "21","22","23","24","25","26","27","28"]
DIENTE_NUMS_INFERIOR = ["48","47","46","45","44","43","42","41",
                         "31","32","33","34","35","36","37","38"]


class OdontogramaView(LoginRequiredMixin, TemplateView):
    """Odontograma FDI interactivo: hover muestra historial, clic registra tratamiento."""
    template_name = "clinical/odontograma.html"

    def post(self, request, paciente_id):
        paciente = get_object_or_404(Paciente, pk=paciente_id)
        diente = request.POST.get("diente", "")
        tipo = request.POST.get("tipo", "")
        notas = request.POST.get("notas", "").strip()
        expediente = paciente.expedientes_dentales.order_by("-fecha_creacion").first()
        if expediente is None:
            expediente = ExpedienteDental.objects.create(
                paciente=paciente,
                motivo="Registro de odontograma",
                creado_por=request.user,
            )
        HistorialDiente.objects.create(
            expediente=expediente,
            paciente=paciente,
            diente_fdi=diente,
            tipo=tipo,
            notas=notas,
        )
        messages.success(request, f"Diente {diente}: {dict(TIPO_TRATAMIENTO).get(tipo, tipo)} registrado.")
        return redirect("clinical:odontograma", paciente_id=paciente.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        paciente = get_object_or_404(Paciente, pk=self.kwargs["paciente_id"])

        colores = {}
        historial = {}
        for h in HistorialDiente.objects.filter(paciente=paciente).order_by("-fecha"):
            colores.setdefault(h.diente_fdi, h.color)
            historial.setdefault(h.diente_fdi, []).append({
                "tipo_display": h.get_tipo_display(),
                "fecha": h.fecha.strftime("%d/%m/%Y"),
                "notas": h.notas,
                "color": h.color,
            })

        ctx.update({
            "paciente": paciente,
            "diente_nums_superior": DIENTE_NUMS_SUPERIOR,
            "diente_nums_inferior": DIENTE_NUMS_INFERIOR,
            "colores_paciente": colores,
            "historial_paciente": historial,
            "tipos_tratamiento": TIPO_TRATAMIENTO,
            "colores_leyenda": [
                ("Sano", COLOR_DIENTE["sano"]),
                ("Caries", COLOR_DIENTE["caries"]),
                ("Obturación", COLOR_DIENTE["obstruccion"]),
                ("Endodoncia", COLOR_DIENTE["endodoncia"]),
                ("Corona", COLOR_DIENTE["corona"]),
                ("Sellante", COLOR_DIENTE["sellante"]),
                ("Extracción", COLOR_DIENTE["extraccion"]),
                ("Prótesis", COLOR_DIENTE["protesis"]),
                ("Implante", COLOR_DIENTE["implante"]),
                ("Ortodoncia", COLOR_DIENTE["ortodoncia"]),
            ],
        })
        return ctx


class ExpedienteDentalListView(LoginRequiredMixin, ListView):
    model = ExpedienteDental
    template_name = "clinical/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 10


class ServicioDentalListView(LoginRequiredMixin, ListView):
    model = ServicioDental
    template_name = "clinical/servicio_list.html"
    context_object_name = "servicios"
    paginate_by = 12


class ExpedienteDentalCreateView(LoginRequiredMixin, CreateView):
    model = ExpedienteDental
    fields = ["paciente", "motivo", "patologias", "alergias", "operaciones", "notas", "archivo_adjunto"]
    template_name = "form.html"
    success_url = reverse_lazy("clinical:expediente_list")
    extra_context = {"title": "Nueva consulta dental"}

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        return super().form_valid(form)
