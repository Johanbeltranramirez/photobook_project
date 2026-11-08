from django.db import connection
from django.utils import timezone


def documentos(modelo, filtro):
    base = connection.cursor().db_conn
    identificadores = [dato['_id'] for dato in base[modelo._meta.db_table].find(filtro, {'_id': 1})]
    return modelo.objects.filter(pk__in=identificadores)


def existe_bloqueo(primero, segundo, ambito):
    base = connection.cursor().db_conn
    filtro = {
        'ambito': {'$in': ['total', ambito]},
        '$and': [
            {'$or': [
                {'bloqueador.nombreUsuario': primero, 'bloqueado.nombreUsuario': segundo},
                {'bloqueador.nombreUsuario': segundo, 'bloqueado.nombreUsuario': primero},
            ]},
            {'$or': [{'fechaExpiracion': None}, {'fechaExpiracion': {'$gt': timezone.now()}}]},
        ],
    }
    return base['moderacion'].find_one(filtro, {'_id': 1}) is not None


def publicacion_visible(usuario, enlace):
    from publicacion_org_contenido.models import Publicacion
    publicacion = Publicacion.objects.filter(archivoUrl=enlace, estado='publicado').first()
    if publicacion and not existe_bloqueo(usuario.nombreUsuario, publicacion.autor['nombreUsuario'], 'contenido'):
        return publicacion
    return None
