from django.shortcuts import render


def handler403(request, exception=None):
    """Manejador de errores 403 - Forbidden (sin permisos)"""
    context = {
        "error_code": "403",
        "error_title": "Acceso denegado",
        "error_message": "No tienes los permisos necesarios para realizar esta acción.",
        "error_detail": (
            str(exception) if exception and request.user.is_superuser else None
        ),
    }
    return render(request, "errors/403.html", context, status=403)


def handler404(request, exception=None):
    """Manejador de errores 404 - No encontrado"""
    context = {
        "error_code": "404",
        "error_title": "Página no encontrada",
        "error_message": "La página que estás buscando no existe o fue movida.",
    }
    return render(request, "errors/404.html", context, status=404)


def handler500(request):
    """Manejador de errores 500 - Error interno del servidor"""
    context = {
        "error_code": "500",
        "error_title": "Error interno del servidor",
        "error_message": "Ocurrió un error inesperado. El equipo técnico ha sido notificado.",
    }
    return render(request, "errors/500.html", context, status=500)
