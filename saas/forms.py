from django import forms
from .models import Clinica


class ClinicaForm(forms.ModelForm):
    class Meta:
        model = Clinica
        fields = ["nombre", "slug", "cliente_nombre", "cliente_email", "cliente_telefono", "notas", "tipo_producto"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "input", "placeholder": "Diente Sano"}),
            "slug": forms.TextInput(attrs={"class": "input", "placeholder": "dientesano"}),
            "cliente_nombre": forms.TextInput(attrs={"class": "input", "placeholder": "Dr. Juan Pérez"}),
            "cliente_email": forms.EmailInput(attrs={"class": "input", "placeholder": "juan@dientesano.com"}),
            "cliente_telefono": forms.TextInput(attrs={"class": "input", "placeholder": "+58 412 1234567"}),
            "notas": forms.Textarea(attrs={"class": "input", "rows": 3}),
        }
