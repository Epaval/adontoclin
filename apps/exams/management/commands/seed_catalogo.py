from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from django.db.models import Q

from apps.exams.models import CostoExamen, Examen, Perfil

# Precios de referencia por perfil (ajustalos a tu mercado)
# Precios en 0: el laboratorio define sus propios precios
PRECIO_PERFIL = {
    "Hematologia": 0, "Coagulacion": 0, "Quimica Sanguinea": 0,
    "Perfil Lipidico": 0, "Hepaticas": 0, "Renal": 0,
    "Electrolitos": 0, "Uroanalisis": 0, "Tiroides": 0,
    "Hormonas": 0, "Marcadores Tumorales": 0, "Serologia / Infecciosas": 0,
    "Vitaminas y Minerales": 0, "Marcadores Cardiacos": 0,
    "Pancreas": 0, "Heces": 0,
    "Heces · Macroscópico": 0, "Heces · Microscópico": 0, "Heces · Químicos": 0, "Heces · Microbiológico": 0, "Inmunologia": 0, "Otros": 0,
    "Orina · Físicos": 0, "Orina · Químicos": 0, "Orina · Microscópico": 0,
}

CATALOGO = {
    "Hematologia": [
        ("Hematologia completa (Hemograma)", "Leucocitos 4.500-11.000/mm3; Hemoglobina 12-17 g/dL; Plaquetas 150.000-450.000/mm3"),
        ("Hemoglobina", "12-17 g/dL"),
        ("Hematocrito", "36-53%"),
        ("Recuento de globulos rojos", "4.2-5.9 M/mm3"),
        ("Leucocitos", "4.500-11.000/mm3"),
        ("Plaquetas", "150.000-450.000/mm3"),
        ("Reticulocitos", "0.5-2.5%"),
        ("Velocidad de sedimentacion (VSG)", "0-20 mm/h"),
        ("Frotis de sangre periferica", "Sin alteraciones"),
        ("Grupo sanguineo ABO", "Tipificacion"),
        ("Factor Rh", "Positivo / Negativo"),
        ("Recuento de eosinofilos", "0-500/mm3"),
    ],
    "Coagulacion": [
        ("Tiempo de Protrombina (TP)", "11-13.5 segundos"),
        ("INR", "0.8-1.2"),
        ("Tiempo de Tromboplastina Parcial (TTP)", "25-35 segundos"),
        ("Fibrinogeno", "200-400 mg/dL"),
        ("Dimero D", "<0.5 ug/mL"),
        ("Tiempo de sangria", "1-9 minutos"),
        ("Tiempo de coagulacion", "5-11 minutos"),
    ],
    "Quimica Sanguinea": [
        ("Glucosa en ayunas", "70-100 mg/dL"),
        ("Glucosa postprandial", "<140 mg/dL"),
        ("Hemoglobina glicosilada (HbA1c)", "4.0-5.7%"),
        ("Urea", "15-45 mg/dL"),
        ("Creatinina", "0.6-1.3 mg/dL"),
        ("Acido urico", "2.4-7.0 mg/dL"),
        ("Proteinas totales", "6.0-8.3 g/dL"),
        ("Albumina", "3.5-5.5 g/dL"),
        ("Calcio", "8.5-10.5 mg/dL"),
        ("Fosforo", "2.5-4.5 mg/dL"),
        ("Magnesio", "1.7-2.2 mg/dL"),
    ],
    "Perfil Lipidico": [
        ("Colesterol total", "<200 mg/dL"),
        ("HDL", ">40 mg/dL (H) / >50 mg/dL (M)"),
        ("LDL", "<100 mg/dL"),
        ("VLDL", "5-40 mg/dL"),
        ("Trigliceridos", "<150 mg/dL"),
        ("Indice aterogenico", "<5"),
    ],
    "Hepaticas": [
        ("Bilirrubina total", "0.1-1.2 mg/dL"),
        ("Bilirrubina directa", "0.0-0.3 mg/dL"),
        ("Bilirrubina indirecta", "0.1-0.9 mg/dL"),
        ("TGO (AST)", "5-40 U/L"),
        ("TGP (ALT)", "7-56 U/L"),
        ("Fosfatasa alcalina", "44-147 U/L"),
        ("GGT", "7-50 U/L"),
        ("LDH", "140-280 U/L"),
    ],
    "Renal": [
        ("Depuracion de creatinina", "90-120 mL/min"),
        ("Microalbuminuria", "<30 mg/24h"),
        ("Cistatina C", "0.5-1.0 mg/L"),
    ],
    "Electrolitos": [
        ("Sodio", "135-145 mEq/L"),
        ("Potasio", "3.5-5.0 mEq/L"),
        ("Cloro", "98-107 mEq/L"),
        ("Anion gap", "8-16 mEq/L"),
    ],
    "Uroanalisis": [
        ("Uroanalisis completo", "pH 4.5-8.0; densidad 1.005-1.030; sin proteinas ni glucosa"),
        ("Urocultivo con antibiograma", "Sin desarrollo bacteriano"),
        ("Proteinas en orina de 24 horas", "<150 mg/24h"),
        ("Prueba de embarazo en orina", "Negativo"),
    ],
    "Tiroides": [
        ("TSH", "0.4-4.0 uUI/mL"),
        ("T4 libre", "0.8-1.8 ng/dL"),
        ("T3 total", "80-200 ng/dL"),
        ("T3 libre", "2.3-4.2 pg/mL"),
        ("Anticuerpos anti-TPO", "<35 UI/mL"),
        ("Anticuerpos antitiroglobulina", "<40 UI/mL"),
    ],
    "Hormonas": [
        ("Prolactina", "2-25 ng/mL"),
        ("FSH", "Variable segun sexo y ciclo"),
        ("LH", "Variable segun sexo y ciclo"),
        ("Estradiol", "Variable segun sexo y ciclo"),
        ("Progesterona", "Variable segun fase del ciclo"),
        ("Testosterona total", "240-950 ng/dL (H)"),
        ("Cortisol (8 am)", "5-23 ug/dL"),
        ("Insulina", "2-25 uUI/mL"),
        ("Peptido C", "1.1-4.4 ng/mL"),
        ("Hormona antimulleriana (AMH)", "Variable segun edad y sexo"),
    ],
    "Marcadores Tumorales": [
        ("PSA (antigeno prostatico)", "<4 ng/mL"),
        ("Alfa-fetoproteina", "<10 ng/mL"),
        ("CEA", "<5 ng/mL"),
        ("CA-125", "<35 U/mL"),
        ("CA 15-3", "<30 U/mL"),
        ("CA 19-9", "<37 U/mL"),
        ("Beta-hCG cuantitativa", "<5 mUI/mL (no embarazada)"),
    ],
    "Serologia / Infecciosas": [
        ("HIV (ELISA)", "No reactivo"),
        ("HIV (prueba rapida)", "No reactivo"),
        ("Hepatitis B (HBsAg)", "No reactivo"),
        ("Anticuerpos anti-HBs", ">10 mUI/mL (inmune)"),
        ("Hepatitis C (anti-HCV)", "No reactivo"),
        ("VDRL", "No reactivo"),
        ("RPR", "No reactivo"),
        ("ASO", "<200 UI/mL"),
        ("Proteina C reactiva (PCR)", "<5 mg/L"),
        ("Factor reumatoide", "<14 UI/mL"),
        ("Widal", "<1:80"),
        ("Dengue (NS1)", "No reactivo"),
        ("Dengue (IgG/IgM)", "No reactivo"),
        ("Toxoplasma (IgG)", "Variable"),
        ("Toxoplasma (IgM)", "No reactivo"),
        ("Rubeola (IgG)", "Variable (inmunidad)"),
        ("Rubeola (IgM)", "No reactivo"),
        ("Helicobacter pylori (antigeno en heces)", "Negativo"),
    ],
    "Vitaminas y Minerales": [
        ("Vitamina D (25-OH)", "20-50 ng/mL"),
        ("Vitamina B12", "200-900 pg/mL"),
        ("Acido folico", "3-17 ng/mL"),
        ("Hierro serico", "60-170 ug/dL"),
        ("Ferritina", "20-250 ng/mL"),
        ("TIBC (capacidad fijacion de hierro)", "250-370 ug/dL"),
    ],
    "Marcadores Cardiacos": [
        ("Troponina I", "<0.04 ng/mL"),
        ("CK-MB", "<5 ng/mL"),
        ("CPK total", "39-308 U/L"),
        ("NT-proBNP", "<125 pg/mL"),
        ("Homocisteina", "5-15 umol/L"),
    ],
    "Pancreas": [
        ("Amilasa", "25-125 U/L"),
        ("Lipasa", "10-140 U/L"),
    ],
    "Heces": [
        ("Coproanalisis", "Sin alteraciones"),
        ("Sangre oculta en heces", "Negativo"),
        ("Parásitos en heces", "Negativo"),
        ("Coprocultivo", "Sin desarrollo de patogenos"),
    ],
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
        ("Helicobacter pylori (antígeno en heces)", "Negativo. Positivo: infección activa."),
        ("Coprocultivo", "Sin desarrollo de patógenos."),
        ("Clostridium difficile toxina A/B", "Negativo. Positivo: colitis pseudomembranosa."),
        ("Rotavirus / Adenovirus", "Negativo."),
    ],
    "Inmunologia": [
        ("ANA (anticuerpos antinucleares)", "<1:40"),
        ("Anti-DNA", "<10 UI/mL"),
        ("Complemento C3", "90-180 mg/dL"),
        ("Complemento C4", "10-40 mg/dL"),
        ("IgE total", "<100 UI/mL"),
        ("IgG", "700-1600 mg/dL"),
        ("IgA", "70-400 mg/dL"),
        ("IgM", "40-230 mg/dL"),
    ],
    "Otros": [
        ("Alcohol en sangre", "<0.0 g/dL"),
        ("Colinesterasa", "5.3-12.9 U/L"),
        ("Ceruloplasmina", "20-60 mg/dL"),
        ("Amonio", "15-45 ug/dL"),
        ("Acido lactico", "0.5-2.2 mmol/L"),
    ],
    "Orina · Físicos": [
        ("Color orina", "Amarillo claro a ámbar (variable con hidratación)."),
        ("Transparencia orina", "Transparente. Turbia sugiere cristales, bacterias o leucocitos."),
        ("Densidad orina", "1.005 - 1.030"),
        ("Olor orina", "Característico suave. Amoniacal o fétido sugiere infección."),
    ],
    "Orina · Químicos": [
        ("pH urinario", "4.5 - 8.0 (promedio ~6.0)"),
        ("Proteínas en orina", "Negativo a trazas. Positivo sugiere proteinuria."),
        ("Glucosa en orina", "Negativo. Positivo sugiere glucemia >180 mg/dL."),
        ("Cetonas en orina", "Negativo. Positivo sugiere cetosis o cetoacidosis."),
        ("Nitritos en orina", "Negativo. Positivo sugiere bacteriuria por gram negativos."),
        ("Leucocitos (esterasa)", "Negativo. Positivo sugiere infección urinaria."),
        ("Sangre en orina", "Negativo. Positivo: hematuria o hemoglobinuria."),
    ],
    "Orina · Microscópico": [
        ("Glóbulos rojos en sedimento", "0 - 3 por campo. Hematuria: >3/campo."),
        ("Glóbulos blancos en sedimento", "0 - 5 por campo. Piuria: >5/campo."),
        ("Bacterias en sedimento", "Ausentes o escasas. Abundantes sugiere bacteriuria."),
        ("Cristales en sedimento", "Ausentes o escasos (tipo depende del pH)."),
        ("Células epiteliales en sedimento", "Escasas. Abundantes sugieren contaminación."),
    ],
}



