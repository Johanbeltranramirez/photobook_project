from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('publicacion-contenido/', include('publicacion_org_contenido.urls')),
]
