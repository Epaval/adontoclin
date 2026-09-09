from django.urls import path
from . import views

app_name = "saas"

urlpatterns = [
    path("", views.ClinicaListView.as_view(), name="clinica_list"),
    path("nueva/", views.ClinicaCreateView.as_view(), name="clinica_create"),
    path("<int:pk>/", views.ClinicaDetailView.as_view(), name="clinica_detail"),
    path("<int:pk>/verificar/", views.ClinicaVerificarView.as_view(), name="clinica_verificar"),
]
