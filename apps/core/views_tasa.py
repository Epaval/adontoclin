from datetime import date as hoy
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from .models import TasaCambio


class TasaCambioView(View):
    def get(self, request):
        return render(request, "core/tasa.html", {"tasa": TasaCambio.actual()})

    def post(self, request):
        raw = request.POST.get("valor", "").strip().replace(",", ".")
        try:
            valor = Decimal(raw)
            if valor <= 0:
                raise InvalidOperation
        except (InvalidOperation, ArithmeticError):
            messages.error(request, "Ingrese un valor valido mayor a 0.")
            return redirect("tasa_cambio")
        TasaCambio.objects.create(valor=valor, fecha=hoy.today())
        from django.core.cache import cache
        cache.delete("tasa_actual_cp")
        messages.success(request, f"Tasa actualizada: {valor} Bs por $.")
        return redirect("dashboard")


from django.views.decorators.http import require_POST


@require_POST
def cambiar_tema(request):
    from django.contrib.admin.views.decorators import staff_member_required
    from apps.core.models import DatosLaboratorio
    tema = request.POST.get("tema", "dark")
    if tema not in ("dark", "azul", "verde", "rosa"):
        tema = "dark"
    d = DatosLaboratorio.objects.first()
    if d:
        d.tema = tema
        d.save(update_fields=["tema"])
    return redirect(request.META.get("HTTP_REFERER", "/"))
