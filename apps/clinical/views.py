from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.patients.models import Paciente

from .models import (
    COLOR_DIENTE,
    DIENTE_NUMS_INFERIOR,
    DIENTE_NUMS_SUPERIOR,
    TIPO_TRATAMIENTO,
    CitaDental,
    ExpedienteDental,
    HistorialDiente,
    ServicioDental,
)


class ServicioDentalListView(LoginRequiredMixin, ListView):
    model = ServicioDental
    template_name = "clinical/servicio_list.html"
    context_object_name = "servicios"
    paginate_by = 12


class ExpedienteDentalListView(LoginRequiredMixin, ListView):
    model = ExpedienteDental
    template_name = "clinical/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 10


class ExpedienteDentalCreateView(LoginRequiredMixin, CreateView):
    model = ExpedienteDental
    fields = ["patologias", "alergias", "operaciones", "notas"]
    template_name = "clinical/expediente_form.html"

    def get_initial(self):
        return {"paciente": self.request.GET.get("paciente")}

    def dispatch(self, request, *args, **kwargs):
        self.paciente = get_object_or_404(Paciente, pk=self.kwargs["paciente_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.paciente = self.paciente
        form.instance.creado_por = self.request.user
        messages.success(self.request, "Historia clínica creada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.paciente.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["paciente"] = self.paciente
        ctx["title"] = f"Historia clínica de {self.paciente.full_name}"
        return ctx


class ExpedienteDentalUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpedienteDental
    fields = ["patologias", "alergias", "operaciones", "notas"]
    template_name = "clinical/expediente_form.html"
    extra_context = {"title": "Editar historia clínica"}

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.object.paciente.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["paciente"] = self.object.paciente
        return ctx


class CitaDentalCreateView(LoginRequiredMixin, CreateView):
    model = CitaDental
    fields = ["fecha", "motivo", "notas", "archivo_adjunto", "estado"]
    template_name = "form.html"
    extra_context = {"title": "Nueva cita dental"}

    def dispatch(self, request, *args, **kwargs):
        self.paciente = get_object_or_404(Paciente, pk=self.kwargs["paciente_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        expediente, _ = ExpedienteDental.objects.get_or_create(
            paciente=self.paciente,
            defaults={"creado_por": self.request.user},
        )
        form.instance.expediente = expediente
        form.instance.creado_por = self.request.user
        messages.success(self.request, "Cita registrada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.paciente.pk})


class CitaDentalUpdateView(LoginRequiredMixin, UpdateView):
    model = CitaDental
    fields = ["fecha", "motivo", "notas", "archivo_adjunto", "estado"]
    template_name = "form.html"
    extra_context = {"title": "Editar cita dental"}

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.object.expediente.paciente.pk})


class OdontogramaView(LoginRequiredMixin, TemplateView):
    """Odontograma GENERAL del paciente: hover historial, clic registra en la última cita."""
    template_name = "clinical/odontograma.html"

    def dispatch(self, request, *args, **kwargs):
        self.paciente = get_object_or_404(Paciente, pk=self.kwargs["paciente_id"])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, paciente_id):
        diente = request.POST.get("diente", "")
        tipo = request.POST.get("tipo", "")
        notas = request.POST.get("notas", "").strip()
        expediente, _ = ExpedienteDental.objects.get_or_create(
            paciente=self.paciente, defaults={"creado_por": request.user}
        )
        cita = expediente.citas.order_by("-fecha").first()
        if cita is None:
            cita = CitaDental.objects.create(
                expediente=expediente,
                motivo="Registro de odontograma",
                creado_por=request.user,
            )
        HistorialDiente.objects.create(
            cita=cita, paciente=self.paciente, diente_fdi=diente, tipo=tipo, notas=notas
        )
        messages.success(request, f"Diente {diente}: {dict(TIPO_TRATAMIENTO).get(tipo, tipo)} registrado.")
        return redirect("clinical:odontograma", paciente_id=self.paciente.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        colores, historial = {}, {}
        for h in HistorialDiente.objects.filter(paciente=self.paciente).order_by("-fecha"):
            colores.setdefault(h.diente_fdi, h.color)
            historial.setdefault(h.diente_fdi, []).append({
                "tipo_display": h.get_tipo_display(),
                "fecha": h.fecha.strftime("%d/%m/%Y %H:%M"),
                "notas": h.notas,
                "color": h.color,
            })
        ctx.update({
            "paciente": self.paciente,
            "diente_nums_superior": DIENTE_NUMS_SUPERIOR,
            "diente_nums_inferior": DIENTE_NUMS_INFERIOR,
            "colores_paciente": colores,
            "historial_paciente": historial,
            "tipos_tratamiento": TIPO_TRATAMIENTO,
            "colores_leyenda": [(l, COLOR_DIENTE[v]) for v, l in TIPO_TRATAMIENTO if v != "otro"],
        })
        return ctx
