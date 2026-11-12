import re

TIPOS = ('imagen', 'video')
FORMATOS = ('jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'webm')
ESTADOS = ('publicado', 'borrador', 'eliminado')
TIPOS_EDICION = ('recorte', 'rotacion', 'filtro', 'brillo', 'contraste', 'saturacion', 'texto')
FORMATOS_COMENTARIO = ('texto', 'markdown', 'html')
REACCIONES = (
    ('meGusta', '👍', 'Me gusta'),
    ('amor', '🧡', 'Me encanta'),
    ('aplauso', '👏', 'Aplauso'),
    ('sorpresa', '😮', 'Sorpresa'),
    ('triste', '😢', 'Tristeza'),
    ('risa', '😂', 'Risa'),
)
TIPOS_REACCION = tuple(dato[0] for dato in REACCIONES)
EXTENSIONES_IMAGEN = ('jpg', 'jpeg', 'png', 'gif')
EXTENSIONES_VIDEO = ('mp4', 'mov', 'webm')
TAMANIO_MAXIMO_IMAGEN = 10 * 1024 * 1024
TAMANIO_MAXIMO_VIDEO = 100 * 1024 * 1024
TIPOS_COLECCION = ('personal', 'colaborativa')
PRIVACIDADES = ('publica', 'privada')
CRITERIOS = ('etiquetas', 'coleccion', 'tendencia', 'similitud', 'preferencias')
PATRON_URL = re.compile(r'^https?://.+$')
PATRON_SLUG = re.compile(r'^[a-z0-9-]+$')
PATRON_CALIDAD = re.compile(r'^[0-9]+p$')
ORDENES_PUBLICACION = {
    'recientes': '-fechaPublicacion',
    'antiguas': 'fechaPublicacion',
    'populares': '-totalReacciones',
    'comentadas': '-totalComentarios',
}
