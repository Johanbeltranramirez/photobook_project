from django import forms


class RolForm(forms.Form):
    nombre = forms.CharField(max_length=50)
    descripcion = forms.CharField(widget=forms.Textarea)
    permiso_usuarios = forms.BooleanField(required=False)
    permiso_contenido = forms.BooleanField(required=False)
    permiso_estadisticas = forms.BooleanField(required=False)
    activo = forms.BooleanField(required=False)


class AccionAdministrativaForm(forms.Form):
    administrador = forms.CharField(max_length=100)
    rol_administrador = forms.CharField(max_length=50)
    accion = forms.CharField(max_length=100)
    entidad = forms.CharField(max_length=50)
    detalle_entidad = forms.CharField(widget=forms.Textarea)
    descripcion = forms.CharField(widget=forms.Textarea)
    fecha = forms.DateTimeField()


class ReporteContenidoForm(forms.Form):
    contenido = forms.CharField(max_length=150)
    tipo_contenido = forms.CharField(max_length=50)
    motivo = forms.CharField(widget=forms.Textarea)
    estado = forms.CharField(max_length=50)
    reportado_por = forms.CharField(max_length=100)
    fecha_reporte = forms.DateTimeField()


class ControlSistemaForm(forms.Form):
    fecha = forms.DateField()
    usuarios_activos = forms.IntegerField(min_value=0)
    publicaciones = forms.IntegerField(min_value=0)
    reportes = forms.IntegerField(min_value=0)
    fecha_respaldo = forms.DateTimeField()
    estado_respaldo = forms.CharField(max_length=30)
