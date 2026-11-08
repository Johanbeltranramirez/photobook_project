from django.utils import timezone
from djongo import models
from publicacion_org_contenido.models import UsuarioEmbebido

class Preferencias(models.Model):
    categorias = models.JSONField(default=list, blank=True)
    etiquetas = models.JSONField(default=list, blank=True)
    artistas = models.JSONField(default=list, blank=True)

    class Meta:
        abstract = True


class ExploracionInspiracion(models.Model):
    _id = models.ObjectIdField()
    usuario = models.EmbeddedField(model_container=UsuarioEmbebido)
    preferencias = models.EmbeddedField(model_container=Preferencias)
    fechaActualizacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'exploracion'
        managed = False

    def __str__(self):
        return self.usuario['nombreUsuario']
