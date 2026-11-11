from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import connection
from django.db.models import Q
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.http import Http404
from .models import Categoria, Coleccion, Publicacion, Recomendacion
from .opciones import *
from .forms import FormularioCategoria, FormularioPublicacion, FormularioColeccion, FormularioRecomendacion
from g_usuarios_perfiles.models import Usuario, Notificacion
from g_usuarios_perfiles.acceso import sesion_requerida, administrador_requerido, comprobar_propietario, resumen_usuario
from photobook.consultas import documentos, existe_bloqueo, publicacion_visible
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods, require_POST


@sesion_requerida
@require_http_methods(['GET'])
def categorias_listar(solicitud):
    texto = solicitud.GET.get('q')
    categorias = Categoria.objects.all()
    if texto:
        categorias = categorias.filter(Q(nombre__icontains=texto) | Q(slug__icontains=texto))
    categorias = categorias.order_by('-totalPublicaciones' if solicitud.GET.get('orden') == 'populares' else 'nombre')
    datos = {'categorias': categorias[:50], 'total': categorias.count()}
    return render(solicitud, 'categorias_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def categoria_detalle(solicitud, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    return render(solicitud, 'categoria_detalle.html', {'datos': {'categoria': categoria}})

@administrador_requerido
@require_http_methods(['GET', 'POST'])
def categoria_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {}
    formulario = FormularioCategoria(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'categoria_form.html', {'datos': contexto})
    errores = []
    nombre = solicitud.POST.get('nombre', '').strip()
    slug = slugify(nombre)
    if not 1 <= len(nombre) <= 60 or not PATRON_SLUG.match(slug):
        errores.append('El nombre debe tener hasta 60 caracteres y generar un slug válido.')
    if Categoria.objects.filter(Q(nombre=nombre) | Q(slug=slug)).exists():
        errores.append('Ya existe una categoría con ese nombre.')
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'categoria_form.html', {'datos': contexto})
    categoria = Categoria.objects.create(nombre=nombre, slug=slug, descripcion=formulario.cleaned_data['descripcion'] or None)
    return redirect('categoria_detalle', slug=categoria.slug)

@administrador_requerido
@require_http_methods(['GET', 'POST'])
def categoria_actualizar(solicitud, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    contexto = {'accion': 'actualizar', 'categoria': categoria}
    valores = {campo: getattr(categoria, campo, None) for campo in FormularioCategoria().fields}
    formulario = FormularioCategoria(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'categoria_form.html', {'datos': contexto})
    errores = []
    slug_anterior = categoria.slug
    nombre = solicitud.POST.get('nombre', '').strip()
    slug = categoria.slug
    if not 1 <= len(nombre) <= 60 or not PATRON_SLUG.match(slug):
        errores.append('El nombre debe tener hasta 60 caracteres y generar un slug válido.')
    if Categoria.objects.filter(Q(nombre=nombre) | Q(slug=slug)).exclude(pk=categoria.pk).exists():
        errores.append('Ya existe otra categoría con ese nombre.')
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'categoria_form.html', {'datos': contexto})
    categoria.descripcion = formulario.cleaned_data['descripcion'] or None
    categoria.nombre = nombre
    categoria.slug = slug
    categoria.save()
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find({'categorias.slug': slug_anterior}, {'_id': 1})]
    for publicacion in Publicacion.objects.filter(pk__in=ids):
        for copia in publicacion.categorias:
            if copia['slug'] == slug_anterior:
                copia['nombre'] = nombre
                copia['slug'] = slug
        publicacion.save()
    from int_social_comunidad.models import Grupo
    for grupo in documentos(Grupo, {'categoria.slug': slug_anterior}):
        grupo.categoria = {'nombre': categoria.nombre, 'slug': categoria.slug}
        grupo.save()
    return redirect('categoria_detalle', slug=categoria.slug)

