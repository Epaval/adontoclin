"""Modelos para el panel SaaS multi-clínica."""
from django.db import models


class Clinica(models.Model):
    """Clínica registrada con acceso remoto vía Cloudflare Tunnel."""
    
    ESTADO_CHOICES = [
        ("creando", "Creando túnel"),
        ("activo", "Activo"),
        ("suspendido", "Suspendido"),
        ("error", "Error"),
    ]
    
    nombre = models.CharField("Nombre comercial", max_length=100, unique=True)
    slug = models.SlugField("Subdominio", max_length=63, unique=True, 
                            help_text="Subdominio (ej: dientesano → dientesano.facdin.com)")
    tunnel_id = models.CharField("Tunnel ID", max_length=100, blank=True)
    token = models.TextField("Token de instalación", blank=True)
    estado = models.CharField("Estado", max_length=20, choices=ESTADO_CHOICES, default="creando")
    
    # Datos del cliente
    cliente_nombre = models.CharField("Nombre del contacto", max_length=150, blank=True)
    cliente_email = models.EmailField("Email del contacto", blank=True)
    cliente_telefono = models.CharField("Teléfono", max_length=30, blank=True)
    
    # Fechas
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_activacion = models.DateTimeField(null=True, blank=True)
    fecha_ultimo_check = models.DateTimeField(null=True, blank=True)
    
    # Notas
    notas = models.TextField("Notas internas", blank=True)
    
    class Meta:
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"
        ordering = ["-fecha_creacion"]
    
    def __str__(self):
        return f"{self.nombre} ({self.slug}.facdin.com)"
    
    @property
    def url_publica(self):
        return f"https://{self.slug}.facdin.com"
