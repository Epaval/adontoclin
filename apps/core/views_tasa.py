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
