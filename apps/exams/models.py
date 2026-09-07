from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import Lower


class Examen(models.Model):
    TIPO_RESULTADO = [
        ("numerico", "Numérico"),
        ("cualitativo", "Cualitativo"),
        ("texto", "Texto libre"),
    ]

    nombre_completo = models.CharField(max_length=255)
    tipo_resultado = models.CharField(
        max_length=20, choices=TIPO_RESULTADO, default="numerico",
        help_text="Tipo de valor que acepta este examen",
    )
    valores_ref = models.TextField(blank=True)
    perfil = models.CharField(max_length=120, blank=True)

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "examen"
        constraints = [
            UniqueConstraint(
                Lower("nombre_completo"),
                name="examen_nombre_lower_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["nombre_completo"]),
            models.Index(fields=["perfil"]),
            models.Index(fields=["tipo_resultado"]),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            from apps.results.models import Resultado

            Resultado.objects.filter(
                examen=self,
                estado="borrador",
                valor_numerico=None,
                valor_cualitativo="",
            ).exclude(tipo_resultado=self.tipo_resultado).update(
                tipo_resultado=self.tipo_resultado
            )
        except Exception:
            pass

    def __str__(self):
        return self.nombre_completo

    @property
    def costo_actual(self):
        return self.costos.filter(activo=True).order_by("-ultima_fecha_act").first()


    @property
    def precio_actual(self):
        """Precio activo del examen (0 si no tiene)"""
        costo = self.costos.filter(activo=True).first()
        return costo.precio if costo else 0


class CostoExamen(models.Model):
    examen = models.ForeignKey(
        Examen,
        on_delete=models.PROTECT,
        related_name="costos",
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "costo_examen"
        constraints = [
            UniqueConstraint(
                fields=["examen"],
                condition=Q(activo=True),
                name="uniq_costo_activo_por_examen",
            ),
        ]

    def __str__(self):
        return f"{self.examen} - {self.precio}"

    def save(self, *args, **kwargs):
        if self.activo:
            CostoExamen.objects.filter(
                examen=self.examen,
                activo=True,
            ).exclude(pk=self.pk).update(activo=False)

        super().save(*args, **kwargs)


class Perfil(models.Model):
    """Perfil personalizado: paquete de examenes seleccionables (M2M)."""
    nombre = models.CharField(max_length=120, unique=True)
    examenes = models.ManyToManyField(Examen, related_name="perfiles_custom", blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "perfil"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
