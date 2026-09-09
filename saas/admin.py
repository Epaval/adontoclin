from django.contrib import admin
from .models import Clinica


@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "slug", "estado", "cliente_nombre", "fecha_creacion"]
    list_filter = ["estado", "fecha_creacion"]
    search_fields = ["nombre", "slug", "cliente_nombre", "cliente_email"]
    readonly_fields = ["tunnel_id", "token", "fecha_creacion", "fecha_activacion"]
