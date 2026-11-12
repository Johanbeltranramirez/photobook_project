import hashlib
import hmac
from bson import ObjectId
from django.conf import settings
from django.core import signing
from .models import Usuario

SAL_RESTABLECER = 'photobook.restablecer-contrasena'


def huella_contrasena(usuario):
    return hashlib.sha256(usuario.contrasena.encode()).hexdigest()[:24]


def crear_token_restablecer(usuario):
    return signing.dumps({'u': str(usuario.pk), 'h': huella_contrasena(usuario)}, salt=SAL_RESTABLECER, compress=True)


def usuario_desde_token(token):
    try:
        datos = signing.loads(token, salt=SAL_RESTABLECER, max_age=settings.TIEMPO_TOKEN_RESTABLECER)
    except signing.BadSignature:
        return None
    if not isinstance(datos, dict) or not ObjectId.is_valid(str(datos.get('u', ''))):
        return None
    usuario = Usuario.objects.filter(pk=ObjectId(datos['u']), activo__in=[True]).first()
    if usuario and hmac.compare_digest(huella_contrasena(usuario), str(datos.get('h', ''))):
        return usuario
    return None
