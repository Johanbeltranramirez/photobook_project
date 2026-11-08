from functools import wraps
from bson import ObjectId
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
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
    return {'usuario_actual': solicitud.usuario, 'permiso_contenido': puede_administrar(solicitud.usuario, 'permiso_contenido'), 'permiso_usuarios': puede_administrar(solicitud.usuario, 'permiso_usuarios'), 'permiso_estadisticas': puede_administrar(solicitud.usuario, 'permiso_estadisticas')}


def sesion_requerida(vista):
    @wraps(vista)
    def comprobar(solicitud, *argumentos, **opciones):
        if solicitud.usuario is None:
            return redirect('iniciar_sesion')
        return vista(solicitud, *argumentos, **opciones)
    return comprobar


def administrador_requerido(vista):
    @wraps(vista)
    @sesion_requerida
    def comprobar(solicitud, *argumentos, **opciones):
        permiso = 'permiso_estadisticas' if 'control' in vista.__name__ else 'permiso_contenido'
        if 'rol' in vista.__name__ or vista.__name__ == 'asignar_rol':
            permiso = 'permiso_usuarios'
            if solicitud.usuario.rol != 'administrador':
                raise PermissionDenied('Solo un administrador puede gestionar los roles.')
        if not puede_administrar(solicitud.usuario, permiso):
            raise PermissionDenied('Esta sección es para administradores.')
        return vista(solicitud, *argumentos, **opciones)
    return comprobar


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
    from admin_contrl_sys.models import Rol
    rol = Rol.objects.filter(nombre=usuario.rol, activo__in=[True]).first()
    return bool(rol and getattr(rol, permiso, False))
