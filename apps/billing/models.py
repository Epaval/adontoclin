from decimal import Decimal

from django.conf import settings
from django.db import models


class Factura(models.Model):
    ESTADO_CHOICES = [
        ("emitida", "Emitida"),
        ("pagada", "Pagada"),
        ("anulada", "Anulada"),
    ]

    METODO_PAGO = [
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
        ("transferencia", "Transferencia"),
        ("seguro", "Seguro / HMO"),
    ]

    numero = models.CharField(max_length=20, unique=True)
    numero_control = models.CharField(
        "Número de control",
        max_length=10,
        unique=True,
        blank=True,
        help_text="Formato fiscal: 00-NNNNN (auto-generado)",
    )

    cita = models.ForeignKey(
        "clinical.CitaDental",
        on_delete=models.PROTECT,
        related_name="facturas",
    )

    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default="emitida")
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO, blank=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    tasa = models.DecimalField("Tasa al emitir (Bs/$)", max_digits=14, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))

    observaciones = models.TextField(blank=True)

    MOTIVO_ANULACION_CHOICES = [
        ("devolucion", "Devolución al cliente"),
        ("falta_resultado", "Falta de resultado"),
        ("otros", "Otros"),
    ]
    motivo_anulacion = models.CharField(
        max_length=20,
        choices=MOTIVO_ANULACION_CHOICES,
        blank=True,
    )
    motivo_anulacion_otro = models.TextField(
        "Especificar motivo",
        blank=True,
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="facturas_creadas",
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "factura"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.numero} · {self.cita.expediente.paciente}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    servicio = models.ForeignKey(
        "clinical.ServicioDental",
        on_delete=models.PROTECT,
        related_name="detalles_factura",
    )
    diente_fdi = models.CharField("Diente", max_length=2, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "detalle_factura"
        constraints = [
            models.UniqueConstraint(
                fields=["factura", "servicio", "diente_fdi"],
                name="uniq_factura_servicio_diente",
            ),
        ]

    def __str__(self):
        return f"{self.factura.numero}: {self.servicio}"
