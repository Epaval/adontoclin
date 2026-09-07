from django import forms
from django.contrib.auth import password_validation

from .models import Empleado, Rol


class ConfigInicialForm(forms.Form):
    nombres = forms.CharField(label="Nombres", max_length=80)
    apellidos = forms.CharField(label="Apellidos", max_length=80)
    nombre_usuario = forms.CharField(label="Usuario", max_length=30)
    email = forms.EmailField(label="Correo electrónico")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput)
    cargar_catalogo = forms.BooleanField(
        required=False,
        initial=True,
        label="Cargar roles y catálogo de exámenes (~150) recomendado",
    )

    def clean_nombre_usuario(self):
        usuario = self.cleaned_data["nombre_usuario"].strip()
        if Empleado.objects.filter(nombre_usuario=usuario).exists():
            raise forms.ValidationError("Ese usuario ya existe")
        return usuario

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        if p2:
            password_validation.validate_password(p2)
        return p2


class EmpleadoCreateForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput)

    class Meta:
        model = Empleado
        fields = ["nombres", "apellidos", "nombre_usuario", "email", "telefono", "rol"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].queryset = Rol.objects.all().order_by("nombre")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        if p2:
            password_validation.validate_password(p2)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmpleadoUpdateForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ["nombres", "apellidos", "nombre_usuario", "email", "telefono", "rol", "is_active"]
        labels = {"is_active": "Usuario activo"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].queryset = Rol.objects.all().order_by("nombre")


class EmpleadoClaveForm(forms.Form):
    password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput)

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        if p2:
            password_validation.validate_password(p2)
        return p2


class RecuperarIdentidadForm(forms.Form):
    nombre_usuario = forms.CharField(label="Usuario", max_length=30)
    email = forms.EmailField(label="Correo electrónico")


class RecuperarClaveForm(forms.Form):
    password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput)

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        if p2:
            password_validation.validate_password(p2)
        return p2
