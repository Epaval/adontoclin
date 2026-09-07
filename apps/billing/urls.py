from django.urls import path

from .views import (
    FacturaAnularView,
    FacturaCreateView,
    FacturaDetailView,
    FacturaListView,
    FacturaPagarView,
    FacturaPDFView,
)

app_name = "billing"

urlpatterns = [
    path("", FacturaListView.as_view(), name="list"),
    path("<int:pk>/", FacturaDetailView.as_view(), name="detail"),
    path("<int:pk>/pdf/", FacturaPDFView.as_view(), name="factura_pdf"),
    path("orden/<int:expediente_pk>/crear/", FacturaCreateView.as_view(), name="crear_desde_orden"),
    path("<int:pk>/pagar/", FacturaPagarView.as_view(), name="pagar"),
    path("<int:pk>/anular/", FacturaAnularView.as_view(), name="anular"),
]
