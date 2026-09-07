"""
Compatibilidad de busqueda sin acentos para SQLite (modo escritorio).

Registra la funcion SQL `unaccent` en conexiones SQLite y el lookup
`unaccent` para CharField/TextField. En PostgreSQL genera el mismo SQL
que django.contrib.postgres, asi que ambos modos quedan cubiertos.

Tambien configura WAL + busy_timeout para trabajo multi-hilo sin bloqueos.
"""
import unicodedata

from django.db.backends.signals import connection_created
from django.db.models import CharField, TextField
from django.db.models.lookups import Transform


def _quitar_acentos(valor):
    if valor is None:
        return None
    return "".join(
        c for c in unicodedata.normalize("NFD", str(valor))
        if unicodedata.category(c) != "Mn"
    )


def _configurar_sqlite(sender, connection, **kwargs):
    """Configura SQLite para trabajo concurrente: WAL + timeout alto"""
    if connection.vendor == "sqlite":
        # Funcion unaccent para busquedas sin acentos
        connection.connection.create_function("unaccent", 1, _quitar_acentos)
        
        # WAL + timeout alto para evitar "database is locked"
        cursor = connection.connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")  # 10 segundos
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")


class Unaccent(Transform):
    function = "unaccent"
    lookup_name = "unaccent"
    bilateral = True


def registrar():
    connection_created.connect(_configurar_sqlite)
    CharField.register_lookup(Unaccent)
    TextField.register_lookup(Unaccent)
