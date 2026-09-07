from django.conf import settings
from django.shortcuts import redirect


class LicenciaMiddleware:
    """Bloquea la app en escritorio si la licencia está vencida"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.ESCRITORIO:
            from .licencias import estado_licencia

            rutas_libres = ("/activacion", "/static", "/favicon")
            if estado_licencia() == "vencida" and not request.path.startswith(rutas_libres):
                return redirect("activacion")

        return self.get_response(request)


class ConfiguracionInicialMiddleware:
    """Primera ejecución: obliga a crear la cuenta principal"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.ESCRITORIO:
            from apps.accounts.models import Empleado

            rutas_libres = ("/configuracion-inicial", "/static", "/favicon", "/activacion")
            if (
                not Empleado.objects.filter(is_superuser=True).exists()
                and not request.path.startswith(rutas_libres)
            ):
                return redirect("configuracion_inicial")

        return self.get_response(request)


class TasaMiddleware:
    """Al entrar el admin, si la tasa no es de hoy, lo primero es registrarla."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and (user.is_superuser or user.is_staff):
            from datetime import date as hoy
            from .models import TasaCambio

            rutas_libres = ("/tasa", "/static", "/favicon", "/logout", "/accounts", "/activacion", "/admin")
            t = TasaCambio.actual()
            if (t is None or t.fecha != hoy.today()) and not request.path.startswith(rutas_libres):
                return redirect("tasa_cambio")
        return self.get_response(request)
