from django import forms
from .archivos import analizar_archivo
from .models import Categoria, Publicacion
from .opciones import CRITERIOS
from g_usuarios_perfiles.models import Usuario

TIPOS_ARCHIVO_ACEPTADOS = 'image/jpeg,image/png,image/gif,video/mp4,video/quicktime,video/webm'


class Deslizador(forms.NumberInput):
    input_type = 'range'


class FormularioCategoria(forms.Form):
    nombre = forms.CharField(max_length=60, widget=forms.TextInput(attrs={'placeholder': 'Ej: Fotografía urbana'}))
    descripcion = forms.CharField(label='Descripción', max_length=300, required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'De qué trata esta categoría'}))


class FormularioPublicacion(forms.Form):
    archivo = forms.FileField(label='Imagen o video', widget=forms.FileInput(attrs={'accept': TIPOS_ARCHIVO_ACEPTADOS}))
    titulo = forms.CharField(label='Título', max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Dale un título a tu publicación'}))
    descripcion = forms.CharField(label='Descripción', max_length=2000, required=False, widget=forms.Textarea(attrs={'rows': 4, 'maxlength': 2000, 'data-contador': 'contador_descripcion', 'placeholder': 'Cuenta algo sobre lo que compartes'}))
    etiquetas = forms.CharField(max_length=929, required=False, help_text='Sepáralas con comas, por ejemplo: paisaje, viaje, montaña.', widget=forms.TextInput(attrs={'placeholder': 'paisaje, viaje, montaña'}))
    categorias = forms.MultipleChoiceField(label='Categorías', required=False, widget=forms.CheckboxSelectMultiple)
    ancho = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput)
    alto = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput)
    duracionSegundos = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput)

    def __init__(self, *argumentos, archivo_obligatorio=True, **opciones):
        super().__init__(*argumentos, **opciones)
        self.info_archivo = None
        self.fields['archivo'].required = archivo_obligatorio
        self.fields['categorias'].choices = [(dato.slug, dato.nombre) for dato in Categoria.objects.order_by('nombre')]

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            self.info_archivo = analizar_archivo(archivo)
        return archivo

    def clean(self):
        datos = super().clean()
        info = self.info_archivo
        if info and info['tipo'] == 'video':
            info['ancho'] = datos.get('ancho')
            info['alto'] = datos.get('alto')
            if not info['duracionSegundos']:
                info['duracionSegundos'] = datos.get('duracionSegundos')
            if not info['duracionSegundos']:
                self.add_error('archivo', 'No pudimos leer la duración del video. Prueba con otro archivo.')
        return datos


class FormularioColeccion(forms.Form):
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Ej: Inspiración para mis viajes'}))
    descripcion = forms.CharField(label='Descripción', max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Para qué sirve esta colección'}))
    tipo = forms.ChoiceField(label='¿Quién puede agregar contenido?', choices=[('personal', 'Personal'), ('colaborativa', 'Colaborativa')], initial='personal', widget=forms.RadioSelect)
    privacidad = forms.ChoiceField(label='¿Quién puede verla?', choices=[('publica', 'Pública'), ('privada', 'Privada')], initial='publica', widget=forms.RadioSelect)


class FormularioRecomendacion(forms.Form):
    usuario = forms.ChoiceField(label='Recomendar a')
    archivoUrl = forms.ChoiceField(label='Publicación recomendada')
    criterio = forms.ChoiceField(label='Motivo de la recomendación', choices=[(dato, dato.capitalize()) for dato in CRITERIOS])
    puntuacion = forms.FloatField(label='Afinidad', min_value=0, max_value=1, initial=0.5, widget=Deslizador(attrs={'min': 0, 'max': 1, 'step': 0.01}))

    def __init__(self, *argumentos, **opciones):
        super().__init__(*argumentos, **opciones)
        self.fields['usuario'].choices = [(dato.nombreUsuario, dato.nombreUsuario) for dato in Usuario.objects.filter(activo__in=[True])]
        self.fields['archivoUrl'].choices = [(dato.archivoUrl, dato.titulo or 'Sin título') for dato in Publicacion.objects.filter(estado='publicado')]
