from functools import wraps
from bson import ObjectId
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils import timezone
from .models import Usuario

class UsuarioActual:
    def __init__(self, obtener_respuesta):
        self.obtener_respuesta = obtener_respuesta

    def __call__(self, solicitud):
        solicitud.usuario = None
        identificador = solicitud.session.get('usuario')
        if identificador and ObjectId.is_valid(identificador):
            solicitud.usuario = Usuario.objects.filter(pk=ObjectId(identificador), activo__in=[True]).first()
        return self.obtener_respuesta(solicitud)


def contexto_usuario(solicitud):
    usuario = solicitud.usuario
    permisos = {nombre: puede_administrar(usuario, nombre) for nombre in ('permiso_contenido', 'permiso_usuarios', 'permiso_estadisticas')}
    return {'usuario_actual': usuario, 'es_administrador': bool(usuario and usuario.rol == 'administrador'), 'es_staff': any(permisos.values()), **permisos}


def sesion_requerida(vista):
    @wraps(vista)
    def comprobar(solicitud, *argumentos, **opciones):
        if solicitud.usuario is None:
            return redirect('iniciar_sesion')
        return vista(solicitud, *argumentos, **opciones)
    return comprobar


def permiso_requerido(permiso, solo_administrador=False):
    def decorador(vista):
        @wraps(vista)
        @sesion_requerida
        def comprobar(solicitud, *argumentos, **opciones):
            if solo_administrador and solicitud.usuario.rol != 'administrador':
                raise PermissionDenied('Solo un administrador puede hacer esto.')
            if not puede_administrar(solicitud.usuario, permiso):
                raise PermissionDenied('Esta sección es para administradores.')
            return vista(solicitud, *argumentos, **opciones)
        return comprobar
    return decorador


administrador_requerido = permiso_requerido('permiso_contenido')


def comprobar_propietario(solicitud, nombre):
    if solicitud.usuario.nombreUsuario != nombre and solicitud.usuario.rol != 'administrador':
        raise PermissionDenied('No tienes permiso para modificar este registro.')


def resumen_usuario(usuario):
    return {'nombreUsuario': usuario.nombreUsuario, 'imagenPerfil': usuario.imagenPerfil}


def puede_administrar(usuario, permiso):
    if usuario is None:
        return False
    if usuario.rol == 'administrador':
        return True
    from aplicaciones.admin_contrl_sys.models import Rol
    rol = Rol.objects.filter(nombre=usuario.rol, activo__in=[True]).first()
    return bool(rol and getattr(rol, permiso, False))


def registrar_accion(administrador, accion, entidad, detalle, descripcion):
    from aplicaciones.admin_contrl_sys.models import AccionAdministrativa
    AccionAdministrativa.objects.create(
        administrador=administrador.nombreUsuario, rol_administrador=administrador.rol,
        accion=accion, entidad=entidad, detalle_entidad=detalle, descripcion=descripcion, fecha=timezone.now())


def puede_gestionar_usuario(actor, objetivo):
    return actor.pk == objetivo.pk or (puede_administrar(actor, 'permiso_usuarios') and objetivo.rol != 'administrador') or actor.rol == 'administrador'
