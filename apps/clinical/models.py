from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


DIENTE_FDI = [(str(n), f"Diente {n}") for n in
              list(range(18, 10, -1)) + list(range(21, 29)) +
              list(range(38, 30, -1)) + list(range(41, 49)) +
              list(range(55, 50, -1)) + list(range(61, 66)) +
              list(range(75, 70, -1)) + list(range(81, 86))]

DIENTE_NUMS_SUPERIOR = [str(n) for n in list(range(18, 10, -1)) + list(range(21, 29))]
DIENTE_NUMS_INFERIOR = [str(n) for n in list(range(48, 40, -1)) + list(range(31, 39))]

TIPO_TRATAMIENTO = [
    ("sano", "Sano"),
    ("caries", "Caries"),
    ("obstruccion", "Obturación/empaste"),
    ("endodoncia", "Endodoncia"),
    ("corona", "Corona"),
    ("sellante", "Sellante"),
    ("extraccion", "Extracción"),
    ("protesis", "Prótesis"),
    ("implante", "Implante"),
    ("ortodoncia", "Ortodoncia"),
    ("otro", "Otro"),
]

COLOR_DIENTE = {
    "sano": "#ffffff", "caries": "#fde047", "obstruccion": "#60a5fa",
    "endodoncia": "#a78bfa", "corona": "#f472b6", "sellante": "#34d399",
    "extraccion": "#dc2626", "protesis": "#fb923c", "implante": "#8b5cf6",
    "ortodoncia": "#06b6d4", "otro": "#94a3b8",
}


class ExpedienteDental(models.Model):
    """Historia clínica GENERAL del paciente (única y editable)."""
    paciente = models.OneToOneField(
        "patients.Paciente",
        on_delete=models.PROTECT,
        related_name="expediente_dental",
    )
    patologias = models.TextField("Patologías detectadas", blank=True)
    alergias = models.TextField("Alergias conocidas", blank=True)
    operaciones = models.TextField("Operaciones anteriores", blank=True)
    notas = models.TextField("Notas generales", blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="expedientes_dentales_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expediente_dental"

    def __str__(self):
        return f"Historia clínica de {self.paciente.full_name}"

    def dientes_unicos(self):
        """Último tratamiento por diente en todas las citas (odontograma general)."""
        vistos = {}
        for h in HistorialDiente.objects.filter(paciente=self.paciente).order_by("-fecha"):
            vistos.setdefault(h.diente_fdi, h)
        return list(vistos.values())

    def historial_completo(self):
        return HistorialDiente.objects.filter(paciente=self.paciente).order_by("-fecha")


ESTADO_CITA = [
    ("programada", "Programada"),
    ("atendida", "Atendida"),
    ("cancelada", "Cancelada"),
]


class CitaDental(models.Model):
    """Cita/consulta con detalle propio (editable)."""
    expediente = models.ForeignKey(
        ExpedienteDental, on_delete=models.CASCADE, related_name="citas"
    )
    fecha = models.DateTimeField(default=timezone.now)
    motivo = models.TextField("Motivo de la consulta", blank=True)
    notas = models.TextField("Notas de la cita", blank=True)
    archivo_adjunto = models.FileField(
        "Archivo adjunto (RX/PDF/imagen)", upload_to="citas/%Y/%m/", blank=True, null=True
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CITA, default="atendida")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="citas_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cita_dental"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Cita {self.pk} · {self.expediente.paciente.full_name} · {self.fecha:%d/%m/%Y}"

    @property
    def total_usd(self):
        from decimal import Decimal
        return sum((i.subtotal_usd for i in self.items.all()), Decimal("0"))


class HistorialDiente(models.Model):
    """Tratamiento aplicado a un diente en una cita específica."""
    cita = models.ForeignKey(CitaDental, on_delete=models.CASCADE, related_name="dientes")
    paciente = models.ForeignKey(
        "patients.Paciente", on_delete=models.CASCADE, related_name="dientes_historial"
    )
    diente_fdi = models.CharField("Diente FDI", max_length=2, choices=DIENTE_FDI)
    tipo = models.CharField("Tipo de tratamiento", max_length=20, choices=TIPO_TRATAMIENTO)
    notas = models.TextField("Notas", blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "historial_diente"
        ordering = ["-fecha"]
        indexes = [models.Index(fields=["paciente", "diente_fdi"])]

    def __str__(self):
        return f"{self.paciente} · diente {self.diente_fdi} · {self.get_tipo_display()}"

    @property
    def color(self):
        return COLOR_DIENTE.get(self.tipo, "#94a3b8")


class ServicioDental(models.Model):
    """Catálogo de servicios dentales con precio en $."""
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio_usd = models.DecimalField("Precio ($)", max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "servicio_dental"
        ordering = ["nombre"]
        verbose_name = "Servicio dental"

    def __str__(self):
        return f"{self.nombre} (${self.precio_usd})"


class CitaItem(models.Model):
    """Servicio aplicado en una cita (para facturación)."""
    cita = models.ForeignKey(CitaDental, on_delete=models.CASCADE, related_name="items")
    servicio = models.ForeignKey(ServicioDental, on_delete=models.PROTECT)
    diente_fdi = models.CharField("Diente", max_length=2, blank=True, choices=DIENTE_FDI)
    cantidad = models.PositiveIntegerField(default=1)
    precio_usd = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "cita_item"

    @property
    def subtotal_usd(self):
        return self.cantidad * self.precio_usd

    def save(self, *args, **kwargs):
        if not self.precio_usd:
            self.precio_usd = self.servicio.precio_usd
        super().save(*args, **kwargs)


class Receta(models.Model):
    """Receta e indicaciones de una cita (odontólogo externo firma con CO)."""
    cita = models.ForeignKey(CitaDental, on_delete=models.CASCADE, related_name="recetas")
    diagnostico = models.TextField("Diagnóstico", blank=True)
    indicaciones_generales = models.TextField(
        "Indicaciones generales adicionales", blank=True,
        help_text="Indicaciones libres que aplican a toda la receta",
    )
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recetas_creadas"
    )
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "receta"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Receta {self.pk} · {self.cita.expediente.paciente.full_name}"


class RecetaMedicamento(models.Model):
    """Medicamento de la receta: se escribe UNA vez y aparece en receta e indicaciones."""
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name="medicamentos")
    nombre = models.CharField("Medicamento", max_length=120)
    dosis = models.CharField("Dosis", max_length=60, blank=True)
    frecuencia = models.CharField("Frecuencia", max_length=60, blank=True)
    duracion = models.CharField("Duración", max_length=60, blank=True)
    indicacion = models.TextField(
        "Indicación específica", blank=True,
        help_text="Si se deja vacía, se genera automáticamente con dosis/frecuencia/duración",
    )

    class Meta:
        db_table = "receta_medicamento"
        ordering = ["id"]

    def __str__(self):
        return self.nombre

    @property
    def indicacion_texto(self):
        if self.indicacion.strip():
            return self.indicacion
        partes = [p for p in (self.dosis, self.frecuencia, self.duracion) if p.strip()]
        return " · ".join(partes) if partes else "Según indicación del odontólogo"
