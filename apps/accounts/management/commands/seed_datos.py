import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Rol, Salario
from apps.doctors.models import Medico
from apps.exams.models import CostoExamen, Examen, Perfil
from apps.patients.models import Paciente

Empleado = get_user_model()

EXAMENES = [
    # Hematología
    ("Hematología completa", "Hematología", "Hemoglobina: 12-16 g/dL (M), 13-17 g/dL (H). Leucocitos: 4500-11000/mm³. Plaquetas: 150000-450000/mm³."),
    ("Hemoglobina", "Hematología", "Mujeres: 12-16 g/dL. Hombres: 13-17 g/dL."),
    ("Hematocrito", "Hematología", "Mujeres: 36-46%. Hombres: 41-53%."),
    ("Plaquetas", "Hematología", "150.000 - 450.000 /mm³"),
    ("Leucocitos", "Hematología", "4.500 - 11.000 /mm³"),
    ("Velocidad de sedimentación (VSG)", "Hematología", "Hombres: 0-15 mm/h. Mujeres: 0-20 mm/h."),
    ("Tiempo de Protrombina (TP)", "Coagulación", "11-13.5 segundos. INR: 0.8-1.2"),
    ("Tiempo de Tromboplastina Parcial (TTP)", "Coagulación", "25-35 segundos"),

    # Química sanguínea
    ("Glucosa en ayunas", "Química Sanguínea", "70-100 mg/dL. Prediabetes: 100-125. Diabetes: ≥126."),
    ("Urea", "Química Sanguínea", "15-45 mg/dL"),
    ("Creatinina", "Química Sanguínea", "Mujeres: 0.6-1.1 mg/dL. Hombres: 0.7-1.3 mg/dL."),
    ("Ácido úrico", "Química Sanguínea", "Mujeres: 2.4-6.0 mg/dL. Hombres: 3.4-7.0 mg/dL."),
    ("Colesterol total", "Perfil Lipídico", "Deseable: <200 mg/dL. Límite: 200-239. Alto: ≥240."),
    ("HDL", "Perfil Lipídico", "Hombres: >40 mg/dL. Mujeres: >50 mg/dL."),
    ("LDL", "Perfil Lipídico", "Óptimo: <100 mg/dL. Casi óptimo: 100-129."),
    ("Triglicéridos", "Perfil Lipídico", "Normal: <150 mg/dL. Límite: 150-199. Alto: 200-499."),

    # Hepáticas
    ("Bilirrubina total", "Hepáticas", "0.1-1.2 mg/dL"),
    ("Bilirrubina directa", "Hepáticas", "0.0-0.3 mg/dL"),
    ("TGO (AST)", "Hepáticas", "5-40 U/L"),
    ("TGP (ALT)", "Hepáticas", "7-56 U/L"),
    ("Fosfatasa alcalina", "Hepáticas", "44-147 U/L"),
    ("Proteínas totales", "Hepáticas", "6.0-8.3 g/dL"),
    ("Albúmina", "Hepáticas", "3.5-5.5 g/dL"),

    # Electrolitos
    ("Calcio", "Electrolitos", "8.5-10.5 mg/dL"),
    ("Fósforo", "Electrolitos", "2.5-4.5 mg/dL"),
    ("Sodio", "Electrolitos", "135-145 mEq/L"),
    ("Potasio", "Electrolitos", "3.5-5.0 mEq/L"),
    ("Cloro", "Electrolitos", "98-107 mEq/L"),

    # Otros
    ("Uroanálisis completo", "Uroanálisis", "pH: 4.5-8.0. Densidad: 1.005-1.030. Sin proteínas, glucosa ni sangre."),
    # ---- Orina · Físicos ----
    ("Color orina", "Orina · Físicos", "Amarillo claro a ámbar (variable con hidratación)."),
    ("Transparencia orina", "Orina · Físicos", "Transparente. Turbia sugiere cristales, bacterias o leucocitos."),
    ("Densidad orina", "Orina · Físicos", "1.005 - 1.030"),
    ("Olor orina", "Orina · Físicos", "Característico suave. Amoniacal o fétido sugiere infección."),
    # ---- Orina · Químicos (tira reactiva) ----
    ("pH urinario", "Orina · Químicos", "4.5 - 8.0 (promedio ~6.0)"),
    ("Proteínas en orina", "Orina · Químicos", "Negativo a trazas. Positivo sugiere proteinuria."),
    ("Glucosa en orina", "Orina · Químicos", "Negativo. Positivo sugiere glucemia >180 mg/dL."),
    ("Cetonas en orina", "Orina · Químicos", "Negativo. Positivo sugiere cetosis o cetoacidosis."),
    ("Nitritos en orina", "Orina · Químicos", "Negativo. Positivo sugiere bacteriuria por gram negativos."),
    ("Leucocitos (esterasa)", "Orina · Químicos", "Negativo. Positivo sugiere infección urinaria."),
    ("Sangre en orina", "Orina · Químicos", "Negativo. Positivo: hematuria o hemoglobinuria."),
    # ---- Orina · Microscópico ----
    ("Glóbulos rojos en sedimento", "Orina · Microscópico", "0 - 3 por campo. Hematuria: >3/campo."),
    ("Glóbulos blancos en sedimento", "Orina · Microscópico", "0 - 5 por campo. Piuria: >5/campo."),
    ("Bacterias en sedimento", "Orina · Microscópico", "Ausentes o escasas. Abundantes sugieren bacteriuria."),
    ("Cristales en sedimento", "Orina · Microscópico", "Ausentes o escasos (tipo depende del pH)."),
    ("Células epiteliales en sedimento", "Orina · Microscópico", "Escasas. Abundantes sugieren contaminación."),

    ("Prueba de embarazo (hCG)", "Hormonas", "Negativo: <5 mUI/mL. Positivo: >25 mUI/mL."),
]

