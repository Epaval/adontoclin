from django.db import migrations

TEXTOS = ["Color orina", "Transparencia orina", "Olor orina",
          "Cristales en sedimento", "Células epiteliales en sedimento"]
CUALITATIVOS = ["Proteínas en orina", "Glucosa en orina", "Cetonas en orina",
                "Nitritos en orina", "Leucocitos (esterasa)", "Sangre en orina",
                "Bacterias en sedimento"]


def forwards(apps, schema_editor):
    Examen = apps.get_model("exams", "Examen")
    Resultado = apps.get_model("results", "Resultado")
    Examen.objects.filter(nombre_completo__in=TEXTOS).update(tipo_resultado="texto")
    Examen.objects.filter(nombre_completo__in=CUALITATIVOS).update(tipo_resultado="cualitativo")
    # Solo borradores: no tocar resultados ya cargados/validados
    Resultado.objects.filter(examen__nombre_completo__in=TEXTOS, estado="borrador").update(tipo_resultado="texto")
    Resultado.objects.filter(examen__nombre_completo__in=CUALITATIVOS, estado="borrador").update(tipo_resultado="cualitativo")


class Migration(migrations.Migration):
    dependencies = [
        ("exams", "0003_examen_tipo_resultado"),
        ("results", "0002_remove_resultado_resultado_resultado_observaciones_and_more"),
    ]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
