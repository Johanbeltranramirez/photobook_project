from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from g_usuarios_perfiles.acceso import sesion_requerida, resumen_usuario
from publicacion_org_contenido.models import Publicacion, Recomendacion, Coleccion
from photobook.consultas import documentos, existe_bloqueo, publicacion_visible
from .models import ExploracionInspiracion
from .forms import FormularioPreferencias


@sesion_requerida
def exploracion_inicio(solicitud):
    perfil = documentos(ExploracionInspiracion, {'usuario.nombreUsuario': solicitud.usuario.nombreUsuario}).first()
    recomendaciones = documentos(Recomendacion, {'usuario.nombreUsuario': solicitud.usuario.nombreUsuario}).order_by('-puntuacion')
    recomendaciones = [dato for dato in recomendaciones if publicacion_visible(solicitud.usuario, dato.publicacion['archivoUrl'])]
    return render(solicitud, 'exploracion_inspiracion/inicio.html', {'perfil': perfil, 'recomendaciones': recomendaciones})


@sesion_requerida
def preferencias_detalle(solicitud):
    perfil = documentos(ExploracionInspiracion, {'usuario.nombreUsuario': solicitud.usuario.nombreUsuario}).first()
    return render(solicitud, 'exploracion_inspiracion/preferencias.html', {'perfil': perfil})


@sesion_requerida
@require_http_methods(['GET', 'POST'])
def preferencias_guardar(solicitud):
    perfil = documentos(ExploracionInspiracion, {'usuario.nombreUsuario': solicitud.usuario.nombreUsuario}).first()
    valores = {}
    if perfil:
        valores = dict(perfil.preferencias)
        valores['etiquetas'] = ', '.join(valores['etiquetas'])
    formulario = FormularioPreferencias(solicitud.POST or None, initial=valores)
    if solicitud.method == 'POST' and formulario.is_valid():
        if perfil is None:
            perfil = ExploracionInspiracion(usuario=resumen_usuario(solicitud.usuario))
        perfil.preferencias = formulario.cleaned_data
        perfil.fechaActualizacion = timezone.now()
        perfil.save()
        actualizar_recomendaciones(solicitud.usuario, perfil)
        return redirect('exploracion_inicio')
    titulo = 'Editar preferencias' if perfil else 'Crear preferencias'
    return render(solicitud, 'comunes/formulario.html', {'formulario': formulario, 'titulo': titulo})


@sesion_requerida
@require_http_methods(['GET', 'POST'])
def preferencias_eliminar(solicitud):
    perfil = documentos(ExploracionInspiracion, {'usuario.nombreUsuario': solicitud.usuario.nombreUsuario}).first()
    if solicitud.method == 'POST':
        if perfil:
            perfil.delete()
        documentos(Recomendacion, {'usuario.nombreUsuario': solicitud.usuario.nombreUsuario, 'criterio': 'preferencias'}).delete()
        return redirect('exploracion_inicio')
    return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar preferencias', 'objeto': 'Tus preferencias y sus recomendaciones automáticas'})


@sesion_requerida
@require_POST
def recomendaciones_generar(solicitud):
    perfil = documentos(ExploracionInspiracion, {'usuario.nombreUsuario': solicitud.usuario.nombreUsuario}).first()
    if perfil:
        actualizar_recomendaciones(solicitud.usuario, perfil)
    return redirect('exploracion_inicio')


def actualizar_recomendaciones(usuario, perfil):
    preferencias = perfil.preferencias
    anteriores = documentos(Recomendacion, {'usuario.nombreUsuario': usuario.nombreUsuario, 'criterio': 'preferencias'})
    urls_vistas = {dato.publicacion['archivoUrl'] for dato in anteriores if dato.vista}
    coincidencias = []
    for publicacion in Publicacion.objects.filter(estado='publicado').order_by('-fechaPublicacion'):
        if publicacion.autor['nombreUsuario'] == usuario.nombreUsuario or existe_bloqueo(usuario.nombreUsuario, publicacion.autor['nombreUsuario'], 'contenido'):
            continue
        factores = []
        if any(dato['slug'] in preferencias['categorias'] for dato in publicacion.categorias):
            factores.append({'nombre': 'Categorías preferidas', 'peso': 1.0 / 3})
        if set(dato.lower() for dato in publicacion.etiquetas) & set(preferencias['etiquetas']):
            factores.append({'nombre': 'Etiquetas preferidas', 'peso': 1.0 / 3})
        if publicacion.autor['nombreUsuario'] in preferencias['artistas']:
            factores.append({'nombre': 'Artista preferido', 'peso': 1.0 / 3})
        if factores:
            coincidencias.append((publicacion, factores))
    coincidencias.sort(key=lambda dato: len(dato[1]), reverse=True)
    vigentes = []
    for publicacion, factores in coincidencias[:20]:
        recomendacion = documentos(Recomendacion, {'usuario.nombreUsuario': usuario.nombreUsuario, 'publicacion.archivoUrl': publicacion.archivoUrl, 'criterio': 'preferencias'}).first()
        if recomendacion is None:
            recomendacion = Recomendacion(usuario=resumen_usuario(usuario), criterio='preferencias')
        recomendacion.publicacion = {'titulo': publicacion.titulo, 'tipo': publicacion.tipo, 'archivoUrl': publicacion.archivoUrl}
        recomendacion.puntuacion = len(factores) / 3
        recomendacion.factores = factores
        recomendacion.vista = publicacion.archivoUrl in urls_vistas
        recomendacion.save()
        vigentes.append(recomendacion.pk)
    for recomendacion in anteriores:
        if recomendacion.pk not in vigentes:
            recomendacion.delete()


@sesion_requerida
def tendencias_listar(solicitud):
    publicaciones = [dato for dato in Publicacion.objects.filter(estado='publicado').order_by('-totalReacciones', '-totalComentarios', '-fechaPublicacion') if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido')][:20]
    return render(solicitud, 'exploracion_inspiracion/publicaciones.html', {'titulo': 'Tendencias', 'publicaciones': publicaciones})


@sesion_requerida
def destacados_listar(solicitud):
    publicaciones = [dato for dato in Publicacion.objects.filter(estado='publicado').order_by('-totalComentarios', '-totalReacciones', '-fechaPublicacion') if not existe_bloqueo(solicitud.usuario.nombreUsuario, dato.autor['nombreUsuario'], 'contenido')][:20]
    return render(solicitud, 'exploracion_inspiracion/publicaciones.html', {'titulo': 'Publicaciones destacadas', 'publicaciones': publicaciones})


@sesion_requerida
def colecciones_colaborativas(solicitud):
    colecciones = documentos(Coleccion, {'tipo': 'colaborativa', '$or': [{'privacidad': 'publica'}, {'creador.nombreUsuario': solicitud.usuario.nombreUsuario}, {'colaboradores.nombreUsuario': solicitud.usuario.nombreUsuario}]})
    return render(solicitud, 'colecciones_lista.html', {'datos': {'colecciones': colecciones, 'total': colecciones.count()}})