@administrador_requerido
@require_http_methods(['GET', 'POST'])
def categoria_eliminar(solicitud, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    if solicitud.method == 'GET':
        return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar categoria', 'objeto': categoria.nombre})
    from int_social_comunidad.models import Grupo
    if documentos(Publicacion, {'categorias.slug': slug}).exists() or documentos(Grupo, {'categoria.slug': slug}).exists():
        errores = ['No se puede eliminar la categoría porque tiene publicaciones asociadas.']
        return render(solicitud, 'categoria_detalle.html', {'datos': {'categoria': categoria, 'errores': errores}}, status=400)
    categoria.delete()
    return redirect('categorias_listar')


@sesion_requerida
@require_http_methods(['GET'])
def colecciones_listar(solicitud):
    creador = solicitud.GET.get('creador')
    sentido = 'nombre'
    colecciones = documentos(Coleccion, {'$or': [{'privacidad': 'publica'}, {'creador.nombreUsuario': solicitud.usuario.nombreUsuario}, {'colaboradores.nombreUsuario': solicitud.usuario.nombreUsuario}]})
    if creador:
        ids = [documento['_id'] for documento in connection.cursor().db_conn[Coleccion._meta.db_table].find({'creador.nombreUsuario': creador}, {'_id': 1})]
        colecciones = colecciones.filter(pk__in=ids)
    colecciones = colecciones.order_by(sentido)
    datos = {'colecciones': colecciones[:50], 'total': colecciones.count()}
    return render(solicitud, 'colecciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def coleccion_detalle(solicitud, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    comprobar_coleccion(solicitud, coleccion)
    return render(solicitud, 'coleccion_detalle.html', {'datos': {'coleccion': coleccion, 'puede_editar': solicitud.usuario.nombreUsuario in [coleccion.creador['nombreUsuario']] + [dato['nombreUsuario'] for dato in coleccion.colaboradores], 'publicaciones': Publicacion.objects.filter(estado='publicado'), 'usuarios': Usuario.objects.filter(activo__in=[True])}})

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def coleccion_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {}
    formulario = FormularioColeccion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'coleccion_form.html', {'datos': contexto})
    errores = []
    nombre = solicitud.POST.get('nombre', '').strip()
    descripcion = solicitud.POST.get('descripcion') or None
    tipo = solicitud.POST.get('tipo') or 'personal'
    privacidad = solicitud.POST.get('privacidad') or 'publica'
    creador = resumen_usuario(solicitud.usuario)
    if not 1 <= len(nombre) <= 100:
        errores.append('El nombre debe tener entre 1 y 100 caracteres')
    if descripcion and len(descripcion) > 500:
        errores.append('La descripción admite máximo 500 caracteres')
    if tipo not in TIPOS_COLECCION:
        errores.append('El tipo debe ser personal o colaborativa')
    if privacidad not in PRIVACIDADES:
        errores.append('La privacidad debe ser publica o privada')
    if not 3 <= len(creador['nombreUsuario']) <= 30:
        errores.append('El creador debe tener un nombre de usuario de 3 a 30 caracteres.')
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'coleccion_form.html', {'datos': contexto})
    coleccion = Coleccion.objects.create(nombre=nombre, descripcion=descripcion, tipo=tipo, privacidad=privacidad, creador=creador)
    return redirect('coleccion_detalle', pk=coleccion.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def coleccion_actualizar(solicitud, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    comprobar_propietario(solicitud, coleccion.creador['nombreUsuario'])
    contexto = {'accion': 'actualizar', 'coleccion': coleccion}
    valores = {campo: getattr(coleccion, campo, None) for campo in FormularioColeccion().fields}
    formulario = FormularioColeccion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'coleccion_form.html', {'datos': contexto})
    errores = []
    nombre = solicitud.POST.get('nombre', '').strip()
    descripcion = solicitud.POST.get('descripcion') or None
    privacidad = solicitud.POST.get('privacidad') or 'publica'
    if not 1 <= len(nombre) <= 100:
        errores.append('El nombre debe tener entre 1 y 100 caracteres.')
    if descripcion and len(descripcion) > 500:
        errores.append('La descripción admite máximo 500 caracteres.')
    if privacidad not in PRIVACIDADES:
        errores.append('La privacidad debe ser publica o privada.')
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'coleccion_form.html', {'datos': contexto})
    coleccion.tipo = formulario.cleaned_data['tipo']
    if coleccion.tipo == 'personal':
        coleccion.colaboradores = []
    coleccion.nombre = nombre
    coleccion.descripcion = descripcion
    coleccion.privacidad = privacidad
    coleccion.save()
    return redirect('coleccion_detalle', pk=coleccion.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def coleccion_eliminar(solicitud, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    comprobar_propietario(solicitud, coleccion.creador['nombreUsuario'])
    if solicitud.method == 'GET':
        return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar coleccion', 'objeto': coleccion.nombre})
    coleccion.delete()
    return redirect('colecciones_listar')


@sesion_requerida
@require_http_methods(['GET'])
def publicaciones_listar(solicitud):
    autor = solicitud.GET.get('autor')
    excepto = solicitud.GET.get('excepto')
    categoria = solicitud.GET.get('categoria')
    orden = ORDENES_PUBLICACION.get(solicitud.GET.get('orden'), '-fechaPublicacion')
    coleccion_mongo = connection.cursor().db_conn[Publicacion._meta.db_table]
    condicion = Q(estado='publicado')
    if autor == solicitud.usuario.nombreUsuario and solicitud.GET.get('estado') in ESTADOS:
        condicion = Q(estado=solicitud.GET['estado'])
    if autor:
        condicion &= Q(pk__in=[documento['_id'] for documento in coleccion_mongo.find({'autor.nombreUsuario': autor}, {'_id': 1})])
    if excepto:
        condicion &= ~Q(pk__in=[documento['_id'] for documento in coleccion_mongo.find({'autor.nombreUsuario': excepto}, {'_id': 1})])
    if categoria:
        condicion &= Q(pk__in=[documento['_id'] for documento in coleccion_mongo.find({'categorias.slug': categoria}, {'_id': 1})])
    publicaciones = Publicacion.objects.filter(condicion).order_by(orden)
    publicaciones = [dato for dato in publicaciones if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido')]
    datos = {'publicaciones': publicaciones[:50], 'total': len(publicaciones)}
    return render(solicitud, 'publicaciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def publicaciones_buscar(solicitud):
    texto = solicitud.GET.get('q', '').strip()
    publicaciones = Publicacion.objects.filter(estado='publicado')
    if texto:
        publicaciones = publicaciones.filter(Q(titulo__icontains=texto) | Q(descripcion__icontains=texto))
    else:
        publicaciones = Publicacion.objects.none()
    total = publicaciones.count()
    publicaciones = [dato for dato in publicaciones if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido')]
    datos = {'publicaciones': publicaciones[:50], 'total': total, 'busqueda': texto}
    return render(solicitud, 'publicaciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def publicaciones_en_debate(solicitud):
    filtro = {'estado': 'publicado', '$expr': {'$gt': ['$totalComentarios', '$totalReacciones']}}
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find(filtro, {'_id': 1})]
    publicaciones = Publicacion.objects.filter(pk__in=ids).order_by('-totalComentarios')
    total = publicaciones.count()
    publicaciones = [dato for dato in publicaciones if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido')]
    datos = {'publicaciones': publicaciones[:50], 'total': total, 'estado': 'en debate'}
    return render(solicitud, 'publicaciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def publicacion_detalle(solicitud, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    comprobar_publicacion(solicitud, publicacion)
    return render(solicitud, 'publicacion_detalle.html', {'datos': {'publicacion': publicacion}})

@sesion_requerida
@require_http_methods(['GET'])
def publicacion_por_url(solicitud):
    publicacion = Publicacion.objects.filter(archivoUrl=solicitud.GET.get('archivoUrl')).first()
    comprobar_publicacion(solicitud, publicacion)
    if publicacion is None:
        raise Http404
    return render(solicitud, 'publicacion_detalle.html', {'datos': {'publicacion': publicacion}})

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def publicacion_crear(solicitud):
    contexto = {'accion': 'crear', 'categorias': Categoria.objects.all().order_by('nombre')}
    valores = {}
    formulario = FormularioPublicacion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'publicacion_form.html', {'datos': contexto})
    errores = []
    autor = resumen_usuario(solicitud.usuario)
    slugs = solicitud.POST.getlist('categorias')
    categorias = Categoria.objects.filter(slug__in=slugs)
    datos = {
        'tipo': solicitud.POST.get('tipo'),
        'titulo': solicitud.POST.get('titulo') or None,
        'descripcion': solicitud.POST.get('descripcion') or None,
        'archivoUrl': solicitud.POST.get('archivoUrl', ''),
        'formato': solicitud.POST.get('formato'),
        'tamanioBytes': solicitud.POST.get('tamanioBytes'),
        'ancho': solicitud.POST.get('ancho') or None,
        'alto': solicitud.POST.get('alto') or None,
        'duracionSegundos': solicitud.POST.get('duracionSegundos') or None,
        'etiquetas': [etiqueta.strip() for etiqueta in solicitud.POST.get('etiquetas', '').split(',') if etiqueta.strip()],
        'categorias': [{'nombre': categoria.nombre, 'slug': categoria.slug} for categoria in categorias],
        'estado': solicitud.POST.get('estado') or 'publicado',
    }
    if not 3 <= len(autor['nombreUsuario']) <= 30:
        errores.append('El autor debe tener un nombre de usuario de 3 a 30 caracteres.')
    if datos['tipo'] not in TIPOS:
        errores.append('El tipo debe ser imagen o video.')
    if datos['formato'] not in FORMATOS:
        errores.append('El formato no es válido.')
    if datos['estado'] not in ESTADOS:
        errores.append('El estado debe ser publicado, borrador o eliminado.')
    if not PATRON_URL.match(datos['archivoUrl']):
        errores.append('El archivoUrl debe ser un enlace válido.')
    elif Publicacion.objects.filter(archivoUrl=datos['archivoUrl']).exists():
        errores.append('Ya existe una publicación con ese archivoUrl.')
    if datos['tipo'] == 'video' and not datos['duracionSegundos']:
        errores.append('Un video necesita su duración en segundos.')
    if len(datos['categorias']) != len(set(slugs)):
        errores.append('Alguna de las categorías no existe.')
    if len(datos['etiquetas']) > 30 or any(len(etiqueta) > 30 for etiqueta in datos['etiquetas']):
        errores.append('Máximo 30 etiquetas de hasta 30 caracteres.')
    publicacion = None
    if not errores:
        datos.update(
            autor=autor,
            totalReacciones=0,
            totalComentarios=0,
            comentarios=[],
            reacciones=[],
            historialEdiciones=[],
            fechaPublicacion=timezone.now(),
        )
        publicacion = Publicacion(**datos)
        try:
            publicacion.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'publicacion_form.html', {'datos': contexto})
    publicacion.save()
    for categoria in categorias:
        categoria.totalPublicaciones += 1
        categoria.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def publicacion_actualizar(solicitud, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    comprobar_propietario(solicitud, publicacion.autor['nombreUsuario'])
    enlace_anterior = publicacion.archivoUrl
    contexto = {
        'accion': 'actualizar',
        'publicacion': publicacion,
        'categorias': Categoria.objects.all().order_by('nombre'),
    }
    valores = {campo: getattr(publicacion, campo, None) for campo in FormularioPublicacion().fields}
    valores['etiquetas'] = ', '.join(publicacion.etiquetas)
    valores['categorias'] = [dato['slug'] for dato in publicacion.categorias]
    formulario = FormularioPublicacion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'publicacion_form.html', {'datos': contexto})
    errores = []
    anteriores = [categoria['slug'] for categoria in publicacion.categorias]
    slugs = solicitud.POST.getlist('categorias')
    categorias = Categoria.objects.filter(slug__in=slugs)
    datos = {
        'tipo': solicitud.POST.get('tipo'),
        'titulo': solicitud.POST.get('titulo') or None,
        'descripcion': solicitud.POST.get('descripcion') or None,
        'archivoUrl': solicitud.POST.get('archivoUrl', ''),
        'formato': solicitud.POST.get('formato'),
        'tamanioBytes': solicitud.POST.get('tamanioBytes'),
        'ancho': solicitud.POST.get('ancho') or None,
        'alto': solicitud.POST.get('alto') or None,
        'duracionSegundos': solicitud.POST.get('duracionSegundos') or None,
        'etiquetas': [etiqueta.strip() for etiqueta in solicitud.POST.get('etiquetas', '').split(',') if etiqueta.strip()],
        'categorias': [{'nombre': categoria.nombre, 'slug': categoria.slug} for categoria in categorias],
        'estado': solicitud.POST.get('estado') or 'publicado',
    }
    edicion = None
    if solicitud.POST.get('tipoEdicion'):
        edicion = {
            'tipoEdicion': solicitud.POST.get('tipoEdicion'),
            'descripcion': solicitud.POST.get('descripcionEdicion') or None,
            'fecha': timezone.now(),
        }
        if edicion['tipoEdicion'] not in TIPOS_EDICION:
            errores.append('El tipo de edición no es válido.')
    if datos['tipo'] not in TIPOS:
        errores.append('El tipo debe ser imagen o video.')
    if datos['formato'] not in FORMATOS:
        errores.append('El formato no es válido.')
    if datos['estado'] not in ESTADOS:
        errores.append('El estado debe ser publicado, borrador o eliminado.')
    if not PATRON_URL.match(datos['archivoUrl']):
        errores.append('El archivoUrl debe ser un enlace válido.')
    elif Publicacion.objects.filter(archivoUrl=datos['archivoUrl']).exclude(pk=publicacion.pk).exists():
        errores.append('Ya existe otra publicación con ese archivoUrl.')
    if datos['tipo'] == 'video' and not datos['duracionSegundos']:
        errores.append('Un video necesita su duración en segundos.')
    if len(datos['categorias']) != len(set(slugs)):
        errores.append('Alguna de las categorías no existe.')
    if len(datos['etiquetas']) > 30 or any(len(etiqueta) > 30 for etiqueta in datos['etiquetas']):
        errores.append('Máximo 30 etiquetas de hasta 30 caracteres.')
    if edicion and len(publicacion.historialEdiciones) >= 100:
        errores.append('¡El historial de ediciones llegó a su límite de 100!')
    if not errores:
        for campo, valor in datos.items():
            setattr(publicacion, campo, valor)
        if edicion:
            publicacion.historialEdiciones.append(edicion)
        try:
            publicacion.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'publicacion_form.html', {'datos': contexto})
    publicacion.save()
    for coleccion in documentos(Coleccion, {'publicaciones.archivoUrl': enlace_anterior}):
        for copia in coleccion.publicaciones:
            if copia['archivoUrl'] == enlace_anterior:
                copia.update(titulo=publicacion.titulo, tipo=publicacion.tipo, archivoUrl=publicacion.archivoUrl)
        coleccion.save()
    for recomendacion in documentos(Recomendacion, {'publicacion.archivoUrl': enlace_anterior}):
        recomendacion.publicacion = {'titulo': publicacion.titulo, 'tipo': publicacion.tipo, 'archivoUrl': publicacion.archivoUrl}
        recomendacion.save()
    for categoria in Categoria.objects.filter(slug__in=list(set(slugs) - set(anteriores))):
        categoria.totalPublicaciones += 1
        categoria.save()
    for categoria in Categoria.objects.filter(slug__in=list(set(anteriores) - set(slugs))):
        categoria.totalPublicaciones = max(0, categoria.totalPublicaciones - 1)
        categoria.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def publicacion_eliminar(solicitud, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    comprobar_propietario(solicitud, publicacion.autor['nombreUsuario'])
    if solicitud.method == 'GET':
        return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar publicacion', 'objeto': publicacion.titulo})
    for categoria in Categoria.objects.filter(slug__in=[copia['slug'] for copia in publicacion.categorias]):
        categoria.totalPublicaciones = max(0, categoria.totalPublicaciones - 1)
        categoria.save()
    retirar_publicacion(publicacion)
    return redirect('publicaciones_listar')

@sesion_requerida
@require_POST
def publicaciones_estado_masivo(solicitud):
    autor = solicitud.usuario.nombreUsuario
    estado_actual = solicitud.POST.get('estadoActual')
    estado_nuevo = solicitud.POST.get('estadoNuevo')
    if estado_actual not in ESTADOS or estado_nuevo not in ESTADOS:
        datos = {'publicaciones': [], 'total': 0, 'errores': ['Los estados deben ser publicado, borrador o eliminado.']}
        return render(solicitud, 'publicaciones_lista.html', {'datos': datos}, status=400)
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find({'autor.nombreUsuario': autor, 'estado': estado_actual}, {'_id': 1})]
    Publicacion.objects.filter(pk__in=ids).update(estado=estado_nuevo)
    return redirect('publicaciones_listar')

@administrador_requerido
@require_POST
def publicaciones_depurar(solicitud):
    eliminadas = list(Publicacion.objects.filter(estado='eliminado'))
    for publicacion in eliminadas:
        for categoria in Categoria.objects.filter(slug__in=[copia['slug'] for copia in publicacion.categorias]):
            categoria.totalPublicaciones = max(0, categoria.totalPublicaciones - 1)
            categoria.save()
        retirar_publicacion(publicacion)
    return redirect('publicaciones_listar')

@sesion_requerida
@require_POST
def publicacion_comentar(solicitud, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    comprobar_publicacion(solicitud, publicacion)
    errores = []
    autor = resumen_usuario(solicitud.usuario)
    contenido = solicitud.POST.get('contenido', '').strip()
    formato = solicitud.POST.get('formato') or 'texto'
    if not 3 <= len(autor['nombreUsuario']) <= 30:
        errores.append('El autor debe tener un nombre de usuario de 3 a 30 caracteres.')
    if not 1 <= len(contenido) <= 500:
        errores.append('El comentario debe tener entre 1 y 500 caracteres...')
    if formato not in FORMATOS_COMENTARIO:
        errores.append('El formato del comentario no es válido.')
    if len(publicacion.comentarios) >= 300:
        errores.append('La publicación llegó al límite de 300 comentarios.')
    if errores:
        return render(solicitud, 'publicacion_detalle.html', {'datos': {'publicacion': publicacion, 'errores': errores}}, status=400)
    comentario = {
        'autor': autor,
        'contenido': contenido,
        'formato': formato,
        'menciones': [],
        'archivosAdjuntos': [],
        'respuestas': [],
        'estado': 'activo',
        'conteoReacciones': {tipo: 0 for tipo in TIPOS_REACCION},
        'fechaCreacion': timezone.now(),
        'fechaEdicion': None,
    }
    if publicacion.autor['nombreUsuario'] != solicitud.usuario.nombreUsuario:
        Notificacion.objects.create(usuarioNotificado=publicacion.autor['nombreUsuario'], usuarioOrigen=solicitud.usuario.nombreUsuario, tipo='comentario', mensaje='Comentaron tu publicación: ' + (publicacion.titulo or '')[:150])
    publicacion.comentarios.append(comentario)
    publicacion.totalComentarios += 1
    publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

@sesion_requerida
@require_POST
def comentario_actualizar(solicitud, pk, indice):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    if not 0 <= indice < len(publicacion.comentarios):
        raise Http404
    comprobar_propietario(solicitud, publicacion.comentarios[indice]['autor']['nombreUsuario'])
    errores = []
    contenido = solicitud.POST.get('contenido', '').strip()
    if not 1 <= len(contenido) <= 500:
        errores.append('El comentario debe tener entre 1 y 500 caracteres...')
    if errores:
        return render(solicitud, 'publicacion_detalle.html', {'datos': {'publicacion': publicacion, 'errores': errores}}, status=400)
    publicacion.comentarios[indice]['contenido'] = contenido
    publicacion.comentarios[indice]['estado'] = 'editado'
    publicacion.comentarios[indice]['fechaEdicion'] = timezone.now()
    publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

@sesion_requerida
@require_POST
def comentario_eliminar(solicitud, pk, indice):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    if not 0 <= indice < len(publicacion.comentarios):
        raise Http404
    comprobar_propietario(solicitud, publicacion.comentarios[indice]['autor']['nombreUsuario'])
    del publicacion.comentarios[indice]
    publicacion.totalComentarios = max(0, publicacion.totalComentarios - 1)
    publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

@sesion_requerida
@require_POST
def publicacion_reaccionar(solicitud, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    comprobar_publicacion(solicitud, publicacion)
    errores = []
    usuario = resumen_usuario(solicitud.usuario)
    tipoReaccion = solicitud.POST.get('tipoReaccion')
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if tipoReaccion not in TIPOS_REACCION:
        errores.append('Tipo de reacción inválido.')
    if errores:
        return render(solicitud, 'publicacion_detalle.html', {'datos': {'publicacion': publicacion, 'errores': errores}}, status=400)
    existente = next((reaccion for reaccion in publicacion.reacciones if reaccion['usuario']['nombreUsuario'] == usuario['nombreUsuario']), None)
    if existente is None:
        publicacion.reacciones.append({'usuario': usuario, 'tipoReaccion': tipoReaccion, 'fecha': timezone.now()})
        publicacion.totalReacciones += 1
    elif existente['tipoReaccion'] == tipoReaccion:
        publicacion.reacciones.remove(existente)
        publicacion.totalReacciones = max(0, publicacion.totalReacciones - 1)
    else:
        existente['tipoReaccion'] = tipoReaccion
        existente['fecha'] = timezone.now()
    publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)


@sesion_requerida
@require_http_methods(['GET'])
def recomendaciones_listar(solicitud):
    usuario = solicitud.usuario.nombreUsuario
    vista = solicitud.GET.get('vista')
    criterio = solicitud.GET.get('criterio')
    filtro = {}
    if usuario:
        filtro['usuario.nombreUsuario'] = usuario
    if vista in ('si', 'no'):
        filtro['vista'] = vista == 'si'
    recomendaciones = Recomendacion.objects.all()
    if filtro:
        ids = [documento['_id'] for documento in connection.cursor().db_conn[Recomendacion._meta.db_table].find(filtro, {'_id': 1})]
        recomendaciones = recomendaciones.filter(pk__in=ids)
    if criterio in CRITERIOS:
        recomendaciones = recomendaciones.filter(criterio=criterio)
    recomendaciones = recomendaciones.order_by('-puntuacion')
    recomendaciones = [dato for dato in recomendaciones if publicacion_visible(solicitud.usuario, dato.publicacion['archivoUrl'])]
    datos = {'recomendaciones': recomendaciones[:10], 'total': len(recomendaciones)}
    return render(solicitud, 'recomendaciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def recomendacion_detalle(solicitud, pk):
    recomendacion = get_object_or_404(Recomendacion, pk=pk)
    comprobar_propietario(solicitud, recomendacion.usuario['nombreUsuario'])
    if publicacion_visible(solicitud.usuario, recomendacion.publicacion['archivoUrl']) is None:
        raise Http404('La publicación recomendada no está disponible.')
    return render(solicitud, 'recomendacion_detalle.html', {'datos': {'recomendacion': recomendacion}})

@administrador_requerido
@require_http_methods(['GET', 'POST'])
def recomendacion_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {}
    formulario = FormularioRecomendacion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'recomendacion_form.html', {'datos': contexto})
    errores = []
    usuario = resumen_usuario(get_object_or_404(Usuario, nombreUsuario=formulario.cleaned_data['usuario'], activo__in=[True]))
    publicacion = Publicacion.objects.filter(archivoUrl=solicitud.POST.get('archivoUrl')).first()
    datos = {
        'criterio': solicitud.POST.get('criterio'),
        'puntuacion': solicitud.POST.get('puntuacion'),
        'vista': False,
    }
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if publicacion is None:
        errores.append('No existe una publicación con ese archivoUrl.')
    if datos['criterio'] not in CRITERIOS:
        errores.append('El criterio debe ser etiquetas, coleccion, tendencia o similitud.')
    recomendacion = None
    if not errores:
        datos.update(
            usuario=usuario,
            publicacion={'titulo': publicacion.titulo, 'tipo': publicacion.tipo, 'archivoUrl': publicacion.archivoUrl},
        )
        recomendacion = Recomendacion(**datos)
        try:
            recomendacion.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'recomendacion_form.html', {'datos': contexto})
    recomendacion.save()
    return redirect('recomendacion_detalle', pk=recomendacion.pk)

@administrador_requerido
@require_http_methods(['GET', 'POST'])
def recomendacion_actualizar(solicitud, pk):
    recomendacion = get_object_or_404(Recomendacion, pk=pk)
    contexto = {'accion': 'actualizar', 'recomendacion': recomendacion}
    valores = {campo: getattr(recomendacion, campo, None) for campo in FormularioRecomendacion().fields}
    valores['usuario'] = recomendacion.usuario['nombreUsuario']
    valores['archivoUrl'] = recomendacion.publicacion['archivoUrl']
    formulario = FormularioRecomendacion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'recomendacion_form.html', {'datos': contexto})
    errores = []
    destino = get_object_or_404(Usuario, nombreUsuario=formulario.cleaned_data['usuario'], activo__in=[True])
    contenido = get_object_or_404(Publicacion, archivoUrl=formulario.cleaned_data['archivoUrl'], estado='publicado')
    recomendacion.usuario = resumen_usuario(destino)
    recomendacion.publicacion = {'titulo': contenido.titulo, 'tipo': contenido.tipo, 'archivoUrl': contenido.archivoUrl}
    datos = {
        'criterio': solicitud.POST.get('criterio'),
        'puntuacion': solicitud.POST.get('puntuacion'),
        'vista': solicitud.POST.get('vista') == 'on',
    }
    if datos['criterio'] not in CRITERIOS:
        errores.append('El criterio debe ser etiquetas, coleccion, tendencia o similitud.')
    if not errores:
        for campo, valor in datos.items():
            setattr(recomendacion, campo, valor)
        try:
            recomendacion.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'recomendacion_form.html', {'datos': contexto})
    recomendacion.save()
    return redirect('recomendacion_detalle', pk=recomendacion.pk)

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def recomendacion_eliminar(solicitud, pk):
    recomendacion = get_object_or_404(Recomendacion, pk=pk)
    comprobar_propietario(solicitud, recomendacion.usuario['nombreUsuario'])
    if solicitud.method == 'GET':
        return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar recomendacion', 'objeto': recomendacion.criterio})
    recomendacion.delete()
    return redirect('recomendaciones_listar')

@sesion_requerida
@require_POST
def recomendaciones_marcar_vistas(solicitud):
    usuario = solicitud.usuario.nombreUsuario
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Recomendacion._meta.db_table].find({'usuario.nombreUsuario': usuario, 'vista': False}, {'_id': 1})]
    Recomendacion.objects.filter(pk__in=ids).update(vista=True)
    return redirect('recomendaciones_listar')

