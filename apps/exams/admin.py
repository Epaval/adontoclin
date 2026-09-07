from django.contrib import admin

from .models import CostoExamen, Examen


@admin.register(CostoExamen)
class CostoExamenAdmin(admin.ModelAdmin):
    list_display = ("examen", "precio", "activo")
    list_filter = ("activo",)
    search_fields = ("examen__nombre_completo",)
    list_editable = ("precio", "activo")


class CostoExamenInline(admin.TabularInline):
    model = CostoExamen
    extra = 0
    fields = ("precio", "activo")


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "perfil", "tipo_resultado", "activo")
    list_editable = ("tipo_resultado", "activo")
    list_filter = ("perfil", "activo", "tipo_resultado")
    search_fields = ("nombre_completo",)
    inlines = [CostoExamenInline]
