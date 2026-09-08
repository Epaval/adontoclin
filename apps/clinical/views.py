from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.patients.models import Paciente

from .forms import CitaItemForm
from .models import (
    COLOR_DIENTE,
    DIENTE_NUMS_INFERIOR,
    DIENTE_NUMS_SUPERIOR,
    TIPO_TRATAMIENTO,
    CitaDental,
    ExpedienteDental,
    HistorialDiente,
    CitaItem,
    Receta,
    RecetaMedicamento,
    ServicioDental,
)


class ServicioDentalListView(LoginRequiredMixin, ListView):
    model = ServicioDental
    template_name = "clinical/servicio_list.html"
    context_object_name = "servicios"
    paginate_by = 12


class ExpedienteDentalListView(LoginRequiredMixin, ListView):
    model = ExpedienteDental
    template_name = "clinical/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 10


class ExpedienteDentalCreateView(LoginRequiredMixin, CreateView):
    model = ExpedienteDental
    fields = ["patologias", "alergias", "operaciones", "notas"]
    template_name = "clinical/expediente_form.html"

    def get_initial(self):
        return {"paciente": self.request.GET.get("paciente")}

    def dispatch(self, request, *args, **kwargs):
        self.paciente = get_object_or_404(Paciente, pk=self.kwargs["paciente_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.paciente = self.paciente
        form.instance.creado_por = self.request.user
        messages.success(self.request, "Historia clínica creada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.paciente.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["paciente"] = self.paciente
        ctx["title"] = f"Historia clínica de {self.paciente.full_name}"
        return ctx


class ExpedienteDentalUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpedienteDental
    fields = ["patologias", "alergias", "operaciones", "notas"]
    template_name = "clinical/expediente_form.html"
    extra_context = {"title": "Editar historia clínica"}

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.object.paciente.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["paciente"] = self.object.paciente
        return ctx


class CitaDentalCreateView(LoginRequiredMixin, CreateView):
    model = CitaDental
    fields = ["fecha", "motivo", "notas", "archivo_adjunto", "estado"]
    template_name = "form.html"
    extra_context = {"title": "Nueva cita dental"}

    def dispatch(self, request, *args, **kwargs):
        self.paciente = get_object_or_404(Paciente, pk=self.kwargs["paciente_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        from datetime import datetime, timedelta
        fecha = form.cleaned_data.get("fecha")
        if fecha and fecha < datetime.now():
            messages.error(self.request, "No se pueden agendar citas en fecha pasada.")
            return self.form_invalid(form)
        if fecha:
            solape = CitaDental.objects.filter(
                fecha__gte=fecha - timedelta(minutes=90),
                fecha__lte=fecha + timedelta(minutes=90),
            ).exclude(estado="cancelada").first()
            if solape:
                messages.error(self.request, f"Solape: mínimo 90 min entre citas (hay una a las {solape.fecha:%H:%M} del {solape.fecha:%d/%m}).")
                return self.form_invalid(form)
        expediente, _ = ExpedienteDental.objects.get_or_create(
            paciente=self.paciente,
            defaults={"creado_por": self.request.user},
        )
        form.instance.expediente = expediente
        form.instance.creado_por = self.request.user
        messages.success(self.request, "Cita registrada.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.paciente.pk})


class CitaDentalUpdateView(LoginRequiredMixin, UpdateView):
    model = CitaDental
    fields = ["fecha", "motivo", "notas", "archivo_adjunto", "estado"]
    template_name = "form.html"
    extra_context = {"title": "Editar cita dental"}

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.object.expediente.paciente.pk})


class OdontogramaView(LoginRequiredMixin, TemplateView):
    """Odontograma GENERAL del paciente: hover historial, clic registra en la última cita."""
    template_name = "clinical/odontograma.html"

    def dispatch(self, request, *args, **kwargs):
        self.paciente = get_object_or_404(Paciente, pk=self.kwargs["paciente_id"])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, paciente_id):
        diente = request.POST.get("diente", "")
        tipo = request.POST.get("tipo", "")
        notas = request.POST.get("notas", "").strip()
        expediente, _ = ExpedienteDental.objects.get_or_create(
            paciente=self.paciente, defaults={"creado_por": request.user}
        )
        cita = expediente.citas.order_by("-fecha").first()
        if cita is None:
            cita = CitaDental.objects.create(
                expediente=expediente,
                motivo="Registro de odontograma",
                creado_por=request.user,
            )
        HistorialDiente.objects.create(
            cita=cita, paciente=self.paciente, diente_fdi=diente, tipo=tipo, notas=notas
        )
        messages.success(request, f"Diente {diente}: {dict(TIPO_TRATAMIENTO).get(tipo, tipo)} registrado.")
        return redirect("clinical:odontograma", paciente_id=self.paciente.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        colores, historial = {}, {}
        for h in HistorialDiente.objects.filter(paciente=self.paciente).order_by("-fecha"):
            colores.setdefault(h.diente_fdi, h.color)
            historial.setdefault(h.diente_fdi, []).append({
                "tipo_display": h.get_tipo_display(),
                "fecha": h.fecha.strftime("%d/%m/%Y %H:%M"),
                "notas": h.notas,
                "color": h.color,
            })
        def _arcada(nums, forma):
            """Offset vertical parabólico: arcada superior ∩ e inferior ∪."""
            c = (len(nums) - 1) / 2
            out = []
            for i, num in enumerate(nums):
                d = abs(i - c)
                off = int((d ** 2) * 0.9) if forma == "sup" else int((c ** 2 - d ** 2) * 0.9)
                out.append({"num": num, "off": off})
            return out

        ctx.update({
            "paciente": self.paciente,
            "dientes_superior": _arcada(DIENTE_NUMS_SUPERIOR, "sup"),
            "dientes_inferior": _arcada(DIENTE_NUMS_INFERIOR, "inf"),
            "colores_paciente": colores,
            "historial_paciente": historial,
            "tipos_tratamiento": TIPO_TRATAMIENTO,
            "colores_leyenda": [(l, COLOR_DIENTE[v]) for v, l in TIPO_TRATAMIENTO if v != "otro"],
        })
        return ctx


class CitaItemCreateView(LoginRequiredMixin, CreateView):
    model = CitaItem
    form_class = CitaItemForm
    template_name = "form.html"

    def dispatch(self, request, *args, **kwargs):
        self.cita = get_object_or_404(CitaDental, pk=self.kwargs["cita_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.cita = self.cita
        messages.success(self.request, "Servicio agregado a la cita.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("patients:historial", kwargs={"pk": self.cita.expediente.paciente.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Agregar servicio · Cita #{self.cita.pk} · {self.cita.expediente.paciente.full_name}"
        return ctx


class CitaItemDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(CitaItem, pk=pk)
        paciente_pk = item.cita.expediente.paciente.pk
        item.delete()
        messages.success(request, "Servicio quitado de la cita.")
        return redirect("patients:historial", pk=paciente_pk)


from django.forms import inlineformset_factory
from django.http import HttpResponse

RecetaMedFormSet = inlineformset_factory(
    Receta, RecetaMedicamento,
    fields=["nombre", "dosis", "frecuencia", "duracion", "indicacion"],
    extra=3, can_delete=True,
)


class RecetaCreateView(LoginRequiredMixin, TemplateView):
    template_name = "clinical/receta_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.cita = get_object_or_404(CitaDental, pk=self.kwargs["cita_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("formset", RecetaMedFormSet())
        ctx["cita"] = self.cita
        ctx["paciente"] = self.cita.expediente.paciente
        return ctx

    def post(self, request, *args, **kwargs):
        formset = RecetaMedFormSet(request.POST)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(formset=formset))
        receta = Receta.objects.create(
            cita=self.cita,
            diagnostico=request.POST.get("diagnostico", "").strip(),
            indicaciones_generales=request.POST.get("indicaciones_generales", "").strip(),
            creada_por=request.user,
        )
        formset.instance = receta
        formset.save()
        messages.success(request, f"Receta #{receta.pk} creada.")
        return redirect("patients:historial", pk=self.cita.expediente.paciente.pk)


class RecetaPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        import base64
        import io
        import os

        from django.template.loader import render_to_string
        from xhtml2pdf import pisa

        from apps.core.models import DatosLaboratorio

        receta = get_object_or_404(
            Receta.objects.select_related("cita__expediente__paciente"), pk=pk
        )
        datos = DatosLaboratorio.objects.first()

        def _b64(fieldfile):
            if not fieldfile or not os.path.exists(fieldfile.path):
                return None, None
            ext = fieldfile.name.lower().rsplit(".", 1)[-1]
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}.get(ext, "image/jpeg")
            with open(fieldfile.path, "rb") as f:
                return base64.b64encode(f.read()).decode(), mime

        logo_b64, logo_mime = _b64(datos.logo) if datos else (None, None)
        firma_b64, firma_mime = _b64(datos.firma_imagen) if datos else (None, None)
        sello_b64, sello_mime = _b64(datos.sello_imagen) if datos else (None, None)

        def _prep(fieldfile, max_w, max_h, dw, dh):
            """Recorta bordes vacios y devuelve (b64, mime, w, h) proporcionales."""
            import io as _io
            if not fieldfile or not os.path.exists(fieldfile.path):
                return None, None, dw, dh
            raw = open(fieldfile.path, "rb").read()
            try:
                from PIL import Image
                im = Image.open(_io.BytesIO(raw)).convert("RGBA")
                bbox = im.getbbox()
                if bbox:
                    im = im.crop(bbox)
                buf = _io.BytesIO()
                im.save(buf, "PNG")
                raw = buf.getvalue()
                w, h = im.size
                r = min(max_w / w, max_h / h)
                if r < 1 or w > max_w or h > max_h:
                    pass
                r = min(max_w / w, max_h / h)
                return base64.b64encode(raw).decode(), "image/png", int(w * r), int(h * r)
            except Exception:
                return base64.b64encode(raw).decode(), "image/png", dw, dh

        if datos and datos.firma_imagen:
            firma_b64, firma_mime, firma_w, firma_h = _prep(datos.firma_imagen, 220, 80, 160, 55)
        else:
            firma_w, firma_h = 160, 55
        if datos and datos.sello_imagen:
            sello_b64, sello_mime, sello_w, sello_h = _prep(datos.sello_imagen, 150, 150, 110, 110)
        else:
            sello_w, sello_h = 110, 110

        html = render_to_string("reports/receta.html", {
            "receta": receta,
            "paciente": receta.cita.expediente.paciente,
            "cita": receta.cita,
            "datos": datos,
            "medicamentos": receta.medicamentos.all(),
            "logo_b64": logo_b64, "logo_mime": logo_mime,
            "firma_b64": firma_b64, "firma_mime": firma_mime,
            "sello_b64": sello_b64, "sello_mime": sello_mime,
            "firma_w": firma_w, "firma_h": firma_h,
            "sello_w": sello_w, "sello_h": sello_h,
        })
        pdf = io.BytesIO()
        pisa.CreatePDF(io.StringIO(html), dest=pdf)
        response = HttpResponse(pdf.getvalue(), content_type="application/pdf")
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Content-Disposition"] = f'inline; filename="receta_{receta.pk}.pdf"'
        return response


class RecetaUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "clinical/receta_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.receta = get_object_or_404(Receta, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("formset", RecetaMedFormSet(instance=self.receta))
        ctx["receta"] = self.receta
        ctx["cita"] = self.receta.cita
        ctx["paciente"] = self.receta.cita.expediente.paciente
        return ctx

    def post(self, request, *args, **kwargs):
        formset = RecetaMedFormSet(request.POST, instance=self.receta)
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(formset=formset))
        self.receta.diagnostico = request.POST.get("diagnostico", "").strip()
        self.receta.indicaciones_generales = request.POST.get("indicaciones_generales", "").strip()
        self.receta.save()
        formset.save()
        messages.success(request, f"Receta #{self.receta.pk} actualizada.")
        return redirect("patients:historial", pk=self.receta.cita.expediente.paciente.pk)


class ServicioDentalCreateView(LoginRequiredMixin, CreateView):
    model = ServicioDental
    fields = ["codigo", "nombre", "descripcion", "precio_usd", "activo"]
    template_name = "form.html"
    success_url = reverse_lazy("clinical:servicio_list")
    extra_context = {"title": "Nuevo servicio dental"}


class ServicioDentalUpdateView(LoginRequiredMixin, UpdateView):
    model = ServicioDental
    fields = ["codigo", "nombre", "descripcion", "precio_usd", "activo"]
    template_name = "form.html"
    success_url = reverse_lazy("clinical:servicio_list")
    extra_context = {"title": "Editar servicio dental"}


class AgendaView(LoginRequiredMixin, TemplateView):
    """Calendario mensual de citas (100% offline: reloj del servidor)."""
    template_name = "clinical/agenda.html"

    def get(self, request, *args, **kwargs):
        fecha_ir = request.GET.get("fecha_ir", "")
        if fecha_ir:
            from datetime import date as _d
            try:
                f = _d.fromisoformat(fecha_ir)
                return redirect(f"/clinical/agenda/?mes={f.year}-{f.month:02d}&dia={f.day}")
            except Exception:
                pass
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        import calendar as cal
        from datetime import date, datetime

        ctx = super().get_context_data(**kwargs)
        hoy = date.today()
        try:
            y, m = map(int, self.request.GET.get("mes", "").split("-"))
        except Exception:
            y, m = hoy.year, hoy.month
        _, ndias = cal.monthrange(y, m)
        offset = date(y, m, 1).weekday()

        citas = (
            CitaDental.objects.filter(fecha__year=y, fecha__month=m)
            .select_related("expediente__paciente")
            .order_by("fecha")
        )
        por_dia = {}
        for c in citas:
            por_dia.setdefault(c.fecha.day, []).append(c)

        celdas = [None] * offset + list(range(1, ndias + 1))
        while len(celdas) % 7:
            celdas.append(None)
        semanas = [celdas[i:i + 7] for i in range(0, len(celdas), 7)]

        pm = m - 1 or 12
        py = y if m > 1 else y - 1
        nm = m + 1 if m < 12 else 1
        ny = y if m < 12 else y + 1
        dia_sel = None
        citas_dia = []
        try:
            dia_sel = int(self.request.GET.get("dia", ""))
            citas_dia = por_dia.get(dia_sel, [])
        except Exception:
            dia_sel = None
        if (y, m) < (hoy.year, hoy.month):
            dias_pasados = set(range(1, ndias + 1))
        elif (y, m) == (hoy.year, hoy.month):
            dias_pasados = set(range(1, hoy.day))
        else:
            dias_pasados = set()
        ctx.update({
            "dias_pasados": dias_pasados,
            "dia_sel": dia_sel, "citas_dia": citas_dia,
            "semanas": semanas, "por_dia": por_dia,
            "mes_nombre": f"{['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][m-1]} {y}",
            "mes_actual": f"{y}-{m:02d}",
            "mes_prev": f"{py}-{pm:02d}", "mes_next": f"{ny}-{nm:02d}",
            "hoy": hoy,
            "ahora": datetime.now(),
            "resumen": {
                "total": citas.count(),
                "programadas": citas.filter(estado="programada").count(),
                "atendidas": citas.filter(estado="atendida").count(),
                "ausentes": citas.filter(estado="ausente").count(),
            },
        })
        return ctx


class CitaNuevaView(LoginRequiredMixin, TemplateView):
    """Nueva cita desde agenda: buscador de paciente + control de solapes."""
    template_name = "clinical/cita_nueva.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from datetime import datetime as _dt
        ctx["fecha_ini"] = self.request.GET.get("fecha", "")
        ctx["fecha_min"] = _dt.now().strftime("%Y-%m-%dT%H:%M")
        return ctx

    def post(self, request):
        from datetime import datetime, timedelta

        paciente_pk = request.POST.get("paciente")
        fecha_str = request.POST.get("fecha", "")
        motivo = request.POST.get("motivo", "").strip()
        estado = request.POST.get("estado", "programada")
        paciente = get_object_or_404(Paciente, pk=paciente_pk) if paciente_pk else None
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M")
        except Exception:
            fecha = None
        if paciente is None or fecha is None:
            messages.error(request, "Seleccione paciente y fecha/hora válidos.")
            return redirect("clinical:agenda")
        if fecha < datetime.now():
            messages.error(request, "No se pueden agendar citas en fecha pasada.")
            return redirect("clinical:agenda")
        solape = CitaDental.objects.filter(
            fecha__gte=fecha - timedelta(minutes=90),
            fecha__lte=fecha + timedelta(minutes=90),
        ).exclude(estado="cancelada").first()
        if solape:
            messages.error(
                request,
                f"Solape: debe haber al menos 90 min entre citas. Ya hay una a las {solape.fecha:%H:%M} del {solape.fecha:%d/%m} de {solape.expediente.paciente.full_name}.",
            )
            return redirect("clinical:agenda")
        expediente, _ = ExpedienteDental.objects.get_or_create(
            paciente=paciente, defaults={"creado_por": request.user}
        )
        CitaDental.objects.create(
            expediente=expediente, fecha=fecha, motivo=motivo,
            estado=estado, creado_por=request.user,
        )
        messages.success(request, f"Cita de {paciente.full_name} agendada {fecha:%d/%m %H:%M}.")
        return redirect("clinical:agenda")


class CitaAnularView(LoginRequiredMixin, View):
    def post(self, request, pk):
        cita = get_object_or_404(CitaDental, pk=pk)
        paciente_pk = cita.expediente.paciente.pk
        cita.estado = "cancelada"
        cita.save(update_fields=["estado"])
        messages.success(request, f"Cita #{cita.pk} anulada.")
        return redirect(request.META.get("HTTP_REFERER") or reverse_lazy("patients:historial", kwargs={"pk": paciente_pk}))
