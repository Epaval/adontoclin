from django import forms

from .models import CostoExamen, Examen


class ExamenForm(forms.ModelForm):
    # Campo extra (no del modelo): el laboratorio define su precio
    precio = forms.DecimalField(
        label="Precio",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            "step": "0.01",
            "placeholder": "0.00",
        }),
        help_text="Precio que cobra el laboratorio por este examen",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["perfil"].widget.attrs.update({
            "list": "perfiles-datalist",
            "placeholder": "Ej: Hematologia, perfil15, perfil20...",
        })

    class Meta:
        model = Examen
        fields = [
            "nombre_completo",
            "valores_ref",
            "perfil",
            "tipo_resultado",
            "activo",
        ]
        widgets = {
            "tipo_resultado": forms.Select(attrs={
                "class": "w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 outline-none",
            }),
            "nombre_completo": forms.TextInput(attrs={
                "placeholder": "Ej: Hematología completa",
            }),
            "valores_ref": forms.TextInput(attrs={
                "placeholder": "Valores de referencia...",
            }),
            "perfil": forms.TextInput(attrs={
                "placeholder": "Ej: Hematología",
            }),
        }

    field_order = ["nombre_completo", "perfil", "valores_ref", "precio", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Al editar, mostrar el precio activo actual
        if self.instance and self.instance.pk:
            costo = self.instance.costos.filter(activo=True).first()
            if costo:
                self.initial["precio"] = costo.precio

    def save(self, commit=True):
        examen = super().save(commit=commit)
        precio = self.cleaned_data.get("precio")
        if precio is None:
            precio = 0

        if commit:
            costo = examen.costos.filter(activo=True).first()
            if costo:
                costo.precio = precio
                costo.save(update_fields=["precio"])
            else:
                CostoExamen.objects.create(
                    examen=examen, precio=precio, activo=True
                )
        return examen
