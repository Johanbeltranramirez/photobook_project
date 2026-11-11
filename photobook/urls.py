from bson import ObjectId
from django.urls import include, path, register_converter
from g_usuarios_perfiles.views import inicio

class IdentificadorMongo:
    regex = '[0-9a-fA-F]{24}'

    def to_python(self, valor):
        return ObjectId(valor)

    def to_url(self, valor):
        return str(valor)

register_converter(IdentificadorMongo, 'oid')

urlpatterns = [
    path('', inicio, name='inicio'),
    path('usuarios/', include('g_usuarios_perfiles.urls')),
    path('publicacion-contenido/', include('publicacion_org_contenido.urls')),
    path('comunidad/', include('int_social_comunidad.urls')),
    path('exploracion/', include('exploracion_inspiracion.urls')),
    path('administracion/', include('admin_contrl_sys.urls')),
]
