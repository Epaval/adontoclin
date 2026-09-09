"""Vistas del panel SaaS."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from django.conf import settings
from django.http import Http404

from .models import Clinica
from .forms import ClinicaForm
from .cloudflare_service import CloudflareService


class ProveedorRequired(LoginRequiredMixin):
    """Solo accesible cuando LABCLIN_ROL == proveedor."""
    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "LABCLIN_ROL", "clinica") != "proveedor":
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class ClinicaListView(ProveedorRequired, ListView):
    """Dashboard: lista de todas las clínicas."""
    model = Clinica
    template_name = "saas/clinica_list.html"
    context_object_name = "clinicas"


class ClinicaCreateView(ProveedorRequired, CreateView):
    """Formulario para crear una nueva clínica."""
    model = Clinica
    form_class = ClinicaForm
    template_name = "saas/clinica_form.html"
    success_url = reverse_lazy("saas:clinica_list")

    def form_valid(self, form):
        clinica = form.save(commit=False)
        clinica.estado = "creando"
        clinica.save()

        # Crear túnel en Cloudflare
        try:
            cf = CloudflareService()
            result = cf.crear_tunnel(clinica.slug)
            
            clinica.tunnel_id = result["tunnel_id"]
            clinica.token = result["token"]
            
            # Crear DNS
            cf.crear_dns_cname(clinica.slug, result["tunnel_id"])
            
            # Configurar ingress en el túnel
            cf.configurar_ingress(result["tunnel_id"], f"{clinica.slug}.facdin.com")
            
            clinica.estado = "activo"
            clinica.fecha_activacion = timezone.now()
            clinica.save()
            
            messages.success(self.request, f"✓ Clínica {clinica.nombre} creada exitosamente")
        except Exception as e:
            clinica.estado = "error"
            clinica.save()
            messages.error(self.request, f"Error creando túnel: {str(e)}")
            return redirect("saas:clinica_list")

        return super().form_valid(form)


class ClinicaDetailView(ProveedorRequired, DetailView):
    """Detalle de una clínica con token e instrucciones."""
    model = Clinica
    template_name = "saas/clinica_detail.html"
    context_object_name = "clinica"


class ClinicaVerificarView(ProveedorRequired, View):
    """Verifica si el túnel de una clínica está activo."""
    
    def get(self, request, pk):
        clinica = get_object_or_404(Clinica, pk=pk)
        
        try:
            cf = CloudflareService()
            activo = cf.verificar_tunel_activo(clinica.tunnel_id)
            clinica.fecha_ultimo_check = timezone.now()
            clinica.estado = "activo" if activo else "suspendido"
            clinica.save()
            
            return JsonResponse({
                "success": True,
                "activo": activo,
                "estado": clinica.estado
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
