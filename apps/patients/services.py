import io

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from apps.core.models import DatosLaboratorio


def _grupos_por_perfil(expediente):
    """Agrupa los resultados del expediente por perfil de examen"""
    grupos = {}
    for r in expediente.resultados.all():
        perfil = (r.examen.perfil or "Otros").strip() or "Otros"
        grupos.setdefault(perfil, []).append(r)

    items = [
        {"perfil": perfil, "resultados": resultados}
        for perfil, resultados in grupos.items()
    ]

    ORDEN_ORINA = {"Orina · Físicos": 0, "Orina · Químicos": 1, "Orina · Microscópico": 2}

    def clave(it):
        p = it["perfil"]
        if p in ORDEN_ORINA:
            return (0, ORDEN_ORINA[p], p)
        return (1, 0, p)

    items.sort(key=clave)
    for i, it in enumerate(items):
        it["es_orina"] = it["perfil"] in ORDEN_ORINA
        it["cabecera_orina"] = it["es_orina"] and (i == 0 or not items[i - 1]["es_orina"])
    return items

def generar_pdf_reporte(paciente, expedientes):
    """Genera el reporte de resultados del paciente en PDF"""
    lab = DatosLaboratorio.cargar()

    expedientes_datos = []
    bioanalista = None

    for exp in expedientes:
        expedientes_datos.append({
            "expediente": exp,
            "grupos": _grupos_por_perfil(exp),
        })
        if bioanalista is None and exp.bioanalista:
            bioanalista = exp.bioanalista

    if lab.bioanalista_nombre:
        nombre_firma = lab.bioanalista_nombre
    elif bioanalista:
        nombre_firma = bioanalista.full_name
    else:
        nombre_firma = ""

    registro_firma = lab.bioanalista_registro

    html = render_to_string(
        "reports/reporte_resultados.html",
        {
            "paciente": paciente,
            "expedientes_datos": expedientes_datos,
            "lab": lab,
            "logo_path": lab.logo_pdf_path,
            "nombre_firma": nombre_firma,
            "registro_firma": registro_firma,
            "firma_path": lab.firma_pdf_path,
            "sello_path": lab.sello_pdf_path,
            "fecha_generacion": timezone.now(),
        },
    )

    buffer = io.BytesIO()
    estado = pisa.CreatePDF(io.StringIO(html), dest=buffer, encoding="utf-8")

    if estado.err:
        raise ValueError("Error al generar el PDF del reporte")

    return buffer.getvalue()


