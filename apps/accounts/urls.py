from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    RecuperarClaveView,
    RecuperarNuevaClaveView,
    EquipoClaveView,
    EquipoCreateView,
    EquipoListView,
    EquipoUpdateView,
)

app_name = "accounts"

urlpatterns = [
    path("recuperar/", RecuperarClaveView.as_view(), name="recuperar"),
    path("recuperar/nueva/", RecuperarNuevaClaveView.as_view(), name="recuperar_nueva"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("equipo/", EquipoListView.as_view(), name="equipo_list"),
    path("equipo/nuevo/", EquipoCreateView.as_view(), name="equipo_create"),
    path("equipo/<int:pk>/editar/", EquipoUpdateView.as_view(), name="equipo_update"),
    path("equipo/<int:pk>/clave/", EquipoClaveView.as_view(), name="equipo_clave"),
]
