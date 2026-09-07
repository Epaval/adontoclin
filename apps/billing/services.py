from decimal import Decimal

from django.db import transaction

from .models import DetalleFactura, Factura

# Solo se facturan exámenes que ya fueron realizados
ESTADOS_REALIZADOS = ["cargado", "validado", "publicado"]


def _generar_numero_control():
    """
    Genera el numero de control fiscal venezolano: 00-NNNNN.
    Secuencial global: 00-00001, 00-00002, 00-00003...
    """
    maximo = 0
    numeros = Factura.objects.filter(
        numero_control__startswith="00-"
    ).values_list("numero_control", flat=True)

    for n in numeros:
        try:
            maximo = max(maximo, int(n.split("-")[1]))
        except (IndexError, ValueError):
            continue

    return f"00-{maximo + 1:05d}"


def _generar_numero():
    ultimo = Factura.objects.order_by("-id").values_list("numero", flat=True).first()
    n = 1
    if ultimo:
        try:
            n = int(ultimo.split("-")[1]) + 1
        except Exception:
            n = Factura.objects.count() + 1
    return f"F-{n:06d}"


def generar_factura(cita, usuario, descuento=Decimal("0")):
    """Crea factura en $ desde una cita dental (Bs con la tasa del día)."""
    from apps.core.models import TasaCambio

    if not cita.items.exists():
        raise ValueError("La cita no tiene servicios cargados. Agregue servicios antes de facturar.")
    with transaction.atomic():
        factura = Factura(
            numero=_generar_numero(),
            numero_control=_generar_numero_control(),
            cita=cita,
            creado_por=usuario,
        )
        factura.save()
        subtotal = Decimal("0")
        for item in cita.items.select_related("servicio").all():
            DetalleFactura.objects.create(
                factura=factura,
                servicio=item.servicio,
                diente_fdi=item.diente_fdi,
                cantidad=item.cantidad,
                precio_unitario=item.precio_usd,
                subtotal=item.subtotal_usd,
            )
            subtotal += item.subtotal_usd
        _t = TasaCambio.actual()
        factura.tasa = _t.valor if _t else Decimal("0")
        factura.subtotal = subtotal
        factura.total = max(subtotal - descuento, Decimal("0"))
        factura.save(update_fields=["subtotal", "total", "tasa"])
        cita.estado = "atendida"
        cita.save(update_fields=["estado"])
        return factura


# ================= PDF DE FACTURA =================

import io

from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from apps.core.models import DatosLaboratorio


def generar_pdf_factura(factura):
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    import io

    tasa = factura.tasa or Decimal("0")
    detalles = []
    for d in factura.detalles.select_related("servicio").all():
        detalles.append({
            "servicio": d.servicio,
            "diente": d.diente_fdi,
            "cantidad": d.cantidad,
            "precio_unitario": d.precio_unitario,
            "precio_bs": (d.precio_unitario * tasa).quantize(Decimal("0.01")),
            "subtotal": d.subtotal,
            "subtotal_bs": (d.subtotal * tasa).quantize(Decimal("0.01")),
        })
    context = {
        "factura": factura,
        "paciente": factura.cita.expediente.paciente,
        "detalles": detalles,
        "subtotal_bs": (factura.subtotal * tasa).quantize(Decimal("0.01")),
        "descuento_bs": (factura.descuento * tasa).quantize(Decimal("0.01")),
        "total_bs": (factura.total * tasa).quantize(Decimal("0.01")),
    }
    try:
        from apps.core.models import DatosLaboratorio
        context["datos"] = DatosLaboratorio.objects.first()
    except Exception:
        context["datos"] = None
    html = render_to_string("reports/factura.html", context)
    pdf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf)
    return pdf.getvalue()


