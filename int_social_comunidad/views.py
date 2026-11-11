from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import connection
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.http import Http404
from .models import Mensaje, Grupo, Moderacion
from publicacion_org_contenido.models import Categoria
from admin_contrl_sys import views as administracion
from .opciones import *
from .forms import FormularioMensaje, FormularioGrupo, FormularioBloqueo
from g_usuarios_perfiles.models import Usuario
from g_usuarios_perfiles.notificaciones import notificar
from g_usuarios_perfiles.acceso import sesion_requerida, administrador_requerido, comprobar_propietario, resumen_usuario
from photobook.consultas import documentos, existe_bloqueo
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST


@sesion_requerida
@require_http_methods(['GET'])
def mensajes_listar(solicitud):
    usuario = solicitud.usuario.nombreUsuario
    con = solicitud.GET.get('con')
    leido = solicitud.GET.get('leido')
    sentido = 'fechaEnvio' if solicitud.GET.get('orden') == 'antiguos' else '-fechaEnvio'
    coleccion_mongo = connection.cursor().db_conn[Mensaje._meta.db_table]
    filtro = {}
    if usuario and con:
        filtro['$or'] = [
            {'emisor.nombreUsuario': usuario, 'receptor.nombreUsuario': con},
            {'emisor.nombreUsuario': con, 'receptor.nombreUsuario': usuario},
        ]
    elif usuario:
        filtro['$or'] = [{'emisor.nombreUsuario': usuario}, {'receptor.nombreUsuario': usuario}]
    if usuario:
        filtro['eliminadoPor'] = {'$ne': usuario}
    if leido in ('si', 'no'):
        filtro['leido'] = leido == 'si'
    mensajes = Mensaje.objects.all()
    if filtro:
        ids = [documento['_id'] for documento in coleccion_mongo.find(filtro, {'_id': 1})]
        mensajes = mensajes.filter(pk__in=ids)
    mensajes = mensajes.order_by(sentido)
    datos = {'mensajes': mensajes[:50], 'total': mensajes.count()}
    return render(solicitud, 'mensajes_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def mensajes_no_leidos(solicitud):
    usuario = solicitud.usuario.nombreUsuario
    ids = []
    if usuario:
        filtro = {'receptor.nombreUsuario': usuario, 'leido': False, 'eliminadoPor': {'$ne': usuario}}
        ids = [documento['_id'] for documento in connection.cursor().db_conn[Mensaje._meta.db_table].find(filtro, {'_id': 1})]
    mensajes = Mensaje.objects.filter(pk__in=ids).order_by('-fechaEnvio')
    datos = {'mensajes': mensajes[:50], 'total': mensajes.count(), 'estado': 'no leídos'}
    return render(solicitud, 'mensajes_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def mensaje_detalle(solicitud, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    comprobar_mensaje(solicitud, mensaje)
    return render(solicitud, 'mensaje_detalle.html', {'datos': {'mensaje': mensaje}})

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def mensaje_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {'estado': 'activo'}
    formulario = FormularioMensaje(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'mensaje_form.html', {'datos': contexto})
    errores = []
    emisor = resumen_usuario(solicitud.usuario)
    receptor = resumen_usuario(get_object_or_404(Usuario, nombreUsuario=formulario.cleaned_data['receptor'], activo__in=[True]))
    datos = {
        'contenido': solicitud.POST.get('contenido', '').strip() or None,
        'tipo': solicitud.POST.get('tipo') or 'texto',
        'adjuntos': [url.strip() for url in solicitud.POST.get('adjuntos', '').split(',') if url.strip()],
    }
    if not 3 <= len(emisor['nombreUsuario']) <= 30:
        errores.append('El emisor debe tener un nombre de usuario de 3 a 30 caracteres.')
    if not 3 <= len(receptor['nombreUsuario']) <= 30:
        errores.append('El receptor debe tener un nombre de usuario de 3 a 30 caracteres.')
    if emisor['nombreUsuario'] == receptor['nombreUsuario']:
        errores.append('No puedes enviarte un mensaje a ti mismo.')
    if datos['tipo'] not in TIPOS_MENSAJE:
        errores.append('El tipo debe ser texto, imagen, video o archivo.')
    if datos['contenido'] and len(datos['contenido']) > 5000:
        errores.append('El mensaje admite máximo 5000 caracteres.')
    if datos['tipo'] == 'texto' and not datos['contenido']:
        errores.append('Un mensaje de texto necesita contenido.')
    if datos['tipo'] != 'texto' and not datos['adjuntos']:
        errores.append('Un mensaje que no es de texto necesita al menos un adjunto.')
    if any(not PATRON_URL.match(url) for url in datos['adjuntos']):
        errores.append('Todos los adjuntos deben ser enlaces válidos.')
    if len(datos['adjuntos']) > 10:
        errores.append('Máximo 10 adjuntos por mensaje.')

    if existe_bloqueo(emisor['nombreUsuario'], receptor['nombreUsuario'], 'mensajes'):
        errores.append('No puedes enviar mensajes a este usuario.')
    mensaje = None
    if not errores:
        datos.update(
            emisor=emisor,
            receptor=receptor,
            reacciones=[],
            leido=False,
            fechaLectura=None,
            eliminadoPor=[],
            fechaEnvio=timezone.now(),
        )
        mensaje = Mensaje(**datos)
        try:
            mensaje.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'mensaje_form.html', {'datos': contexto})
    mensaje.save()
    vista_previa = mensaje.contenido if mensaje.tipo == 'texto' and mensaje.contenido else 'Te envió un archivo adjunto.'
    notificar(receptor['nombreUsuario'], 'mensaje', 'Tienes un mensaje de ' + emisor['nombreUsuario'], origen=emisor['nombreUsuario'], categoria='mensajes', asunto='Nuevo mensaje de ' + emisor['nombreUsuario'], ruta=reverse('mensaje_detalle', kwargs={'pk': mensaje.pk}), detalle=vista_previa, boton='Leer el mensaje')
    return redirect('mensaje_detalle', pk=mensaje.pk)

@sesion_requerida
@require_POST
def mensaje_marcar_leido(solicitud, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    comprobar_mensaje(solicitud, mensaje)
    if mensaje.receptor['nombreUsuario'] != solicitud.usuario.nombreUsuario:
        raise PermissionDenied('Solo el receptor puede marcarlo como leído.')
    if not mensaje.leido:
        mensaje.leido = True
        mensaje.fechaLectura = timezone.now()
        mensaje.save()
    return redirect('mensaje_detalle', pk=mensaje.pk)

@sesion_requerida
@require_POST
def mensajes_marcar_leidos(solicitud):
    receptor = solicitud.usuario.nombreUsuario
    emisor = solicitud.POST.get('emisor')
    filtro = {'receptor.nombreUsuario': receptor, 'leido': False}
    if emisor:
        filtro['emisor.nombreUsuario'] = emisor
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Mensaje._meta.db_table].find(filtro, {'_id': 1})]
    Mensaje.objects.filter(pk__in=ids).update(leido=True, fechaLectura=timezone.now())
    return redirect('mensajes_listar')

