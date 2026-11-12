from django import forms
from aplicaciones.g_usuarios_perfiles.models import Usuario
from aplicaciones.publicacion_org_contenido.models import Categoria

class FormularioPreferencias(forms.Form):
    categorias = forms.MultipleChoiceField(label='Categorías', required=False)
    etiquetas = forms.CharField(required=False, max_length=929, help_text='Separa las etiquetas con comas.')
    artistas = forms.MultipleChoiceField(required=False)

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.fields['categorias'].choices = [(dato.slug, dato.nombre) for dato in Categoria.objects.order_by('nombre')]
        self.fields['artistas'].choices = [(dato.nombreUsuario, dato.nombreUsuario) for dato in Usuario.objects.filter(activo__in=[True])]

    def clean_etiquetas(self):
        etiquetas = list(dict.fromkeys(dato.strip().lower() for dato in self.cleaned_data['etiquetas'].split(',') if dato.strip()))
        if len(etiquetas) > 30 or any(len(dato) > 30 for dato in etiquetas):
            raise forms.ValidationError('Puedes seleccionar hasta 30 etiquetas de 30 caracteres.')
        return etiquetas
