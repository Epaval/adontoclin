from django.db import migrations


def forwards(apps, schema_editor):
    Examen = apps.get_model("exams", "Examen")
    Examen.objects.filter(nombre_completo="Coprocultivo").update(perfil="Heces · Microbiológico")


class Migration(migrations.Migration):
    dependencies = [("exams", "0008_fix_heces_tildes")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
