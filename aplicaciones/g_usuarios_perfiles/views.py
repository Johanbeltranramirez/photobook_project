import hashlib
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from aplicaciones.publicacion_org_contenido.models import Publicacion
from photobook.utilidades.consultas import documentos, existe_bloqueo
from .acceso import sesion_requerida, comprobar_propietario, puede_administrar, puede_gestionar_usuario, registrar_accion
from photobook.utilidades.correo import enlace, enviar_correo
from .forms import FormularioRegistro, FormularioIngreso, FormularioPerfil, FormularioOlvido, FormularioNuevaContrasena, FormularioPreferenciasCorreo
from .models import Usuario, Notificacion, PreferenciaCorreo
from .notificaciones import notificar, preferencia_de, CATEGORIAS_CORREO
from .tokens import crear_token_restablecer, usuario_desde_token


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
        notificar(usuario.nombreUsuario, 'sistema', 'Te damos la bienvenida a Photobook. Completa tu perfil y comparte tu primera publicación.', categoria=None, asunto='Te damos la bienvenida a Photobook', ruta=reverse('perfil_detalle', args=[usuario.nombreUsuario]), boton='Ir a mi perfil')
        return redirect('perfil_detalle', nombre=usuario.nombreUsuario)
    return render(solicitud, 'formularios/formulario.html', {'formulario': formulario, 'titulo': 'Crear cuenta'})


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
    return render(solicitud, 'acceso/ingresar.html', {'formulario': formulario})


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
    return render(solicitud, 'formularios/formulario.html', {'formulario': formulario, 'titulo': 'Editar perfil'})


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
            enviar_correo(usuario.correo, 'Tu cuenta fue desactivada', {'titulo': 'Tu cuenta fue desactivada', 'saludo': 'Hola, %s' % usuario.nombreUsuario, 'texto': 'Un administrador desactivó tu cuenta de Photobook, por lo que ya no podrás iniciar sesión. Tu contenido se conserva. Si crees que se trata de un error, comunícate con el equipo de la plataforma.'})
        if solicitud.usuario.pk == usuario.pk:
            solicitud.session.flush()
        return redirect('inicio')
    return render(solicitud, 'formularios/eliminar.html', {'titulo': 'Desactivar cuenta', 'objeto': nombre, 'explicacion': 'La cuenta dejará de iniciar sesión. Se conserva el contenido y su autoría.'})


@sesion_requerida
@require_POST
def seguir_usuario(solicitud, nombre):
    otro = get_object_or_404(Usuario, nombreUsuario=nombre, activo__in=[True])
    usuario = solicitud.usuario
    if otro.pk == usuario.pk or existe_bloqueo(usuario.nombreUsuario, nombre, 'contenido'):
        raise PermissionDenied('No puedes seguir este perfil.')
    nuevo_seguimiento = False
    if any(dato['usuario'] == nombre for dato in usuario.siguiendo):
        usuario.siguiendo = [dato for dato in usuario.siguiendo if dato['usuario'] != nombre]
        otro.seguidores = [dato for dato in otro.seguidores if dato['usuario'] != usuario.nombreUsuario]
    else:
        fecha = timezone.now()
        usuario.siguiendo.append({'usuario': nombre, 'inicioSeg': fecha})
        otro.seguidores.append({'usuario': usuario.nombreUsuario, 'inicioSeg': fecha})
        nuevo_seguimiento = True
    usuario.save()
    otro.save()
    if nuevo_seguimiento:
        notificar(nombre, 'seguir', usuario.nombreUsuario + ' comenzó a seguirte.', origen=usuario.nombreUsuario, categoria='seguidores', asunto=usuario.nombreUsuario + ' comenzó a seguirte', ruta=reverse('perfil_detalle', args=[usuario.nombreUsuario]), boton='Ver su perfil', ambito_bloqueo='contenido')
    return redirect('perfil_detalle', nombre=nombre)


@sesion_requerida
def notificaciones_listar(solicitud):
    notificaciones = Notificacion.objects.filter(usuarioNotificado=solicitud.usuario.nombreUsuario).order_by('-fechaCreacion')
    return render(solicitud, 'notificaciones/lista.html', {'notificaciones': notificaciones})


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
    return render(solicitud, 'formularios/eliminar.html', {'titulo': 'Eliminar notificación', 'objeto': notificacion.mensaje})


MENSAJE_OLVIDO = 'Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña. Revisa tu bandeja de entrada y la carpeta de spam.'


