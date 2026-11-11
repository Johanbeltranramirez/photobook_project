from django.urls import path
from . import views

urlpatterns = [
    path('', views.usuarios_listar, name='usuarios_listar'),
    path('registro/', views.registrar_usuario, name='registrar_usuario'),
    path('ingresar/', views.iniciar_sesion, name='iniciar_sesion'),
    path('salir/', views.cerrar_sesion, name='cerrar_sesion'),
    path('notificaciones/', views.notificaciones_listar, name='notificaciones_listar'),
    path('notificaciones/<oid:pk>/leer/', views.notificacion_leer, name='notificacion_leer'),
    path('notificaciones/<oid:pk>/eliminar/', views.notificacion_eliminar, name='notificacion_eliminar'),
    path('olvido/', views.olvido_contrasena, name='olvido_contrasena'),
    path('restablecer/<str:token>/', views.restablecer_contrasena, name='restablecer_contrasena'),
    path('correo/', views.preferencias_correo, name='preferencias_correo'),
    path('<str:nombre>/', views.perfil_detalle, name='perfil_detalle'),
    path('<str:nombre>/editar/', views.perfil_actualizar, name='perfil_actualizar'),
    path('<str:nombre>/eliminar/', views.perfil_eliminar, name='perfil_eliminar'),
    path('<str:nombre>/seguir/', views.seguir_usuario, name='seguir_usuario'),
]
