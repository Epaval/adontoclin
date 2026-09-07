from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import Lower


class Medico(models.Model):
    class Meta:
        verbose_name = "Odontólogo"
        verbose_name_plural = "Odontólogos"

    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)

    ci = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        verbose_name="CI / matrícula",
    )

    telefono = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    especialidad = models.CharField(max_length=120, blank=True)

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medico"
        constraints = [
            UniqueConstraint(
                Lower("ci"),
                condition=Q(ci__isnull=False),
                name="medico_ci_lower_unique",
            ),
            UniqueConstraint(
                Lower("telefono"),
                condition=Q(telefono__isnull=False),
                name="medico_telefono_lower_unique",
            ),
            UniqueConstraint(
                Lower("email"),
                condition=Q(email__isnull=False),
                name="medico_email_lower_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["apellidos", "nombres"]),
        ]

    def __str__(self):
        return f"Dr(a). {self.nombres} {self.apellidos}".strip()

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
