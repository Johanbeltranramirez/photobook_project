from django import forms
from django.core.validators import URLValidator
from django.utils import timezone
from g_usuarios_perfiles.models import Usuario
from publicacion_org_contenido.models import Categoria
from .opciones import TIPOS_MENSAJE, TIPOS_GRUPO, AMBITOS_BLOQUEO

class FormularioMensaje(forms.Form):
    receptor = forms.ChoiceField()
    contenido = forms.CharField(max_length=5000, required=False, widget=forms.Textarea)
    tipo = forms.ChoiceField(choices=[(dato, dato.capitalize()) for dato in TIPOS_MENSAJE])
    adjuntos = forms.CharField(required=False, max_length=5009, widget=forms.Textarea, help_text='Enlaces separados por comas.')

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.fields['receptor'].choices = [(dato.nombreUsuario, dato.nombreUsuario) for dato in Usuario.objects.filter(activo__in=[True])]

    def clean_adjuntos(self):
        texto = self.cleaned_data['adjuntos']
        enlaces = [dato.strip() for dato in texto.split(',') if dato.strip()]
        if len(enlaces) > 10:
            raise forms.ValidationError('Se permiten hasta diez archivos adjuntos.')
        for enlace in enlaces:
            URLValidator()(enlace)
            if len(enlace) > 500:
                raise forms.ValidationError('Cada enlace admite hasta 500 caracteres.')
        return texto


class FormularioGrupo(forms.Form):
    nombre = forms.CharField(min_length=3, max_length=80)
    descripcion = forms.CharField(label='Descripción', max_length=1000, required=False, widget=forms.Textarea)
    tipo = forms.ChoiceField(choices=[(dato, dato.capitalize()) for dato in TIPOS_GRUPO])
    imagenUrl = forms.URLField(label='Enlace de la imagen', max_length=500, required=False)
    categoria = forms.ChoiceField(label='Categoría')
    reglas = forms.CharField(max_length=6019, required=False, widget=forms.Textarea, help_text='Una regla por línea.')
    estado = forms.ChoiceField(choices=[('activo', 'Activo'), ('archivado', 'Archivado')])

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.fields['categoria'].choices = [(dato.slug, dato.nombre) for dato in Categoria.objects.order_by('nombre')]


class FormularioBloqueo(forms.Form):
    bloqueado = forms.ChoiceField(label='Usuario que deseas bloquear')
    ambito = forms.ChoiceField(label='Ámbito', choices=[(dato, dato.capitalize()) for dato in AMBITOS_BLOQUEO])
    fechaExpiracion = forms.DateTimeField(label='Expira el', required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), input_formats=['%Y-%m-%dT%H:%M'])

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.fields['bloqueado'].choices = [(dato.nombreUsuario, dato.nombreUsuario) for dato in Usuario.objects.filter(activo__in=[True])]

    def clean_fechaExpiracion(self):
        fecha = self.cleaned_data['fechaExpiracion']
        if fecha and fecha <= timezone.now():
            raise forms.ValidationError('La fecha debe ser futura.')
        return fecha