def puede_solicitar_enlace(correo):
    clave = hashlib.sha256(correo.encode()).hexdigest()
    if not cache.add('olvido_pausa:' + clave, 1, 60):
        return False
    intentos = cache.get('olvido_total:' + clave, 0)
    if intentos >= 5:
        return False
    cache.set('olvido_total:' + clave, intentos + 1, 3600)
    return True


def ocultar_correo(correo):
    nombre, _, dominio = correo.partition('@')
    return nombre[:2] + '***@' + dominio


@require_http_methods(['GET', 'POST'])
def olvido_contrasena(solicitud):
    formulario = FormularioOlvido(solicitud.POST or None)
    enviado = False
    if solicitud.method == 'POST' and formulario.is_valid():
        correo = formulario.cleaned_data['correo']
        usuario = Usuario.objects.filter(correo=correo, activo__in=[True]).first()
        if usuario and puede_solicitar_enlace(correo):
            token = crear_token_restablecer(usuario)
            enviar_correo(usuario.correo, 'Restablece tu contraseña', {
                'titulo': 'Restablece tu contraseña',
                'saludo': 'Hola, %s' % usuario.nombreUsuario,
                'texto': 'Recibimos una solicitud para restablecer la contraseña de tu cuenta. El enlace funciona una sola vez y vence en %d minutos.' % (settings.TIEMPO_TOKEN_RESTABLECER // 60),
                'boton_texto': 'Crear nueva contraseña',
                'boton_url': enlace(reverse('restablecer_contrasena', args=[token])),
                'nota': 'Si tú no lo solicitaste, ignora este mensaje: tu contraseña actual seguirá funcionando.',
            })
        enviado = True
    return render(solicitud, 'acceso/olvido.html', {'formulario': formulario, 'enviado': enviado, 'mensaje_envio': MENSAJE_OLVIDO, 'minutos': settings.TIEMPO_TOKEN_RESTABLECER // 60})


@require_http_methods(['GET', 'POST'])
def restablecer_contrasena(solicitud, token):
    usuario = usuario_desde_token(token)
    if usuario is None:
        return render(solicitud, 'acceso/restablecer.html', {'valido': False}, status=400)
    formulario = FormularioNuevaContrasena(solicitud.POST or None)
    if solicitud.method == 'POST' and formulario.is_valid():
        usuario.contrasena = make_password(formulario.cleaned_data['contrasena'])
        usuario.save()
        solicitud.session.flush()
        enviar_correo(usuario.correo, 'Tu contraseña fue cambiada', {
            'titulo': 'Tu contraseña fue cambiada',
            'saludo': 'Hola, %s' % usuario.nombreUsuario,
            'texto': 'Acabas de cambiar la contraseña de tu cuenta de Photobook. Si fuiste tú, no necesitas hacer nada más.',
            'nota': 'Si no reconoces este cambio, restablece tu contraseña de inmediato desde la página de ingreso y avísale al equipo de la plataforma.',
            'boton_texto': 'Iniciar sesión',
            'boton_url': enlace(reverse('iniciar_sesion')),
        })
        messages.success(solicitud, 'Tu contraseña se actualizó. Ya puedes iniciar sesión.')
        return redirect('iniciar_sesion')
    return render(solicitud, 'acceso/restablecer.html', {'valido': True, 'formulario': formulario, 'usuario_token': usuario})


@sesion_requerida
@require_http_methods(['GET', 'POST'])
def preferencias_correo(solicitud):
    nombre = solicitud.usuario.nombreUsuario
    preferencia = preferencia_de(nombre)
    actuales = {campo: True if preferencia is None else bool(getattr(preferencia, campo)) for campo, _, _ in CATEGORIAS_CORREO}
    if solicitud.method == 'POST':
        formulario = FormularioPreferenciasCorreo(solicitud.POST)
        if formulario.is_valid():
            preferencia = preferencia or PreferenciaCorreo(usuario=nombre)
            for campo in actuales:
                setattr(preferencia, campo, formulario.cleaned_data[campo])
            preferencia.fechaActualizacion = timezone.now()
            preferencia.save()
            messages.success(solicitud, 'Guardamos tus preferencias de correo.')
            return redirect('preferencias_correo')
    opciones = [{'campo': campo, 'titulo': titulo, 'descripcion': descripcion, 'activo': actuales[campo]} for campo, titulo, descripcion in CATEGORIAS_CORREO]
    return render(solicitud, 'notificaciones/preferencias_correo.html', {'opciones': opciones, 'correo': ocultar_correo(solicitud.usuario.correo)})
