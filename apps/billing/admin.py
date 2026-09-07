from django.contrib import admin

from .models import DetalleFactura, Factura


class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 0
    readonly_fields = ["servicio", "diente_fdi", "cantidad", "precio_unitario", "subtotal"]


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ["numero", "numero_control", "paciente", "estado", "total", "tasa", "fecha_creacion"]
    list_filter = ["estado", "metodo_pago"]
    search_fields = ["numero", "numero_control", "cita__expediente__paciente__nombres", "cita__expediente__paciente__apellidos"]
    readonly_fields = ["numero", "numero_control", "cita", "subtotal", "total", "tasa", "fecha_creacion"]
    inlines = [DetalleFacturaInline]

    @admin.display(description="Paciente")
    def paciente(self, obj):
        return obj.cita.expediente.paciente
