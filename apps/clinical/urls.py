from django.urls import path

from . import views

app_name = "clinical"
urlpatterns = [
    path("agenda/", views.AgendaView.as_view(), name="agenda"),
    path("citas/nueva-agenda/", views.CitaNuevaView.as_view(), name="cita_nueva"),
    path("servicios/", views.ServicioDentalListView.as_view(), name="servicio_list"),
    path("servicios/nuevo/", views.ServicioDentalCreateView.as_view(), name="servicio_create"),
    path("servicios/<int:pk>/editar/", views.ServicioDentalUpdateView.as_view(), name="servicio_update"),
    path("expedientes/", views.ExpedienteDentalListView.as_view(), name="expediente_list"),
    path("expedientes/nueva/<int:paciente_id>/", views.ExpedienteDentalCreateView.as_view(), name="expediente_create"),
    path("expedientes/<int:pk>/editar/", views.ExpedienteDentalUpdateView.as_view(), name="expediente_update"),
    path("citas/nueva/<int:paciente_id>/", views.CitaDentalCreateView.as_view(), name="cita_create"),
    path("citas/<int:pk>/editar/", views.CitaDentalUpdateView.as_view(), name="cita_update"),
    path("citas/<int:cita_pk>/servicios/nuevo/", views.CitaItemCreateView.as_view(), name="cita_item_create"),
    path("servicios-item/<int:pk>/eliminar/", views.CitaItemDeleteView.as_view(), name="cita_item_delete"),
    path("recetas/nueva/<int:cita_pk>/", views.RecetaCreateView.as_view(), name="receta_create"),
    path("recetas/<int:pk>/editar/", views.RecetaUpdateView.as_view(), name="receta_update"),
    path("recetas/<int:pk>/pdf/", views.RecetaPDFView.as_view(), name="receta_pdf"),
    path("odontograma/<int:paciente_id>/", views.OdontogramaView.as_view(), name="odontograma"),
]
