from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from publicacion_org_contenido.models import Publicacion
from photobook.consultas import documentos, existe_bloqueo
from .acceso import sesion_requerida, comprobar_propietario, puede_administrar, puede_gestionar_usuario, registrar_accion
from .forms import FormularioRegistro, FormularioIngreso, FormularioPerfil
from .models import Usuario, Notificacion


def inicio(solicitud):
    publicaciones = Publicacion.objects.filter(estado='publicado').order_by('-fechaPublicacion')
    if solicitud.usuario:
        publicaciones = [dato for dato in publicaciones if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido')]
    return render(solicitud, 'usuarios/inicio.html', {'publicaciones': publicaciones[:12]})


@require_http_methods(['GET', 'POST'])
def registrar_usuario(solicitud):
    formulario = FormularioRegistro(solicitud.POST or None)
    if solicitud.method == 'POST' and formulario.is_valid():
        datos = formulario.cleaned_data
        usuario = Usuario.objects.create(
            nombreUsuario=datos['nombreUsuario'], correo=datos['correo'],
            contrasena=make_password(datos['contrasena']), rol='artista',
            privacidad={'perfilPublico': True, 'correoVisible': False},
        )
        solicitud.session.flush()
        solicitud.session['usuario'] = str(usuario.pk)
        return redirect('perfil_detalle', nombre=usuario.nombreUsuario)
    return render(solicitud, 'comunes/formulario.html', {'formulario': formulario, 'titulo': 'Crear cuenta'})


@require_http_methods(['GET', 'POST'])
def iniciar_sesion(solicitud):
    formulario = FormularioIngreso(solicitud.POST or None)
    if solicitud.method == 'POST' and formulario.is_valid():
        datos = formulario.cleaned_data
        usuario = Usuario.objects.filter(nombreUsuario=datos['nombreUsuario'].lower(), activo__in=[True]).first()
        if usuario and check_password(datos['contrasena'], usuario.contrasena):
            solicitud.session.flush()
            solicitud.session['usuario'] = str(usuario.pk)
            return redirect('inicio')
        formulario.add_error(None, 'El usuario o la contraseña no son correctos.')
    return render(solicitud, 'comunes/formulario.html', {'formulario': formulario, 'titulo': 'Iniciar sesión'})


@require_POST
def cerrar_sesion(solicitud):
    solicitud.session.flush()
    return redirect('inicio')


@sesion_requerida
def usuarios_listar(solicitud):
    es_gestor = puede_administrar(solicitud.usuario, 'permiso_usuarios')
    usuarios = (Usuario.objects.all() if es_gestor else Usuario.objects.filter(activo__in=[True])).order_by('nombreUsuario')
    texto = solicitud.GET.get('buscar', '').strip()
    if texto:
        usuarios = usuarios.filter(nombreUsuario__icontains=texto)
    return render(solicitud, 'usuarios/lista.html', {'usuarios': usuarios, 'es_gestor': es_gestor})


@sesion_requerida
def perfil_detalle(solicitud, nombre):
    usuario = get_object_or_404(Usuario, nombreUsuario=nombre, activo__in=[True])
    propio = solicitud.usuario.pk == usuario.pk
    puede_ver = propio or usuario.privacidad['perfilPublico'] or solicitud.usuario.rol == 'administrador'
    if existe_bloqueo(solicitud.usuario.nombreUsuario, nombre, 'contenido'):
        raise PermissionDenied('Este perfil no está disponible.')
    publicaciones = documentos(Publicacion, {'autor.nombreUsuario': nombre, 'estado': 'publicado'}) if puede_ver else []
    return render(solicitud, 'usuarios/detalle.html', {'perfil': usuario, 'propio': propio, 'puede_ver': puede_ver, 'puede_editar': puede_gestionar_usuario(solicitud.usuario, usuario), 'publicaciones': publicaciones})


@sesion_requerida
@require_http_methods(['GET', 'POST'])
def perfil_actualizar(solicitud, nombre):
    usuario = get_object_or_404(Usuario, nombreUsuario=nombre, activo__in=[True])
    if not puede_administrar(solicitud.usuario, 'permiso_usuarios') or usuario.rol == 'administrador':
        comprobar_propietario(solicitud, nombre)
    datos = {'imagenPerfil': usuario.imagenPerfil, 'biografia': usuario.biografia, **usuario.privacidad}
    formulario = FormularioPerfil(solicitud.POST or None, initial=datos)
    if solicitud.method == 'POST' and formulario.is_valid():
        datos = formulario.cleaned_data
        usuario.imagenPerfil = datos['imagenPerfil'] or None
        usuario.biografia = datos['biografia'] or None
        usuario.privacidad = {'perfilPublico': datos['perfilPublico'], 'correoVisible': datos['correoVisible']}
        usuario.save()
        return redirect('perfil_detalle', nombre=nombre)
    return render(solicitud, 'comunes/formulario.html', {'formulario': formulario, 'titulo': 'Editar perfil'})


@sesion_requerida
@require_http_methods(['GET', 'POST'])
def perfil_eliminar(solicitud, nombre):
    usuario = get_object_or_404(Usuario, nombreUsuario=nombre, activo__in=[True])
    if not puede_administrar(solicitud.usuario, 'permiso_usuarios') or usuario.rol == 'administrador':
        comprobar_propietario(solicitud, nombre)
    if usuario.rol == 'administrador' and Usuario.objects.filter(rol='administrador', activo__in=[True]).count() <= 1:
        raise PermissionDenied('No se puede desactivar al último administrador.')
    if solicitud.method == 'POST':
        usuario.activo = False
        usuario.save()
        if solicitud.usuario.pk != usuario.pk:
            registrar_accion(solicitud.usuario, 'Desactivar usuario', 'usuarios', nombre, 'Cuenta desactivada por un administrador')
        if solicitud.usuario.pk == usuario.pk:
            solicitud.session.flush()
        return redirect('inicio')
    return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Desactivar cuenta', 'objeto': nombre, 'explicacion': 'La cuenta dejará de iniciar sesión. Se conserva el contenido y su autoría.'})


@sesion_requerida
@require_POST
def seguir_usuario(solicitud, nombre):
    otro = get_object_or_404(Usuario, nombreUsuario=nombre, activo__in=[True])
    usuario = solicitud.usuario
    if otro.pk == usuario.pk or existe_bloqueo(usuario.nombreUsuario, nombre, 'contenido'):
        raise PermissionDenied('No puedes seguir este perfil.')
    if any(dato['usuario'] == nombre for dato in usuario.siguiendo):
        usuario.siguiendo = [dato for dato in usuario.siguiendo if dato['usuario'] != nombre]
        otro.seguidores = [dato for dato in otro.seguidores if dato['usuario'] != usuario.nombreUsuario]
    else:
        fecha = timezone.now()
        usuario.siguiendo.append({'usuario': nombre, 'inicioSeg': fecha})
        otro.seguidores.append({'usuario': usuario.nombreUsuario, 'inicioSeg': fecha})
        Notificacion.objects.create(usuarioNotificado=nombre, usuarioOrigen=usuario.nombreUsuario, tipo='seguir', mensaje=usuario.nombreUsuario + ' comenzó a seguirte.')
    usuario.save()
    otro.save()
    return redirect('perfil_detalle', nombre=nombre)


@sesion_requerida
def notificaciones_listar(solicitud):
    notificaciones = Notificacion.objects.filter(usuarioNotificado=solicitud.usuario.nombreUsuario).order_by('-fechaCreacion')
    return render(solicitud, 'usuarios/notificaciones.html', {'notificaciones': notificaciones})


@sesion_requerida
@require_POST
def notificacion_leer(solicitud, pk):
    notificacion = get_object_or_404(Notificacion, pk=pk, usuarioNotificado=solicitud.usuario.nombreUsuario)
    notificacion.notificacionLeer = True
    notificacion.save()
    return redirect('notificaciones_listar')


@sesion_requerida
@require_http_methods(['GET', 'POST'])
def notificacion_eliminar(solicitud, pk):
    notificacion = get_object_or_404(Notificacion, pk=pk, usuarioNotificado=solicitud.usuario.nombreUsuario)
    if solicitud.method == 'POST':
        notificacion.delete()
        return redirect('notificaciones_listar')
    return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar notificación', 'objeto': notificacion.mensaje})
