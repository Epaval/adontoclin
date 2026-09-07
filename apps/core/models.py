from datetime import date
import os

from django.core.exceptions import ValidationError
from django.db import models


def validar_logo(value):
    ext = value.name.rsplit(".", 1)[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "svg"):
        raise ValidationError("Formato permitido: PNG, JPG o SVG")


class DatosLaboratorio(models.Model):
    """Datos del laboratorio para encabezados de PDF (registro unico)"""

    nombre = models.CharField(max_length=150, default="LAB CLINICO")
    rif = models.CharField("RIF", max_length=30, blank=True)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    ciudad = models.CharField(max_length=80, blank=True)
    lema = models.CharField(max_length=120, blank=True)
    simbolo_moneda = models.CharField(max_length=5, default="Bs.")
    logo = models.FileField(
        "Logo del laboratorio (PNG, JPG o SVG)",
        upload_to="logo/",
        null=True,
        blank=True,
        validators=[validar_logo],
        help_text="Se muestra en el encabezado de reportes y facturas en PDF",
    )
    bioanalista_nombre = models.CharField(
        "Bioanalista para firma", max_length=120, blank=True
    )
    bioanalista_registro = models.CharField(
        "Nro de registro del bioanalista", max_length=40, blank=True
    )
    firma_imagen = models.ImageField(
        "Firma del bioanalista (PNG transparente)",
        upload_to="firmas/", null=True, blank=True,
        help_text="Se imprime sobre la línea de firma en los PDF",
    )
    sello_imagen = models.ImageField(
        "Sello del laboratorio (PNG transparente)",
        upload_to="sellos/", null=True, blank=True,
        help_text="Se imprime junto a la firma en los PDF",
    )

    class Meta:
        verbose_name = "Datos del laboratorio"
        verbose_name_plural = "Datos del laboratorio"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @property
    def logo_pdf_path(self):
        """Ruta del logo para el PDF (xhtml2pdf renderiza SVG nativamente)"""
        if not self.logo:
            return None
        return self.logo.path

    @property
    def firma_pdf_path(self):
        return self.firma_imagen.path if self.firma_imagen else None

    @property
    def sello_pdf_path(self):
        return self.sello_imagen.path if self.sello_imagen else None

    @classmethod
    def cargar(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj


class TasaCambio(models.Model):
    """Tasa de cambio del día (Bs por $)."""
    valor = models.DecimalField("Tasa (Bs por $)", max_digits=14, decimal_places=2)
    fecha = models.DateField(default=date.today)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "Tasa de cambio"

    def __str__(self):
        return f"{self.valor} Bs/$ ({self.fecha})"

    @classmethod
    def actual(cls):
        return cls.objects.order_by("-fecha", "-id").first()
