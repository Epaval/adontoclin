from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


DIENTE_FDI = [
    # Cuadrante superior derecho (adulto)
    ("11", "Incisivo central superior derecho"),
    ("12", "Incisivo lateral superior derecho"),
    ("13", "Canino superior derecho"),
    ("14", "Primer premolar superior derecho"),
    ("15", "Segundo premolar superior derecho"),
    ("16", "Primer molar superior derecho"),
    ("17", "Segundo molar superior derecho"),
    ("18", "Tercer molar superior derecho"),
    # Cuadrante superior izquierdo
    ("21", "Incisivo central superior izquierdo"),
    ("22", "Incisivo lateral superior izquierdo"),
    ("23", "Canino superior izquierdo"),
    ("24", "Primer premolar superior izquierdo"),
    ("25", "Segundo premolar superior izquierdo"),
    ("26", "Primer molar superior izquierdo"),
    ("27", "Segundo molar superior izquierdo"),
    ("28", "Tercer molar superior izquierdo"),
    # Cuadrante inferior izquierdo
    ("31", "Incisivo central inferior izquierdo"),
    ("32", "Incisivo lateral inferior izquierdo"),
    ("33", "Canino inferior izquierdo"),
    ("34", "Primer premolar inferior izquierdo"),
    ("35", "Segundo premolar inferior izquierdo"),
    ("36", "Primer molar inferior izquierdo"),
    ("37", "Segundo molar inferior izquierdo"),
    ("38", "Tercer molar inferior izquierdo"),
    # Cuadrante inferior derecho
    ("41", "Incisivo central inferior derecho"),
    ("42", "Incisivo lateral inferior derecho"),
    ("43", "Canino inferior derecho"),
    ("44", "Primer premolar inferior derecho"),
    ("45", "Segundo premolar inferior derecho"),
    ("46", "Primer molar inferior derecho"),
    ("47", "Segundo molar inferior derecho"),
    ("48", "Tercer molar inferior derecho"),
    # Deciduos
    ("51", "Incisivo central superior derecho deciduo"),
    ("52", "Incisivo lateral superior derecho deciduo"),
    ("53", "Canino superior derecho deciduo"),
    ("54", "Primer molar superior derecho deciduo"),
    ("55", "Segundo molar superior derecho deciduo"),
    ("61", "Incisivo central superior izquierdo deciduo"),
    ("62", "Incisivo lateral superior izquierdo deciduo"),
    ("63", "Canino superior izquierdo deciduo"),
    ("64", "Primer molar superior izquierdo deciduo"),
    ("65", "Segundo molar superior izquierdo deciduo"),
    ("71", "Incisivo central inferior izquierdo deciduo"),
    ("72", "Incisivo lateral inferior izquierdo deciduo"),
    ("73", "Canino inferior izquierdo deciduo"),
    ("74", "Primer molar inferior izquierdo deciduo"),
    ("75", "Segundo molar inferior izquierdo deciduo"),
    ("81", "Incisivo central inferior derecho deciduo"),
    ("82", "Incisivo lateral inferior derecho deciduo"),
    ("83", "Canino inferior derecho deciduo"),
    ("84", "Primer molar inferior derecho deciduo"),
    ("85", "Segundo molar inferior derecho deciduo"),
]


class ExpedienteDental(models.Model):
    """Expediente/consulta dental con motivo, patologías, alergias y archivo adjunto."""
    paciente = models.ForeignKey(
        "patients.Paciente",
        on_delete=models.PROTECT,
        related_name="expedientes_dentales",
    )
    motivo = models.TextField("Motivo de la consulta", blank=True)
    patologias = models.TextField("Patologías detectadas", blank=True)
    alergias = models.TextField("Alergias conocidas", blank=True)
    operaciones = models.TextField("Operaciones anteriores", blank=True)
    notas = models.TextField("Notas clínicas", blank=True)
    archivo_adjunto = models.FileField(
        "Archivo adjunto (RX/PDF/imagen)",
        upload_to="expedientes/%Y/%m/",
        blank=True,
        null=True,
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="expedientes_dentales_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expediente_dental"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Consulta {self.pk} - {self.paciente.full_name}"


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
    "sano": "#ffffff",
    "caries": "#fde047",
    "obstruccion": "#60a5fa",
    "endodoncia": "#a78bfa",
    "corona": "#f472b6",
    "sellante": "#34d399",
    "extraccion": "#dc2626",
    "protesis": "#fb923c",
    "implante": "#8b5cf6",
    "ortodoncia": "#06b6d4",
    "otro": "#94a3b8",
}


class HistorialDiente(models.Model):
    """Registro histórico de tratamiento en un diente específico (FDI)."""
    expediente = models.ForeignKey(
        ExpedienteDental,
        on_delete=models.CASCADE,
        related_name="historial_dientes",
    )
    paciente = models.ForeignKey(
        "patients.Paciente",
        on_delete=models.CASCADE,
        related_name="dientes_historial",
    )
    diente_fdi = models.CharField(
        "Diente FDI",
        max_length=2,
        choices=DIENTE_FDI,
    )
    tipo = models.CharField(
        "Tipo de tratamiento",
        max_length=20,
        choices=TIPO_TRATAMIENTO,
    )
    notas = models.TextField("Notas", blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "historial_diente"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["paciente", "diente_fdi"]),
        ]

    def __str__(self):
        return f"{self.paciente} · diente {self.diente_fdi} · {self.get_tipo_display()}"

    @property
    def color(self):
        return COLOR_DIENTE.get(self.tipo, "#94a3b8")

    def clean(self):
        super().clean()
        if self.diente_fdi not in dict(DIENTE_FDI):
            raise ValidationError("Número de diente FDI inválido.")


class ServicioDental(models.Model):
    """Catálogo de servicios dentales (limpieza, obturación, extracción...)."""
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio_usd = models.DecimalField(
        "Precio ($)",
        max_digits=10,
        decimal_places=2,
        help_text="Precio en dólares. Se facturará en Bs usando la tasa del día.",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "servicio_dental"
        ordering = ["nombre"]
        verbose_name = "Servicio dental"

    def __str__(self):
        return f"{self.nombre} (${self.precio_usd})"


class OrdenDental(models.Model):
    """Orden de trabajo vinculada a un expediente."""
    ESTADO = [
        ("abierta", "Abierta"),
        ("en_proceso", "En proceso"),
        ("completada", "Completada"),
        ("anulada", "Anulada"),
    ]
    expediente = models.ForeignKey(
        ExpedienteDental,
        on_delete=models.PROTECT,
        related_name="ordenes",
    )
    estado = models.CharField(max_length=15, choices=ESTADO, default="abierta")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ordenes_dentales",
    )

    class Meta:
        db_table = "orden_dental"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"Orden #{self.pk} - {self.expediente.paciente.full_name}"

    @property
    def total_usd(self):
        from decimal import Decimal
        return sum((d.subtotal_usd for d in self.items.all()), Decimal("0"))


class OrdenDentalItem(models.Model):
    orden = models.ForeignKey(OrdenDental, on_delete=models.CASCADE, related_name="items")
    servicio = models.ForeignKey(ServicioDental, on_delete=models.PROTECT)
    diente_fdi = models.CharField(
        "Diente (opcional)",
        max_length=2,
        blank=True,
        choices=DIENTE_FDI,
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_usd = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "orden_dental_item"

    @property
    def subtotal_usd(self):
        return self.cantidad * self.precio_usd

    def save(self, *args, **kwargs):
        if not self.precio_usd:
            self.precio_usd = self.servicio.precio_usd
        super().save(*args, **kwargs)
