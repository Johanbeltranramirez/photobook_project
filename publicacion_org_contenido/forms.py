from django import forms
from .models import Categoria, Publicacion
from .opciones import TIPOS, FORMATOS, ESTADOS, TIPOS_COLECCION, PRIVACIDADES, CRITERIOS
from g_usuarios_perfiles.models import Usuario

class FormularioCategoria(forms.Form):
    nombre = forms.CharField(max_length=60)
    descripcion = forms.CharField(label='Descripción', max_length=300, required=False, widget=forms.Textarea)


class FormularioPublicacion(forms.Form):
    titulo = forms.CharField(label='Título', max_length=150)
    descripcion = forms.CharField(label='Descripción', max_length=2000, required=False, widget=forms.Textarea)
    tipo = forms.ChoiceField(choices=[(dato, dato.capitalize()) for dato in TIPOS])
    archivoUrl = forms.URLField(label='Enlace del archivo', max_length=500)
    formato = forms.ChoiceField(choices=[(dato, dato) for dato in FORMATOS])
    tamanioBytes = forms.IntegerField(label='Tamaño en bytes', min_value=1)
    ancho = forms.IntegerField(min_value=1, required=False)
    alto = forms.IntegerField(min_value=1, required=False)
    duracionSegundos = forms.IntegerField(label='Duración en segundos', min_value=1, required=False)
    etiquetas = forms.CharField(max_length=929, required=False, help_text='Separa las etiquetas con comas.')
    categorias = forms.MultipleChoiceField(label='Categorías', required=False)
    estado = forms.ChoiceField(choices=[(dato, dato.capitalize()) for dato in ESTADOS])

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.fields['categorias'].choices = [(dato.slug, dato.nombre) for dato in Categoria.objects.order_by('nombre')]

    def clean(self):
        datos = super().clean()
        formato = datos.get('formato')
        if datos.get('tipo') == 'imagen' and formato not in ('jpg', 'jpeg', 'png', 'gif'):
            self.add_error('formato', 'Selecciona un formato de imagen.')
        if datos.get('tipo') == 'video':
            if formato not in ('mp4', 'mov', 'webm'):
                self.add_error('formato', 'Selecciona un formato de video.')
            if not datos.get('duracionSegundos'):
                self.add_error('duracionSegundos', 'Indica la duración del video.')
        return datos


class FormularioColeccion(forms.Form):
    nombre = forms.CharField(max_length=100)
    descripcion = forms.CharField(label='Descripción', max_length=500, required=False, widget=forms.Textarea)
    tipo = forms.ChoiceField(choices=[(dato, dato.capitalize()) for dato in TIPOS_COLECCION])
    privacidad = forms.ChoiceField(choices=[(dato, dato.capitalize()) for dato in PRIVACIDADES])


class FormularioRecomendacion(forms.Form):
    usuario = forms.ChoiceField()
    archivoUrl = forms.ChoiceField(label='Publicación')
    criterio = forms.ChoiceField(label='Criterio', choices=[(dato, dato.capitalize()) for dato in CRITERIOS])
    puntuacion = forms.FloatField(label='Puntuación', min_value=0, max_value=1)
    vista = forms.BooleanField(required=False)

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.fields['usuario'].choices = [(dato.nombreUsuario, dato.nombreUsuario) for dato in Usuario.objects.filter(activo__in=[True])]
        self.fields['archivoUrl'].choices = [(dato.archivoUrl, dato.titulo or dato.archivoUrl) for dato in Publicacion.objects.filter(estado='publicado')]
