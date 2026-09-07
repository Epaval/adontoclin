import unicodedata
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.exams.models import Examen


def sin_acentos(texto):
    if not texto:
        return texto
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class Command(BaseCommand):
    help = "Unifica perfiles con acentos a su version sin acentos"

    def handle(self, *args, **options):
        grupos = {}
        for ex in Examen.objects.exclude(perfil=""):
            grupos.setdefault(sin_acentos(ex.perfil), []).append(ex)
        movidos = 0
        with transaction.atomic():
            for clave, examenes in grupos.items():
                for ex in examenes:
                    if ex.perfil != clave:
                        ex.perfil = clave
                        ex.save(update_fields=["perfil"])
                        movidos += 1
        self.stdout.write(self.style.SUCCESS(f"{movidos} examenes normalizados"))
