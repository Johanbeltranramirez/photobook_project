from django.core.exceptions import ValidationError
from django.core.validators import (MaxValueValidator, MinLengthValidator, MinValueValidator)
from django.utils import timezone
from djongo import models



def validar_lista_urls_max10(valor):
    from django.core.validators import URLValidator
    if not isinstance(valor, list):
        raise ValidationError("Debe ser una lista.")
    if len(valor) > 10:
        raise ValidationError("Máximo 10 adjuntos.")
    url_validator = URLValidator()
    for item in valor:
        if not isinstance(item, str):
            raise ValidationError("Cada adjunto debe ser un texto (URL).")
        url_validator(item)


def validar_lista_strings(valor):
    
    if not isinstance(valor, list) or not all(isinstance(v, str) for v in valor):
        raise ValidationError("Debe ser una lista de textos.")



class CategoriaGrupo(models.Model):
    nombre = models.CharField(max_length=60)

    class Meta:
        abstract = True



class Comentario(ComentarioEmbebido):
    _id = models.ObjectIdField()
    publicacionId = models.ObjectIdField()  # La publicación que se está comentando

    class Meta:
        db_table = "comentarios"
        managed = False

    def __str__(self):
        return f"{self.autor.nombreUsuario}: {self.contenido[:40]}"


class Reaccion(ReaccionEmbebida):
    TIPO_ELEMENTO_CHOICES = [
        ("publicacion", "Publicación"),
        ("comentario", "Comentario"),
    ]

    _id = models.ObjectIdField()
    elementoId = models.ObjectIdField()  # Elemento sobre el que se reacciona
    tipoElemento = models.CharField(max_length=11, choices=TIPO_ELEMENTO_CHOICES)

    class Meta:
        db_table = "reacciones"
        managed = False

    def __str__(self):
        return f"{self.tipoReaccion} -> {self.tipoElemento}"



class Mensaje(models.Model):
    TIPO_CHOICES = [
        ("texto", "Texto"),
        ("imagen", "Imagen"),
        ("video", "Video"),
        ("archivo", "Archivo"),
    ]

    _id = models.ObjectIdField()
    emisor = models.EmbeddedField(model_container=UsuarioEmbebido)
    receptor = models.EmbeddedField(model_container=UsuarioEmbebido)
    conversacionId = models.ObjectIdField(blank=True, null=True)
    contenido = models.TextField(validators=[MinLengthValidator(1)])
    tipo = models.CharField(max_length=7, choices=TIPO_CHOICES, default="texto")
    leido = models.BooleanField(default=False)
    adjuntos = models.JSONField(default=list, blank=True, validators=[validar_lista_urls_max10])
    fechaEnvio = models.DateTimeField(default=timezone.now)
    fechaLectura = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "mensajes"
        managed = False

    def clean(self):
        # dependencies: { fechaLectura: ["leido"] }
        if self.fechaLectura and not self.leido:
            raise ValidationError({"fechaLectura": "No puede haber fechaLectura si el mensaje no está leído."})

    def __str__(self):
        return f"{self.emisor.nombreUsuario} -> {self.receptor.nombreUsuario}"


class Grupo(models.Model):
    TIPO_CHOICES = [
        ("publico", "Público"),
        ("privado", "Privado"),
    ]

    _id = models.ObjectIdField()
    nombre = models.CharField(max_length=100, validators=[MinLengthValidator(1)])
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=7, choices=TIPO_CHOICES)
    creador = models.EmbeddedField(model_container=UsuarioEmbebido)
    categoria = models.EmbeddedField(model_container=CategoriaGrupo, blank=True, null=True)
    miembros = models.ArrayField(model_container=UsuarioEmbebido, default=list, blank=True)
    moderadores = models.ArrayField(model_container=UsuarioEmbebido, default=list, blank=True)
    reglas = models.JSONField(default=list, blank=True, validators=[validar_lista_strings])
    fechaCreacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "grupos"
        managed = False

    def clean(self):
        if len(self.miembros or []) > 1000:
            raise ValidationError({"miembros": "Máximo 1000 miembros."})
        if len(self.moderadores or []) > 50:
            raise ValidationError({"moderadores": "Máximo 50 moderadores."})
        # dependencies: { moderadores: ["miembros"] }
        if self.moderadores and not self.miembros:
            raise ValidationError({"moderadores": "No puede haber moderadores si el grupo no tiene miembros."})

    def __str__(self):
        return self.nombre