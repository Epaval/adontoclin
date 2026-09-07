from django import forms

from .models import CitaItem


class CitaItemForm(forms.ModelForm):
    class Meta:
        model = CitaItem
        fields = ["servicio", "diente_fdi", "cantidad"]
        widgets = {
            "servicio": forms.Select(attrs={"class": "w-full"}),
            "diente_fdi": forms.Select(attrs={"class": "w-full"}),
            "cantidad": forms.NumberInput(attrs={"min": 1, "value": 1}),
        }
