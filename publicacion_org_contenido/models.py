from django.core.validators import (MaxValueValidator, MinLengthValidator, MinValueValidator)
from django.utils import timezone
from djongo import models

class UsuarioEmbebido(models.Model):
    nombreUsuario = models.CharField(max_length=30, validators=[MinLengthValidator(3)])
    imagenPerfil = models.URLField(max_length=500, blank=True, null=True)
 
    class Meta:
        abstract = True
 
class PublicacionResumen(models.Model):
    titulo = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=10)
    archivoUrl = models.URLField(max_length=500)
 
    class Meta:
        abstract = True
 
class CategoriaResumen(models.Model):
    nombre = models.CharField(max_length=60)
    slug = models.CharField(max_length=60)
 
    class Meta:
        abstract = True
 
class ItemColeccion(models.Model):
    orden = models.PositiveIntegerField(validators=[MinValueValidator(1)]
    )
    titulo = models.CharField(max_length=150, blank=True, null=True)
    tipo = models.CharField(max_length=10)
    archivoUrl = models.URLField(max_length=500)
 
    class Meta:
        abstract = True
 
class ResolucionVideo(models.Model):
    calidad = models.CharField(max_length=10)
    url = models.URLField(max_length=500)
 
    class Meta:
        abstract = True
 
class EdicionPublicacion(models.Model):
    tipoEdicion = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=255,blank=True,null=True)
    fecha = models.DateTimeField(default=timezone.now)
 
    class Meta:
        abstract = True
 
class Subcategoria(models.Model):
    nombre = models.CharField(max_length=60)
    slug = models.CharField(max_length=60)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
 
    class Meta:
        abstract = True
 
class FactorRecomendacion(models.Model):
    nombre = models.CharField(max_length=60)
    peso = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
 
    class Meta:
        abstract = True
 
class Publicacion(models.Model):
    _id = models.ObjectIdField()
    autor = models.EmbeddedField(model_container=UsuarioEmbebido)
    tipo = models.CharField(max_length=10)
    titulo = models.CharField(max_length=150, blank=True, null=True)
    descripcion = models.TextField(max_length=2000, blank=True, null=True)
    archivoUrl = models.URLField(max_length=500,unique=True)
    formato = models.CharField(max_length=5)
    tamanioBytes = models.BigIntegerField(validators=[MinValueValidator(1)])
    ancho = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    alto = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    duracionSegundos = models.PositiveIntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    etiquetas = models.JSONField(default=list, blank=True)
    categorias = models.ArrayField(model_container=CategoriaResumen, default=list, blank=True)
    totalReacciones = models.PositiveIntegerField(default=0)
    totalComentarios = models.PositiveIntegerField(default=0)
    resoluciones = models.ArrayField(model_container=ResolucionVideo, default=list, blank=True)
    estado = models.CharField(max_length=10, default="publicado")
    fechaPublicacion = models.DateTimeField(default=timezone.now)
    historialEdiciones = models.ArrayField(model_container=EdicionPublicacion, default=list, blank=True)
 
    class Meta:
        db_table = "publicaciones"
        managed = False
 
    def __str__(self):
        return self.titulo or self.archivoUrl
 
class Coleccion(models.Model):
    _id = models.ObjectIdField()
    creador = models.EmbeddedField(model_container=UsuarioEmbebido)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500, blank=True, null=True)
    tipo = models.CharField(max_length=12, default="personal")
    privacidad = models.CharField(max_length=7, default="publica")
    portadaUrl = models.URLField(max_length=500, blank=True, null=True)
    publicaciones = models.ArrayField(model_container=ItemColeccion, default=list, blank=True)
    colaboradores = models.ArrayField(model_container=UsuarioEmbebido, default=list, blank=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = "colecciones"
        managed = False
 
    def __str__(self):
        return self.nombre
 
class Categoria(models.Model):
    _id = models.ObjectIdField()
    nombre = models.CharField(max_length=60, unique=True)
    descripcion = models.TextField(max_length=300, blank=True, null=True)
    slug = models.CharField(max_length=60,unique=True)
    subcategorias = models.ArrayField(model_container=Subcategoria, default=list, blank=True)
    sinonimos = models.JSONField(default=list, blank=True)
    totalPublicaciones = models.PositiveIntegerField(default=0)
 
    class Meta:
        db_table = "categorias"
        managed = False
 
    def __str__(self):
        return self.nombre
 
class Recomendacion(models.Model):
    _id = models.ObjectIdField()
    usuario = models.EmbeddedField(model_container=UsuarioEmbebido)
    publicacion = models.EmbeddedField(model_container=PublicacionResumen)
    criterio = models.CharField(max_length=10)
    puntuacion = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    fechaGeneracion = models.DateTimeField(auto_now_add=True)
    vista = models.BooleanField(default=False)
    factores = models.ArrayField(model_container=FactorRecomendacion, default=list, blank=True)
 
    class Meta:
        db_table = "recomendaciones"
        managed = False
 
    def __str__(self):
        return f"{self.criterio} ({self.puntuacion:.2f})"