PACIENTES = [
    ("María", "González", "V12345678", "F", date(1985, 3, 15), "+584141234567", "maria.gonzalez@test.com"),
    ("Juan", "Pérez", "V15678901", "M", date(1978, 7, 22), "+584242345678", "juan.perez@test.com"),
    ("Ana", "Rodríguez", "V18901234", "F", date(1992, 11, 8), "+584123456789", "ana.rodriguez@test.com"),
    ("Carlos", "Martínez", "V20345678", "M", date(1965, 5, 30), "+584164567890", "carlos.martinez@test.com"),
    ("Laura", "Hernández", "V22678901", "F", date(2001, 1, 12), "+584265678901", "laura.hernandez@test.com"),
    ("Pedro", "López", "V10987654", "M", date(1995, 9, 5), "+584146789012", "pedro.lopez@test.com"),
    ("Sofía", "García", "V24321098", "F", date(1988, 12, 20), "+584247890123", "sofia.garcia@test.com"),
    ("Miguel", "Ramírez", "V13456789", "M", date(1972, 4, 18), "+584128901234", "miguel.ramirez@test.com"),
    ("Carmen", "Torres", "V16789012", "F", date(1999, 6, 25), "+584169012345", "carmen.torres@test.com"),
    ("Luis", "Morales", "V19012345", "M", date(1983, 10, 3), "+584260123456", "luis.morales@test.com"),
]

EMPLEADOS = [
    # (nombre_usuario, nombres, apellidos, rol, telefono)
    ("jefe_lab1", "Roberto", "Mendoza", "jefe_lab", "+584141111111"),
    ("bio1", "Patricia", "Castro", "bioanalista", "+584142222222"),
    ("bio2", "Andrea", "Silva", "bioanalista", "+584143333333"),
    ("bio3", "Gabriela", "Rivas", "bioanalista", "+584144444444"),
    ("aux1", "Valentina", "Paredes", "auxiliar", "+584145555555"),
    ("aux2", "Daniela", "Vargas", "auxiliar", "+584146666666"),
]

PASSWORD = "Lab12345*"
SALARIO_POR_ROL = {
    "jefe_lab": Decimal("2500.00"),
    "bioanalista": Decimal("1800.00"),
    "auxiliar": Decimal("1200.00"),
}


