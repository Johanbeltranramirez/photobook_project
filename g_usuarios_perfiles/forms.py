from django import forms
from .models import Usuario

NOMBRES_RESERVADOS = ('registro', 'ingresar', 'salir', 'notificaciones', 'olvido', 'restablecer', 'correo')

class FormularioRegistro(forms.Form):
    nombreUsuario = forms.RegexField(r'^[a-zA-Z0-9_]{3,30}$', label='Nombre de usuario', max_length=30)
    correo = forms.EmailField(max_length=120)
    contrasena = forms.CharField(label='Contraseña', min_length=8, max_length=128, widget=forms.PasswordInput)
    confirmacion = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    def clean_nombreUsuario(self):
        nombre = self.cleaned_data['nombreUsuario'].lower()
        if nombre in NOMBRES_RESERVADOS:
            raise forms.ValidationError('Ese nombre de usuario está reservado.')
        if Usuario.objects.filter(nombreUsuario=nombre).exists():
            raise forms.ValidationError('Este nombre de usuario ya está registrado.')
        return nombre

    def clean_correo(self):
        correo = self.cleaned_data['correo'].lower()
        if Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError('Este correo ya está registrado.')
        return correo

    def clean(self):
        datos = super().clean()
        if datos.get('contrasena') != datos.get('confirmacion'):
            self.add_error('confirmacion', 'Las contraseñas no coinciden.')
        return datos


class FormularioIngreso(forms.Form):
    nombreUsuario = forms.CharField(label='Nombre de usuario', max_length=30)
    contrasena = forms.CharField(label='Contraseña', max_length=128, widget=forms.PasswordInput)


class FormularioPerfil(forms.Form):
    imagenPerfil = forms.URLField(label='Enlace de la imagen', max_length=500, required=False)
    biografia = forms.CharField(label='Biografía', max_length=255, required=False, widget=forms.Textarea)
    perfilPublico = forms.BooleanField(label='Perfil público', required=False)
    correoVisible = forms.BooleanField(label='Mostrar correo', required=False)



class FormularioOlvido(forms.Form):
    correo = forms.EmailField(label='Correo electrónico', max_length=120, widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'tucorreo@ejemplo.com'}))

    def clean_correo(self):
        return self.cleaned_data['correo'].strip().lower()


class FormularioNuevaContrasena(forms.Form):
    contrasena = forms.CharField(label='Nueva contraseña', min_length=8, max_length=128, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    confirmacion = forms.CharField(label='Confirmar contraseña', max_length=128, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    def clean(self):
        datos = super().clean()
        if datos.get('contrasena') and datos.get('contrasena') != datos.get('confirmacion'):
            self.add_error('confirmacion', 'Las contraseñas no coinciden.')
        return datos


class FormularioPreferenciasCorreo(forms.Form):
    seguidores = forms.BooleanField(required=False)
    comentarios = forms.BooleanField(required=False)
    reacciones = forms.BooleanField(required=False)
    mensajes = forms.BooleanField(required=False)
    avisos = forms.BooleanField(required=False)
