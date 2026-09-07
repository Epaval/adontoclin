"""
Endpoints JSON simples para autocompletadores del frontend.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.views import View

from .models import Paciente


class BuscarPacientesView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "patients.view_paciente"

    def get(self, request):
        q = request.GET.get("q", "").strip()
        if len(q) < 2:
            return JsonResponse([], safe=False)

        pacientes = (
            Paciente.objects.filter(activo=True)
            .filter(
                Q(nombres__unaccent__icontains=q)
                | Q(apellidos__unaccent__icontains=q)
                | Q(ci__icontains=q)
                | Q(telefono__icontains=q)
            )
            .order_by("apellidos", "nombres")[:15]
        )

        resultados = [
            {
                "id": p.pk,
                "nombre": f"{p.apellidos}, {p.nombres}",
                "ci": p.ci or "",
                "edad": f"{p.edad} años" if p.edad else "",
                "sexo": p.get_sexo_display(),
            }
            for p in pacientes
        ]
        return JsonResponse(resultados, safe=False)
