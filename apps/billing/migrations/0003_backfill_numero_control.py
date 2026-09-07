from django.db import migrations, models


def backfill_numero_control(apps, schema_editor):
    """Asigna numero de control 00-NNNNN a facturas creadas antes del campo"""
    Factura = apps.get_model("billing", "Factura")

    existentes = Factura.objects.filter(
        numero_control__startswith="00-"
    ).values_list("numero_control", flat=True)

    maximo = 0
    for n in existentes:
        try:
            maximo = max(maximo, int(n.split("-")[1]))
        except (IndexError, ValueError):
            continue

    sec = maximo + 1
    for factura in Factura.objects.filter(numero_control="").order_by("id"):
        factura.numero_control = f"00-{sec:05d}"
        factura.save(update_fields=["numero_control"])
        sec += 1


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0002_factura_numero_control"),
    ]

    operations = [
        migrations.RunPython(backfill_numero_control, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='factura',
            name='numero_control',
            field=models.CharField(blank=True, help_text='Formato fiscal: 00-NNNNN (auto-generado)', max_length=10, unique=True, verbose_name='Número de control'),
        ),
    ]
