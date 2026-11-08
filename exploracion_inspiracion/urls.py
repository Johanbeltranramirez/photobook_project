from django.urls import path
from . import views

urlpatterns = [

    path("", views.inicio, name="inicio"),

    path("categorias/", views.categorias, name="categorias"),

    path("tendencias/", views.tendencias, name="tendencias"),

    path("destacados/", views.destacados, name="destacados"),

    path("para-ti/", views.para_ti, name="para_ti"),

    path("colecciones/", views.colecciones, name="colecciones"),

    path("estado/", views.estado, name="estado"),

    path("crear/", views.crear, name="crear"),

    path("consultar/", views.consultar, name="consultar"),

    path("eliminar/<str:id>/", views.eliminar, name="eliminar"),

]