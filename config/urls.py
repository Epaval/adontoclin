from apps.core.views import BackupView, BusquedaGlobalView
from apps.core.views_activacion import ActivacionView
from apps.core.views_tasa import TasaCambioView
from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import ConfiguracionInicialView, DashboardView
from . import views as error_views
from apps.core.admin_tools import AjusteMasivoPreciosView, EstadisticasView, FacturaExportarExcelView, AbrirCarpetaExportView, AdminAccesoRemotoView, InstalarCloudflaredView, LicenciaView

urlpatterns = [
    path('tema/', __import__('apps.core.views_tasa', fromlist=['cambiar_tema']).cambiar_tema, name='cambiar_tema'),
    path("clinical/", include("apps.clinical.urls")),
    path("admin/", admin.site.urls),
    path("", DashboardView.as_view(), name="dashboard"),
    path("buscar/", BusquedaGlobalView.as_view(), name="busqueda_global"),
    path("admin-lab/estadisticas/", EstadisticasView.as_view(), name="estadisticas"),
    path("admin-lab/licencia/", LicenciaView.as_view(), name="licencia_panel"),
    path("saas/", include("saas.urls")),
    path("admin-lab/acceso-remoto/", AdminAccesoRemotoView.as_view(), name="acceso_remoto"),
    path("instalar-cloudflared/", InstalarCloudflaredView.as_view(), name="instalar_cloudflared"),
    path("admin-lab/acceso-remoto/", AdminAccesoRemotoView.as_view(), name="acceso_remoto"),
    path("admin-lab/abrir-carpeta/", AbrirCarpetaExportView.as_view(), name="abrir_carpeta_export"),
    path("admin-lab/exportar-excel/", FacturaExportarExcelView.as_view(), name="exportar_excel"),
    path("admin-lab/ajuste-precios/", AjusteMasivoPreciosView.as_view(), name="ajuste_masivo"),
    path("configuracion-inicial/", ConfiguracionInicialView.as_view(), name="configuracion_inicial"),
    path("respaldo/", BackupView.as_view(), name="backup"),
    path("activacion/", ActivacionView.as_view(), name="activacion"),
    path("tasa/", TasaCambioView.as_view(), name="tasa_cambio"),
    path("accounts/", include("apps.accounts.urls")),
    path("pacientes/", include("apps.patients.urls")),
    path("facturas/", include("apps.billing.urls")),
]

# Handlers personalizados de errores
handler403 = "config.views.handler403"
handler404 = "config.views.handler404"
handler500 = "config.views.handler500"

from django.conf import settings as _settings
from django.conf.urls.static import static as _static
urlpatterns += _static(_settings.MEDIA_URL, document_root=_settings.MEDIA_ROOT)
