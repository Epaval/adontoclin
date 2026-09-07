from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Cuentas"

    def ready(self):
        """Crea roles dentales al arrancar si no existen (idempotente)."""
        try:
            from django.db import connection
            if not connection.introspection.table_names():
                return
            from django.contrib.auth.models import Group, Permission
            admin, _ = Group.objects.get_or_create(name="admin")
            if admin.permissions.count() == 0:
                admin.permissions.set(Permission.objects.all())
            aux, _ = Group.objects.get_or_create(name="auxiliar")
            if aux.permissions.count() == 0:
                aux.permissions.set(Permission.objects.filter(codename__in=[
                    "view_paciente", "add_paciente", "change_paciente",
                    "view_expedientedental", "add_expedientedental", "change_expedientedental",
                    "view_citadental", "add_citadental", "change_citadental",
                    "view_historialdiente", "add_historialdiente",
                    "view_receta", "add_receta", "change_receta",
                    "view_serviciodental",
                ]))
            for viejo in ("bioanalista", "jefe_lab", "jefe"):
                Group.objects.filter(name=viejo).delete()
        except Exception:
            pass

