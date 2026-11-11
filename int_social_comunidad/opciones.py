import re

TIPOS_MENSAJE = ('texto', 'imagen', 'video', 'archivo')
TIPOS_REACCION = ('meGusta', 'amor', 'aplauso', 'sorpresa', 'triste', 'risa')
ICONOS_REACCION = {'meGusta': '👍', 'amor': '❤️', 'aplauso': '👏', 'sorpresa': '😮', 'triste': '😢', 'risa': '😂'}
FORMATOS_COMENTARIO = ('texto', 'markdown', 'html')

TIPOS_GRUPO = ('publico', 'privado')
ESTADOS_GRUPO = ('activo', 'archivado', 'suspendido')
ROLES_GRUPO = ('miembro', 'moderador', 'administrador')

TIPOS_MODERACION = ('bloqueo',)
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