TIPO_POR_NOMBRE = {
    "Color orina": "texto", "Transparencia orina": "texto", "Olor orina": "texto",
    "Cristales en sedimento": "texto", "Células epiteliales en sedimento": "texto",
    "Proteínas en orina": "cualitativo", "Glucosa en orina": "cualitativo",
    "Cetonas en orina": "cualitativo", "Nitritos en orina": "cualitativo",
    "Leucocitos (esterasa)": "cualitativo", "Sangre en orina": "cualitativo",
    "Bacterias en sedimento": "cualitativo",
    # Heces
    "Color heces": "texto", "Olor heces": "texto", "Huevos de parásitos": "texto", "Coprocultivo": "texto",
    "Consistencia heces": "texto", "Forma heces": "texto", "Moco en heces": "cualitativo",
    "Pus en heces": "cualitativo", "Sangre visible en heces": "cualitativo",
    "Parásitos en heces": "cualitativo", "Eritrocitos en heces": "cualitativo",
    "Leucocitos en heces": "numerico", "Grasa en heces (Sudan III)": "cualitativo",
    "Alimentos no digeridos": "cualitativo", "Levaduras en heces": "cualitativo",
    "Sangre oculta en heces": "cualitativo", "Sustancias reductoras en heces": "cualitativo",
    "Tripsina fecal": "cualitativo", "Helicobacter pylori (antígeno en heces)": "cualitativo",
    "Clostridium difficile toxina A/B": "cualitativo", "Rotavirus / Adenovirus": "cualitativo",
}

