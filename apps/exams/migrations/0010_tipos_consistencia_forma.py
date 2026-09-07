from django.db import migrations

A_TEXTO = ["Consistencia heces", "Forma heces"]


def forwards(apps, schema_editor):
    Examen = apps.get_model("exams", "Examen")
    Resultado = apps.get_model("results", "Resultado")
    Examen.objects.filter(nombre_completo__in=A_TEXTO).update(tipo_resultado="texto")
    Resultado.objects.filter(examen__nombre_completo__in=A_TEXTO, estado="borrador").update(tipo_resultado="texto")


class Migration(migrations.Migration):
    dependencies = [("exams", "0009_coprocultivo_perfil")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
