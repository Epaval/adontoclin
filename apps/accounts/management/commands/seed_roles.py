from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLES = {
    "admin": "__all__",
    "auxiliar": [
        "view_paciente", "add_paciente", "change_paciente",
        "view_expedientedental", "add_expedientedental", "change_expedientedental",
        "view_citadental", "add_citadental", "change_citadental",
        "view_historialdiente", "add_historialdiente",
        "view_receta", "add_receta", "change_receta",
        "view_serviciodental",
    ],
}


class Command(BaseCommand):
    help = "Crea los roles dentales: admin (todo) y auxiliar (operación diaria)"

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        # eliminar roles de laboratorio si existen
        for viejo in ("bioanalista", "jefe_lab", "jefe"):
            g = Group.objects.filter(name=viejo).first()
            if g:
                g.delete()
                self.stdout.write(f"- rol de laboratorio eliminado: {viejo}")

        for nombre, perms in ROLES.items():
            group, _ = Group.objects.get_or_create(name=nombre)
            if perms == "__all__":
                group.permissions.set(Permission.objects.all())
            else:
                group.permissions.set(
                    Permission.objects.filter(codename__in=perms)
                )
            self.stdout.write(self.style.SUCCESS(f"rol {nombre}: {group.permissions.count()} permisos"))
