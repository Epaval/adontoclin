from django.db import migrations


def recalcular_estados(apps, schema_editor):
    """Recalcula estado de expedientes abiertos/procesando segun sus resultados."""
    Expediente = apps.get_model("patients", "Expediente")
    for exp in Expediente.objects.filter(estado__in=["abierto", "procesando"]):
        estados = list(exp.resultados.values_list("estado", flat=True))
        if not estados:
            continue
        if all(e != "borrador" for e in estados):
            exp.estado = "cerrado"
            exp.save(update_fields=["estado"])
        elif any(e != "borrador" for e in estados) and exp.estado == "abierto":
            exp.estado = "procesando"
            exp.save(update_fields=["estado"])


class Migration(migrations.Migration):

    dependencies = [
        ("patients", "0003_unaccent"),
    ]

    operations = [
        migrations.RunPython(recalcular_estados, migrations.RunPython.noop),
    ]
