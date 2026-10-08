from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone



class ContextoComentario(models.Model):
    tipo = models.CharField(max_length=10)
    publicacionUrl = models.URLField(max_length=500, blank=True, null=True)
    grupoId = models.ObjectIdField(blank=True, null=True)
    foroId = models.ObjectIdField(blank=True, null=True)

    class Meta:
        abstract = True

class MiembroGrupo(models.Model):
    nombreUsuario = models.CharField(max_length=30, validators=[MinLengthValidator(3)])
    imagenPerfil = models.URLField(max_length=500, blank=True, null=True)
    rol = models.CharField(max_length=10, default="miembro")
    fechaIngreso = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

class ForoGrupo(models.Model):
    _id = models.ObjectIdField()
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    fechaCreacion = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

class ObjetivoReporte(models.Model):
    publicacionUrl = models.URLField(max_length=500, blank=True, null=True)
    comentarioId = models.ObjectIdField(blank=True, null=True)
    mensajeId = models.ObjectIdField(blank=True, null=True)
    grupoId = models.ObjectIdField(blank=True, null=True)
    nombreUsuario = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        abstract = True


class Comentario(models.Model):
    _id = models.ObjectIdField()
    autor = models.EmbeddedField(model_container=UsuarioEmbebido)
    contexto = models.EmbeddedField(model_container=ContextoComentario)
    titulo = models.CharField(max_length=150, blank=True, null=True)
    comentarioPadreId = models.ObjectIdField(blank=True, null=True)
    contenido = models.TextField(max_length=5000)
    formato = models.CharField(max_length=10, default="texto")
    menciones = models.JSONField(default=list, blank=True)
    archivosAdjuntos = models.JSONField(default=list, blank=True)
    reacciones = models.ArrayField(model_container=ReaccionEmbebida, default=list, blank=True)
    totalReacciones = models.PositiveIntegerField(default=0)
    totalRespuestas = models.PositiveIntegerField(default=0)
    fijado = models.BooleanField(default=False)
    cerrado = models.BooleanField(default=False)
    estado = models.CharField(max_length=10, default="activo")
    fechaCreacion = models.DateTimeField(default=timezone.now)
    fechaEdicion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "comentarios"
        managed = False

    def __str__(self):
        return self.titulo or self.contenido[:50]

class Mensaje(models.Model):
    _id = models.ObjectIdField()
    emisor = models.EmbeddedField(model_container=UsuarioEmbebido)
    receptor = models.EmbeddedField(model_container=UsuarioEmbebido)
    contenido = models.TextField(max_length=5000, blank=True, null=True)
    tipo = models.CharField(max_length=10, default="texto")
    adjuntos = models.JSONField(default=list, blank=True)
    reacciones = models.ArrayField(model_container=ReaccionEmbebida, default=list, blank=True)
    leido = models.BooleanField(default=False)
    fechaLectura = models.DateTimeField(blank=True, null=True)
    eliminadoPor = models.JSONField(default=list, blank=True)
    fechaEnvio = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "mensajes"
        managed = False

    def __str__(self):
        return f"{self.emisor.nombreUsuario} -> {self.receptor.nombreUsuario}"

class Grupo(models.Model):
    _id = models.ObjectIdField()
    nombre = models.CharField(max_length=80, validators=[MinLengthValidator(3)])
    descripcion = models.TextField(max_length=1000, blank=True, null=True)
    tipo = models.CharField(max_length=10, default="publico")
    imagenUrl = models.URLField(max_length=500, blank=True, null=True)
    creador = models.EmbeddedField(model_container=UsuarioEmbebido)
    categoria = models.EmbeddedField(model_container=CategoriaResumen)
    miembros = models.ArrayField(model_container=MiembroGrupo, default=list, blank=True)
    foros = models.ArrayField(model_container=ForoGrupo, default=list, blank=True)
    reglas = models.JSONField(default=list, blank=True)
    estado = models.CharField(max_length=10, default="activo")
    totalMiembros = models.PositiveIntegerField(default=0)
    fechaCreacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "grupos"
        managed = False

    def __str__(self):
        return self.nombre

class Moderacion(models.Model):
    _id = models.ObjectIdField()
    tipo = models.CharField(max_length=10)

    
    reportante = models.EmbeddedField(model_container=UsuarioEmbebido, blank=True, null=True)
    tipoElemento = models.CharField(max_length=12, blank=True, null=True)
    objetivo = models.EmbeddedField(model_container=ObjetivoReporte, blank=True, null=True)
    motivo = models.CharField(max_length=25, blank=True, null=True)
    descripcion = models.TextField(max_length=1000, blank=True, null=True)
    estado = models.CharField(max_length=12, blank=True, null=True)
    moderador = models.EmbeddedField(model_container=UsuarioEmbebido, blank=True, null=True)
    accionTomada = models.CharField(max_length=20, blank=True, null=True)
    fechaResolucion = models.DateTimeField(blank=True, null=True)

    # Campos de bloqueo
    bloqueador = models.EmbeddedField(model_container=UsuarioEmbebido, blank=True, null=True)
    bloqueado = models.EmbeddedField(model_container=UsuarioEmbebido, blank=True, null=True)
    ambito = models.CharField(max_length=10, blank=True, null=True)
    grupoId = models.ObjectIdField(blank=True, null=True)
    fechaExpiracion = models.DateTimeField(blank=True, null=True)

    fechaCreacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "moderacion"
        managed = False

    def __str__(self):
        return f"{self.tipo} ({self.estado or self.ambito})"