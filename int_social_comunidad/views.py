
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import connection
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.http import Http404
from .models import Categoria, Mensaje, Grupo, Moderacion
from .arrays import *
 
 
"""MENSAJES VIEWS"""
def mensajes_listar(request):
    usuario = request.GET.get('usuario')
    con = request.GET.get('con')
    leido = request.GET.get('leido')
    sentido = 'fechaEnvio' if request.GET.get('orden') == 'antiguos' else '-fechaEnvio'
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
        mensajes = mensajes.filter(id_buscar=ids)
    mensajes = mensajes.order_by(sentido)
    data = {'mensajes': mensajes[:50], 'total': mensajes.count()}
    return render(request, 'mensajes_lista.html', {'data': data})
 
def mensajes_no_leidos(request):
    usuario = request.GET.get('usuario')
    ids = []
    if usuario:
        filtro = {'receptor.nombreUsuario': usuario, 'leido': False, 'eliminadoPor': {'$ne': usuario}}
        ids = [documento['_id'] for documento in connection.cursor().db_conn[Mensaje._meta.db_table].find(filtro, {'_id': 1})]
    mensajes = Mensaje.objects.filter(id_buscar=ids).order_by('-fechaEnvio')
    data = {'mensajes': mensajes[:50], 'total': mensajes.count(), 'estado': 'no leídos'}
    return render(request, 'mensajes_lista.html', {'data': data})
 
def mensaje_detalle(request, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    return render(request, 'mensaje_detalle.html', {'data': {'mensaje': mensaje}})
 
def mensaje_crear(request):
    contexto = {'accion': 'crear'}
    if request.method == 'GET':
        return render(request, 'mensaje_form.html', {'data': contexto})
    errores = []
    emisor = {'nombreUsuario': request.POST.get('emisor', ''), 'imagenPerfil': None}
    receptor = {'nombreUsuario': request.POST.get('receptor', ''), 'imagenPerfil': None}
    datos = {
        'contenido': request.POST.get('contenido', '').strip() or None,
        'tipo': request.POST.get('tipo') or 'texto',
        'adjuntos': [url.strip() for url in request.POST.get('adjuntos', '').split(',') if url.strip()],
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
        errores.append('Todos los adjuntos deben ser links válidos.')
    if len(datos['adjuntos']) > 10:
        errores.append('Máximo 10 adjuntos por mensaje.')
    
    if not errores:
        filtro = {
            'tipo': 'bloqueo',
            'bloqueador.nombreUsuario': receptor['nombreUsuario'],
            'bloqueado.nombreUsuario': emisor['nombreUsuario'],
            '$or': [{'fechaExpiracion': None}, {'fechaExpiracion': {'$gt': timezone.now()}}],
        }
        if connection.cursor().db_conn[Moderacion._meta.db_table].find_one(filtro, {'_id': 1}):
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
        return render(request, 'mensaje_form.html', {'data': contexto})
    mensaje.save()
    return redirect('mensaje_detalle', pk=mensaje.pk)
 
def mensaje_marcar_leido(request, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    if not mensaje.leido:
        mensaje.leido = True
        mensaje.fechaLectura = timezone.now()
        mensaje.save()
    return redirect('mensaje_detalle', pk=mensaje.pk)
 
def mensajes_marcar_leidos(request):
    receptor = request.POST.get('receptor')
    emisor = request.POST.get('emisor')
    filtro = {'receptor.nombreUsuario': receptor, 'leido': False}
    if emisor:
        filtro['emisor.nombreUsuario'] = emisor
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Mensaje._meta.db_table].find(filtro, {'_id': 1})]
    Mensaje.objects.filter(id_buscar=ids).update(leido=True, fechaLectura=timezone.now())
    return redirect('mensajes_listar')
 
def mensaje_reaccionar(request, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    errores = []
    usuario = {'nombreUsuario': request.POST.get('usuario', ''), 'imagenPerfil': None}
    tipoReaccion = request.POST.get('tipoReaccion')
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if tipoReaccion not in TIPOS_REACCION:
        errores.append('Tipo de reacción inválido.')
    if usuario['nombreUsuario'] not in (mensaje.emisor['nombreUsuario'], mensaje.receptor['nombreUsuario']):
        errores.append('Solo los participantes de la conversación pueden reaccionar.')
    if errores:
        return render(request, 'mensaje_detalle.html', {'data': {'mensaje': mensaje, 'errores': errores}}, status=400)
    existente = next((reaccion for reaccion in mensaje.reacciones if reaccion['usuario']['nombreUsuario'] == usuario['nombreUsuario']), None)
    if existente is None:
        mensaje.reacciones.append({'usuario': usuario, 'tipoReaccion': tipoReaccion, 'fecha': timezone.now()})
    elif existente['tipoReaccion'] == tipoReaccion:
        mensaje.reacciones.remove(existente)
    else:
        existente['tipoReaccion'] = tipoReaccion
        existente['fecha'] = timezone.now()
    mensaje.save()
    return redirect('mensaje_detalle', pk=mensaje.pk)
 
def mensaje_eliminar(request, pk):
    mensaje = get_object_or_404(Mensaje, pk=pk)
    usuario = request.POST.get('usuario', '')
    participantes = (mensaje.emisor['nombreUsuario'], mensaje.receptor['nombreUsuario'])
    if usuario not in participantes:
        errores = ['Solo los participantes de la conversación pueden eliminar el mensaje.']
        return render(request, 'mensaje_detalle.html', {'data': {'mensaje': mensaje, 'errores': errores}}, status=400)
    # Eliminación "para mí": se borra de verdad cuando ambos lo eliminaron
    if usuario not in mensaje.eliminadoPor:
        mensaje.eliminadoPor.append(usuario)
    if all(participante in mensaje.eliminadoPor for participante in participantes):
        mensaje.delete()
        return redirect('mensajes_listar')
    mensaje.save()
    return redirect('mensajes_listar')
 
def mensajes_depurar(request):
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Mensaje._meta.db_table].find({'eliminadoPor.1': {'$exists': True}}, {'_id': 1})]
    Mensaje.objects.filter(id_buscar=ids).delete()
    return redirect('mensajes_listar')
 
 
