from bson import ObjectId
from django.urls import path, register_converter
from .views import *

class IdConvertido:
    def to_python(self, value):
        return ObjectId(value)
    def to_url(self, value):
        return str(value)

register_converter(IdConvertido, 'oid')

urlpatterns = [
    # Categorías
    path('categorias/', categorias_listar, name='categorias_listar'),
    path('categorias/crear/', categoria_crear, name='categoria_crear'),
    path('categorias/<slug:slug>/', categoria_detalle, name='categoria_detalle'),
    path('categorias/<slug:slug>/actualizar/', categoria_actualizar, name='categoria_actualizar'),
    path('categorias/<slug:slug>/eliminar/', categoria_eliminar, name='categoria_eliminar'),

    # Colecciones
    path('colecciones/', colecciones_listar, name='colecciones_listar'),
    path('colecciones/crear/', coleccion_crear, name='coleccion_crear'),
    path('colecciones/<oid:pk>/', coleccion_detalle, name='coleccion_detalle'),
    path('colecciones/<oid:pk>/actualizar/', coleccion_actualizar, name='coleccion_actualizar'),
    path('colecciones/<oid:pk>/eliminar/', coleccion_eliminar, name='coleccion_eliminar'),

    # Publicaciones
    path('publicaciones/', publicaciones_listar, name='publicaciones_listar'),
    path('publicaciones/buscar/', publicaciones_buscar, name='publicaciones_buscar'),
    path('publicaciones/en-debate/', publicaciones_en_debate, name='publicaciones_en_debate'),
    path('publicaciones/por-url/', publicacion_por_url, name='publicacion_por_url'),
    path('publicaciones/crear/', publicacion_crear, name='publicacion_crear'),
    path('publicaciones/estado-masivo/', publicaciones_estado_masivo, name='publicaciones_estado_masivo'),
    path('publicaciones/depurar/', publicaciones_depurar, name='publicaciones_depurar'),
    path('publicaciones/<oid:pk>/', publicacion_detalle, name='publicacion_detalle'),
    path('publicaciones/<oid:pk>/actualizar/', publicacion_actualizar, name='publicacion_actualizar'),
    path('publicaciones/<oid:pk>/eliminar/', publicacion_eliminar, name='publicacion_eliminar'),
    path('publicaciones/<oid:pk>/comentar/', publicacion_comentar, name='publicacion_comentar'),
    path('publicaciones/<oid:pk>/reaccionar/', publicacion_reaccionar, name='publicacion_reaccionar'),
    path('publicaciones/<oid:pk>/comentarios/<int:indice>/actualizar/', comentario_actualizar, name='comentario_actualizar'),
    path('publicaciones/<oid:pk>/comentarios/<int:indice>/eliminar/', comentario_eliminar, name='comentario_eliminar'),

    # Recomendaciones
    path('recomendaciones/', recomendaciones_listar, name='recomendaciones_listar'),
    path('recomendaciones/crear/', recomendacion_crear, name='recomendacion_crear'),
    path('recomendaciones/marcar-vistas/', recomendaciones_marcar_vistas, name='recomendaciones_marcar_vistas'),
    path('recomendaciones/limpiar-vistas/', recomendaciones_limpiar_vistas, name='recomendaciones_limpiar_vistas'),
    path('recomendaciones/<oid:pk>/', recomendacion_detalle, name='recomendacion_detalle'),
    path('recomendaciones/<oid:pk>/actualizar/', recomendacion_actualizar, name='recomendacion_actualizar'),
    path('recomendaciones/<oid:pk>/eliminar/', recomendacion_eliminar, name='recomendacion_eliminar'),
]
