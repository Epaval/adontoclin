from django.contrib import admin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ["full_name", "ci", "telefono", "edad", "activo"]
    search_fields = ["nombres", "apellidos", "ci", "telefono"]
    list_filter = ["activo", "sexo"]