"""GRUPOS VIEWS"""
def grupos_listar(request):
    texto = request.GET.get('q')
    tipo = request.GET.get('tipo')
    categoria = request.GET.get('categoria')
    miembro = request.GET.get('miembro')
    creador = request.GET.get('creador')
    coleccion_mongo = connection.cursor().db_conn[Grupo._meta.db_table]
    orden = '-totalMiembros' if request.GET.get('orden') == 'populares' else 'nombre'
    condicion = Q(estado=request.GET.get('estado') or 'activo')
    if texto:
        condicion &= Q(nombre__tiene=texto) | Q(descripcion__tiene=texto)
    if tipo in TIPOS_GRUPO:
        condicion &= Q(tipo=tipo)
    if categoria:
        condicion &= Q(id_buscar=[documento['_id'] for documento in coleccion_mongo.find({'categoria.slug': categoria}, {'_id': 1})])
    if miembro:
        condicion &= Q(id_buscar=[documento['_id'] for documento in coleccion_mongo.find({'miembros.nombreUsuario': miembro}, {'_id': 1})])
    if creador:
        condicion &= Q(id_buscar=[documento['_id'] for documento in coleccion_mongo.find({'creador.nombreUsuario': creador}, {'_id': 1})])
    grupos = Grupo.objects.filter(condicion).order_by(orden)
    data = {'grupos': grupos[:50], 'total': grupos.count()}
    return render(request, 'grupos_lista.html', {'data': data})
 
def grupo_detalle(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo}})
 
