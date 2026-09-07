from django.contrib import admin

from .models import Expediente, ExpedienteMedico, Paciente, Resumen, ResumenDetalle


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ("full_name", "ci", "telefono", "email", "edad", "activo")
    search_fields = ("nombres", "apellidos", "ci", "telefono", "email")
    list_filter = ("sexo", "activo")


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ("id", "paciente", "estado", "bioanalista", "creado_por", "fecha_creacion")
    list_filter = ("estado",)
    search_fields = ("paciente__nombres", "paciente__apellidos", "paciente__ci")


@admin.register(ExpedienteMedico)
class ExpedienteMedicoAdmin(admin.ModelAdmin):
    list_display = ("expediente", "medico", "principal")


@admin.register(Resumen)
class ResumenAdmin(admin.ModelAdmin):
    list_display = ("id", "paciente", "titulo", "creado_por", "activo")


@admin.register(ResumenDetalle)
class ResumenDetalleAdmin(admin.ModelAdmin):
    list_display = ("resumen", "resultado")
