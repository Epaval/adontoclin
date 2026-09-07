import uuid

from django.conf import settings
from django.db import models


class Resultado(models.Model):
    TIPO_RESULTADO = [
        ("numerico", "Numérico"),
        ("cualitativo", "Cualitativo"),
        ("texto", "Texto libre"),
    ]

    ESTADO_CHOICES = [
        ("borrador", "Pendiente"),
        ("cargado", "Cargado"),
        ("validado", "Validado"),
        ("publicado", "Publicado"),
        ("anulado", "Anulado"),
    ]

    expediente = models.ForeignKey(
        "patients.Expediente",
        on_delete=models.PROTECT,
        related_name="resultados",
    )

    examen = models.ForeignKey(
        "exams.Examen",
        on_delete=models.PROTECT,
        related_name="resultados",
    )

    # Campos estructurados
    tipo_resultado = models.CharField(
        max_length=20,
        choices=TIPO_RESULTADO,
        default="numerico",
    )

    valor_numerico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor numérico",
    )

    unidad = models.CharField(
        max_length=20,
        blank=True,
        help_text="Ej: mg/dL, mm/h, U/L",
    )

    valor_cualitativo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Resultado cualitativo",
        help_text="Ej: Positivo, Negativo, Reactivo",
    )

    observaciones = models.TextField(
        blank=True,
        help_text="Notas adicionales sobre el resultado",
    )

    # Estado y auditoría
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default="borrador",
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resultados_creados",
    )

    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="resultados_actualizados",
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "resultado"
        permissions = [
            ("editar_result", "Editar resultado"),
            ("cargar_result", "Cargar resultado"),
        ]
        indexes = [
            models.Index(fields=["expediente", "estado"]),
            models.Index(fields=["examen", "estado"]),
            models.Index(fields=["fecha_creacion"]),
            models.Index(fields=["estado", "fecha_creacion"]),
            models.Index(fields=["tipo_resultado"]),
        ]

    def __str__(self):
        return f"{self.examen.nombre_completo}: {self.resultado_texto}"

    @property
    def resultado_texto(self):
        """Representación legible del resultado"""
        if self.tipo_resultado == "numerico" and self.valor_numerico is not None:
            texto = str(self.valor_numerico)
            if self.unidad:
                texto += f" {self.unidad}"
            return texto
        elif self.tipo_resultado in ("cualitativo", "texto") and self.valor_cualitativo:
            return self.valor_cualitativo
        elif self.observaciones:
            return self.observaciones
        return "Sin resultado"

    @property
    def tiene_resultado(self):
        """Verifica si ya tiene un resultado cargado"""
        if self.tipo_resultado == "numerico":
            return self.valor_numerico is not None
        elif self.tipo_resultado in ("cualitativo", "texto"):
            return bool(self.valor_cualitativo)
        return bool(self.observaciones)


class ResultadoAcceso(models.Model):
    """Tokens seguros para acceso público a resultados"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    resultado = models.ForeignKey(
        Resultado,
        on_delete=models.CASCADE,
        related_name="accesos",
    )

    token_hash = models.CharField(max_length=64, unique=True)
    expira = models.DateTimeField()

    usado = models.BooleanField(default=False)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    ip_uso = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resultado_acceso"
        indexes = [
            models.Index(fields=["token_hash", "usado", "expira"]),
        ]

    def __str__(self):
        return f"Acceso {self.resultado_id}"
