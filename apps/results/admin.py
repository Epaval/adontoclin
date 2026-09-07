from django.contrib import admin

from .models import Resultado, ResultadoAcceso


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ("id", "examen", "expediente", "estado", "creado_por", "fecha_creacion")
    list_filter = ("estado", "examen")
    search_fields = (
        "expediente__paciente__nombres",
        "expediente__paciente__apellidos",
        "examen__nombre_completo",
    )


@admin.register(ResultadoAcceso)
class ResultadoAccesoAdmin(admin.ModelAdmin):
    list_display = ("resultado", "expira", "usado", "fecha_uso", "ip_uso")
    list_filter = ("usado",)
