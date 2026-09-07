from django.urls import path

from .views import (
    ExamenCreateView,
    ExamenListView,
    ExamenUpdateView,
    AjusteMasivoView,
    PerfilBuilderView,
    PerfilDeleteView,
)

app_name = "exams"

urlpatterns = [
    path("", ExamenListView.as_view(), name="list"),
    path("nuevo/", ExamenCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", ExamenUpdateView.as_view(), name="update"),
    path("ajuste-masivo/", AjusteMasivoView.as_view(), name="ajuste_masivo"),
    path("perfiles/", PerfilBuilderView.as_view(), name="perfiles"),
    path("perfiles/<int:pk>/eliminar/", PerfilDeleteView.as_view(), name="perfil_delete"),
]
