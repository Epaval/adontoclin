from django.contrib import admin

from .models import Medico


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ("nombres", "apellidos", "ci", "telefono", "email", "especialidad", "activo")
    search_fields = ("nombres", "apellidos", "ci", "telefono", "email")
    list_filter = ("activo", "especialidad")
