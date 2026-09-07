from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Empleado


@receiver(post_save, sender=Empleado)
def sincronizar_grupo_rol(sender, instance, **kwargs):
    """
    Cuando un empleado tiene rol, se sincroniza con el grupo Django asociado.
    """
    if not instance.pk:
        return

    if instance.rol_id and instance.rol.group_id:
        instance.groups.set([instance.rol.group])
    elif instance.rol_id is None:
        instance.groups.clear()
