from photobook.campos import FechaDocumento
from django.core.validators import  MinLengthValidator
from django.utils import timezone
from djongo import models

class Privacidad(models.Model):

    perfilPublico = models.BooleanField(default=True)
    correoVisible = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Seguido(models.Model):

    usuario = models.CharField(max_length=30)
    inicioSeg = FechaDocumento()

    class Meta:
        abstract = True

class Seguidor(models.Model):

    usuario = models.CharField(max_length=30)
    inicioSeg = FechaDocumento()

    class Meta:
        abstract = True

class Usuario(models.Model):
    _id = models.ObjectIdField()
    activo = models.BooleanField(default=True)

    nombreUsuario = models.CharField(max_length=30, unique=True, validators=[MinLengthValidator(3)])
    correo = models.EmailField(max_length=120,unique=True)
    contrasena = models.CharField(max_length=255)
    imagenPerfil = models.URLField(max_length=500,blank=True,null=True)
    biografia = models.CharField(max_length=255,blank=True,null=True)
    rol = models.CharField(max_length=50, default="artista")


    privacidad = models.EmbeddedField( model_container=Privacidad, default=dict)
    siguiendo = models.ArrayField( model_container=Seguido,default=list, blank=True)
    seguidores = models.ArrayField( model_container=Seguidor,default=list, blank=True)

    creacionCuenta = models.DateTimeField(auto_now_add=True)
    fechaActualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "usuarios"
        managed = False

    def __str__(self):
        return self.nombreUsuario

class Notificacion(models.Model):
    _id = models.ObjectIdField()

    usuarioNotificado = models.CharField(max_length=30)
    usuarioOrigen = models.CharField(max_length=30,blank=True,null=True)

    tipo = models.CharField(
        max_length=15,
        choices=[("seguir","Seguir"), ("meGusta","Me gusta"),
                ("comentario","Comentario"), ("mensaje","Mensaje"), ("sistema","Sistema") ])

    mensaje = models.CharField(max_length=255)
    notificacionLeer = models.BooleanField(default=False)
    fechaCreacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notificaciones"
        managed = False
        indexes = [
            models.Index(fields=["usuarioNotificado", "notificacionLeer", "fechaCreacion",]),
        ]

    def __str__(self):
        return f"{self.tipo} {self.usuarioNotificado}"

class PreferenciaCorreo(models.Model):
    _id = models.ObjectIdField()

    usuario = models.CharField(max_length=30, unique=True)
    seguidores = models.BooleanField(default=True)
    comentarios = models.BooleanField(default=True)
    reacciones = models.BooleanField(default=True)
    mensajes = models.BooleanField(default=True)
    avisos = models.BooleanField(default=True)
    fechaActualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "preferenciasCorreo"
        managed = False

    def __str__(self):
        return f"Preferencias de correo de {self.usuario}"