@sesion_requerida
@require_POST
def recomendaciones_limpiar_vistas(solicitud):
    usuario = solicitud.usuario.nombreUsuario
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Recomendacion._meta.db_table].find({'usuario.nombreUsuario': usuario, 'vista': True}, {'_id': 1})]
    Recomendacion.objects.filter(pk__in=ids).delete()
    return redirect('recomendaciones_listar')
def comprobar_publicacion(solicitud, publicacion):
    if publicacion is None:
        raise Http404
    if publicacion.estado != 'publicado':
        comprobar_propietario(solicitud, publicacion.autor['nombreUsuario'])
    if existe_bloqueo(solicitud.usuario.nombreUsuario, publicacion.autor['nombreUsuario'], 'contenido'):
        raise PermissionDenied('El contenido no está disponible.')


def comprobar_coleccion(solicitud, coleccion):
    nombres = [coleccion.creador['nombreUsuario']] + [dato['nombreUsuario'] for dato in coleccion.colaboradores]
    if coleccion.privacidad == 'privada' and solicitud.usuario.nombreUsuario not in nombres and solicitud.usuario.rol != 'administrador':
        raise PermissionDenied('Esta colección es privada.')


def retirar_publicacion(publicacion):
    for coleccion in documentos(Coleccion, {'publicaciones.archivoUrl': publicacion.archivoUrl}):
        coleccion.publicaciones = [dato for dato in coleccion.publicaciones if dato['archivoUrl'] != publicacion.archivoUrl]
        for orden, dato in enumerate(coleccion.publicaciones, 1):
            dato['orden'] = orden
        coleccion.save()
    documentos(Recomendacion, {'publicacion.archivoUrl': publicacion.archivoUrl}).delete()
    publicacion.delete()


