from django.db import migrations


def activar_unaccent(apps, schema_editor):
    """Crea la extension unaccent solo en PostgreSQL (SQLite usa compat.py)."""
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")


class Migration(migrations.Migration):

    dependencies = [
        ("patients", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(activar_unaccent, migrations.RunPython.noop),
    ]
