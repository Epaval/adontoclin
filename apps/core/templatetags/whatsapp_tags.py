from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def wa_link(cita):
    from apps.core.models import ConfiguracionClinica
    from apps.core.whatsapp import armar_link_wa, renderizar_plantilla
    cfg = ConfiguracionClinica.cargar()
    pac = cita.expediente.paciente
    tel = (getattr(pac, "telefono", "") or "").strip()
    if not tel:
        return mark_safe('<span class="opacity-40 text-xs" title="Paciente sin teléfono cargado">📲</span>')
    nombre = f"{pac.nombres} {pac.apellidos}".strip()
    try:
        servicio = cita.items.first().servicio.nombre
    except Exception:
        servicio = "su cita"
    msg = renderizar_plantilla(cfg.plantilla_whatsapp, nombre=nombre, clinica=cfg.nombre_clinica,
                               servicio=servicio, fecha=cita.fecha.strftime("%d/%m/%Y"),
                               hora=cita.fecha.strftime("%H:%M"))
    url = armar_link_wa(tel, msg, cfg.wa_prefijo)
    return mark_safe(
        f'<a href="{escape(url)}" target="_blank" rel="noopener" title="Enviar recordatorio a {escape(nombre)}" '
        f'class="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs font-bold">📲 Recordar</a>')
