from django.urls import path
from . import views

urlpatterns = [
    path('roles/', views.consultar_roles, name='consultar_roles'),
    path('roles/crear/', views.crear_rol, name='crear_rol'),
    path('roles/<oid:pk>/editar/', views.actualizar_rol, name='actualizar_rol'),
    path('roles/<oid:pk>/eliminar/', views.eliminar_rol, name='eliminar_rol'),
    path('acciones/', views.consultar_acciones, name='consultar_acciones'),
    path('acciones/crear/', views.crear_accion, name='crear_accion'),
    path('acciones/<oid:pk>/editar/', views.actualizar_accion, name='actualizar_accion'),
    path('acciones/<oid:pk>/eliminar/', views.eliminar_accion, name='eliminar_accion'),
    path('controles/', views.consultar_controles, name='consultar_controles'),
    path('controles/crear/', views.crear_control, name='crear_control'),
    path('controles/<oid:pk>/editar/', views.actualizar_control, name='actualizar_control'),
    path('controles/<oid:pk>/eliminar/', views.eliminar_control, name='eliminar_control'),
    path('reportes/crear/', views.crear_reporte, name='reporte_crear'),
    path('reportes/consultar/', views.consultar_reportes, name='reportes_listar'),
    path('reportes/<oid:pk>/', views.detalle_reporte, name='reporte_detalle'),
    path('reportes/<oid:pk>/actualizar/', views.actualizar_reporte, name='reporte_actualizar'),
    path('reportes/<oid:pk>/resolver/', views.resolver_reporte, name='reporte_resolver'),
    path('reportes/<oid:pk>/eliminar/', views.eliminar_reporte, name='reporte_eliminar'),
    path('usuarios/<str:nombre>/rol/', views.asignar_rol, name='asignar_rol'),
]
