from django.urls import path
from . import views
from publicacion_org_contenido import views as publicaciones

urlpatterns = [
    path('recomendaciones/<oid:pk>/', publicaciones.recomendacion_detalle, name='exploracion_recomendacion'),
    path('recomendaciones/<oid:pk>/eliminar/', publicaciones.recomendacion_eliminar, name='exploracion_recomendacion_eliminar'),
    path('', views.exploracion_inicio, name='exploracion_inicio'),
    path('preferencias/', views.preferencias_detalle, name='preferencias_detalle'),
    path('preferencias/crear/', views.preferencias_guardar, name='preferencias_crear'),
    path('preferencias/editar/', views.preferencias_guardar, name='preferencias_actualizar'),
    path('preferencias/eliminar/', views.preferencias_eliminar, name='preferencias_eliminar'),
    path('recomendaciones/generar/', views.recomendaciones_generar, name='recomendaciones_generar'),
    path('tendencias/', views.tendencias_listar, name='tendencias_listar'),
    path('destacados/', views.destacados_listar, name='destacados_listar'),
    path('colecciones/', views.colecciones_colaborativas, name='colecciones_colaborativas'),
]
