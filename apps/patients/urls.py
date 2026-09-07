from django.urls import path

from .api import BuscarPacientesView
from .views import (
    PacienteCreateView,
    PacienteHistorialView,
    PacienteListView,
    PacienteUpdateView,
)

app_name = "patients"
urlpatterns = [
    path("", PacienteListView.as_view(), name="list"),
    path("nuevo/", PacienteCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", PacienteUpdateView.as_view(), name="update"),
    path("<int:pk>/historial/", PacienteHistorialView.as_view(), name="historial"),
    path("api/buscar/", BuscarPacientesView.as_view(), name="api_buscar"),
]