class Command(BaseCommand):
    help = "Carga el catalogo completo de examenes de laboratorio por perfil"

    def handle(self, *args, **options):
        nuevos = 0
        for perfil, examenes in CATALOGO.items():
            precio = Decimal(str(PRECIO_PERFIL.get(perfil, 0)))

            for nombre, valores_ref in examenes:
                examen, creado = Examen.objects.get_or_create(
                    nombre_completo=nombre,
                    defaults={
                        "perfil": perfil,
                        "valores_ref": valores_ref,
                        "activo": True,
                    },
                )

                if creado:
                    CostoExamen.objects.create(
                        examen=examen, precio=precio, activo=True
                    )
                    nuevos += 1
                elif not examen.costos.filter(activo=True).exists():
                    CostoExamen.objects.create(
                        examen=examen, precio=precio, activo=True
                    )


        # Aplicar tipos por nombre (idempotente)
        upd = 0
        for nombre, tipo in TIPO_POR_NOMBRE.items():
            upd += Examen.objects.filter(nombre_completo=nombre).exclude(tipo_resultado=tipo).update(tipo_resultado=tipo)
        if upd:
            self.stdout.write(f"  Tipos actualizados: {upd} exámenes")

        # Perfil paquete de uroanálisis (idempotente)
        try:
            perfil_orina, _ = Perfil.objects.get_or_create(nombre="Examen de Orina (Uroanálisis)")
            perfil_orina.examenes.set(
                Examen.objects.filter(
                    Q(perfil__startswith="Orina ·") | Q(nombre_completo="Uroanálisis completo")
                )
            )
            self.stdout.write(f"  Perfil uroanálisis: {perfil_orina.examenes.count()} exámenes")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ⚠ perfil orina: {e}"))


        # Perfil paquete de heces (coprológico)
        try:
            ph, _ = Perfil.objects.get_or_create(nombre="Examen de Heces (Coprológico)")
            Examen.objects.filter(nombre_completo="Coprocultivo").update(perfil="Heces · Microbiológico")
            ph.examenes.set(Examen.objects.filter(perfil__startswith="Heces ·"))
            self.stdout.write(f"  Perfil heces: {ph.examenes.count()} exámenes")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ⚠ perfil heces: {e}"))

        total = Examen.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"[OK] {nuevos} examenes nuevos. Catalogo total: {total} examenes"
        ))
