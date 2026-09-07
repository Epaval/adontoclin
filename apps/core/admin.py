from django.contrib import admin

from .models import DatosLaboratorio


@admin.register(DatosLaboratorio)
class DatosLaboratorioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rif", "telefono")
    fieldsets = (
        ("Identificacion", {"fields": ("nombre", "rif", "lema", "logo")}),
        ("Contacto", {"fields": ("direccion", "ciudad", "telefono", "email")}),
        ("Facturacion", {"fields": ("simbolo_moneda",)}),
        ("Firma del reporte", {"fields": ("bioanalista_nombre", "bioanalista_registro", "firma_imagen", "sello_imagen")}),
    )

    def has_add_permission(self, request):
        return not DatosLaboratorio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# Ocultar modelos de axes (seguridad) del admin
from django.contrib import admin as _admin
try:
    from axes.models import AccessAttempt, AccessLog, AccessFailure
    for _m in (AccessAttempt, AccessLog, AccessFailure):
        if _admin.site.is_registered(_m):
            _admin.site.unregister(_m)
except Exception:
    pass
