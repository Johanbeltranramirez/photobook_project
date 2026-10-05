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
    inicioSeg = models.DateTimeField()

    class Meta:
        abstract = True

class Seguidor(models.Model):

    usuario = models.CharField(max_length=30)
    inicioSeg = models.DateTimeField()

    class Meta:
        abstract = True

class Usuario(models.Model):

    nombreUsuario = models.CharField(max_length=30, validators=[MinLengthValidator(3)])
    correo = models.EmailField(max_length=120,unique=True)
    contrasena = models.CharField(max_length=255)
    imagenPerfil = models.URLField(max_length=500,blank=True,null=True)
    biografia = models.CharField(max_length=255,blank=True,null=True)
    rol = models.CharField(max_length=10,choices=[
        ("artista","Artista"),("administrador","Administrador")])


    privacidad = models.EmbeddedField( model_container=Privacidad, default=dict)
    siguiendo = models.ArrayField( model_container=Seguido,default=list, blank=True)
    seguidores = models.ArrayField( model_container=Seguidor,default=list, blank=True)

    creacionCuenta = models.DateTimeField(auto_now_add=True)
    fechaActualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "usuarios"

    def _str_(self):
        return self.nombreUsuario

class Notificacion(models.Model):
    _id = models.ObjectIdField()

    usuarioNotificado = models.CharField(max_length=24)
    usuarioOrigen = models.CharField(max_length=24,blank=True,null=True)

    tipo = models.CharField(
        max_Length=15,
        choice=[("seguir","Seguir"), ("meGusta","Me gusta"),
                ("comentario","Comentario"), ("mensaje","Mensaje"), ("sistema","Sistema") ])

    mensaje = models.CharField(max_length=255)
    notificacionLeer = models.BooleanField(default=False)
    fechaCreacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notificaciones"
        managed = False
        indexes = [
            models.Index(fields=["usuarioNotificado", "notificacionLee", "fechaCreacion",]),
        ]

    def _str_(self):
        return f"{self.tipo} {self.usuarioNotificado}"
