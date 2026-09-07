from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    Group,
    PermissionsMixin,
)
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.functions import Lower
from django.utils import timezone


class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    group = models.OneToOneField(
        Group,
        on_delete=models.PROTECT,
        related_name="rol",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "rol"
        verbose_name = "rol"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre


class EmpleadoManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, nombre_usuario, email, password=None, **extra_fields):
        if not nombre_usuario:
            raise ValueError("El nombre de usuario es obligatorio")
        if not email:
            raise ValueError("El email es obligatorio")

        email = self.normalize_email(email).lower()
        user = self.model(nombre_usuario=nombre_usuario, email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_user(self, nombre_usuario, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(nombre_usuario, email, password, **extra_fields)

    def create_superuser(self, nombre_usuario, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self._create_user(nombre_usuario, email, password, **extra_fields)


class Empleado(AbstractBaseUser, PermissionsMixin):
    nombre_usuario = models.CharField(
        "nombre_usuario",
        max_length=150,
        unique=True,
        db_column="nombre_usuario",
    )
    email = models.EmailField("email", db_index=True)
    telefono = models.CharField(
        "telefono",
        max_length=30,
        null=True,
        blank=True,
        db_index=True,
    )
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)

    rol = models.ForeignKey(
        Rol,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="empleados",
    )

    is_active = models.BooleanField(default=True, db_column="activo")
    is_staff = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    objects = EmpleadoManager()

    USERNAME_FIELD = "nombre_usuario"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "empleado"
        constraints = [
            UniqueConstraint(
                Lower("email"),
                name="empleado_email_lower_unique",
            ),
            UniqueConstraint(
                Lower("telefono"),
                condition=Q(telefono__isnull=False),
                name="empleado_telefono_lower_unique",
            ),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f"{self.nombres} {self.apellidos}".strip()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()

        if self.telefono:
            self.telefono = "".join(
                ch for ch in self.telefono if ch.isdigit() or ch == "+"
            )
        else:
            self.telefono = None

        super().save(*args, **kwargs)


class Salario(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.PROTECT,
        related_name="salarios",
    )
    rol = models.ForeignKey(
        Rol,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="salarios",
    )

    salario_actual = models.DecimalField(max_digits=12, decimal_places=2)
    ultimo_salario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    vigente = models.BooleanField(default=False)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_fecha_act = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "salario"
        constraints = [
            models.CheckConstraint(
                check=Q(salario_actual__gte=0),
                name="salario_actual_positivo",
            ),
            UniqueConstraint(
                fields=["empleado"],
                condition=Q(vigente=True),
                name="uniq_salario_vigente_por_empleado",
            ),
        ]

    def __str__(self):
        return f"Salario {self.empleado} - {self.salario_actual}"

    def save(self, *args, **kwargs):
        if self.vigente:
            Salario.objects.filter(
                empleado=self.empleado,
                vigente=True,
            ).exclude(pk=self.pk).update(
                vigente=False,
                ultima_fecha_act=timezone.now(),
            )
        super().save(*args, **kwargs)
