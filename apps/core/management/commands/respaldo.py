import sqlite3
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea una copia de seguridad de la base de datos (modo escritorio)"

    def handle(self, *args, **options):
        if not settings.ESCRITORIO:
            raise CommandError("Solo disponible en modo escritorio")

        origen = settings.DATABASES["default"]["NAME"]

        dir_backups = settings.DATA_DIR / "backups"
        dir_backups.mkdir(parents=True, exist_ok=True)

        nombre = f"labclin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        destino = dir_backups / nombre

        # Copia en caliente (segura aunque la app esté en uso)
        src = sqlite3.connect(str(origen))
        dst = sqlite3.connect(str(destino))
        with dst:
            src.backup(dst)
        src.close()
        dst.close()

        self.stdout.write(self.style.SUCCESS(f"Respaldo creado: {destino}"))
