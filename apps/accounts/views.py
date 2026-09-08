from django.utils import timezone
from django.db import models
from apps.billing.models import DetalleFactura, Factura
from datetime import date, datetime, time, timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.management import call_command
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.doctors.models import Medico
from apps.clinical.models import ServicioDental, ExpedienteDental, CitaDental
from apps.patients.models import Paciente

from .forms import (
    RecuperarClaveForm,
    RecuperarIdentidadForm,
    ConfigInicialForm,
    EmpleadoClaveForm,
    EmpleadoCreateForm,
    EmpleadoUpdateForm,
)
from .models import Empleado, Rol
from django.core.cache import cache


class DashboardView(LoginRequiredMixin, TemplateView):
    """Panel principal con métricas dentales."""
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        from datetime import date

        from django.db.models import Count, Sum

        from apps.billing.models import DetalleFactura, Factura
        from apps.clinical.models import ExpedienteDental, CitaDental, ServicioDental
        from apps.doctors.models import Medico
        from apps.patients.models import Paciente

        context = super().get_context_data(**kwargs)
        hoy = date.today()
        hoy_dt = datetime.combine(hoy, time.min)
        manana_dt = hoy_dt + timedelta(days=1)
        stats = {
            "total_pacientes": Paciente.objects.filter(activo=True).count(),
            "total_medicos": Medico.objects.filter(activo=True).count(),
            "total_examenes": ServicioDental.objects.filter(activo=True).count(),
            "total_resultados": ExpedienteDental.objects.count(),
            "pacientes_del_dia": Paciente.objects.filter(
                expediente_dental__citas__fecha__date=hoy
            ).distinct().count(),
            "ordenes_abiertas": CitaDental.objects.filter(
                estado__in=["abierta", "en_proceso"]
            ).count(),
            "ordenes_cerradas_hoy": CitaDental.objects.filter(
                estado="completada", fecha_creacion__date=hoy
            ).count(),
            "ingresos_hoy": Factura.objects.filter(
                estado="emitida", fecha_creacion__date=hoy
            ).aggregate(t=Sum("total"))["t"] or 0,
            "ingresos_mes": Factura.objects.filter(
                estado="emitida", fecha_creacion__date__gte=hoy.replace(day=1)
            ).aggregate(t=Sum("total"))["t"] or 0,
            "top_examenes": list(
                DetalleFactura.objects.values("servicio__nombre")
                .annotate(total=Count("id"))
                .order_by("-total")[:5]
            ),
        }
        context.update(stats)
        context["modo_escritorio"] = settings.ESCRITORIO
        return context



class ConfiguracionInicialView(View):
    """Primera vez que se abre la app: el cliente crea su cuenta principal"""

    def get(self, request):
        if Empleado.objects.filter(is_superuser=True).exists():
            return redirect("dashboard")
        return render(request, "core/configuracion_inicial.html", {
            "form": ConfigInicialForm(),
        })

    def post(self, request):
        if Empleado.objects.filter(is_superuser=True).exists():
            return redirect("dashboard")

        form = ConfigInicialForm(request.POST)
        if not form.is_valid():
            return render(request, "core/configuracion_inicial.html", {"form": form}, status=400)

        data = form.cleaned_data

        # Roles siempre; catálogo si el cliente lo desea
        if data.get("cargar_catalogo"):
            _seed_dental()

        user = Empleado.objects.create_superuser(
            nombre_usuario=data["nombre_usuario"],
            email=data["email"],
            password=data["password1"],
            nombres=data["nombres"],
            apellidos=data["apellidos"],
        )

        rol_admin = Rol.objects.filter(nombre="admin").first()
        if rol_admin:
            user.rol = rol_admin
            user.save(update_fields=["rol"])

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "¡Cuenta principal creada! Bienvenido a Lab Clínico")
        return redirect("dashboard")


# ================= SECCIÓN EQUIPO =================

class EquipoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Empleado
    permission_required = "accounts.change_empleado"
    template_name = "accounts/equipo_list.html"
    context_object_name = "object_list"
    paginate_by = 6

    def get_queryset(self):
        qs = Empleado.objects.select_related("rol").order_by("apellidos", "nombres")
        q = self.request.GET.get("q", "").strip()
        if q:
            for term in q.split():
                qs = qs.filter(
                    Q(nombres__unaccent__icontains=term)
                    | Q(apellidos__unaccent__icontains=term)
                    | Q(nombre_usuario__unaccent__icontains=term)
                )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class EquipoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Empleado
    form_class = EmpleadoCreateForm
    permission_required = "accounts.add_empleado"
    template_name = "form.html"
    success_url = reverse_lazy("accounts:equipo_list")
    extra_context = {"title": "Nuevo miembro del equipo"}

    def form_valid(self, form):
        messages.success(self.request, f"Usuario {form.instance.nombre_usuario} creado")
        return super().form_valid(form)


class EquipoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Empleado
    form_class = EmpleadoUpdateForm
    permission_required = "accounts.change_empleado"
    template_name = "form.html"
    success_url = reverse_lazy("accounts:equipo_list")
    extra_context = {"title": "Editar miembro del equipo"}

    def form_valid(self, form):
        messages.success(self.request, "Datos actualizados correctamente")
        return super().form_valid(form)


class EquipoClaveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "accounts.change_empleado"

    def get(self, request, pk):
        empleado = Empleado.objects.get(pk=pk)
        return render(request, "accounts/equipo_clave.html", {
            "form": EmpleadoClaveForm(),
            "empleado": empleado,
        })

    def post(self, request, pk):
        empleado = Empleado.objects.get(pk=pk)
        form = EmpleadoClaveForm(request.POST)

        if form.is_valid():
            empleado.set_password(form.cleaned_data["password1"])
            empleado.save(update_fields=["password"])
            messages.success(request, f"Contraseña de {empleado.nombre_usuario} actualizada")
            return redirect("accounts:equipo_list")

        return render(request, "accounts/equipo_clave.html", {
            "form": form,
            "empleado": empleado,
        }, status=400)


# ================= RECUPERAR CLAVE (sin correo) =================

from django.shortcuts import get_object_or_404  # noqa: E402


class RecuperarClaveView(View):
    """Paso 1: identificar la cuenta por usuario o correo"""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, "accounts/recuperar.html", {
            "form": RecuperarIdentidadForm(),
        })

    def post(self, request):
        form = RecuperarIdentidadForm(request.POST)
        if form.is_valid():
            usuario = form.cleaned_data["nombre_usuario"].strip()
            correo = form.cleaned_data["email"].strip()
            user = Empleado.objects.filter(
                nombre_usuario__iexact=usuario,
                email__iexact=correo,
                is_active=True,
            ).first()

            if user:
                request.session["recuperar_uid"] = user.pk
                return redirect("accounts:recuperar_nueva")

            form.add_error(None, "El usuario y el correo no coinciden con ninguna cuenta activa")

        return render(request, "accounts/recuperar.html", {"form": form}, status=400)


class RecuperarNuevaClaveView(View):
    """Paso 2: escribir la nueva clave"""

    def get(self, request):
        if not request.session.get("recuperar_uid"):
            return redirect("accounts:recuperar")
        return render(request, "accounts/recuperar_nueva.html", {
            "form": RecuperarClaveForm(),
        })

    def post(self, request):
        uid = request.session.get("recuperar_uid")
        if not uid:
            return redirect("accounts:recuperar")

        user = get_object_or_404(Empleado, pk=uid)
        form = RecuperarClaveForm(request.POST)

        if form.is_valid():
            user.set_password(form.cleaned_data["password1"])
            user.save(update_fields=["password"])
            del request.session["recuperar_uid"]
            messages.success(request, "Clave actualizada. Ya puedes iniciar sesión")
            return redirect("accounts:login")

        return render(request, "accounts/recuperar_nueva.html", {"form": form}, status=400)


def _seed_dental():
    """Catálogo inicial de servicios dentales (reemplaza seed de laboratorio)."""
    from apps.clinical.models import ServicioDental
    servs = [
        ("LIM", "Limpieza dental (profilaxis)", "Limpieza profunda con ultrasonido", "30.00"),
        ("OBT", "Obturación (empaste)", "Resina compuesta", "40.00"),
        ("EXT", "Extracción simple", "Extracción de pieza dental", "50.00"),
        ("EXTC", "Extracción compleja", "Muela del juicio / incluida", "120.00"),
        ("END", "Endodoncia", "Tratamiento de conducto", "180.00"),
        ("COR", "Corona dental", "Porcelana o zirconio", "350.00"),
        ("IMP", "Implante dental", "Implante de titanio + corona", "800.00"),
        ("ORT", "Ortodoncia", "Brackets metálicos (mensual)", "60.00"),
        ("BLA", "Blanqueamiento dental", "Blanqueamiento en consultorio", "250.00"),
        ("RX", "Radiografía periapical", "Placa individual", "10.00"),
    ]
    for c, n, d, p in servs:
        ServicioDental.objects.get_or_create(
            codigo=c, defaults={"nombre": n, "descripcion": d, "precio_usd": p}
        )
