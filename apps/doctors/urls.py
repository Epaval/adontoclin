from django.urls import path

from .views import (
    MedicoCreateView,
    MedicoListView,
    MedicoUpdateView,
)

app_name = "doctors"

urlpatterns = [
    path("", MedicoListView.as_view(), name="list"),
    path("nuevo/", MedicoCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", MedicoUpdateView.as_view(), name="update"),
]
