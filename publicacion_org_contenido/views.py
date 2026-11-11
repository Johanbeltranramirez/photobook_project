from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import connection
from django.db.models import Q
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from . import archivos
from .models import Categoria, Coleccion, Publicacion, Recomendacion
from .opciones import *
from .forms import FormularioCategoria, FormularioPublicacion, FormularioColeccion, FormularioRecomendacion
from g_usuarios_perfiles.models import Usuario
from g_usuarios_perfiles.notificaciones import notificar
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
    return render(solicitud, 'categorias/categorias_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def categoria_detalle(solicitud, slug):
    categoria = get_object_or_404(Categoria, slug=slug)
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find({'categorias.slug': slug, 'estado': 'publicado'}, {'_id': 1})]
    recientes = []
    for dato in Publicacion.objects.filter(pk__in=ids).order_by('-fechaPublicacion'):
        if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido'):
            recientes.append(dato)
        if len(recientes) == 8:
            break
    return render(solicitud, 'categorias/categoria_detalle.html', {'datos': {'categoria': categoria, 'publicaciones': recientes}})

@administrador_requerido
@require_http_methods(['GET', 'POST'])
def categoria_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {}
    formulario = FormularioCategoria(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'categorias/categoria_form.html', {'datos': contexto})
    errores = []
    nombre = solicitud.POST.get('nombre', '').strip()
    slug = slugify(nombre)
    if not 1 <= len(nombre) <= 60 or not PATRON_SLUG.match(slug):
        errores.append('El nombre debe tener hasta 60 caracteres y generar un slug válido.')
    if Categoria.objects.filter(Q(nombre=nombre) | Q(slug=slug)).exists():
        errores.append('Ya existe una categoría con ese nombre.')
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'categorias/categoria_form.html', {'datos': contexto})
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
        return render(solicitud, 'categorias/categoria_form.html', {'datos': contexto})
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
        return render(solicitud, 'categorias/categoria_form.html', {'datos': contexto})
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
        return render(solicitud, 'categorias/categoria_detalle.html', {'datos': {'categoria': categoria, 'errores': errores}}, status=400)
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
    return render(solicitud, 'colecciones/colecciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def coleccion_detalle(solicitud, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk)
    comprobar_coleccion(solicitud, coleccion)
    usuario = solicitud.usuario
    editores = [coleccion.creador['nombreUsuario']] + [dato['nombreUsuario'] for dato in coleccion.colaboradores]
    puede_gestionar = usuario.nombreUsuario == coleccion.creador['nombreUsuario'] or usuario.rol == 'administrador'
    puede_editar = usuario.nombreUsuario in editores
    disponibles = []
    if puede_editar:
        usadas = {dato['archivoUrl'] for dato in coleccion.publicaciones}
        for dato in Publicacion.objects.filter(estado='publicado').order_by('-fechaPublicacion'):
            if dato.archivoUrl not in usadas and not existe_bloqueo(usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido'):
                disponibles.append(dato)
            if len(disponibles) == 24:
                break
    candidatos = []
    if puede_gestionar and coleccion.tipo == 'colaborativa':
        candidatos = [dato for dato in Usuario.objects.filter(activo__in=[True]) if dato.nombreUsuario not in editores]
    datos = {'coleccion': coleccion, 'puede_editar': puede_editar, 'puede_gestionar': puede_gestionar, 'disponibles': disponibles, 'candidatos': candidatos}
    return render(solicitud, 'colecciones/coleccion_detalle.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def coleccion_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {}
    formulario = FormularioColeccion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'colecciones/coleccion_form.html', {'datos': contexto})
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
        return render(solicitud, 'colecciones/coleccion_form.html', {'datos': contexto})
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
        return render(solicitud, 'colecciones/coleccion_form.html', {'datos': contexto})
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
        return render(solicitud, 'colecciones/coleccion_form.html', {'datos': contexto})
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
    return render(solicitud, 'publicaciones/publicaciones_lista.html', {'datos': datos})

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
    return render(solicitud, 'publicaciones/publicaciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def publicaciones_en_debate(solicitud):
    filtro = {'estado': 'publicado', '$expr': {'$gt': ['$totalComentarios', '$totalReacciones']}}
    ids = [documento['_id'] for documento in connection.cursor().db_conn[Publicacion._meta.db_table].find(filtro, {'_id': 1})]
    publicaciones = Publicacion.objects.filter(pk__in=ids).order_by('-totalComentarios')
    total = publicaciones.count()
    publicaciones = [dato for dato in publicaciones if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido')]
    datos = {'publicaciones': publicaciones[:50], 'total': total, 'estado': 'en debate'}
    return render(solicitud, 'publicaciones/publicaciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def publicacion_detalle(solicitud, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    comprobar_publicacion(solicitud, publicacion)
    return render(solicitud, 'publicaciones/publicacion_detalle.html', {'datos': contexto_publicacion(solicitud, publicacion)})

@sesion_requerida
@require_http_methods(['GET'])
def publicacion_por_url(solicitud):
    publicacion = Publicacion.objects.filter(archivoUrl=solicitud.GET.get('archivoUrl')).first()
    comprobar_publicacion(solicitud, publicacion)
    if publicacion is None:
        raise Http404
    return render(solicitud, 'publicaciones/publicacion_detalle.html', {'datos': contexto_publicacion(solicitud, publicacion)})

@sesion_requerida
@require_http_methods(['GET', 'POST'])
def publicacion_crear(solicitud):
    contexto = {'accion': 'crear'}
    enviado = solicitud.method == 'POST'
    formulario = FormularioPublicacion(solicitud.POST if enviado else None, solicitud.FILES if enviado else None)
    contexto['formulario'] = formulario
    if not enviado or not formulario.is_valid():
        return render(solicitud, 'publicaciones/publicacion_form.html', {'datos': contexto})
    autor = resumen_usuario(solicitud.usuario)
    info = formulario.info_archivo
    slugs = formulario.cleaned_data['categorias']
    categorias = Categoria.objects.filter(slug__in=slugs)
    etiquetas = separar_etiquetas(formulario.cleaned_data['etiquetas'])
    errores = validar_publicacion(autor, categorias, slugs, etiquetas)
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'publicaciones/publicacion_form.html', {'datos': contexto})
    nombre_archivo = archivos.guardar_archivo(formulario.cleaned_data['archivo'], info['formato'])
    publicacion = Publicacion(
        autor=autor,
        tipo=info['tipo'],
        titulo=formulario.cleaned_data['titulo'] or None,
        descripcion=formulario.cleaned_data['descripcion'] or None,
        archivoUrl=archivos.url_archivo(solicitud, nombre_archivo),
        formato=info['formato'],
        tamanioBytes=info['tamanioBytes'],
        ancho=info['ancho'],
        alto=info['alto'],
        duracionSegundos=info['duracionSegundos'],
        etiquetas=etiquetas,
        categorias=[{'nombre': categoria.nombre, 'slug': categoria.slug} for categoria in categorias],
        estado='borrador' if solicitud.POST.get('accion') == 'borrador' else 'publicado',
        totalReacciones=0,
        totalComentarios=0,
        comentarios=[],
        reacciones=[],
        historialEdiciones=[],
        fechaPublicacion=timezone.now(),
    )
    try:
        publicacion.full_clean(validate_unique=False)
        publicacion.save()
    except ValidationError as excepcion:
        archivos.eliminar_archivo(publicacion.archivoUrl)
        contexto['errores'] = excepcion.messages
        return render(solicitud, 'publicaciones/publicacion_form.html', {'datos': contexto})
    except Exception:
        archivos.eliminar_archivo(publicacion.archivoUrl)
        raise
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
    contexto = {'accion': 'actualizar', 'publicacion': publicacion}
    valores = {campo: getattr(publicacion, campo, None) for campo in FormularioPublicacion().fields}
    valores['etiquetas'] = ', '.join(publicacion.etiquetas)
    valores['categorias'] = [dato['slug'] for dato in publicacion.categorias]
    enviado = solicitud.method == 'POST'
    formulario = FormularioPublicacion(solicitud.POST if enviado else None, solicitud.FILES if enviado else None, initial=valores, archivo_obligatorio=False)
    contexto['formulario'] = formulario
    if not enviado or not formulario.is_valid():
        return render(solicitud, 'publicaciones/publicacion_form.html', {'datos': contexto})
    anteriores = [categoria['slug'] for categoria in publicacion.categorias]
    slugs = formulario.cleaned_data['categorias']
    categorias = Categoria.objects.filter(slug__in=slugs)
    etiquetas = separar_etiquetas(formulario.cleaned_data['etiquetas'])
    errores = validar_publicacion(publicacion.autor, categorias, slugs, etiquetas)
    edicion = None
    if solicitud.POST.get('tipoEdicion'):
        edicion = {
            'tipoEdicion': solicitud.POST.get('tipoEdicion'),
            'descripcion': solicitud.POST.get('descripcionEdicion') or None,
            'fecha': timezone.now(),
        }
        if edicion['tipoEdicion'] not in TIPOS_EDICION:
            errores.append('El tipo de edición no es válido.')
    if edicion and len(publicacion.historialEdiciones) >= 100:
        errores.append('¡El historial de ediciones llegó a su límite de 100!')
    if errores:
        contexto['errores'] = errores
        return render(solicitud, 'publicaciones/publicacion_form.html', {'datos': contexto})
    datos = {
        'titulo': formulario.cleaned_data['titulo'] or None,
        'descripcion': formulario.cleaned_data['descripcion'] or None,
        'etiquetas': etiquetas,
        'categorias': [{'nombre': categoria.nombre, 'slug': categoria.slug} for categoria in categorias],
    }
    accion = solicitud.POST.get('accion')
    if accion == 'borrador':
        datos['estado'] = 'borrador'
    elif accion == 'publicar':
        datos['estado'] = 'publicado'
    nombre_nuevo = None
    nuevo = formulario.cleaned_data['archivo']
    if nuevo:
        info = formulario.info_archivo
        nombre_nuevo = archivos.guardar_archivo(nuevo, info['formato'])
        datos.update(tipo=info['tipo'], archivoUrl=archivos.url_archivo(solicitud, nombre_nuevo), formato=info['formato'], tamanioBytes=info['tamanioBytes'], ancho=info['ancho'], alto=info['alto'], duracionSegundos=info['duracionSegundos'])
    originales = {campo: getattr(publicacion, campo) for campo in datos}
    for campo, valor in datos.items():
        setattr(publicacion, campo, valor)
    if edicion:
        publicacion.historialEdiciones.append(edicion)
    try:
        publicacion.full_clean(validate_unique=False)
        publicacion.save()
    except ValidationError as excepcion:
        for campo, valor in originales.items():
            setattr(publicacion, campo, valor)
        if nombre_nuevo:
            archivos.eliminar_archivo(datos['archivoUrl'])
        contexto['errores'] = excepcion.messages
        return render(solicitud, 'publicaciones/publicacion_form.html', {'datos': contexto})
    except Exception:
        if nombre_nuevo:
            archivos.eliminar_archivo(datos['archivoUrl'])
        raise
    if nombre_nuevo:
        archivos.eliminar_archivo(enlace_anterior)
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
@require_POST
def publicacion_publicar(solicitud, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    comprobar_propietario(solicitud, publicacion.autor['nombreUsuario'])
    if publicacion.estado == 'borrador':
        publicacion.estado = 'publicado'
        publicacion.save()
    return redirect('publicacion_detalle', pk=publicacion.pk)

@require_http_methods(['GET', 'HEAD'])
def archivo_publicacion(solicitud, nombre):
    return archivos.responder_archivo(solicitud, nombre)

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
        return render(solicitud, 'publicaciones/publicaciones_lista.html', {'datos': datos}, status=400)
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
        return render(solicitud, 'publicaciones/publicacion_detalle.html', {'datos': contexto_publicacion(solicitud, publicacion, errores=errores)}, status=400)
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
    notificar_comentario(solicitud, publicacion, contenido)
    return volver_a_publicacion(publicacion, 'comentarios')

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
        return render(solicitud, 'publicaciones/publicacion_detalle.html', {'datos': contexto_publicacion(solicitud, publicacion, errores=errores)}, status=400)
    publicacion.comentarios[indice]['contenido'] = contenido
    publicacion.comentarios[indice]['estado'] = 'editado'
    publicacion.comentarios[indice]['fechaEdicion'] = timezone.now()
    publicacion.save()
    return volver_a_publicacion(publicacion, 'comentarios')

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
    return volver_a_publicacion(publicacion, 'comentarios')

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
        return render(solicitud, 'publicaciones/publicacion_detalle.html', {'datos': contexto_publicacion(solicitud, publicacion, errores=errores)}, status=400)
    existente = next((reaccion for reaccion in publicacion.reacciones if reaccion['usuario']['nombreUsuario'] == usuario['nombreUsuario']), None)
    nueva = False
    if existente is None:
        publicacion.reacciones.append({'usuario': usuario, 'tipoReaccion': tipoReaccion, 'fecha': timezone.now()})
        publicacion.totalReacciones += 1
        nueva = True
    elif existente['tipoReaccion'] == tipoReaccion:
        publicacion.reacciones.remove(existente)
        publicacion.totalReacciones = max(0, publicacion.totalReacciones - 1)
    else:
        existente['tipoReaccion'] = tipoReaccion
        existente['fecha'] = timezone.now()
        nueva = True
    publicacion.save()
    if nueva:
        notificar_reaccion(solicitud, publicacion, tipoReaccion)
    return volver_a_publicacion(publicacion, 'reacciones')


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
    return render(solicitud, 'recomendaciones/recomendaciones_lista.html', {'datos': datos})

@sesion_requerida
@require_http_methods(['GET'])
def recomendacion_detalle(solicitud, pk):
    recomendacion = get_object_or_404(Recomendacion, pk=pk)
    comprobar_propietario(solicitud, recomendacion.usuario['nombreUsuario'])
    if publicacion_visible(solicitud.usuario, recomendacion.publicacion['archivoUrl']) is None:
        raise Http404('La publicación recomendada no está disponible.')
    return render(solicitud, 'recomendaciones/recomendacion_detalle.html', {'datos': {'recomendacion': recomendacion}})

@administrador_requerido
@require_http_methods(['GET', 'POST'])
def recomendacion_crear(solicitud):
    contexto = {'accion': 'crear'}
    valores = {}
    formulario = FormularioRecomendacion(solicitud.POST if solicitud.method == 'POST' else None, initial=valores)
    contexto['formulario'] = formulario
    if solicitud.method == 'GET' or not formulario.is_valid():
        return render(solicitud, 'recomendaciones/recomendacion_form.html', {'datos': contexto})
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
        return render(solicitud, 'recomendaciones/recomendacion_form.html', {'datos': contexto})
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
        return render(solicitud, 'recomendaciones/recomendacion_form.html', {'datos': contexto})
    errores = []
    destino = get_object_or_404(Usuario, nombreUsuario=formulario.cleaned_data['usuario'], activo__in=[True])
    contenido = get_object_or_404(Publicacion, archivoUrl=formulario.cleaned_data['archivoUrl'], estado='publicado')
    recomendacion.usuario = resumen_usuario(destino)
    recomendacion.publicacion = {'titulo': contenido.titulo, 'tipo': contenido.tipo, 'archivoUrl': contenido.archivoUrl}
    datos = {
        'criterio': solicitud.POST.get('criterio'),
        'puntuacion': solicitud.POST.get('puntuacion'),
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
        return render(solicitud, 'recomendaciones/recomendacion_form.html', {'datos': contexto})
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
def notificar_comentario(solicitud, publicacion, contenido):
    actor = solicitud.usuario.nombreUsuario
    titulo = publicacion.titulo or 'Sin título'
    ruta = reverse('publicacion_detalle', kwargs={'pk': publicacion.pk}) + '#comentarios'
    dueno = publicacion.autor['nombreUsuario']
    notificar(dueno, 'comentario', '%s comentó tu publicación «%s».' % (actor, titulo), origen=actor, categoria='comentarios', asunto='%s comentó tu publicación' % actor, ruta=ruta, detalle=contenido, boton='Ver comentario', ambito_bloqueo='contenido')
    participantes = []
    for dato in publicacion.comentarios:
        nombre = dato['autor']['nombreUsuario']
        if nombre not in (actor, dueno) and nombre not in participantes:
            participantes.append(nombre)
    for nombre in participantes[:20]:
        notificar(nombre, 'comentario', '%s también comentó en «%s».' % (actor, titulo), origen=actor, categoria='comentarios', asunto='%s también comentó en una publicación' % actor, ruta=ruta, detalle=contenido, boton='Ver conversación', ambito_bloqueo='contenido')


def notificar_reaccion(solicitud, publicacion, tipo):
    actor = solicitud.usuario.nombreUsuario
    icono, etiqueta = next((dato[1], dato[2]) for dato in REACCIONES if dato[0] == tipo)
    notificar(publicacion.autor['nombreUsuario'], 'meGusta', '%s reaccionó %s a tu publicación «%s».' % (actor, icono, publicacion.titulo or 'Sin título'), origen=actor, categoria='reacciones', asunto='%s reaccionó a tu publicación (%s)' % (actor, etiqueta), ruta=reverse('publicacion_detalle', kwargs={'pk': publicacion.pk}) + '#reacciones', boton='Ver publicación', ambito_bloqueo='contenido')


def separar_etiquetas(texto):
    vistas = set()
    etiquetas = []
    for etiqueta in (texto or '').split(','):
        etiqueta = etiqueta.strip().lstrip('#').strip()
        if etiqueta and etiqueta.lower() not in vistas:
            vistas.add(etiqueta.lower())
            etiquetas.append(etiqueta)
    return etiquetas


def validar_publicacion(autor, categorias, slugs, etiquetas):
    errores = []
    if not 3 <= len(autor['nombreUsuario']) <= 30:
        errores.append('El autor debe tener un nombre de usuario de 3 a 30 caracteres.')
    if len(categorias) != len(set(slugs)):
        errores.append('Alguna de las categorías no existe.')
    if len(etiquetas) > 30 or any(len(etiqueta) > 30 for etiqueta in etiquetas):
        errores.append('Máximo 30 etiquetas de hasta 30 caracteres.')
    return errores


def volver_a_publicacion(publicacion, ancla):
    return redirect(reverse('publicacion_detalle', kwargs={'pk': publicacion.pk}) + '#' + ancla)


def contexto_publicacion(solicitud, publicacion, **extra):
    usuario = solicitud.usuario
    conteo = {tipo: 0 for tipo in TIPOS_REACCION}
    iconos = {tipo: (icono, etiqueta) for tipo, icono, etiqueta in REACCIONES}
    mia = None
    quienes = []
    for reaccion in publicacion.reacciones:
        tipo = reaccion['tipoReaccion']
        if tipo not in conteo:
            continue
        conteo[tipo] += 1
        if reaccion['usuario']['nombreUsuario'] == usuario.nombreUsuario:
            mia = tipo
        quienes.append({'usuario': reaccion['usuario'], 'icono': iconos[tipo][0], 'etiqueta': iconos[tipo][1]})
    resumen = [{'tipo': tipo, 'icono': icono, 'etiqueta': etiqueta, 'total': conteo[tipo], 'mia': tipo == mia} for tipo, icono, etiqueta in REACCIONES]
    mis_colecciones = []
    if publicacion.estado == 'publicado':
        filtro = {'$or': [{'creador.nombreUsuario': usuario.nombreUsuario}, {'colaboradores.nombreUsuario': usuario.nombreUsuario}]}
        for coleccion in documentos(Coleccion, filtro).order_by('nombre'):
            contiene = any(dato['archivoUrl'] == publicacion.archivoUrl for dato in coleccion.publicaciones)
            mis_colecciones.append({'coleccion': coleccion, 'contiene': contiene})
    datos = {
        'publicacion': publicacion,
        'puede_gestionar': usuario.nombreUsuario == publicacion.autor['nombreUsuario'] or usuario.rol == 'administrador',
        'resumen_reacciones': resumen,
        'mi_reaccion': mia,
        'quienes_reaccionaron': quienes[:40],
        'mis_colecciones': mis_colecciones,
    }
    datos.update(extra)
    return datos


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
    enlace = publicacion.archivoUrl
    publicacion.delete()
    archivos.eliminar_archivo(enlace)


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
        actor = solicitud.usuario.nombreUsuario
        notificar(publicacion.autor['nombreUsuario'], 'sistema', '%s guardó tu publicación «%s» en una colección.' % (actor, publicacion.titulo or 'Sin título'), origen=actor, categoria='reacciones', asunto='%s guardó tu publicación' % actor, ruta=reverse('publicacion_detalle', kwargs={'pk': publicacion.pk}), boton='Ver publicación', ambito_bloqueo='contenido')
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
        actor = solicitud.usuario.nombreUsuario
        notificar(usuario.nombreUsuario, 'sistema', '%s te invitó a colaborar en la colección «%s».' % (actor, coleccion.nombre), origen=actor, categoria='avisos', asunto='%s te invitó a una colección' % actor, ruta=reverse('coleccion_detalle', kwargs={'pk': coleccion.pk}), boton='Ver la colección', ambito_bloqueo='contenido')
        return redirect('coleccion_detalle', pk=pk)
    coleccion.save()
    return redirect('coleccion_detalle', pk=pk)
