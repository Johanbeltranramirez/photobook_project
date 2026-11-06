from djongo import models


class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField()
    permiso_usuarios = models.BooleanField(default=False)
    permiso_contenido = models.BooleanField(default=False)
    permiso_estadisticas = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)


class AccionAdministrativa(models.Model):
    administrador = models.CharField(max_length=100)
    rol_administrador = models.CharField(max_length=50)
    accion = models.CharField(max_length=100)
    entidad = models.CharField(max_length=50)
    detalle_entidad = models.TextField()
    descripcion = models.TextField()
    fecha = models.DateTimeField()


class ReporteContenido(models.Model):
    contenido = models.CharField(max_length=150)
    tipo_contenido = models.CharField(max_length=50)
    motivo = models.TextField()
    estado = models.CharField(max_length=50)
    reportado_por = models.CharField(max_length=100)
    fecha_reporte = models.DateTimeField()


class ControlSistema(models.Model):
    fecha = models.DateField()
    usuarios_activos = models.PositiveIntegerField()
    publicaciones = models.PositiveIntegerField()
    reportes = models.PositiveIntegerField()
    fecha_respaldo = models.DateTimeField()
    estado_respaldo = models.CharField(max_length=30)
