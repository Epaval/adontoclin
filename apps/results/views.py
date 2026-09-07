from django.shortcuts import get_object_or_404, render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, UpdateView

from .forms import ResultadoForm
from .models import Resultado


class ResultadoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Resultado
    permission_required = "results.view_resultado"
    template_name = "generic_list.html"
    context_object_name = "object_list"
    paginate_by = 20
    extra_context = {"title": "Resultados"}


class ResultadoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Resultado
    form_class = ResultadoForm
    permission_required = "results.editar_result"
    template_name = "results/resultado_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Cargar resultado: {self.object.examen.nombre_completo}"
        context["valores_ref"] = self.object.examen.valores_ref
        return context

    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user

        if self.object.estado == "borrador" and self.object.tiene_resultado:
            form.instance.estado = "cargado"

        messages.success(self.request, "Resultado guardado correctamente")
        response = super().form_valid(form)
        self.object.expediente.actualizar_estado_resultados()
        return response

    def get_success_url(self):
        return reverse_lazy(
            "patients:orden_detail",
            kwargs={"pk": self.object.expediente_id},
        )



class CargarOrdenResultadosView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Carga masiva de resultados para todos los exámenes de una orden"""
    permission_required = "results.editar_result"

    def get(self, request, pk):
        from apps.patients.models import Expediente
        orden = get_object_or_404(Expediente, pk=pk)
        resultados = orden.resultados.select_related("examen").order_by("examen__nombre_completo")
        
        return render(request, "results/cargar_orden.html", {
            "orden": orden,
            "resultados": resultados,
            "title": f"Cargar resultados · Orden #{orden.pk}",
        })

    def post(self, request, pk):
        from apps.patients.models import Expediente
        from django.db import transaction
        from decimal import Decimal, InvalidOperation

        orden = get_object_or_404(Expediente, pk=pk)
        resultados = orden.resultados.select_related("examen").all()
        
        modo = request.POST.get("modo", "parcial")  # "todo" o "parcial"
        guardados = 0
        errores = []

        with transaction.atomic():
            for r in resultados:
                prefix = f"r{r.pk}"
                
                # Validar que el campo existe en el POST
                if f"{prefix}_valor" not in request.POST:
                    continue

                valor_str = request.POST.get(f"{prefix}_valor", "").strip()
                unidad = request.POST.get(f"{prefix}_unidad", "").strip()
                obs = request.POST.get(f"{prefix}_obs", "").strip()

                # Si está vacío y el modo es "parcial", saltar
                if not valor_str and modo == "parcial":
                    continue
                
                # Si está vacío y el modo es "todo", error
                if not valor_str and modo == "todo":
                    errores.append(f"{r.examen.nombre_completo}: valor requerido")
                    continue

                try:
                    # SIEMPRE el tipo del examen (el del borrador puede estar desactualizado)
                    tipo = r.examen.tipo_resultado
                    if tipo == "numerico":
                        r.valor_numerico = Decimal(valor_str.replace(",", "."))
                        r.unidad = unidad
                        r.valor_cualitativo = ""
                    else:  # cualitativo o texto
                        r.valor_cualitativo = valor_str
                        r.valor_numerico = None
                    r.tipo_resultado = tipo
                    r.estado = "cargado"
                    r.save()
                    guardados += 1
                except (InvalidOperation, ValueError) as e:
                    errores.append(f"{r.examen.nombre_completo}: valor inválido")

        orden.actualizar_estado_resultados()

        if errores:
            messages.error(request, f"Guardados {guardados}, errores: {', '.join(errores)}")
        elif guardados == 0:
            messages.info(request, "No hay valores nuevos para guardar")
        else:
            messages.success(request, f"Se guardaron {guardados} resultado(s) correctamente")

        return redirect("patients:orden_detail", pk=orden.pk)
