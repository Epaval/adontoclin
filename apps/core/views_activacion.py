from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from .licencias import (
    clave_valida,
    clave_vencida,
    dias_restantes,
    estado_licencia,
    fecha_vencimiento,
    guardar_licencia,
    huella_maquina,
    MODO_DEV,
    PRUEBA_DIAS,
    leer_licencia,
    tipo_licencia_actual,
)


class ActivacionView(View):
    def get(self, request):
        vencimiento = None
        licencia = leer_licencia()
        if licencia and clave_valida(licencia[1], licencia[0]):
            vencimiento = fecha_vencimiento(*licencia)

        return render(request, "core/activacion.html", {
            "huella": huella_maquina(),
            "estado": estado_licencia(),
            "dias": dias_restantes(),
            "tipo": tipo_licencia_actual(),
            "vencimiento": vencimiento,
            "dev": MODO_DEV,
            "prueba_dias": PRUEBA_DIAS,
        })

    def post(self, request):
        clave = request.POST.get("clave", "").strip().upper()

        if clave_valida(clave, "perpetua"):
            guardar_licencia("perpetua", clave)
            messages.success(request, "[OK] Licencia PERPETUA activada. Gracias!")
            return redirect("dashboard")

        if clave_valida(clave, "anual"):
            if clave_vencida(clave):
                messages.error(
                    request,
                    "Esta clave anual ya vencio. Solicita una renovacion a tu proveedor.",
                )
                return redirect("activacion")
            guardar_licencia("anual", clave)
            messages.success(request, "[OK] Licencia ANUAL activada por 1 anio. Gracias!")
            return redirect("dashboard")

        messages.error(request, "Clave de licencia invalida para esta maquina")
        return redirect("activacion")
