from django.urls import include, path, register_converter
from aplicaciones.g_usuarios_perfiles.views import inicio
from photobook.utilidades.conversores import IdentificadorMongo

register_converter(IdentificadorMongo, 'oid')

urlpatterns = [
    path('', inicio, name='inicio'),
    path('usuarios/', include('aplicaciones.g_usuarios_perfiles.urls')),
    path('publicacion-contenido/', include('aplicaciones.publicacion_org_contenido.urls')),
    path('comunidad/', include('aplicaciones.int_social_comunidad.urls')),
    path('exploracion/', include('aplicaciones.exploracion_inspiracion.urls')),
    path('administracion/', include('aplicaciones.admin_contrl_sys.urls')),
]
