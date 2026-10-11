import re

TIPOS = ('imagen', 'video')
FORMATOS = ('jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'webm')
ESTADOS = ('publicado', 'borrador', 'eliminado')
TIPOS_EDICION = ('recorte', 'rotacion', 'filtro', 'brillo', 'contraste', 'saturacion', 'texto')
FORMATOS_COMENTARIO = ('texto', 'markdown', 'html')
TIPOS_REACCION = ('like', 'amor', 'aplauso', 'sorpresa', 'triste', 'risa')
TIPOS_COLECCION = ('personal', 'colaborativa')
PRIVACIDADES = ('publica', 'privada')
CRITERIOS = ('etiquetas', 'coleccion', 'tendencia', 'similitud')
PATRON_URL = re.compile(r'^https?://.+$')
PATRON_SLUG = re.compile(r'^[a-z0-9-]+$')
PATRON_CALIDAD = re.compile(r'^[0-9]+p$')
ORDENES_PUBLICACION = {
    'recientes': '-fechaPublicacion',
    'antiguas': 'fechaPublicacion',
    'populares': '-totalReacciones',
    'comentadas': '-totalComentarios',
}