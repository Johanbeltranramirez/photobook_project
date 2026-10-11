from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import connection
from django.db.models import Q
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.http import Http404
from .models import Categoria, Coleccion, Publicacion, Recomendacion
from .arrays import *

"""CATEGORÍAS VIEWS"""
def categorias_listar(request):
    texto = request.GET.get('q')
    categorias = Categoria.objects.all()
    if texto:
        categorias = categorias.filter(Q(nombre__tiene=texto) | Q(slug__tiene=texto))
    categorias = categorias.order_by('-totalPublicaciones' if request.GET.get('orden') == 'populares' else 'nombre')
    data = {'categorias': categorias[:50], 'total': categorias.count()}
    return render(request, 'categorias_lista.html', {'data': data})

def categoria_detalle(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    return render(request, 'categoria_detalle.html', {'data': {'categoria': categoria}})

def categoria_crear(request):
    contexto = {'accion': 'crear'}
    if request.method == 'GET':
        return render(request, 'categoria_form.html', {'data': contexto})
    errores = []
    nombre = request.POST.get('nombre', '').strip()
    slug = slugify(nombre)
    if not 1 <= len(nombre) <= 60 or not PATRON_SLUG.match(slug):
        errores.append('El nombre debe tener hasta 60 caracteres y generar un slug válido.')
    if Categoria.objects.filter(Q(nombre=nombre) | Q(slug=slug)).exists():
        errores.append('Ya existe una categoría con ese nombre.')
    if errores:
        contexto['errores'] = errores
        return render(request, 'categoria_form.html', {'data': contexto})
    categoria = Categoria.objects.create(nombre=nombre, slug=slug)
    return redirect('categoria_detalle', slug=categoria.slug)

def categoria_actualizar(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    contexto = {'accion': 'actualizar', 'categoria': categoria}
    if request.method == 'GET':
        return render(request, 'categoria_form.html', {'data': contexto})
    errores = []
    slug_anterior = categoria.slug
    nombre = request.POST.get('nombre', '').strip()
    slug = slugify(nombre)
    if not 1 <= len(nombre) <= 60 or not PATRON_SLUG.match(slug):
        errores.append('El nombre debe tener hasta 60 caracteres y generar un slug válido.')
    if Categoria.objects.filter(Q(nombre=nombre) | Q(slug=slug)).exclude(pk=categoria.pk).exists():
        errores.append('Ya existe otra categoría con ese nombre.')
    if errores:
        contexto['errores'] = errores
        return render(request, 'categoria_form.html', {'data': contexto})
    categoria.nombre = nombre
    categoria.slug = slug
    categoria.save()
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find({'categorias.slug': slug_anterior}, {'_id': 1})]
    for publicacion in Publicacion.objects.filter(id_buscar=ids):
        for copia in publicacion.categorias:
            if copia['slug'] == slug_anterior:
                copia['nombre'] = nombre
                copia['slug'] = slug
        publicacion.save()
    return redirect('categoria_detalle', slug=categoria.slug)

def categoria_eliminar(request, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    if categoria.totalPublicaciones > 0:
        errores = ['No se puede eliminar la categoría porque tiene publicaciones asociadas.']
        return render(request, 'categoria_detalle.html', {'data': {'categoria': categoria, 'errores': errores}}, status=400)
    categoria.delete()
    return redirect('categorias_listar')

"""COLECCIONES VIEWS"""
def colecciones_listar(request):
    privacidad = request.GET.get('privacidad') or 'publica'
    creador = request.GET.get('creador')
    sentido = '-nombre' if request.GET.get('orden') == 'desc' else 'nombre'
    colecciones = Coleccion.objects.filter(privacidad=privacidad)
    if creador:
        ids = [documento['_id'] for documento in connection.cursor().db_conn[Coleccion._meta.db_table].find({'creador.nombreUsuario': creador}, {'_id': 1})]
        colecciones = colecciones.filter(id_buscar=ids)
    colecciones = colecciones.order_by(sentido)
    data = {'colecciones': colecciones[:50], 'total': colecciones.count()}
    return render(request, 'colecciones_lista.html', {'data': data})

def coleccion_detalle(request, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    return render(request, 'coleccion_detalle.html', {'data': {'coleccion': coleccion}})

def coleccion_crear(request):
    contexto = {'accion': 'crear'}
    if request.method == 'GET':
        return render(request, 'coleccion_form.html', {'data': contexto})
    errores = []
    nombre = request.POST.get('nombre', '').strip()
    descripcion = request.POST.get('descripcion') or None
    tipo = request.POST.get('tipo') or 'personal'
    privacidad = request.POST.get('privacidad') or 'publica'
    creador = {'nombreUsuario': request.POST.get('creador', ''), 'imagenPerfil': None}
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
        return render(request, 'coleccion_form.html', {'data': contexto})
    coleccion = Coleccion.objects.create(nombre=nombre, descripcion=descripcion, tipo=tipo, privacidad=privacidad, creador=creador)
    return redirect('coleccion_detalle', pk=coleccion.pk)

def coleccion_actualizar(request, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    contexto = {'accion': 'actualizar', 'coleccion': coleccion}
    if request.method == 'GET':
        return render(request, 'coleccion_form.html', {'data': contexto})
    errores = []
    nombre = request.POST.get('nombre', '').strip()
    descripcion = request.POST.get('descripcion') or None
    privacidad = request.POST.get('privacidad') or 'publica'
    if not 1 <= len(nombre) <= 100:
        errores.append('El nombre debe tener entre 1 y 100 caracteres.')
    if descripcion and len(descripcion) > 500:
        errores.append('La descripción admite máximo 500 caracteres.')
    if privacidad not in PRIVACIDADES:
        errores.append('La privacidad debe ser publica o privada.')
    if errores:
        contexto['errores'] = errores
        return render(request, 'coleccion_form.html', {'data': contexto})
    coleccion.nombre = nombre
    coleccion.descripcion = descripcion
    coleccion.privacidad = privacidad
    coleccion.save()
    return redirect('coleccion_detalle', pk=coleccion.pk)

def coleccion_eliminar(request, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    if len(coleccion.publicaciones) > 0:
        errores = ['No se puede eliminar la colección porque tiene publicaciones asociadas.']
        return render(request, 'coleccion_detalle.html', {'data': {'coleccion': coleccion, 'errores': errores}}, status=400)
    coleccion.delete()
    return redirect('colecciones_listar')

"""PUBLICACIONES VIEWS"""
def publicaciones_listar(request):
    autor = request.GET.get('autor')
    excepto = request.GET.get('excepto')
    categoria = request.GET.get('categoria')
    orden = ORDENES_PUBLICACION.get(request.GET.get('orden'), '-fechaPublicacion')
    coleccion_mongo = connection.cursor().db_conn[Publicacion._meta.db_table]
    condicion = Q(estado=request.GET.get('estado') or 'publicado')
    if autor:
        condicion &= Q(id_buscar=[documento['_id'] for documento in coleccion_mongo.find({'autor.nombreUsuario': autor}, {'_id': 1})])
    if excepto:
        condicion &= ~Q(id_buscar=[documento['_id'] for documento in coleccion_mongo.find({'autor.nombreUsuario': excepto}, {'_id': 1})])
    if categoria:
        condicion &= Q(id_buscar=[documento['_id'] for documento in coleccion_mongo.find({'categorias.slug': categoria}, {'_id': 1})])
    publicaciones = Publicacion.objects.filter(condicion).order_by(orden)
    data = {'publicaciones': publicaciones[:50], 'total': publicaciones.count()}
    return render(request, 'publicaciones_lista.html', {'data': data})

def publicaciones_buscar(request):
    texto = request.GET.get('q')
    publicaciones = Publicacion.objects.none()
    if texto:
        puntaje = {'$meta': 'textScore'}
        cursor = connection.cursor().db_conn[Publicacion._meta.db_table].find({'$text': {'$search': texto}}, {'_id': 1, 'puntaje': puntaje}).sort([('puntaje', puntaje)]).limit(50)
        ids = [documento['_id'] for documento in cursor]
        publicaciones = Publicacion.objects.filter(id_buscar=ids, estado='publicado').order_by('-fechaPublicacion')
    total = publicaciones.count()
    data = {'publicaciones': publicaciones[:50], 'total': total, 'busqueda': texto}
    return render(request, 'publicaciones_lista.html', {'data': data})

def publicaciones_en_debate(request):
    filtro = {'estado': 'publicado', '$expr': {'$gt': ['$totalComentarios', '$totalReacciones']}}
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find(filtro, {'_id': 1})]
    publicaciones = Publicacion.objects.filter(id_buscar=ids).order_by('-totalComentarios')
    total = publicaciones.count()
    data = {'publicaciones': publicaciones[:50], 'total': total, 'estado': 'en debate'}
    return render(request, 'publicaciones_lista.html', {'data': data})

def publicacion_detalle(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    return render(request, 'publicacion_detalle.html', {'data': {'publicacion': publicacion}})

def publicacion_por_url(request):
    publicacion = Publicacion.objects.filter(archivoUrl=request.GET.get('archivoUrl')).first()
    if publicacion is None:
        raise Http404
    return render(request, 'publicacion_detalle.html', {'data': {'publicacion': publicacion}})

def publicacion_crear(request):
    contexto = {'accion': 'crear', 'categorias': Categoria.objects.all().order_by('nombre')}
    if request.method == 'GET':
        return render(request, 'publicacion_form.html', {'data': contexto})
    errores = []
    autor = {'nombreUsuario': request.POST.get('autor', ''), 'imagenPerfil': None}
    slugs = request.POST.getlist('categorias')
    categorias = Categoria.objects.filter(slug_buscar=slugs)
    datos = {
        'tipo': request.POST.get('tipo'),
        'titulo': request.POST.get('titulo') or None,
        'descripcion': request.POST.get('descripcion') or None,
        'archivoUrl': request.POST.get('archivoUrl', ''),
        'formato': request.POST.get('formato'),
        'tamanioBytes': request.POST.get('tamanioBytes'),
        'ancho': request.POST.get('ancho') or None,
        'alto': request.POST.get('alto') or None,
        'duracionSegundos': request.POST.get('duracionSegundos') or None,
        'etiquetas': [etiqueta.strip() for etiqueta in request.POST.get('etiquetas', '').split(',') if etiqueta.strip()],
        'categorias': [{'nombre': categoria.nombre, 'slug': categoria.slug} for categoria in categorias],
        'estado': request.POST.get('estado') or 'publicado',
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
        errores.append('El archivoUrl debe ser un link válido.')
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
        return render(request, 'publicacion_form.html', {'data': contexto})
    publicacion.save()
    for categoria in categorias:
        categoria.totalPublicaciones += 1
        categoria.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

def publicacion_actualizar(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    contexto = {
        'accion': 'actualizar',
        'publicacion': publicacion,
        'categorias': Categoria.objects.all().order_by('nombre'),
    }
    if request.method == 'GET':
        return render(request, 'publicacion_form.html', {'data': contexto})
    errores = []
    anteriores = [categoria['slug'] for categoria in publicacion.categorias]
    slugs = request.POST.getlist('categorias')
    categorias = Categoria.objects.filter(slug_buscar=slugs)
    datos = {
        'tipo': request.POST.get('tipo'),
        'titulo': request.POST.get('titulo') or None,
        'descripcion': request.POST.get('descripcion') or None,
        'archivoUrl': request.POST.get('archivoUrl', ''),
        'formato': request.POST.get('formato'),
        'tamanioBytes': request.POST.get('tamanioBytes'),
        'ancho': request.POST.get('ancho') or None,
        'alto': request.POST.get('alto') or None,
        'duracionSegundos': request.POST.get('duracionSegundos') or None,
        'etiquetas': [etiqueta.strip() for etiqueta in request.POST.get('etiquetas', '').split(',') if etiqueta.strip()],
        'categorias': [{'nombre': categoria.nombre, 'slug': categoria.slug} for categoria in categorias],
        'estado': request.POST.get('estado') or 'publicado',
    }
    edicion = None
    if request.POST.get('tipoEdicion'):
        edicion = {
            'tipoEdicion': request.POST.get('tipoEdicion'),
            'descripcion': request.POST.get('descripcionEdicion') or None,
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
        errores.append('El archivoUrl debe ser un link válido.')
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
        return render(request, 'publicacion_form.html', {'data': contexto})
    publicacion.save()
    for categoria in Categoria.objects.filter(slug_buscar=list(set(slugs) - set(anteriores))):
        categoria.totalPublicaciones += 1
        categoria.save()
    for categoria in Categoria.objects.filter(slug_buscar=list(set(anteriores) - set(slugs))):
        categoria.totalPublicaciones = max(0, categoria.totalPublicaciones - 1)
        categoria.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

def publicacion_eliminar(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    for categoria in Categoria.objects.filter(slug_buscar=[copia['slug'] for copia in publicacion.categorias]):
        categoria.totalPublicaciones = max(0, categoria.totalPublicaciones - 1)
        categoria.save()
    publicacion.delete()
    return redirect('publicaciones_listar')

def publicaciones_estado_masivo(request):
    autor = request.POST.get('autor')
    estado_actual = request.POST.get('estadoActual')
    estado_nuevo = request.POST.get('estadoNuevo')
    if estado_actual not in ESTADOS or estado_nuevo not in ESTADOS:
        data = {'publicaciones': [], 'total': 0, 'errores': ['Los estados deben ser publicado, borrador o eliminado.']}
        return render(request, 'publicaciones_lista.html', {'data': data}, status=400)
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find({'autor.nombreUsuario': autor, 'estado': estado_actual}, {'_id': 1})]
    Publicacion.objects.filter(id_buscar=ids).update(estado=estado_nuevo)
    return redirect('publicaciones_listar')

def publicaciones_depurar(request):
    eliminadas = list(Publicacion.objects.filter(estado='eliminado'))
    for publicacion in eliminadas:
        for categoria in Categoria.objects.filter(slug_buscar=[copia['slug'] for copia in publicacion.categorias]):
            categoria.totalPublicaciones = max(0, categoria.totalPublicaciones - 1)
            categoria.save()
        publicacion.delete()
    return redirect('publicaciones_listar')

def publicacion_comentar(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    errores = []
    autor = {'nombreUsuario': request.POST.get('autor', ''), 'imagenPerfil': None}
    contenido = request.POST.get('contenido', '').strip()
    formato = request.POST.get('formato') or 'texto'
    if not 3 <= len(autor['nombreUsuario']) <= 30:
        errores.append('El autor debe tener un nombre de usuario de 3 a 30 caracteres.')
    if not 1 <= len(contenido) <= 500:
        errores.append('El comentario debe tener entre 1 y 500 caracteres...')
    if formato not in FORMATOS_COMENTARIO:
        errores.append('El formato del comentario no es válido.')
    if len(publicacion.comentarios) >= 300:
        errores.append('La publicación llegó al límite de 300 comentarios.')
    if errores:
        return render(request, 'publicacion_detalle.html', {'data': {'publicacion': publicacion, 'errores': errores}}, status=400)
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
    publicacion.comentarios.append(comentario)
    publicacion.totalComentarios += 1
    publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

def comentario_actualizar(request, pk, indice):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    if not 0 <= indice < len(publicacion.comentarios):
        raise Http404
    errores = []
    contenido = request.POST.get('contenido', '').strip()
    if not 1 <= len(contenido) <= 500:
        errores.append('El comentario debe tener entre 1 y 500 caracteres...')
    if errores:
        return render(request, 'publicacion_detalle.html', {'data': {'publicacion': publicacion, 'errores': errores}}, status=400)
    publicacion.comentarios[indice]['contenido'] = contenido
    publicacion.comentarios[indice]['estado'] = 'editado'
    publicacion.comentarios[indice]['fechaEdicion'] = timezone.now()
    publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

def comentario_eliminar(request, pk, indice):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    if not 0 <= indice < len(publicacion.comentarios):
        raise Http404
    del publicacion.comentarios[indice]
    publicacion.totalComentarios = max(0, publicacion.totalComentarios - 1)
    publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

def publicacion_reaccionar(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    errores = []
    usuario = {'nombreUsuario': request.POST.get('usuario', ''), 'imagenPerfil': None}
    tipoReaccion = request.POST.get('tipoReaccion')
    if not 3 <= len(usuario['nombreUsuario']) <= 30:
        errores.append('El usuario debe tener un nombre de 3 a 30 caracteres.')
    if tipoReaccion not in TIPOS_REACCION:
        errores.append('Tipo de reacción inválido.')
    if errores:
        return render(request, 'publicacion_detalle.html', {'data': {'publicacion': publicacion, 'errores': errores}}, status=400)
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

"""RECOMENDACIONES VIEWS"""
def recomendaciones_listar(request):
    usuario = request.GET.get('usuario')
    vista = request.GET.get('vista')
    criterio = request.GET.get('criterio')
    filtro = {}
    if usuario:
        filtro['usuario.nombreUsuario'] = usuario
    if vista in ('si', 'no'):
        filtro['vista'] = vista == 'si'
    recomendaciones = Recomendacion.objects.all()
    if filtro:
        ids = [documento['_id'] for documento in connection.cursor().db_conn[Recomendacion._meta.db_table].find(filtro, {'_id': 1})]
        recomendaciones = recomendaciones.filter(id_buscar=ids)
    if criterio in CRITERIOS:
        recomendaciones = recomendaciones.filter(criterio=criterio)
    recomendaciones = recomendaciones.order_by('-puntuacion')
    data = {'recomendaciones': recomendaciones[:10], 'total': recomendaciones.count()}
    return render(request, 'recomendaciones_lista.html', {'data': data})

def recomendacion_detalle(request, pk):
    recomendacion = get_object_or_404(Recomendacion, pk=pk)
    return render(request, 'recomendacion_detalle.html', {'data': {'recomendacion': recomendacion}})

def recomendacion_crear(request):
    contexto = {'accion': 'crear'}
    if request.method == 'GET':
        return render(request, 'recomendacion_form.html', {'data': contexto})
    errores = []
    usuario = {'nombreUsuario': request.POST.get('usuario', ''), 'imagenPerfil': None}
    publicacion = Publicacion.objects.filter(archivoUrl=request.POST.get('archivoUrl')).first()
    datos = {
        'criterio': request.POST.get('criterio'),
        'puntuacion': request.POST.get('puntuacion'),
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
        return render(request, 'recomendacion_form.html', {'data': contexto})
    recomendacion.save()
    return redirect('recomendacion_detalle', pk=recomendacion.pk)

def recomendacion_actualizar(request, pk):
    recomendacion = get_object_or_404(Recomendacion, pk=pk)
    contexto = {'accion': 'actualizar', 'recomendacion': recomendacion}
    if request.method == 'GET':
        return render(request, 'recomendacion_form.html', {'data': contexto})
    errores = []
    datos = {
        'criterio': request.POST.get('criterio'),
        'puntuacion': request.POST.get('puntuacion'),
        'vista': request.POST.get('vista') == 'on',
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
        return render(request, 'recomendacion_form.html', {'data': contexto})
    recomendacion.save()
    return redirect('recomendacion_detalle', pk=recomendacion.pk)

def recomendacion_eliminar(request, pk):
    recomendacion = get_object_or_404(Recomendacion, pk=pk)
    recomendacion.delete()
    return redirect('recomendaciones_listar')

def recomendaciones_marcar_vistas(request):
    usuario = request.POST.get('usuario')
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Recomendacion._meta.db_table].find({'usuario.nombreUsuario': usuario, 'vista': False}, {'_id': 1})]
    Recomendacion.objects.filter(id_buscar=ids).update(vista=True)
    return redirect('recomendaciones_listar')

def recomendaciones_limpiar_vistas(request):
    usuario = request.POST.get('usuario')
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Recomendacion._meta.db_table].find({'usuario.nombreUsuario': usuario, 'vista': True}, {'_id': 1})]
    Recomendacion.objects.filter(id_buscar=ids).delete()
    return redirect('recomendaciones_listar')
