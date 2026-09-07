from django.db import migrations


def forwards(apps, schema_editor):
    Resultado = apps.get_model("results", "Resultado")
    for tipo in ["numerico", "cualitativo", "texto"]:
        Resultado.objects.filter(
            examen__tipo_resultado=tipo,
            estado="borrador",
            valor_numerico=None,
            valor_cualitativo="",
        ).exclude(tipo_resultado=tipo).update(tipo_resultado=tipo)


class Migration(migrations.Migration):
    dependencies = [("exams", "0005_indices_tipo_resultado")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
