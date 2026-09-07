from django.urls import path

from .api import BuscarPacientesView
from .views import (
    ExpedienteCreateView,
    ExpedienteDetailView,
    EliminarResultadoView,
    ExpedienteListView,
    PacienteCreateView,
    PacienteHistorialView,
    PacienteListView,
    PacienteReportePDFView,
    PacienteUpdateView,
    buscar_representante,
    crear_representante_rapido,
)

app_name = "patients"

urlpatterns = [
    path('buscar-representante/', buscar_representante, name='buscar_representante'),
    path('representante-rapido/', crear_representante_rapido, name='representante_rapido'),
    path("api/buscar-pacientes/", BuscarPacientesView.as_view(), name="api_buscar_pacientes"),
    path("", PacienteListView.as_view(), name="list"),
    path("nuevo/", PacienteCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", PacienteUpdateView.as_view(), name="update"),

    path("<int:pk>/historial/", PacienteHistorialView.as_view(), name="historial"),
    path("<int:pk>/reporte/pdf/", PacienteReportePDFView.as_view(), name="reporte_pdf"),

    path("ordenes/", ExpedienteListView.as_view(), name="orden_list"),
    path("ordenes/nueva/", ExpedienteCreateView.as_view(), name="orden_create"),
    path("ordenes/<int:pk>/", ExpedienteDetailView.as_view(), name="orden_detail"),
    path("ordenes/<int:pk>/resultado/<int:resultado_pk>/eliminar/", EliminarResultadoView.as_view(), name="eliminar_resultado"),
]
