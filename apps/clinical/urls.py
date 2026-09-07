from django.urls import path
from . import views

app_name = "clinical"
urlpatterns = [
    path("odontograma/<int:paciente_id>/", views.OdontogramaView.as_view(), name="odontograma"),
    path("expedientes/", views.ExpedienteDentalListView.as_view(), name="expediente_list"),
    path("expedientes/nueva/", views.ExpedienteDentalCreateView.as_view(), name="expediente_create"),
    path("servicios/", views.ServicioDentalListView.as_view(), name="servicio_list"),
]
