from django.urls import path

from . import views

app_name = "clinical"
urlpatterns = [
    path("servicios/", views.ServicioDentalListView.as_view(), name="servicio_list"),
    path("expedientes/", views.ExpedienteDentalListView.as_view(), name="expediente_list"),
    path("expedientes/nueva/<int:paciente_id>/", views.ExpedienteDentalCreateView.as_view(), name="expediente_create"),
    path("expedientes/<int:pk>/editar/", views.ExpedienteDentalUpdateView.as_view(), name="expediente_update"),
    path("citas/nueva/<int:paciente_id>/", views.CitaDentalCreateView.as_view(), name="cita_create"),
    path("citas/<int:pk>/editar/", views.CitaDentalUpdateView.as_view(), name="cita_update"),
    path("odontograma/<int:paciente_id>/", views.OdontogramaView.as_view(), name="odontograma"),
]
