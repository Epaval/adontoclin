from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Empleado, Rol, Salario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre", "group")
    search_fields = ("nombre",)


@admin.register(Empleado)
class EmpleadoAdmin(UserAdmin):
    list_display = ("nombre_usuario", "email", "full_name", "rol", "is_active")
    list_filter = ("rol", "is_active")
    search_fields = ("nombre_usuario", "email", "nombres", "apellidos")
    ordering = ("nombre_usuario",)

    fieldsets = (
        (None, {"fields": ("nombre_usuario", "password")}),
        ("Datos personales", {"fields": ("nombres", "apellidos", "email", "telefono", "rol")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
        ("Último acceso", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "nombre_usuario",
                    "email",
                    "telefono",
                    "nombres",
                    "apellidos",
                    "rol",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(Salario)
class SalarioAdmin(admin.ModelAdmin):
    list_display = ("empleado", "rol", "salario_actual", "ultimo_salario", "vigente")
    list_filter = ("vigente", "rol")