def grupo_crear(request):
    contexto = {'accion': 'crear', 'categorias': Categoria.objects.all().order_by('nombre')}
    if request.method == 'GET':
        return render(request, 'grupo_form.html', {'data': contexto})
    errores = []
    creador = {'nombreUsuario': request.POST.get('creador', ''), 'imagenPerfil': None}
    categoria = Categoria.objects.filter(slug=request.POST.get('categoria')).first()
    datos = {
        'nombre': request.POST.get('nombre', '').strip(),
        'descripcion': request.POST.get('descripcion') or None,
        'tipo': request.POST.get('tipo') or 'publico',
        'imagenUrl': request.POST.get('imagenUrl') or None,
        'reglas': [regla.strip() for regla in request.POST.get('reglas', '').split('\n') if regla.strip()],
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
        errores.append('La imagenUrl debe ser un link válido.')
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
            miembros=[{**creador, 'rol': 'admin', 'fechaIngreso': timezone.now()}],
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
        return render(request, 'grupo_form.html', {'data': contexto})
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def grupo_actualizar(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    contexto = {
        'accion': 'actualizar',
        'grupo': grupo,
        'categorias': Categoria.objects.all().order_by('nombre'),
    }
    if request.method == 'GET':
        return render(request, 'grupo_form.html', {'data': contexto})
    errores = []
    categoria = Categoria.objects.filter(slug=request.POST.get('categoria')).first()
    datos = {
        'nombre': request.POST.get('nombre', '').strip(),
        'descripcion': request.POST.get('descripcion') or None,
        'tipo': request.POST.get('tipo') or 'publico',
        'imagenUrl': request.POST.get('imagenUrl') or None,
        'reglas': [regla.strip() for regla in request.POST.get('reglas', '').split('\n') if regla.strip()],
        'estado': request.POST.get('estado') or 'activo',
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
        errores.append('La imagenUrl debe ser un link válido.')
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
        return render(request, 'grupo_form.html', {'data': contexto})
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def grupo_eliminar(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    if grupo.totalMiembros > 1:
        errores = ['No se puede eliminar el grupo porque todavía tiene miembros además del creador.']
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.delete()
    return redirect('grupos_listar')
 
def grupo_unirse(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    usuario = {'nombreUsuario': request.POST.get('usuario', ''), 'imagenPerfil': None}
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if grupo.estado != 'activo':
        errores.append('Solo puedes unirte a grupos activos.')
    if grupo.tipo == 'privado':
        errores.append('Este grupo es privado; solo se ingresa por invitación.')
    if any(miembro['nombreUsuario'] == usuario['nombreUsuario'] for miembro in grupo.miembros):
        errores.append('Ya eres miembro de este grupo.')
    if len(grupo.miembros) >= 1000:
        errores.append('El grupo llegó al límite de 1000 miembros.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.append({**usuario, 'rol': 'miembro', 'fechaIngreso': timezone.now()})
    grupo.totalMiembros += 1
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def grupo_invitar(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = request.POST.get('invitador', '')
    usuario = {'nombreUsuario': request.POST.get('usuario', ''), 'imagenPerfil': None}
    invitador = next((miembro for miembro in grupo.miembros if miembro['nombreUsuario'] == quien), None)
    if invitador is None or invitador['rol'] not in ('admin', 'moderador'):
        errores.append('Solo un admin o moderador del grupo puede invitar.')
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if any(miembro['nombreUsuario'] == usuario['nombreUsuario'] for miembro in grupo.miembros):
        errores.append('Ese usuario ya es miembro del grupo.')
    if len(grupo.miembros) >= 1000:
        errores.append('El grupo llegó al límite de 1000 miembros.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.append({**usuario, 'rol': 'miembro', 'fechaIngreso': timezone.now()})
    grupo.totalMiembros += 1
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def grupo_salir(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    usuario = request.POST.get('usuario', '')
    miembro = next((m for m in grupo.miembros if m['nombreUsuario'] == usuario), None)
    errores = []
    if miembro is None:
        errores.append('No eres miembro de este grupo.')
    elif usuario == grupo.creador['nombreUsuario']:
        errores.append('El creador no puede salir del grupo; elimínalo o transfiere el grupo.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.remove(miembro)
    grupo.totalMiembros = max(0, grupo.totalMiembros - 1)
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def grupo_cambiar_rol(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = request.POST.get('admin', '')
    usuario = request.POST.get('usuario', '')
    rol = request.POST.get('rol')
    administrador = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    miembro = next((m for m in grupo.miembros if m['nombreUsuario'] == usuario), None)
    if administrador is None or administrador['rol'] != 'admin':
        errores.append('Solo un admin puede cambiar roles.')
    if miembro is None:
        errores.append('El usuario no es miembro del grupo.')
    if rol not in ROLES_GRUPO:
        errores.append('El rol debe ser miembro, moderador o admin.')
    if usuario == grupo.creador['nombreUsuario'] and rol != 'admin':
        errores.append('El creador siempre debe ser admin.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    miembro['rol'] = rol
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def grupo_expulsar(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = request.POST.get('moderador', '')
    usuario = request.POST.get('usuario', '')
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    miembro = next((m for m in grupo.miembros if m['nombreUsuario'] == usuario), None)
    if ejecutor is None or ejecutor['rol'] not in ('admin', 'moderador'):
        errores.append('Solo un admin o moderador puede expulsar miembros.')
    if miembro is None:
        errores.append('El usuario no es miembro del grupo.')
    elif usuario == grupo.creador['nombreUsuario']:
        errores.append('No se puede expulsar al creador del grupo.')
    elif miembro['rol'] == 'admin' and ejecutor and ejecutor['rol'] != 'admin':
        errores.append('Un moderador no puede expulsar a un admin.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.miembros.remove(miembro)
    grupo.totalMiembros = max(0, grupo.totalMiembros - 1)
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
"""FOROS DE GRUPO VIEWS"""
def foro_crear(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    errores = []
    quien = request.POST.get('usuario', '')
    nombre = request.POST.get('nombre', '').strip()
    descripcion = request.POST.get('descripcion') or None
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    if ejecutor is None or ejecutor['rol'] not in ('admin', 'moderador'):
        errores.append('Solo un admin o moderador puede crear foros.')
    if not 1 <= len(nombre) <= 80:
        errores.append('El nombre del foro debe tener entre 1 y 80 caracteres.')
    if any(foro['nombre'].lower() == nombre.lower() for foro in grupo.foros):
        errores.append('Ya existe un foro con ese nombre en el grupo.')
    if descripcion and len(descripcion) > 500:
        errores.append('La descripción admite máximo 500 caracteres.')
    if len(grupo.foros) >= 10:
        errores.append('El grupo llegó al límite de 10 foros.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    grupo.foros.append({
        'nombre': nombre,
        'descripcion': descripcion,
        'comentarios': [],
        'fechaCreacion': timezone.now(),
    })
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def foro_eliminar(request, pk, indice_foro):
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    quien = request.POST.get('usuario', '')
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    if ejecutor is None or ejecutor['rol'] not in ('admin', 'moderador'):
        errores = ['Solo un admin o moderador puede eliminar foros.']
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    del grupo.foros[indice_foro]
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def foro_comentar(request, pk, indice_foro):
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    foro = grupo.foros[indice_foro]
    errores = []
    autor = {'nombreUsuario': request.POST.get('autor', ''), 'imagenPerfil': None}
    titulo = request.POST.get('titulo') or None
    contenido = request.POST.get('contenido', '').strip()
    formato = request.POST.get('formato') or 'texto'
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
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
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
    return redirect('grupo_detalle', pk=grupo.pk)
 
def foro_comentario_actualizar(request, pk, indice_foro, indice):
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    comentarios = grupo.foros[indice_foro]['comentarios']
    if not 0 <= indice < len(comentarios):
        raise Http404
    errores = []
    contenido = request.POST.get('contenido', '').strip()
    if comentarios[indice]['cerrado']:
        errores.append('El comentario está cerrado y no admite ediciones.')
    if not 1 <= len(contenido) <= 1000:
        errores.append('El comentario debe tener entre 1 y 1000 caracteres.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    comentarios[indice]['contenido'] = contenido
    comentarios[indice]['estado'] = 'editado'
    comentarios[indice]['fechaEdicion'] = timezone.now()
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def foro_comentario_moderar(request, pk, indice_foro, indice):
    """Fija/desfija o cierra/abre un comentario del foro (solo admin o moderador)."""
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    comentarios = grupo.foros[indice_foro]['comentarios']
    if not 0 <= indice < len(comentarios):
        raise Http404
    quien = request.POST.get('usuario', '')
    accion = request.POST.get('accion')
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    errores = []
    if ejecutor is None or ejecutor['rol'] not in ('admin', 'moderador'):
        errores.append('Solo un admin o moderador puede moderar comentarios.')
    if accion not in ('fijar', 'cerrar'):
        errores.append('La acción debe ser fijar o cerrar.')
    if errores:
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    campo = 'fijado' if accion == 'fijar' else 'cerrado'
    comentarios[indice][campo] = not comentarios[indice][campo]
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
def foro_comentario_eliminar(request, pk, indice_foro, indice):
    grupo = get_object_or_404(Grupo, pk=pk)
    if not 0 <= indice_foro < len(grupo.foros):
        raise Http404
    comentarios = grupo.foros[indice_foro]['comentarios']
    if not 0 <= indice < len(comentarios):
        raise Http404
    quien = request.POST.get('usuario', '')
    ejecutor = next((m for m in grupo.miembros if m['nombreUsuario'] == quien), None)
    es_autor = comentarios[indice]['autor']['nombreUsuario'] == quien
    if not es_autor and (ejecutor is None or ejecutor['rol'] not in ('admin', 'moderador')):
        errores = ['Solo el autor, un admin o un moderador puede eliminar el comentario.']
        return render(request, 'grupo_detalle.html', {'data': {'grupo': grupo, 'errores': errores}}, status=400)
    del comentarios[indice]
    grupo.save()
    return redirect('grupo_detalle', pk=grupo.pk)
 
 
"""MODERACIÓN VIEWS"""
def moderaciones_listar(request):
    tipo = request.GET.get('tipo')
    estado = request.GET.get('estado')
    usuario = request.GET.get('usuario')
    coleccion_mongo = connection.cursor().db_conn[Moderacion._meta.db_table]
    filtro = {}
    if usuario:
        filtro['$or'] = [
            {'reportante.nombreUsuario': usuario},
            {'moderador.nombreUsuario': usuario},
            {'bloqueador.nombreUsuario': usuario},
            {'bloqueado.nombreUsuario': usuario},
            {'objetivo.nombreUsuario': usuario},
        ]
    moderaciones = Moderacion.objects.all()
    if filtro:
        ids = [documento['_id'] for documento in coleccion_mongo.find(filtro, {'_id': 1})]
        moderaciones = moderaciones.filter(id_buscar=ids)
    if tipo in TIPOS_MODERACION:
        moderaciones = moderaciones.filter(tipo=tipo)
    if estado in ESTADOS_REPORTE:
        moderaciones = moderaciones.filter(estado=estado)
    moderaciones = moderaciones.order_by('-fechaCreacion')
    data = {'moderaciones': moderaciones[:50], 'total': moderaciones.count()}
    return render(request, 'moderacion_lista.html', {'data': data})
 
def reportes_pendientes(request):
    motivo = request.GET.get('motivo')
    tipo_elemento = request.GET.get('tipoElemento')
    reportes = Moderacion.objects.filter(tipo='reporte', estado='pendiente')
    if motivo in MOTIVOS_REPORTE:
        reportes = reportes.filter(motivo=motivo)
    if tipo_elemento in TIPOS_ELEMENTO:
        reportes = reportes.filter(tipoElemento=tipo_elemento)
    reportes = reportes.order_by('fechaCreacion')
    data = {'moderaciones': reportes[:50], 'total': reportes.count(), 'estado': 'pendientes'}
    return render(request, 'moderacion_lista.html', {'data': data})
 
def bloqueos_activos(request):
    usuario = request.GET.get('usuario')
    filtro = {
        'tipo': 'bloqueo',
        '$or': [{'fechaExpiracion': None}, {'fechaExpiracion': {'$gt': timezone.now()}}],
    }
    if usuario:
        filtro['bloqueador.nombreUsuario'] = usuario
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Moderacion._meta.db_table].find(filtro, {'_id': 1})]
    bloqueos = Moderacion.objects.filter(id_buscar=ids).order_by('-fechaCreacion')
    data = {'moderaciones': bloqueos[:50], 'total': bloqueos.count(), 'estado': 'activos'}
    return render(request, 'moderacion_lista.html', {'data': data})
 
def moderacion_detalle(request, pk):
    moderacion = get_object_or_404(Moderacion, pk=pk)
    return render(request, 'moderacion_detalle.html', {'data': {'moderacion': moderacion}})
 
def reporte_crear(request):
    contexto = {'accion': 'crear'}
    if request.method == 'GET':
        return render(request, 'reporte_form.html', {'data': contexto})
    errores = []
    reportante = {'nombreUsuario': request.POST.get('reportante', ''), 'imagenPerfil': None}
    objetivo = {
        'publicacionUrl': request.POST.get('publicacionUrl') or None,
        'nombreUsuario': request.POST.get('nombreUsuarioObjetivo') or None,
    }
    datos = {
        'tipo': 'reporte',
        'tipoElemento': request.POST.get('tipoElemento'),
        'motivo': request.POST.get('motivo'),
        'descripcion': request.POST.get('descripcion') or None,
        'estado': 'pendiente',
    }
    if not 3 <= len(reportante['nombreUsuario']) <= 30:
        errores.append('El reportante debe tener un nombre de usuario de 3 a 30 caracteres.')
    if datos['tipoElemento'] not in TIPOS_ELEMENTO:
        errores.append('El tipo de elemento debe ser publicacion, comentario o usuario.')
    if datos['motivo'] not in MOTIVOS_REPORTE:
        errores.append('El motivo del reporte no es válido.')
    if datos['descripcion'] and len(datos['descripcion']) > 1000:
        errores.append('La descripción admite máximo 1000 caracteres.')
    if datos['tipoElemento'] in ('publicacion', 'comentario'):
        if not objetivo['publicacionUrl'] or not PATRON_URL.match(objetivo['publicacionUrl']):
            errores.append('El reporte necesita la URL de la publicación como un link válido.')
    if datos['tipoElemento'] == 'usuario' or objetivo['nombreUsuario']:
        if not objetivo['nombreUsuario'] or not 3 <= len(objetivo['nombreUsuario']) <= 30:
            errores.append('El usuario reportado debe tener un nombre de usuario de 3 a 30 caracteres.')
    if objetivo['nombreUsuario'] == reportante['nombreUsuario']:
        errores.append('No puedes reportarte a ti mismo.')
    if not errores:
        filtro = {
            'tipo': 'reporte',
            'estado': 'pendiente',
            'reportante.nombreUsuario': reportante['nombreUsuario'],
            'tipoElemento': datos['tipoElemento'],
            'objetivo.publicacionUrl': objetivo['publicacionUrl'],
            'objetivo.nombreUsuario': objetivo['nombreUsuario'],
        }
        if connection.cursor().db_conn[Moderacion._meta.db_table].find_one(filtro, {'_id': 1}):
            errores.append('Ya tienes un reporte pendiente sobre este elemento.')
    moderacion = None
    if not errores:
        datos.update(
            reportante=reportante,
            objetivo=objetivo,
            fechaCreacion=timezone.now(),
        )
        moderacion = Moderacion(**datos)
        try:
            moderacion.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(request, 'reporte_form.html', {'data': contexto})
    moderacion.save()
    return redirect('moderacion_detalle', pk=moderacion.pk)
 
def reporte_resolver(request, pk):
    moderacion = get_object_or_404(Moderacion, pk=pk, tipo='reporte')
    contexto = {'accion': 'resolver', 'moderacion': moderacion}
    if request.method == 'GET':
        return render(request, 'reporte_resolver_form.html', {'data': contexto})
    errores = []
    moderador = {'nombreUsuario': request.POST.get('moderador', ''), 'imagenPerfil': None}
    estado = request.POST.get('estado')
    accion = request.POST.get('accionTomada') or None
    if moderacion.estado in ('resuelto', 'descartado'):
        errores.append('El reporte ya fue resuelto.')
    if not 3 <= len(moderador['nombreUsuario']) <= 30:
        errores.append('El moderador debe tener un nombre de usuario de 3 a 30 caracteres.')
    if moderador['nombreUsuario'] == moderacion.reportante['nombreUsuario']:
        errores.append('El moderador no puede resolver un reporte propio.')
    if estado not in ('resuelto', 'descartado'):
        errores.append('El estado debe ser resuelto o descartado.')
    if estado == 'resuelto' and accion not in ACCIONES_MODERACION:
        errores.append('Un reporte resuelto necesita una acción tomada válida.')
    if estado == 'descartado':
        accion = 'ninguna'
    if errores:
        contexto['errores'] = errores
        return render(request, 'reporte_resolver_form.html', {'data': contexto})
    moderacion.estado = estado
    moderacion.moderador = moderador
    moderacion.accionTomada = accion
    moderacion.fechaResolucion = timezone.now()
    try:
        moderacion.full_clean(validate_unique=False)
    except ValidationError as excepcion:
        contexto['errores'] = excepcion.messages
        return render(request, 'reporte_resolver_form.html', {'data': contexto})
    moderacion.save()
    return redirect('moderacion_detalle', pk=moderacion.pk)
 
def bloqueo_crear(request):
    contexto = {'accion': 'crear'}
    if request.method == 'GET':
        return render(request, 'bloqueo_form.html', {'data': contexto})
    errores = []
    bloqueador = {'nombreUsuario': request.POST.get('bloqueador', ''), 'imagenPerfil': None}
    bloqueado = {'nombreUsuario': request.POST.get('bloqueado', ''), 'imagenPerfil': None}
    ambito = request.POST.get('ambito') or 'total'
    expiracion_texto = request.POST.get('fechaExpiracion')
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
        return render(request, 'bloqueo_form.html', {'data': contexto})
    moderacion.save()
    return redirect('moderacion_detalle', pk=moderacion.pk)
 
def bloqueo_eliminar(request, pk):
    """Desbloquear: solo el bloqueador puede quitar su propio bloqueo."""
    moderacion = get_object_or_404(Moderacion, pk=pk, tipo='bloqueo')
    if request.POST.get('usuario') != moderacion.bloqueador['nombreUsuario']:
        errores = ['Solo quien creó el bloqueo puede quitarlo.']
        return render(request, 'moderacion_detalle.html', {'data': {'moderacion': moderacion, 'errores': errores}}, status=400)
    moderacion.delete()
    return redirect('moderaciones_listar')
 
def moderacion_eliminar(request, pk):
    moderacion = get_object_or_404(Moderacion, pk=pk)
    if moderacion.tipo == 'reporte' and moderacion.estado == 'pendiente':
        errores = ['No se puede eliminar un reporte pendiente; resuélvelo o descártalo primero.']
        return render(request, 'moderacion_detalle.html', {'data': {'moderacion': moderacion, 'errores': errores}}, status=400)
    moderacion.delete()
    return redirect('moderaciones_listar')
 
def bloqueos_depurar(request):
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Moderacion._meta.db_table].find({'tipo': 'bloqueo', 'fechaExpiracion': {'$lte': timezone.now()}}, {'_id': 1})]
    Moderacion.objects.filter(id_buscar=ids).delete()
    return redirect('moderaciones_listar')