from django import forms
from .models import Resultado


class ResultadoForm(forms.ModelForm):
    class Meta:
        model = Resultado
        fields = [
            "tipo_resultado",
            "valor_numerico",
            "unidad",
            "valor_cualitativo",
            "observaciones",
        ]
        widgets = {
            "tipo_resultado": forms.Select(attrs={
                "class": "w-full",
                "id": "tipo-resultado-select",
            }),
            "valor_numerico": forms.NumberInput(attrs={
                "step": "0.01",
                "placeholder": "Ej: 12.5",
                "class": "w-full",
            }),
            "unidad": forms.TextInput(attrs={
                "placeholder": "Ej: mg/dL",
                "class": "w-full",
            }),
            "valor_cualitativo": forms.Select(attrs={
                "class": "w-full",
            }, choices=[
                ("", "---------"),
                ("Positivo", "Positivo"),
                ("Negativo", "Negativo"),
                ("Reactivo", "Reactivo"),
                ("No reactivo", "No reactivo"),
                ("Normal", "Normal"),
                ("Anormal", "Anormal"),
            ]),
            "observaciones": forms.Textarea(attrs={
                "rows": 2,
                "placeholder": "Notas adicionales (opcional)",
                "class": "w-full",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo_resultado")

        if tipo == "numerico":
            valor = cleaned_data.get("valor_numerico")
            if valor is None:
                self.add_error("valor_numerico", "El valor numérico es obligatorio")
        elif tipo == "cualitativo":
            valor = cleaned_data.get("valor_cualitativo")
            if not valor:
                self.add_error("valor_cualitativo", "El resultado cualitativo es obligatorio")

        return cleaned_data