@sesion_requerida
@require_POST
def mensaje_reaccionar(solicitud, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    comprobar_mensaje(solicitud, mensaje)
    errores = []
    usuario = resumen_usuario(solicitud.usuario)
    tipoReaccion = solicitud.POST.get('tipoReaccion')
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if tipoReaccion not in TIPOS_REACCION:
        errores.append('Tipo de reacción inválido.')
    if usuario['nombreUsuario'] not in (mensaje.emisor['nombreUsuario'], mensaje.receptor['nombreUsuario']):
        errores.append('Solo los participantes de la conversación pueden reaccionar.')
    if errores:
        return render(solicitud, 'mensaje_detalle.html', {'datos': {'mensaje': mensaje, 'errores': errores}}, status=400)
    existente = next((reaccion for reaccion in mensaje.reacciones if reaccion['usuario']['nombreUsuario'] == usuario['nombreUsuario']), None)
    nueva = False
    if existente is None:
        mensaje.reacciones.append({'usuario': usuario, 'tipoReaccion': tipoReaccion, 'fecha': timezone.now()})
        nueva = True
    elif existente['tipoReaccion'] == tipoReaccion:
        mensaje.reacciones.remove(existente)
    else:
        existente['tipoReaccion'] = tipoReaccion
        existente['fecha'] = timezone.now()
        nueva = True
    mensaje.save()
    if nueva:
        otro = mensaje.receptor['nombreUsuario'] if usuario['nombreUsuario'] == mensaje.emisor['nombreUsuario'] else mensaje.emisor['nombreUsuario']
        notificar(otro, 'meGusta', '%s reaccionó %s a tu mensaje.' % (usuario['nombreUsuario'], ICONOS_REACCION[tipoReaccion]), origen=usuario['nombreUsuario'], categoria='reacciones', asunto='%s reaccionó a tu mensaje' % usuario['nombreUsuario'], ruta=reverse('mensaje_detalle', kwargs={'pk': mensaje.pk}), boton='Ver mensaje', ambito_bloqueo='mensajes')
    return redirect('mensaje_detalle', pk=mensaje.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def mensaje_eliminar(solicitud, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    comprobar_mensaje(solicitud, mensaje)
    if solicitud.method == 'GET':
        return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar mensaje', 'objeto': mensaje.contenido})
    usuario = solicitud.usuario.nombreUsuario
    participantes = (mensaje.emisor['nombreUsuario'], mensaje.receptor['nombreUsuario'])
    if usuario not in participantes:
        errores = ['Solo los participantes de la conversación pueden eliminar el mensaje.']
        return render(solicitud, 'mensaje_detalle.html', {'datos': {'mensaje': mensaje, 'errores': errores}}, status=400)

    if usuario not in mensaje.eliminadoPor:
        mensaje.eliminadoPor.append(usuario)
    if all(participante in mensaje.eliminadoPor for participante in participantes):
        mensaje.delete()
        return redirect('mensajes_listar')
    mensaje.save()
    return redirect('mensajes_listar')

@administrador_requerido
@require_POST
def mensajes_depurar(solicitud):
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Mensaje._meta.db_table].find({'eliminadoPor.1': {'$exists': True}}, {'_id': 1})]
    Mensaje.objects.filter(pk__in=ids).delete()
    return redirect('mensajes_listar')


@sesion_requerida
@require_http_methods(['GET'])
def grupos_listar(solicitud):
    texto = solicitud.GET.get('q')
    tipo = solicitud.GET.get('tipo')
    categoria = solicitud.GET.get('categoria')
    miembro = solicitud.GET.get('miembro')
    creador = solicitud.GET.get('creador')
    coleccion_mongo = connection.cursor().db_conn[Grupo._meta.db_table]
    orden = '-totalMiembros' if solicitud.GET.get('orden') == 'populares' else 'nombre'
    condicion = Q(estado=solicitud.GET.get('estado') or 'activo')
    if texto:
        condicion &= Q(nombre__icontains=texto) | Q(descripcion__icontains=texto)
    if tipo in TIPOS_GRUPO:
        condicion &= Q(tipo=tipo)
    if categoria:
        condicion &= Q(pk__in=[documento['_id'] for documento in coleccion_mongo.find({'categoria.slug': categoria}, {'_id': 1})])
    if miembro:
        condicion &= Q(pk__in=[documento['_id'] for documento in coleccion_mongo.find({'miembros.nombreUsuario': miembro}, {'_id': 1})])
    if creador:
        condicion &= Q(pk__in=[documento['_id'] for documento in coleccion_mongo.find({'creador.nombreUsuario': creador}, {'_id': 1})])
    grupos = Grupo.objects.filter(condicion).order_by(orden)
    datos = {'grupos': grupos[:50], 'total': grupos.count()}
    return render(solicitud, 'grupos_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def grupo_detalle(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    comprobar_grupo(solicitud, grupo)
    miembro = next((dato for dato in grupo.miembros if dato['nombreUsuario'] == solicitud.usuario.nombreUsuario), None)
    return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'usuarios': Usuario.objects.filter(activo__in=[True]), 'es_miembro': miembro is not None, 'puede_moderar': miembro is not None and miembro['rol'] in ('administrador', 'moderador'), 'es_administrador': miembro is not None and miembro['rol'] == 'administrador'}})

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def grupo_crear(solicitud):
    contexto = {'accion': 'crear', 'categorias': Categoria.objects.all().order_by('nombre')}
    valores = {'estado': 'activo'}
    formulario = FormularioGrupo(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'grupo_form.html', {'datos': contexto})
    errores = []
    creador = resumen_usuario(solicitud.usuario)
    categoria = Categoria.objects.filter(slug=solicitud.POST.get('categoria')).first()
    datos = {
        'nombre': solicitud.POST.get('nombre', '').strip(),
        'descripcion': solicitud.POST.get('descripcion') or None,
        'tipo': solicitud.POST.get('tipo') or 'publico',
        'imagenUrl': solicitud.POST.get('imagenUrl') or None,
        'reglas': [regla.strip() for regla in solicitud.POST.get('reglas', '').split('\n') if regla.strip()],
        'estado': 'activo',
    }
    if not 3 <= len(datos['nombre']) <= 80:
        errores.append('El nombre debe tener entre 3 y 80 caracteres.')
    if Grupo.objects.filter(nombre=datos['nombre']).exists():
        errores.append('Ya existe un grupo con ese nombre.')
    if datos['descripcion'] and len(datos['descripcion']) > 1000:
        errores.append('La descripción admite máximo 1000 caracteres.')
    if datos['tipo'] not in TIPOS_GRUPO:
        errores.append('El tipo debe ser publico o privado.')
    if datos['imagenUrl'] and not PATRON_URL.match(datos['imagenUrl']):
        errores.append('La imagenUrl debe ser un enlace válido.')
    if not 3 <= len(creador['nombreUsuario']) <= 30:
        errores.append('El creador debe tener un nombre de usuario de 3 a 30 caracteres.')
    if categoria is None:
        errores.append('La categoría no existe.')
    if len(datos['reglas']) > 20 or any(len(regla) > 300 for regla in datos['reglas']):
        errores.append('Máximo 20 reglas de hasta 300 caracteres.')
    grupo = None
    if not errores:
        datos.update(
            creador=creador,
            categoria={'nombre': categoria.nombre, 'slug': categoria.slug},
            miembros=[{**creador, 'rol': 'administrador', 'fechaIngreso': timezone.now()}],
            foros=[],
            totalMiembros=1,
            fechaCreacion=timezone.now(),
        )
        grupo = Grupo(**datos)
        try:
            grupo.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'grupo_form.html', {'datos': contexto})
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def grupo_actualizar(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    comprobar_propietario(solicitud, grupo.creador['nombreUsuario'])
    contexto = {
        'accion': 'actualizar',
        'grupo': grupo,
        'categorias': Categoria.objects.all().order_by('nombre'),
    }
    valores = {campo: getattr(grupo, campo, None) for campo in FormularioGrupo().fields}
    valores['categoria'] = grupo.categoria['slug']
    valores['reglas'] = '\n'.join(grupo.reglas)
    formulario = FormularioGrupo(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'grupo_form.html', {'datos': contexto})
    errores = []
    categoria = Categoria.objects.filter(slug=solicitud.POST.get('categoria')).first()
    datos = {
        'nombre': solicitud.POST.get('nombre', '').strip(),
        'descripcion': solicitud.POST.get('descripcion') or None,
        'tipo': solicitud.POST.get('tipo') or 'publico',
        'imagenUrl': solicitud.POST.get('imagenUrl') or None,
        'reglas': [regla.strip() for regla in solicitud.POST.get('reglas', '').split('\n') if regla.strip()],
        'estado': solicitud.POST.get('estado') or 'activo',
    }
    if not 3 <= len(datos['nombre']) <= 80:
        errores.append('El nombre debe tener entre 3 y 80 caracteres.')
    if Grupo.objects.filter(nombre=datos['nombre']).exclude(pk=grupo.pk).exists():
        errores.append('Ya existe otro grupo con ese nombre.')
    if datos['descripcion'] and len(datos['descripcion']) > 1000:
        errores.append('La descripción admite máximo 1000 caracteres.')
    if datos['tipo'] not in TIPOS_GRUPO:
        errores.append('El tipo debe ser publico o privado.')
    if datos['estado'] not in ESTADOS_GRUPO:
        errores.append('El estado debe ser activo, archivado o suspendido.')
    if datos['imagenUrl'] and not PATRON_URL.match(datos['imagenUrl']):
        errores.append('La imagenUrl debe ser un enlace válido.')
    if categoria is None:
        errores.append('La categoría no existe.')
    if len(datos['reglas']) > 20 or any(len(regla) > 300 for regla in datos['reglas']):
        errores.append('Máximo 20 reglas de hasta 300 caracteres.')
    if not errores:
        for campo, valor in datos.items():
            setattr(grupo, campo, valor)
        grupo.categoria = {'nombre': categoria.nombre, 'slug': categoria.slug}
        try:
            grupo.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'grupo_form.html', {'datos': contexto})
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def grupo_eliminar(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    comprobar_propietario(solicitud, grupo.creador['nombreUsuario'])
    if solicitud.method == 'GET':
        return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar grupo', 'objeto': grupo.nombre})
    if grupo.totalMiembros > 1:
        errores = ['No se puede eliminar el grupo porque todavía tiene miembros además del creador.']
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.delete()
    return redirect('grupos_listar')

@sesion_requerida
@require_POST
def grupo_unirse(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    usuario = resumen_usuario(solicitud.usuario)
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if grupo.estado != 'activo':
        errores.append('Solo puedes unirte a grupos activos.')
    if grupo.tipo == 'privado':
        errores.append('Este grupo es privado; solo se ingresa por invitación.')
    if any(miembro['nombreUsuario'] == usuario['nombreUsuario'] for miembro in grupo.miembros):
        errores.append('Ya eres miembro de este grupo.')
    if grupo.estado != 'activo':
        errores.append('El grupo no está activo.')
    if len(grupo.miembros) >= 1000:
        errores.append('El grupo llegó al límite de 1000 miembros.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.append({**usuario, 'rol': 'miembro', 'fechaIngreso': timezone.now()})
    grupo.totalMiembros += 1
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def grupo_invitar(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = solicitud.usuario.nombreUsuario
    usuario = resumen_usuario(get_object_or_404(Usuario, nombreUsuario=solicitud.POST.get('usuario', ''), activo__in=[True]))
    invitador = next((miembro for miembro in grupo.miembros if miembro['nombreUsuario'] == quien), None)
    if invitador is None or invitador['rol'] not in ('administrador', 'moderador'):
        errores.append('Solo un administrador o moderador del grupo puede invitar.')
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if any(miembro['nombreUsuario'] == usuario['nombreUsuario'] for miembro in grupo.miembros):
        errores.append('Ese usuario ya es miembro del grupo.')
    if grupo.estado != 'activo':
        errores.append('El grupo no está activo.')
    if len(grupo.miembros) >= 1000:
        errores.append('El grupo llegó al límite de 1000 miembros.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.append({**usuario, 'rol': 'miembro', 'fechaIngreso': timezone.now()})
    grupo.totalMiembros += 1
    grupo.save()
    notificar(usuario['nombreUsuario'], 'sistema', '%s te agregó al grupo «%s».' % (quien, grupo.nombre), origen=quien, categoria='avisos', asunto='%s te agregó a un grupo' % quien, ruta=reverse('grupo_detalle', kwargs={'pk': grupo.pk}), boton='Ver el grupo', ambito_bloqueo='contenido')
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def grupo_salir(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    usuario = solicitud.usuario.nombreUsuario
    miembro = next((m for m in grupo.miembros if m['nombreUsuario'] == usuario), None)
    errores = []
    if miembro is None:
        errores.append('No eres miembro de este grupo.')
    elif usuario == grupo.creador['nombreUsuario']:
        errores.append('El creador no puede salir del grupo; elimínalo o transfiere el grupo.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.remove(miembro)
    grupo.totalMiembros = max(0, grupo.totalMiembros - 1)
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def grupo_cambiar_rol(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = solicitud.usuario.nombreUsuario
    usuario = solicitud.POST.get('usuario', '')
    rol = solicitud.POST.get('rol')
    administrador = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    miembro = next((m for m in grupo.miembros if m['nombreUsuario'] == usuario), None)
    if administrador is None or administrador['rol'] != 'administrador':
        errores.append('Solo un administrador puede cambiar roles.')
    if miembro is None:
        errores.append('El usuario no es miembro del grupo.')
    if rol == 'administrador' and quien != grupo.creador['nombreUsuario']:
        errores.append('Solo el creador puede nombrar administradores.')
    if rol not in ROLES_GRUPO:
        errores.append('El rol debe ser miembro, moderador o admin.')
    if usuario == grupo.creador['nombreUsuario'] and rol != 'administrador':
        errores.append('El creador siempre debe ser admin.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    miembro['rol'] = rol
    grupo.save()
    notificar(usuario, 'sistema', 'Tu rol en el grupo «%s» ahora es %s.' % (grupo.nombre, rol), origen=quien, categoria='avisos', asunto='Cambió tu rol en un grupo', ruta=reverse('grupo_detalle', kwargs={'pk': grupo.pk}), boton='Ver el grupo')
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def grupo_expulsar(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = solicitud.usuario.nombreUsuario
    usuario = solicitud.POST.get('usuario', '')
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    miembro = next((m for m in grupo.miembros if m['nombreUsuario'] == usuario), None)
    if ejecutor is None or ejecutor['rol'] not in ('administrador', 'moderador'):
        errores.append('Solo un administrador o moderador puede expulsar miembros.')
    if miembro is None:
        errores.append('El usuario no es miembro del grupo.')
    elif usuario == grupo.creador['nombreUsuario']:
        errores.append('No se puede expulsar al creador del grupo.')
    elif miembro['rol'] == 'administrador' and ejecutor and ejecutor['rol'] != 'administrador':
        errores.append('Un moderador no puede expulsar a un administrador.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.remove(miembro)
    grupo.totalMiembros = max(0, grupo.totalMiembros - 1)
    grupo.save()
    notificar(usuario, 'sistema', 'Ya no eres parte del grupo «%s».' % grupo.nombre, origen=quien, categoria='avisos', asunto='Saliste de un grupo')
    return redirect('grupo_detalle', pk=grupo.pk)


@sesion_requerida
@require_POST
def foro_crear(solicitud, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = solicitud.usuario.nombreUsuario
    nombre = solicitud.POST.get('nombre', '').strip()
    descripcion = solicitud.POST.get('descripcion') or None
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    if ejecutor is None or ejecutor['rol'] not in ('administrador', 'moderador'):
        errores.append('Solo un administrador o moderador puede crear foros.')
    if not 1 <= len(nombre) <= 80:
        errores.append('El nombre del foro debe tener entre 1 y 80 caracteres.')
    if any(foro['nombre'].lower() == nombre.lower() for foro in grupo.foros):
        errores.append('Ya existe un foro con ese nombre en el grupo.')
    if descripcion and len(descripcion) > 500:
        errores.append('La descripción admite máximo 500 caracteres.')
    if len(grupo.foros) >= 10:
        errores.append('El grupo llegó al límite de 10 foros.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.foros.append({
        'nombre': nombre,
        'descripcion': descripcion,
        'comentarios': [],
        'fechaCreacion': timezone.now(),
    })
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def foro_eliminar(solicitud, pk, indice_foro):
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    quien = solicitud.usuario.nombreUsuario
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    if ejecutor is None or ejecutor['rol'] not in ('administrador', 'moderador'):
        errores = ['Solo un administrador o moderador puede eliminar foros.']
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    del grupo.foros[indice_foro]
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def foro_comentar(solicitud, pk, indice_foro):
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    foro = grupo.foros[indice_foro]
    errores = []
    autor = resumen_usuario(solicitud.usuario)
    titulo = solicitud.POST.get('titulo') or None
    contenido = solicitud.POST.get('contenido', '').strip()
    formato = solicitud.POST.get('formato') or 'texto'
    if not any(m['nombreUsuario'] == autor['nombreUsuario'] for m in grupo.miembros):
        errores.append('Solo los miembros del grupo pueden comentar en sus foros.')
    if titulo and len(titulo) > 150:
        errores.append('El título admite máximo 150 caracteres.')
    if not 1 <= len(contenido) <= 1000:
        errores.append('El comentario debe tener entre 1 y 1000 caracteres.')
    if formato not in FORMATOS_COMENTARIO:
        errores.append('El formato del comentario no es válido.')
    if len(foro['comentarios']) >= 200:
        errores.append('El foro llegó al límite de 200 comentarios.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    foro['comentarios'].append({
        'autor': autor,
        'titulo': titulo,
        'contenido': contenido,
        'formato': formato,
        'menciones': [],
        'archivosAdjuntos': [],
        'respuestas': [],
        'reacciones': [],
        'conteoReacciones': {tipo: 0 for tipo in TIPOS_REACCION},
        'fijado': False,
        'cerrado': False,
        'estado': 'activo',
        'fechaCreacion': timezone.now(),
        'fechaEdicion': None,
    })
    grupo.save()
    responsables = [m['nombreUsuario'] for m in grupo.miembros if m['rol'] in ('administrador', 'moderador')]
    for responsable in responsables[:20]:
        notificar(responsable, 'comentario', '%s comentó en el foro «%s» del grupo «%s».' % (autor['nombreUsuario'], foro['nombre'], grupo.nombre), origen=autor['nombreUsuario'], categoria='comentarios', asunto='Nuevo comentario en el grupo «%s»' % grupo.nombre, ruta=reverse('grupo_detalle', kwargs={'pk': grupo.pk}), detalle=contenido, boton='Ver el foro', ambito_bloqueo='contenido')
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def foro_comentario_actualizar(solicitud, pk, indice_foro, indice):
    grupo = get_object_or_404(Grupo, pk=pk)
    comprobar_grupo(solicitud, grupo)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    comentarios = grupo.foros[indice_foro]['comentarios']
    if not 0 <= indice < len(comentarios):
        raise Http404
    comprobar_propietario(solicitud, comentarios[indice]['autor']['nombreUsuario'])
    errores = []
    contenido = solicitud.POST.get('contenido', '').strip()
    if comentarios[indice]['cerrado']:
        errores.append('El comentario está cerrado y no admite ediciones.')
    if not 1 <= len(contenido) <= 1000:
        errores.append('El comentario debe tener entre 1 y 1000 caracteres.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    comentarios[indice]['contenido'] = contenido
    comentarios[indice]['estado'] = 'editado'
    comentarios[indice]['fechaEdicion'] = timezone.now()
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def foro_comentario_moderar(solicitud, pk, indice_foro, indice):

    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    comentarios = grupo.foros[indice_foro]['comentarios']
    if not 0 <= indice < len(comentarios):
        raise Http404
    quien = solicitud.usuario.nombreUsuario
    accion = solicitud.POST.get('accion')
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    errores = []
    if ejecutor is None or ejecutor['rol'] not in ('administrador', 'moderador'):
        errores.append('Solo un administrador o moderador puede moderar comentarios.')
    if accion not in ('fijar', 'cerrar'):
        errores.append('La acción debe ser fijar o cerrar.')
    if errores:
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    campo = 'fijado' if accion == 'fijar' else 'cerrado'
    comentarios[indice][campo] = not comentarios[indice][campo]
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)

@sesion_requerida
@require_POST
def foro_comentario_eliminar(solicitud, pk, indice_foro, indice):
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    comentarios = grupo.foros[indice_foro]['comentarios']
    if not 0 <= indice < len(comentarios):
        raise Http404
    quien = solicitud.usuario.nombreUsuario
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    es_autor = comentarios[indice]['autor']['nombreUsuario'] == quien
    if not es_autor and (ejecutor is None or ejecutor['rol'] not in ('administrador', 'moderador')):
        errores = ['Solo el autor, un administrador o un moderador puede eliminar el comentario.']
        return render(solicitud, 'grupo_detalle.html', {'datos': {'grupo': grupo, 'errores': errores}}, status=400)
    del comentarios[indice]
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)


@sesion_requerida
@require_http_methods(['GET'])
def moderaciones_listar(solicitud):
    return bloqueos_activos(solicitud)

@sesion_requerida
@require_http_methods(['GET'])
def reportes_pendientes(solicitud):
    return administracion.consultar_reportes(solicitud, pendientes=True)

@sesion_requerida
@require_http_methods(['GET'])
def bloqueos_activos(solicitud):
    usuario = solicitud.usuario.nombreUsuario
    filtro = {
        'tipo': 'bloqueo',
        '$or': [{'fechaExpiracion': None}, {'fechaExpiracion': {'$gt': timezone.now()}}],
    }
    if usuario:
        filtro['bloqueador.nombreUsuario'] = usuario
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Moderacion._meta.db_table].find(filtro, {'_id': 1})]
    bloqueos = Moderacion.objects.filter(pk__in=ids).order_by('-fechaCreacion')
    datos = {'moderaciones': bloqueos[:50], 'total': bloqueos.count(), 'estado': 'activos'}
    return render(solicitud, 'moderacion_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def moderacion_detalle(solicitud, pk):
    moderacion = get_object_or_404(Moderacion, pk=pk, tipo='bloqueo')
    comprobar_propietario(solicitud, moderacion.bloqueador['nombreUsuario'])
    return render(solicitud, 'moderacion_detalle.html', {'datos': {'moderacion': moderacion}})

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def reporte_crear(solicitud):
    return administracion.crear_reporte(solicitud)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def reporte_resolver(solicitud, pk):
    return administracion.resolver_reporte(solicitud, pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def bloqueo_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {'estado': 'activo'}
    formulario = FormularioBloqueo(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'bloqueo_form.html', {'datos': contexto})
    errores = []
    bloqueador = resumen_usuario(solicitud.usuario)
    bloqueado = resumen_usuario(get_object_or_404(Usuario, nombreUsuario=formulario.cleaned_data['bloqueado'], activo__in=[True]))
    ambito = solicitud.POST.get('ambito') or 'total'
    expiracion_texto = solicitud.POST.get('fechaExpiracion')
    expiracion = None
    if expiracion_texto:
        expiracion = parse_datetime(expiracion_texto)
        if expiracion is None:
            errores.append('La fecha de expiración no tiene un formato válido.')
        else:
            if timezone.is_naive(expiracion):
                expiracion = timezone.make_aware(expiracion)
            if expiracion <= timezone.now():
                errores.append('La fecha de expiración debe ser futura.')
    if not 3 <= len(bloqueador['nombreUsuario']) <= 30:
        errores.append('El bloqueador debe tener un nombre de usuario de 3 a 30 caracteres.')
    if not 3 <= len(bloqueado['nombreUsuario']) <= 30:
        errores.append('El bloqueado debe tener un nombre de usuario de 3 a 30 caracteres.')
    if bloqueador['nombreUsuario'] == bloqueado['nombreUsuario']:
        errores.append('No puedes bloquearte a ti mismo.')
    if ambito not in AMBITOS_BLOQUEO:
        errores.append('El ámbito debe ser total, mensajes o contenido.')
    if not errores:
        filtro = {
            'tipo': 'bloqueo',
            'bloqueador.nombreUsuario': bloqueador['nombreUsuario'],
            'bloqueado.nombreUsuario': bloqueado['nombreUsuario'],
            'ambito': ambito,
            '$or': [{'fechaExpiracion': None}, {'fechaExpiracion': {'$gt': timezone.now()}}],
        }
        if connection.cursor().db_conn[Moderacion._meta.db_table].find_one(filtro, {'_id': 1}):
            errores.append('Ya existe un bloqueo activo con ese usuario y ámbito.')
    moderacion = None
    if not errores:
        moderacion = Moderacion(
            tipo='bloqueo',
            bloqueador=bloqueador,
            bloqueado=bloqueado,
            ambito=ambito,
            fechaExpiracion=expiracion,
            fechaCreacion=timezone.now(),
        )
        try:
            moderacion.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'bloqueo_form.html', {'datos': contexto})
    moderacion.save()
    return redirect('moderacion_detalle', pk=moderacion.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def bloqueo_eliminar(solicitud, pk):

    moderacion = get_object_or_404(Moderacion, pk=pk, tipo='bloqueo')
    comprobar_propietario(solicitud, moderacion.bloqueador['nombreUsuario'])
    if solicitud.method == 'GET':
        return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar moderacion', 'objeto': moderacion.ambito})
    if solicitud.usuario.nombreUsuario != moderacion.bloqueador['nombreUsuario'] and solicitud.usuario.rol != 'administrador':
        errores = ['Solo quien creó el bloqueo puede quitarlo.']
        return render(solicitud, 'moderacion_detalle.html', {'datos': {'moderacion': moderacion, 'errores': errores}}, status=400)
    moderacion.delete()
    return redirect('moderaciones_listar')

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def moderacion_eliminar(solicitud, pk):
    return bloqueo_eliminar(solicitud, pk)

@administrador_requerido
@require_POST
def bloqueos_depurar(solicitud):
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Moderacion._meta.db_table].find({'tipo': 'bloqueo', 'fechaExpiracion': {'$lte': timezone.now()}}, {'_id': 1})]
    Moderacion.objects.filter(pk__in=ids).delete()
    return redirect('moderaciones_listar')


def comprobar_mensaje(solicitud, mensaje):
    nombre = solicitud.usuario.nombreUsuario
    if nombre not in (mensaje.emisor['nombreUsuario'], mensaje.receptor['nombreUsuario']) or nombre in mensaje.eliminadoPor:
        raise PermissionDenied('No puedes consultar este mensaje.')


def comprobar_grupo(solicitud, grupo):
    if grupo.tipo == 'privado' and not any(dato['nombreUsuario'] == solicitud.usuario.nombreUsuario for dato in grupo.miembros) and solicitud.usuario.rol != 'administrador':
        raise PermissionDenied('Este grupo es privado.')


@sesion_requerida
@require_http_methods(['GET', 'POST'])
def mensaje_actualizar(solicitud, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    comprobar_mensaje(solicitud, mensaje)
    if mensaje.emisor['nombreUsuario'] != solicitud.usuario.nombreUsuario or mensaje.leido:
        raise PermissionDenied('Solo puedes editar tus mensajes antes de que sean leídos.')
    from django import forms
    class FormularioContenido(forms.Form):
        contenido = forms.CharField(max_length=5000, widget=forms.Textarea)
    formulario = FormularioContenido(solicitud.POST or None, initial={'contenido': mensaje.contenido})
    if solicitud.method == 'POST' and formulario.is_valid():
        mensaje.contenido = formulario.cleaned_data['contenido']
        mensaje.save()
        return redirect('mensaje_detalle', pk=pk)
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Editar mensaje', 'formulario': formulario})
