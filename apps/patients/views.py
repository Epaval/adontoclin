from django.shortcuts import redirect
from itertools import groupby

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.exams.models import Examen, Perfil
from apps.results.models import Resultado

from .forms import ExpedienteForm, PacienteForm
from .models import Expediente, ExpedienteMedico, Paciente
from .services import generar_pdf_reporte


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
        return qs

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


# ================= HISTORIAL Y REPORTES =================

class PacienteHistorialView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Paciente
    permission_required = "patients.view_paciente"
    template_name = "patients/paciente_historial.html"
    context_object_name = "paciente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expedientes"] = (
            self.object.expedientes.prefetch_related("resultados__examen")
            .order_by("-fecha_creacion")
        )
        return context


class PacienteReportePDFView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "patients.view_paciente"

    def get(self, request, pk):
        paciente = get_object_or_404(Paciente, pk=pk)
        orden_pk = request.GET.get("orden")

        expedientes = (
            paciente.expedientes.prefetch_related("resultados__examen")
            .order_by("-fecha_creacion")
        )
        if orden_pk:
            expedientes = expedientes.filter(pk=orden_pk)

        pdf = generar_pdf_reporte(paciente, expedientes)

        nombre = f"Resultado_Orden_{orden_pk}_{paciente.full_name}.pdf" if orden_pk else f"reporte_{paciente.pk}.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{nombre}"'
        return response


# ================= ÓRDENES DE LABORATORIO =================


class ExpedienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Expediente
    permission_required = "patients.view_expediente"
    template_name = "patients/expediente_list.html"
    context_object_name = "object_list"
    paginate_by = 6

    def get_queryset(self):
        qs = (
            Expediente.objects.select_related("paciente", "creado_por")
            .order_by("-fecha_creacion")
        )
        # Filtro por estado (default: abiertas + procesando)
        estado = self.request.GET.get("estado", "activas")
        if estado == "cerradas":
            qs = qs.filter(estado="cerrado")
        elif estado == "todas":
            pass
        else:  # activas (default)
            qs = qs.filter(estado__in=["abierto", "procesando"])
        # Búsqueda por nombre o CI del paciente
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                models.Q(paciente__nombres__icontains=q)
                | models.Q(paciente__apellidos__icontains=q)
                | models.Q(paciente__ci__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["estado"] = self.request.GET.get("estado", "activas")
        return context


class ExpedienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Expediente
    form_class = ExpedienteForm
    permission_required = "patients.crear_orden_lab"
    template_name = "patients/expediente_form.html"
    extra_context = {"title": "Nueva orden de laboratorio"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        examenes = (
            Examen.objects.filter(activo=True)
            .order_by("perfil", "nombre_completo")
        )
        perfiles = []
        for perfil, items in groupby(examenes, key=lambda e: e.perfil or "General"):
            perfiles.append({"nombre": perfil, "examenes": list(items)})
        context["perfiles"] = perfiles
        context["perfiles_custom"] = [
            {
                "nombre": p.nombre,
                "pks": ",".join(str(pk) for pk in p.examenes.values_list("pk", flat=True)),
                "total": p.examenes.count(),
            }
            for p in Perfil.objects.all()
        ]
        return context

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        response = super().form_valid(form)

        examenes = form.cleaned_data["examenes"]
        for examen in examenes:
            Resultado.objects.get_or_create(
                expediente=self.object,
                examen=examen,
                defaults={"tipo_resultado": examen.tipo_resultado, "estado": "borrador", "creado_por": self.request.user},
            )
        for medico in form.cleaned_data["medicos"]:
            ExpedienteMedico.objects.get_or_create(
                expediente=self.object, medico=medico
            )

        messages.success(
            self.request,
            f"Orden #{self.object.pk} creada con {examenes.count()} examen(es) pendiente(s)",
        )
        return response

    def get_success_url(self):
        return reverse_lazy("patients:orden_detail", kwargs={"pk": self.object.pk})


class ExpedienteDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Expediente
    permission_required = "patients.view_expediente"
    template_name = "patients/expediente_detail.html"
    context_object_name = "expediente"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resultados = (
            self.object.resultados.select_related("examen", "creado_por")
            .order_by("examen__perfil", "examen__nombre_completo")
        )
        total = resultados.count()
        cargados = resultados.exclude(estado="borrador").exclude(estado="anulado").count()
        context["resultados"] = resultados
        context["total_examenes"] = total
        context["examenes_cargados"] = cargados
        context["progreso"] = int((cargados / total) * 100) if total else 0
        context["factura"] = self.object.facturas.exclude(estado="anulada").first()
        context["examenes_realizados"] = (
            self.object.resultados.exclude(estado="borrador").exclude(estado="anulado").count()
        )
        return context


class EliminarResultadoView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "results.delete_result"

    def post(self, request, pk, resultado_pk):
        resultado = get_object_or_404(Resultado, pk=resultado_pk, expediente__pk=pk)
        
        # Validación: solo se puede eliminar si está en borrador
        if resultado.estado != "borrador":
            messages.error(
                request,
                f"No se puede eliminar '{resultado.examen.nombre_completo}' porque ya fue cargado o validado."
            )
            return redirect("patients:orden_detail", pk=pk)
        
        # Validación: no eliminar si ya está en factura
        from apps.billing.models import DetalleFactura
        if DetalleFactura.objects.filter(examen=resultado.examen, factura__expediente=resultado.expediente).exists():
            messages.error(
                request,
                f"No se puede eliminar '{resultado.examen.nombre_completo}' porque ya fue facturado."
            )
            return redirect("patients:orden_detail", pk=pk)
        
        nombre_examen = resultado.examen.nombre_completo
        resultado.delete()
        messages.success(request, f"Examen '{nombre_examen}' eliminado de la orden.")
        return redirect("patients:orden_detail", pk=pk)


# ================= REPRESENTANTE (AJAX) =================

from datetime import date as _date
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


def _edad(fnac):
    hoy = _date.today()
    return hoy.year - fnac.year - ((hoy.month, hoy.day) < (fnac.month, fnac.day))


@login_required
def buscar_representante(request):
    """Busca adultos por nombre, CI o telefono para el modal de representante."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    hoy = _date.today()
    try:
        limite = hoy.replace(year=hoy.year - 18)
    except ValueError:
        limite = hoy
    qs = Paciente.objects.filter(activo=True, fecha_nac__lte=limite).filter(
        Q(nombres__unaccent__icontains=q)
        | Q(apellidos__unaccent__icontains=q)
        | Q(ci__unaccent__icontains=q)
        | Q(telefono__unaccent__icontains=q)
    )[:8]
    return JsonResponse({"results": [
        {"id": p.pk, "nombre": p.full_name, "ci": p.ci or "-", "telefono": p.telefono or "-"}
        for p in qs
    ]})


@login_required
@require_POST
def crear_representante_rapido(request):
    """Crea un adulto sin salir del formulario del menor."""
    form = PacienteForm(request.POST)
    if form.is_valid():
        p = form.save()
        return JsonResponse({"ok": True, "id": p.pk, "nombre": p.full_name})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)
