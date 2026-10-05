from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from djongo import models

class Preferencias(models.Model):

    categorias = models.ArrayField(
        model_container=models.CharField(max_length=50),
        default=list,
        blank=True
    )

    etiquetas = models.ArrayField(
        model_container=models.CharField(max_length=50),
        default=list,
        blank=True
    )

    artistas = models.ArrayField(
        model_container=models.CharField(max_length=100),
        default=list,
        blank=True
    )

    class Meta:
        abstract = True


class Contenido(models.Model):

    titulo = models.CharField(max_length=150)
    imagen = models.URLField(max_length=500)
    categoria = models.CharField(max_length=50)
    autor = models.CharField(max_length=100)

    etiquetas = models.ArrayField(
        model_container=models.CharField(max_length=50),
        default=list,
        blank=True
    )

    class Meta:
        abstract = True



class Recomendacion(models.Model):

    contenido = models.EmbeddedField(model_container=Contenido,default=dict)
    motivo = models.CharField(max_length=255)

    puntuacion = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    class Meta:
        abstract = True


class Tendencia(models.Model):

    contenido = models.EmbeddedField(model_container=Contenido,default=dict)
    posicion = models.IntegerField(validators=[MinValueValidator(1)])

    puntuacion = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)
        ]
    )

    class Meta:
        abstract = True


class Destacado(models.Model):

    contenido = models.EmbeddedField(model_container=Contenido,default=dict)
    motivo = models.CharField(max_length=255)

    puntuacion = models.FloatField(
        validators=[MinValueValidator(0.0),MaxValueValidator(1.0)],
        blank=True, null=True
    )

    class Meta:
        abstract = True


class ContenidoColeccion(models.Model):

    titulo = models.CharField(max_length=150)
    imagen = models.URLField(max_length=500)
    categoria = models.CharField(max_length=50)
    autor = models.CharField(max_length=100)

    class Meta:
        abstract = True


class ColeccionColaborativa(models.Model):

    nombre = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=500)

    contenidos = models.ArrayField(
        model_container=ContenidoColeccion,
        default=list,
        blank=True
    )

    class Meta:
        abstract = True


class ExploracionInspiracion(models.Model):

    _id = models.ObjectIdField()
    preferencias = models.EmbeddedField(model_container=Preferencias,default=dict)
    feed = models.ArrayField(model_container=Recomendacion,default=list,blank=True)
    tendencias = models.ArrayField(model_container=Tendencia,default=list,blank=True)
    destacados = models.ArrayField(model_container=Destacado,default=list,blank=True)
    coleccionesColaborativas = models.ArrayField(model_container=ColeccionColaborativa,default=list,blank=True)
    fechaActualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "exploracion_inspiracion"

    def __str__(self):
        return f"Exploración e Inspiración {self._id}"