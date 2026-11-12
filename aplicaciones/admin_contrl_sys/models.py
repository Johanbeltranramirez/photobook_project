from django.utils import timezone
from djongo import models


class Rol(models.Model):
    _id = models.ObjectIdField()
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    permiso_usuarios = models.BooleanField(default=False)
    permiso_contenido = models.BooleanField(default=False)
    permiso_estadisticas = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)


    class Meta:
        db_table = "roles"
        managed = False


class AccionAdministrativa(models.Model):
    _id = models.ObjectIdField()
    administrador = models.CharField(max_length=100)
    rol_administrador = models.CharField(max_length=50)
    accion = models.CharField(max_length=100)
    entidad = models.CharField(max_length=50)
    detalle_entidad = models.TextField()
    descripcion = models.TextField()
    fecha = models.DateTimeField()

    class Meta:
        db_table = "accionesAdministrativas"
        managed = False


class ReporteContenido(models.Model):
    _id = models.ObjectIdField()
    contenido = models.CharField(max_length=500)
    tipo_contenido = models.CharField(max_length=50)
    motivo = models.TextField()
    estado = models.CharField(max_length=50, default="pendiente")
    reportado_por = models.CharField(max_length=100)
    fecha_reporte = models.DateTimeField(default=timezone.now)
    moderador = models.CharField(max_length=100, blank=True, null=True)
    accion_tomada = models.CharField(max_length=100, blank=True, null=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "reporteContenido"
        managed = False


class ControlSistema(models.Model):
    _id = models.ObjectIdField()
    fecha = models.DateField()
    usuarios_activos = models.PositiveIntegerField()
    publicaciones = models.PositiveIntegerField()
    reportes = models.PositiveIntegerField()
    fecha_respaldo = models.DateTimeField(blank=True, null=True)
    estado_respaldo = models.CharField(max_length=30)

    class Meta:
        db_table = "controlSistema"
        managed = False
