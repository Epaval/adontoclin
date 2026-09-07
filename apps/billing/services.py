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


def generar_factura(expediente, usuario, descuento=Decimal("0")):
    """
    Genera la factura de una orden tomando los exámenes realizados
    y congelando el precio vigente de cada examen al momento de facturar.
    """
    with transaction.atomic():
        if expediente.facturas.exclude(estado="anulada").exists():
            raise ValueError("Esta orden ya tiene una factura activa")

        realizados = (
            expediente.resultados.filter(estado__in=ESTADOS_REALIZADOS)
            .select_related("examen")
        )

        if not realizados.exists():
            raise ValueError("La orden aún no tiene exámenes realizados para facturar")

        ultima = Factura.objects.order_by("-id").first()
        numero = f"F-{(ultima.id + 1) if ultima else 1:06d}"

        factura = Factura.objects.create(
            numero=numero,
            numero_control=_generar_numero_control(),
            expediente=expediente,
            descuento=descuento,
            creado_por=usuario,
        )

        subtotal = Decimal("0")
        for resultado in realizados:
            costo = resultado.examen.costo_actual
            precio = costo.precio if costo else Decimal("0")

            DetalleFactura.objects.create(
                factura=factura,
                examen=resultado.examen,
                cantidad=1,
                precio_unitario=precio,
                subtotal=precio,
            )
            subtotal += precio

        factura.subtotal = subtotal
        factura.total = max(subtotal - descuento, Decimal("0"))
        from apps.core.models import TasaCambio
        _t = TasaCambio.actual()
        factura.tasa = _t.valor if _t else Decimal("0")
        factura.save(update_fields=["subtotal", "total", "tasa"])

        return factura


# ================= PDF DE FACTURA =================

import io

from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from apps.core.models import DatosLaboratorio


def generar_pdf_factura(factura):
    """Genera el PDF de la factura con el encabezado del laboratorio"""
    lab = DatosLaboratorio.cargar()

    from apps.core.models import TasaCambio

    _t = TasaCambio.actual()
    tasa = factura.tasa or (_t.valor if _t else Decimal("0"))
    detalles = []
    for d in factura.detalles.select_related("examen").all():
        detalles.append({
            "examen": d.examen, "cantidad": d.cantidad,
            "precio_unitario": d.precio_unitario, "subtotal": d.subtotal,
            "precio_bs": d.precio_unitario * tasa, "subtotal_bs": d.subtotal * tasa,
        })

    html = render_to_string(
        "reports/factura.html",
        {
            "tasa": tasa,
            "factura": factura,
            "paciente": factura.expediente.paciente,
            "detalles": detalles,
            "subtotal_bs": factura.subtotal * tasa,
            "descuento_bs": factura.descuento * tasa,
            "total_bs": factura.total * tasa,
            "lab": lab,
            "logo_path": lab.logo_pdf_path,
            "fecha_generacion": timezone.now(),
        },
    )

    buffer = io.BytesIO()
    estado = pisa.CreatePDF(io.StringIO(html), dest=buffer, encoding="utf-8")

    if estado.err:
        raise ValueError("Error al generar el PDF de la factura")

    return buffer.getvalue()