class Command(BaseCommand):
    help = "Carga datos de prueba: exámenes, pacientes, médicos y empleados"

    def handle(self, *args, **options):
        # Cada sección es independiente: si una falla, las demás quedan sembradas.
        # Fundamental para instalaciones que actualizan y tienen empleados/pacientes
        # con constraints que puedan fallar sin tirar el catálogo de exámenes.
        errores = []

        self.stdout.write(self.style.NOTICE("Creando exámenes (catálogo único)..."))
        try:
            call_command("seed_catalogo")
        except Exception as e:
            errores.append(f"exámenes: {e}")
            self.stdout.write(self.style.ERROR(f"  ⚠ error en exámenes: {e}"))

        self.stdout.write(self.style.NOTICE("Creando pacientes..."))
        try:
            self._seed_pacientes()
        except Exception as e:
            errores.append(f"pacientes: {e}")
            self.stdout.write(self.style.ERROR(f"  ⚠ error en pacientes: {e}"))

        self.stdout.write(self.style.NOTICE("Creando médicos..."))
        try:
            self._seed_medicos()
        except Exception as e:
            errores.append(f"médicos: {e}")
            self.stdout.write(self.style.ERROR(f"  ⚠ error en médicos: {e}"))

        self.stdout.write(self.style.NOTICE("Creando empleados..."))
        try:
            self._seed_empleados()
        except Exception as e:
            errores.append(f"empleados: {e}")
            self.stdout.write(self.style.ERROR(f"  ⚠ error en empleados: {e}"))

        if errores:
            self.stdout.write(self.style.WARNING(f"\n[PARCIAL] Datos sembrados con errores en: {', '.join(errores)}"))
        else:
            self.stdout.write(self.style.SUCCESS("\n[OK] Datos de prueba cargados correctamente"))
            self.stdout.write(self.style.WARNING(f"\nContraseña por defecto para empleados: {PASSWORD}"))
            self.stdout.write(self.style.WARNING("Usuarios creados:"))
            self.stdout.write("  jefe_lab1, bio1, bio2, bio3, aux1, aux2")

    def _seed_examenes(self):
        for nombre, perfil, valores_ref in EXAMENES:
            examen, creado = Examen.objects.get_or_create(
                nombre_completo=nombre,
                defaults={
                    "perfil": perfil,
                    "valores_ref": valores_ref,
                    "activo": True,
                },
            )

            if creado or not examen.costos.filter(activo=True).exists():
                CostoExamen.objects.filter(examen=examen, activo=True).update(activo=False)
                precio = Decimal(str(random.randint(8, 45)))
                CostoExamen.objects.create(
                    examen=examen,
                    precio=precio,
                    activo=True,
                )
                self.stdout.write(f"  + {nombre} (${precio})")

    def _seed_pacientes(self):
        for nombres, apellidos, ci, sexo, fecha_nac, telefono, email in PACIENTES:
            paciente, creado = Paciente.objects.get_or_create(
                ci=ci,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "sexo": sexo,
                    "fecha_nac": fecha_nac,
                    "telefono": telefono,
                    "email": email,
                    "direccion": "Dirección de prueba",
                    "activo": True,
                },
            )
            if creado:
                self.stdout.write(f"  + {paciente.full_name} ({paciente.edad} años)")

    def _seed_medicos(self):
        medicos = [
            ("Dr.", "Alejandro", "Fernández", "V5432109", "Cardiología", "+584147777777", "cardio@test.com"),
            ("Dr.", "Beatriz", "Acosta", "V8765432", "Endocrinología", "+584148888888", "endo@test.com"),
            ("Dra.", "Isabel", "Romero", "V7654321", "Medicina Interna", "+584149999999", "medint@test.com"),
        ]

        for prefijo, nombres, apellidos, ci, especialidad, telefono, email in medicos:
            medico, creado = Medico.objects.get_or_create(
                ci=ci,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "especialidad": especialidad,
                    "telefono": telefono,
                    "email": email,
                    "activo": True,
                },
            )
            if creado:
                self.stdout.write(f"  + {prefijo} {nombres} {apellidos}")

    def _seed_empleados(self):
        # Primero asegurar que los roles existen
        if not Rol.objects.filter(nombre="jefe_lab").exists():
            self.stdout.write(self.style.ERROR(
                "\n⚠ Los roles no existen. Ejecuta primero: python manage.py seed_roles"
            ))
            return

        for username, nombres, apellidos, rol_nombre, telefono in EMPLEADOS:
            rol = Rol.objects.get(nombre=rol_nombre)

            if Empleado.objects.filter(nombre_usuario=username).exists():
                self.stdout.write(f"  - {username} ya existe")
                continue

            empleado = Empleado.objects.create_user(
                nombre_usuario=username,
                email=f"{username}@labclin.test",
                password=PASSWORD,
                nombres=nombres,
                apellidos=apellidos,
                telefono=telefono,
                rol=rol,
                is_active=True,
            )

            # Crear salario vigente
            Salario.objects.filter(empleado=empleado, vigente=True).update(vigente=False)
            Salario.objects.create(
                empleado=empleado,
                rol=rol,
                salario_actual=SALARIO_POR_ROL[rol_nombre],
                vigente=True,
            )

            self.stdout.write(f"  + {username} ({rol_nombre})")
