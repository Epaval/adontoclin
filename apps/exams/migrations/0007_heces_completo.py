from django.db import migrations
from decimal import Decimal

HECES_NUEVOS = {
    "Heces · Macroscópico": [
        ("Color heces", "Marrón (normal). Arcilloso, negro o rojo sugiere patología."),
        ("Consistencia heces", "Formada blanda (Bristol 3-4). Dura, líquida o pastosa anormal."),
        ("Forma heces", "Cilíndrica. Acintada, fragmentada o caprina anormal."),
        ("Olor heces", "Característico. Fétido o pútrido sugiere malabsorción."),
        ("Moco en heces", "Ausente o escaso. Abundante sugiere inflamación."),
        ("Pus en heces", "Ausente. Presente sugiere infección o enfermedad inflamatoria."),
        ("Sangre visible en heces", "Ausente. Roja sugiere sangrado distal; negra, proximal."),
    ],
    "Heces · Microscópico": [
        ("Huevos de parásitos", "Ausentes. Identificación por especie si presentes."),
        ("Leucocitos en heces", "0 - 2 por campo. Abundantes sugieren colitis infecciosa."),
        ("Eritrocitos en heces", "Ausentes. Presencia sugiere sangrado o colitis."),
        ("Grasa en heces (Sudan III)", "Ausente o escasa. Abundante: esteatorrea."),
        ("Alimentos no digeridos", "Escasos. Abundantes: maldigestión."),
        ("Levaduras en heces", "Escasas. Abundantes sugieren sobrecrecimiento."),
    ],
    "Heces · Químicos": [
        ("pH fecal", "6.0 - 7.5"),
        ("Sustancias reductoras en heces", "Negativo. Positivo: intolerancia a carbohidratos."),
        ("Tripsina fecal", "Positiva (actividad normal)."),
        ("Elastasa pancreática fecal", ">200 ug/g (normal). 100-200 leve; <100 insuficiencia."),
    ],
    "Heces · Microbiológico": [
        ("Coprocultivo", "Sin desarrollo de patógenos."),
        ("Clostridium difficile toxina A/B", "Negativo. Positivo: colitis pseudomembranosa."),
        ("Rotavirus / Adenovirus", "Negativo."),
    ],
}

TIPOS = {
    "Color heces": "texto", "Olor heces": "texto", "Huevos de parásitos": "texto", "Coprocultivo": "texto",
    "Consistencia heces": "cualitativo", "Forma heces": "cualitativo", "Moco en heces": "cualitativo",
    "Pus en heces": "cualitativo", "Sangre visible en heces": "cualitativo",
    "Parásitos en heces": "cualitativo", "Grasa en heces (Sudan III)": "cualitativo",
    "Alimentos no digeridos": "cualitativo", "Levaduras en heces": "cualitativo",
    "Sangre oculta en heces": "cualitativo", "Sustancias reductoras en heces": "cualitativo",
    "Tripsina fecal": "cualitativo", "Helicobacter pylori (antígeno en heces)": "cualitativo",
    "Clostridium difficile toxina A/B": "cualitativo", "Rotavirus / Adenovirus": "cualitativo",
}


def forwards(apps, schema_editor):
    Examen = apps.get_model("exams", "Examen")
    CostoExamen = apps.get_model("exams", "CostoExamen")
    Perfil = apps.get_model("exams", "Perfil")
    Resultado = apps.get_model("results", "Resultado")

    # 1) Normalizar los 3 heces existentes (nombre/perfil/tipo)
    Examen.objects.filter(nombre_completo="Helicobacter pylori (antigeno en heces)").update(
        nombre_completo="Helicobacter pylori (antígeno en heces)",
        perfil="Heces · Microbiológico", tipo_resultado="cualitativo")
    Examen.objects.filter(nombre_completo="Sangre oculta en heces").update(
        perfil="Heces · Químicos", tipo_resultado="cualitativo")
    Examen.objects.filter(nombre_completo="Parásitos en heces").update(
        perfil="Heces · Microscópico", tipo_resultado="cualitativo")

    # 2) Crear los nuevos
    for perfil, examenes in HECES_NUEVOS.items():
        for nombre, valores_ref in examenes:
            ex, creado = Examen.objects.get_or_create(
                nombre_completo=nombre,
                defaults={"perfil": perfil, "valores_ref": valores_ref, "activo": True,
                          "tipo_resultado": TIPOS.get(nombre, "numerico")})
            if creado:
                CostoExamen.objects.create(examen=ex, precio=Decimal("0"), activo=True)

    # 3) Tipos correctos
    for nombre, tipo in TIPOS.items():
        Examen.objects.filter(nombre_completo=nombre).exclude(tipo_resultado=tipo).update(tipo_resultado=tipo)

    # 4) Perfil paquete
    ph, _ = Perfil.objects.get_or_create(nombre="Examen de Heces (Coprológico)")
    ph.examenes.set(Examen.objects.filter(perfil__startswith="Heces ·"))

    # 5) Sincronizar borradores con el tipo de su examen
    for tipo in ["numerico", "cualitativo", "texto"]:
        Resultado.objects.filter(examen__tipo_resultado=tipo, estado="borrador").exclude(
            tipo_resultado=tipo).update(tipo_resultado=tipo)


class Migration(migrations.Migration):
    dependencies = [("exams", "0006_sincronizar_borradores")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
