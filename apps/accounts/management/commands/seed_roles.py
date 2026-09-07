from django.db import transaction
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.accounts.models import Rol


APP_LABELS = [
    "accounts",
    "doctors",
    "exams",
    "patients",
    "results",
    "billing",
]

BASE_VIEW_PERMS = [
    "accounts.view_empleado",
    "doctors.view_medico",
    "exams.view_examen",
    "patients.view_paciente",
    "patients.view_expediente",
    "results.view_resultado",
    "billing.view_factura",
]

ROLE_PERMISSIONS = {
    "admin": "__all__",
    "jefe_lab": "__all__",
    "bioanalista": BASE_VIEW_PERMS + [
        "patients.add_paciente",
        "patients.change_paciente",
        "patients.crear_orden_lab",
        "results.add_resultado",
        "results.change_resultado",
        "results.editar_result",
    ],
    "auxiliar": BASE_VIEW_PERMS + [
        "patients.add_paciente",
        "patients.change_paciente",
        "patients.crear_paciente",
        "patients.add_expediente",
        "patients.change_expediente",
        "patients.crear_orden_lab",
        "results.add_resultado",
        "results.change_resultado",
        "results.cargar_result",
        "billing.add_factura",
        "billing.change_factura",
    ],
}


class Command(BaseCommand):
    help = "Crea roles, grupos y permisos base del laboratorio"

    @transaction.atomic
    def handle(self, *args, **options):
        for role_name, perms in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role_name)

            if perms == "__all__":
                permissions = Permission.objects.filter(
                    content_type__app_label__in=APP_LABELS
                )
            else:
                q = Q()
                for perm in perms:
                    app_label, codename = perm.split(".")
                    q |= Q(content_type__app_label=app_label, codename=codename)
                permissions = Permission.objects.filter(q).distinct()

            group.permissions.set(permissions)

            rol, _ = Rol.objects.get_or_create(nombre=role_name)
            rol.group = group
            rol.save(update_fields=["group"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Rol {role_name} sincronizado con {permissions.count()} permisos"
                )
            )
