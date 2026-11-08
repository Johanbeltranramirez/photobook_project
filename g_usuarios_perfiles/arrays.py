import re


PATRON_URL = re.compile(r'^https?://[^\s]+$')
PATRON_CORREO = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


ROLES_USUARIO = ('artista', 'administrador')
MIN_LONGITUD_NOMBRE_USUARIO = 3


TIPOS_NOTIFICACION = ('seguir', 'meGusta', 'comentario', 'mensaje', 'sistema')

ORDENES_NOTIFICACION = {
    'recientes': '-fechaCreacion',
    'antiguas': 'fechaCreacion',
    'no_leidas': 'notificacionLeer',
    'leidas': '-notificacionLeer',
}