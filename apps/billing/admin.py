from django.contrib import admin

from .models import DetalleFactura, Factura


class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 0
    readonly_fields = ("examen", "cantidad", "precio_unitario", "subtotal")


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "numero_control",
        "paciente",
        "total",
        "estado",
        "motivo_anulacion",
        "fecha_creacion",
    )
    list_filter = ("estado", "motivo_anulacion", "metodo_pago")
    search_fields = ("numero", "numero_control", "expediente__paciente__nombres", "expediente__paciente__apellidos")
    readonly_fields = ("numero", "numero_control", "expediente", "creado_por", "fecha_creacion", "ultima_fecha_act")
    inlines = [DetalleFacturaInline]

    def paciente(self, obj):
        return obj.expediente.paciente

    def get_motivo_anulacion_display(self, obj):
        return obj.get_motivo_anulacion_display() or "—"
    get_motivo_anulacion_display.short_description = "Motivo de anulación"


@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = ("factura", "examen", "cantidad", "precio_unitario", "subtotal")
    readonly_fields = ("factura", "examen", "cantidad", "precio_unitario", "subtotal")
