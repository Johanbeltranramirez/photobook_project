from django.urls import path
from . import views


urlpatterns = [
    path('roles/crear/', views.crear_rol),
    path('roles/consultar/', views.consultar_roles),
    path('roles/actualizar/', views.actualizar_rol),
    path('roles/eliminar/', views.eliminar_rol),

    path('acciones/crear/', views.crear_accion),
    path('acciones/consultar/', views.consultar_acciones),
    path('acciones/actualizar/', views.actualizar_accion),
    path('acciones/eliminar/', views.eliminar_accion),

    path('reportes/crear/', views.crear_reporte),
    path('reportes/consultar/', views.consultar_reportes),
    path('reportes/actualizar/', views.actualizar_reporte),
    path('reportes/eliminar/', views.eliminar_reporte),

    path('control/crear/', views.crear_control),
    path('control/consultar/', views.consultar_controles),
    path('control/actualizar/', views.actualizar_control),
    path('control/eliminar/', views.eliminar_control),
]
