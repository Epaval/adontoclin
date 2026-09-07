from django import forms

from apps.doctors.models import Medico


from .models import Paciente


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            "nombres", "apellidos", "ci", "direccion",
            "telefono", "email", "sexo", "fecha_nac", "representante",
        ]
        widgets = {
            "nombres": forms.TextInput(attrs={"placeholder": "Ej: María"}),
            "apellidos": forms.TextInput(attrs={"placeholder": "Ej: González"}),
            "ci": forms.TextInput(attrs={"placeholder": "Ej: V12345678"}),
            "direccion": forms.Textarea(attrs={"rows": 2, "placeholder": "Dirección completa"}),
            "telefono": forms.TextInput(attrs={"placeholder": "+584141234567"}),
            "representante": forms.HiddenInput(),
            "email": forms.EmailInput(attrs={"placeholder": "email@ejemplo.com"}),
            "fecha_nac": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        fnac = cleaned.get("fecha_nac")
        rep = cleaned.get("representante")
        telefono = cleaned.get("telefono")
        if fnac:
            from datetime import date
            hoy = date.today()
            edad = hoy.year - fnac.year - ((hoy.month, hoy.day) < (fnac.month, fnac.day))
            if 9 <= edad < 18 and not cleaned.get("ci"):
                self.add_error("ci", "Obligatorio entre 9 y 17 años.")
            if edad < 18:
                if not rep:
                    self.add_error("representante", "Obligatorio para menores de edad.")
                else:
                    # Menor: siempre usa telefono y direccion del representante
                    cleaned["telefono"] = None
                    if rep and not cleaned.get("direccion"):
                        cleaned["direccion"] = rep.direccion
            if edad >= 18 and not telefono:
                self.add_error("telefono", "El telefono es obligatorio.")
        return cleaned

    def clean_fecha_nac(self):
        from django.utils import timezone

        fecha = self.cleaned_data.get("fecha_nac")
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura")
        return fecha

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["telefono"].required = False
        self.fields["email"].required = False
        from datetime import date
        hoy = date.today()
        adultos = [p.pk for p in Paciente.objects.all()
                   if p.fecha_nac and (hoy.year - p.fecha_nac.year - ((hoy.month, hoy.day) < (p.fecha_nac.month, p.fecha_nac.day))) >= 18]
        self.fields["representante"].queryset = Paciente.objects.filter(pk__in=adultos)
        # En edición, la fecha de nacimiento es inmutable (solo lectura)
        if self.instance and self.instance.pk:
            self.fields["fecha_nac"].widget = forms.DateInput(
                attrs={
                    "readonly": True,
                    "class": "bg-slate-100 cursor-not-allowed",
                },
                format="%d/%m/%Y",
            )
            self.fields["fecha_nac"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]
            self.fields["fecha_nac"].help_text = "La fecha de nacimiento no se puede modificar"


