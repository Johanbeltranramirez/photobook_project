import re

TIPOS_MENSAJE = ('texto', 'imagen', 'video', 'archivo')
TIPOS_REACCION = ('like', 'amor', 'aplauso', 'sorpresa', 'triste', 'risa')
FORMATOS_COMENTARIO = ('texto', 'markdown', 'html')

TIPOS_GRUPO = ('publico', 'privado')
ESTADOS_GRUPO = ('activo', 'archivado', 'suspendido')
ROLES_GRUPO = ('miembro', 'moderador', 'admin')

TIPOS_MODERACION = ('reporte', 'bloqueo')
ESTADOS_REPORTE = ('pendiente', 'resuelto', 'descartado')
TIPOS_ELEMENTO = ('publicacion', 'comentario', 'usuario')
MOTIVOS_REPORTE = ('spam', 'acoso', 'odio', 'violencia', 'contenido_inapropiado', 'desinformacion', 'suplantacion', 'otro')
ACCIONES_MODERACION = ('advertencia', 'eliminar_contenido', 'suspender_usuario', 'bloquear_usuario')
AMBITOS_BLOQUEO = ('total', 'mensajes', 'contenido')

PATRON_URL = re.compile(r'^https?://.+$')

ORDENES_MENSAJE = {
    'recientes': '-fechaEnvio',
    'antiguos': 'fechaEnvio',
}
ORDENES_GRUPO = {
    'alfabetico': 'nombre',
    'populares': '-totalMiembros',
}