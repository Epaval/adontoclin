from django import forms
from .models import Medico


class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = [
            "nombres",
            "apellidos",
            "ci",
            "telefono",
            "email",
            "especialidad",
            "activo",
        ]
        widgets = {
            "nombres": forms.TextInput(attrs={
                "placeholder": "Ej: Alejandro",
            }),
            "apellidos": forms.TextInput(attrs={
                "placeholder": "Ej: Fernández",
            }),
            "ci": forms.TextInput(attrs={
                "placeholder": "V5432109",
            }),
            "telefono": forms.TextInput(attrs={
                "placeholder": "+584147777777",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "dr.fernandez@ejemplo.com",
            }),
            "especialidad": forms.TextInput(attrs={
                "placeholder": "Ej: Cardiología",
            }),
        }
