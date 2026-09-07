from django.db import migrations


def forwards(apps, schema_editor):
    Examen = apps.get_model("exams", "Examen")
    Resultado = apps.get_model("results", "Resultado")

    # Renombrar sin tilde -> con tilde + perfil + tipo correcto
    Examen.objects.filter(nombre_completo="Parasitos en heces").update(
        nombre_completo="Parásitos en heces",
        perfil="Heces · Microscópico",
        tipo_resultado="cualitativo",
    )
    # Tipos pendientes de la 0007
    Examen.objects.filter(nombre_completo="Eritrocitos en heces").update(tipo_resultado="cualitativo")
    Examen.objects.filter(nombre_completo="Leucocitos en heces").update(tipo_resultado="numerico")
    Examen.objects.filter(nombre_completo="Sangre oculta en heces").update(
        perfil="Heces · Químicos", tipo_resultado="cualitativo")

    # Sincronizar borradores afectados
    for tipo in ["numerico", "cualitativo", "texto"]:
        Resultado.objects.filter(examen__tipo_resultado=tipo, estado="borrador").exclude(
            tipo_resultado=tipo).update(tipo_resultado=tipo)


class Migration(migrations.Migration):
    dependencies = [("exams", "0007_heces_completo")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
