from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import MedicoForm
from .models import Medico


class MedicoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Medico
    ordering = ["apellidos", "nombres"]
    permission_required = "doctors.view_medico"
    template_name = "generic_list.html"
    context_object_name = "object_list"
    paginate_by = 20

    extra_context = {
        "title": "Médicos",
        "create_url": "doctors:create",
        "update_url_name": "doctors:update",
    }


class MedicoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Medico
    form_class = MedicoForm
    permission_required = "doctors.add_medico"
    template_name = "form.html"
    success_url = reverse_lazy("doctors:list")

    extra_context = {
        "title": "Nuevo médico",
    }


class MedicoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Medico
    form_class = MedicoForm
    permission_required = "doctors.change_medico"
    template_name = "form.html"
    success_url = reverse_lazy("doctors:list")

    extra_context = {
        "title": "Editar médico",
    }
