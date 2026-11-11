import logging
from datetime import timedelta
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from photobook.consultas import existe_bloqueo
from photobook.correo import enlace, enviar_correo
from .models import Notificacion, PreferenciaCorreo, Usuario

registro = logging.getLogger('photobook.notificaciones')

CATEGORIAS_CORREO = (
    ('seguidores', 'Nuevos seguidores', 'Cuando alguien comienza a seguirte.'),
    ('comentarios', 'Comentarios', 'Cuando comentan tus publicaciones o los foros que moderas.'),
    ('reacciones', 'Reacciones y guardados', 'Cuando reaccionan a tus publicaciones o mensajes, o las guardan en una colección.'),
    ('mensajes', 'Mensajes privados', 'Cuando recibes un mensaje nuevo.'),
    ('avisos', 'Avisos de la comunidad', 'Invitaciones, cambios de rol, colecciones compartidas y reportes.'),
)
MINUTOS_ANTIREPETICION = 10


def preferencia_de(nombre):
    return PreferenciaCorreo.objects.filter(usuario=nombre).first()


def desea_correo(nombre, categoria):
    preferencia = preferencia_de(nombre)
    return True if preferencia is None else bool(getattr(preferencia, categoria, True))


def recortar(texto, limite):
    texto = ' '.join((texto or '').split())
    return texto if len(texto) <= limite else texto[:limite - 1].rstrip() + '…'


def es_repetida(destinatario, origen, tipo, mensaje):
    limite = timezone.now() - timedelta(minutes=MINUTOS_ANTIREPETICION)
    filtro = {'usuarioNotificado': destinatario, 'usuarioOrigen': origen, 'tipo': tipo, 'mensaje': mensaje, 'fechaCreacion': {'$gte': limite}}
    return connection.cursor().db_conn[Notificacion._meta.db_table].find_one(filtro, {'_id': 1}) is not None


def notificar(destinatario, tipo, mensaje, origen=None, categoria='avisos', asunto=None, ruta=None, detalle=None, boton=None, ambito_bloqueo=None):
    try:
        if not destinatario or destinatario == origen:
            return None
        if origen and ambito_bloqueo and existe_bloqueo(destinatario, origen, ambito_bloqueo):
            return None
        mensaje = recortar(mensaje, 255)
        if es_repetida(destinatario, origen, tipo, mensaje):
            return None
        usuario = Usuario.objects.filter(nombreUsuario=destinatario, activo__in=[True]).first()
        if usuario is None:
            return None
        notificacion = Notificacion.objects.create(usuarioNotificado=destinatario, usuarioOrigen=origen, tipo=tipo, mensaje=mensaje)
        if categoria is None or desea_correo(destinatario, categoria):
            enviar_correo(usuario.correo, asunto or mensaje, {
                'titulo': asunto or mensaje,
                'saludo': 'Hola, %s' % usuario.nombreUsuario,
                'texto': mensaje,
                'detalle': recortar(detalle, 300) if detalle else None,
                'boton_texto': boton or 'Abrir en Photobook',
                'boton_url': enlace(ruta) if ruta else None,
                'preferencias_url': enlace(reverse('preferencias_correo')) if categoria else None,
            })
        return notificacion
    except Exception:
        registro.exception('No se pudo registrar la notificación para %s', destinatario)
        return None
