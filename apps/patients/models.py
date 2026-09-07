from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import Lower
from django.utils import timezone


class Paciente(models.Model):
    SEXO_CHOICES = [
        ("F", "Femenino"),
        ("M", "Masculino"),
        ("O", "Otro"),
    ]

    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)

    ci = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        verbose_name="CI",
    )

    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)

    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    fecha_nac = models.DateField(verbose_name="Fecha de nacimiento")
    representante = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="representados", verbose_name="Representante legal",
    )

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "paciente"
        permissions = [
            ("crear_paciente", "Crear paciente"),
        ]
        constraints = [
            UniqueConstraint(
                Lower("ci"),
                condition=Q(ci__isnull=False),
                name="paciente_ci_lower_unique",
            ),
            UniqueConstraint(
                Lower("telefono"),
                condition=Q(telefono__isnull=False),
                name="paciente_telefono_lower_unique",
            ),
            UniqueConstraint(
                Lower("email"),
                condition=Q(email__isnull=False),
                name="paciente_email_lower_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["apellidos", "nombres"]),
            models.Index(fields=["ci"]),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def edad(self):
        if not self.fecha_nac:
            return None

        hoy = timezone.localdate()

        if self.fecha_nac > hoy:
            return 0

        anos = hoy.year - self.fecha_nac.year

        if (hoy.month, hoy.day) < (self.fecha_nac.month, self.fecha_nac.day):
            anos -= 1

        return anos

    @property
    def es_menor(self):
        return self.edad is not None and self.edad < 18

    def ci_efectivo(self):
        """CI propia o la del representante si es menor sin CI."""
        if self.ci:
            return self.ci
        if self.es_menor and self.representante:
            return self.representante.ci
        return self.ci

    def telefono_efectivo(self):
        """Para menores siempre el telefono del representante."""
        if self.es_menor and self.representante:
            return self.representante.telefono or self.telefono
        return self.telefono

    def clean(self):
        super().clean()
        if self.fecha_nac and 9 <= self.edad < 18 and not self.ci:
            raise ValidationError("Los pacientes entre 9 y 17 años deben tener CI.")
        if self.fecha_nac and self.es_menor and not self.representante_id:
            raise ValidationError("Los menores de 18 años deben tener un representante legal.")
        if self.representante_id:
            if self.representante_id == self.pk:
                raise ValidationError("Un paciente no puede ser su propio representante.")
            if self.representante.es_menor:
                raise ValidationError("El representante debe ser mayor de edad.")

    def save(self, *args, **kwargs):
        self.email = self.email.lower() if self.email else None

        if self.telefono:
            self.telefono = "".join(
                ch for ch in self.telefono if ch.isdigit() or ch == "+"
            )
        else:
            self.telefono = None

        self.ci = self.ci.strip() if self.ci else None

        super().save(*args, **kwargs)


class Expediente(models.Model):
    ESTADO_CHOICES = [
        ("abierto", "Abierto"),
        ("procesando", "Procesando"),
        ("cerrado", "Cerrado"),
        ("anulado", "Anulado"),
    ]

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name="expedientes",
    )

    bioanalista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expedientes_asignados",
        limit_choices_to={"rol__nombre": "bioanalista", "is_active": True},
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expedientes_creados",
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="abierto",
    )

    observaciones = models.TextField(blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expediente"
        permissions = [
            ("crear_orden_lab", "Crear orden de laboratorio"),
        ]
        indexes = [
            models.Index(fields=["paciente", "estado"]),
            models.Index(fields=["fecha_creacion"]),
        ]

    def actualizar_estado_resultados(self):
        """Avanza/cierra el estado segun el progreso de los resultados."""
        if self.estado not in ("abierto", "procesando"):
            return
        estados = list(self.resultados.values_list("estado", flat=True))
        if not estados:
            return
        if all(e != "borrador" for e in estados):
            self.estado = "cerrado"
        elif any(e != "borrador" for e in estados) and self.estado == "abierto":
            self.estado = "procesando"
        else:
            return
        self.save(update_fields=["estado"])

    def __str__(self):
        return f"Expediente {self.pk} - {self.paciente}"


class ExpedienteMedico(models.Model):
    expediente = models.ForeignKey(
        Expediente,
        on_delete=models.CASCADE,
        related_name="expedientes_medicos",
    )
    medico = models.ForeignKey(
        "doctors.Medico",
        on_delete=models.CASCADE,
        related_name="expedientes_medicos",
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    principal = models.BooleanField(default=False)

    class Meta:
        db_table = "expediente_medico"
        constraints = [
            UniqueConstraint(
                fields=["expediente", "medico"],
                name="uniq_expediente_medico",
            ),
        ]

    def __str__(self):
        return f"{self.expediente} - {self.medico}"


class Resumen(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name="resumenes",
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resumenes_creados",
    )

    titulo = models.CharField(max_length=255)
    observacion = models.TextField(blank=True)

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resumen"

    def __str__(self):
        return f"Resumen {self.pk} - {self.paciente}"


class ResumenDetalle(models.Model):
    resumen = models.ForeignKey(
        Resumen,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    resultado = models.ForeignKey(
        "results.Resultado",
        on_delete=models.PROTECT,
        related_name="resumen_detalles",
    )

    class Meta:
        db_table = "resumen_detalle"
        constraints = [
            UniqueConstraint(
                fields=["resumen", "resultado"],
                name="uniq_resumen_resultado",
            ),
        ]

    def __str__(self):
        return f"{self.resumen} - {self.resultado}"
