from django import forms


class FormularioRol(forms.Form):
    nombre = forms.CharField(max_length=50)
    descripcion = forms.CharField(max_length=1000, widget=forms.Textarea)
    permiso_usuarios = forms.BooleanField(label="Administrar usuarios", required=False)
    permiso_contenido = forms.BooleanField(label="Administrar contenido", required=False)
    permiso_estadisticas = forms.BooleanField(label="Consultar estadísticas", required=False)
    activo = forms.BooleanField(required=False)


class FormularioAccion(forms.Form):
    accion = forms.CharField(max_length=100)
    entidad = forms.CharField(max_length=50)
    detalle_entidad = forms.CharField(max_length=1000, widget=forms.Textarea)
    descripcion = forms.CharField(max_length=1000, widget=forms.Textarea)


class FormularioReporte(forms.Form):
    contenido = forms.CharField(max_length=500, label="Contenido o usuario reportado")
    tipo_contenido = forms.ChoiceField(choices=[
        ("publicacion", "Publicación"),
        ("comentario", "Comentario"),
        ("usuario", "Usuario"),
    ])
    motivo = forms.CharField(max_length=1000, widget=forms.Textarea)


class FormularioResolucion(forms.Form):
    estado = forms.ChoiceField(choices=[
        ("resuelto", "Resuelto"),
        ("descartado", "Descartado"),
    ])
    accion_tomada = forms.CharField(max_length=100, widget=forms.Textarea)


class FormularioControl(forms.Form):
    fecha = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), input_formats=["%Y-%m-%d"])
    usuarios_activos = forms.IntegerField(min_value=0)
    publicaciones = forms.IntegerField(min_value=0)
    reportes = forms.IntegerField(min_value=0)
    fecha_respaldo = forms.DateTimeField(required=False, label="Fecha de respaldo", widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), input_formats=["%Y-%m-%dT%H:%M"])
    estado_respaldo = forms.ChoiceField(label="Estado del respaldo", choices=[("sin_registrar", "Sin registrar"), ("exitoso", "Exitoso"), ("fallido", "Fallido")])