@sesion_requerida
@require_POST
def coleccion_guardar_publicacion(solicitud, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    nombres = [coleccion.creador['nombreUsuario']] + [dato['nombreUsuario'] for dato in coleccion.colaboradores]
    if solicitud.usuario.nombreUsuario not in nombres:
        raise PermissionDenied('No puedes editar esta colección.')
    publicacion = get_object_or_404(Publicacion, archivoUrl=solicitud.POST.get('archivoUrl'), estado='publicado')
    comprobar_publicacion(solicitud, publicacion)
    if not any(dato['archivoUrl'] == publicacion.archivoUrl for dato in coleccion.publicaciones):
        coleccion.publicaciones.append({'orden': len(coleccion.publicaciones) + 1, 'titulo': publicacion.titulo, 'tipo': publicacion.tipo, 'archivoUrl': publicacion.archivoUrl})
        coleccion.save()
    return redirect('coleccion_detalle', pk=pk)


@sesion_requerida
@require_POST
def coleccion_quitar_publicacion(solicitud, pk, indice):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    nombres = [coleccion.creador['nombreUsuario']] + [dato['nombreUsuario'] for dato in coleccion.colaboradores]
    if solicitud.usuario.nombreUsuario not in nombres:
        raise PermissionDenied('No puedes editar esta colección.')
    if not 0 <= indice < len(coleccion.publicaciones):
        raise Http404
    del coleccion.publicaciones[indice]
    for orden, dato in enumerate(coleccion.publicaciones, 1):
        dato['orden'] = orden
    coleccion.save()
    return redirect('coleccion_detalle', pk=pk)


@sesion_requerida
@require_POST
def coleccion_colaboradores(solicitud, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    comprobar_propietario(solicitud, coleccion.creador['nombreUsuario'])
    if coleccion.tipo != 'colaborativa':
        raise PermissionDenied('La colección debe ser colaborativa.')
    usuario = get_object_or_404(Usuario, nombreUsuario=solicitud.POST.get('usuario'), activo__in=[True])
    if usuario.nombreUsuario == coleccion.creador['nombreUsuario']:
        return redirect('coleccion_detalle', pk=pk)
    if any(dato['nombreUsuario'] == usuario.nombreUsuario for dato in coleccion.colaboradores):
        coleccion.colaboradores = [dato for dato in coleccion.colaboradores if dato['nombreUsuario'] != usuario.nombreUsuario]
    else:
        coleccion.colaboradores.append(resumen_usuario(usuario))
    coleccion.save()
    return redirect('coleccion_detalle', pk=pk)
