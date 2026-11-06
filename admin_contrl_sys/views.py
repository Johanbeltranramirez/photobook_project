from django.http import HttpResponse

from .models import Rol, AccionAdministrativa, ReporteContenido, ControlSistema


def crear_rol(request):
    Rol.objects.create(
        nombre="Moderador",
        descripcion="Encargado de revisar y moderar el contenido de Photobook",
        permiso_usuarios=False,
        permiso_contenido=True,
        permiso_estadisticas=True,
        activo=True
    )

    return HttpResponse("Rol creado correctamente")


def consultar_roles(request):
    roles = Rol.objects.all()

    return HttpResponse(str(roles))


def actualizar_rol(request):
    rol = Rol.objects.get(nombre="Moderador")

    rol.descripcion = "Encargado de moderar contenido y revisar reportes"
    rol.permiso_usuarios = True

    rol.save()

    return HttpResponse("Rol actualizado correctamente")


def eliminar_rol(request):
    rol = Rol.objects.get(nombre="Moderador")

    rol.delete()

    return HttpResponse("Rol eliminado correctamente")


def crear_accion(request):
    AccionAdministrativa.objects.create(
        administrador="Diego Arias",
        rol_administrador="Moderador",
        accion="Ocultar publicacion",
        entidad="Publicacion",
        detalle_entidad="Publicacion de fotografia reportada por la comunidad",
        descripcion="La publicacion fue ocultada por incumplir las normas de Photobook",
        fecha="2026-11-06 12:00:00"
    )

    return HttpResponse("Accion administrativa creada correctamente")


def consultar_acciones(request):
    acciones = AccionAdministrativa.objects.all()

    return HttpResponse(str(acciones))


def actualizar_accion(request):
    accion = AccionAdministrativa.objects.get(
        administrador="Diego Arias",
        accion="Ocultar publicacion"
    )

    accion.descripcion = "La publicacion fue revisada y posteriormente ocultada"
    accion.detalle_entidad = "Publicacion revisada por el equipo de moderacion"

    accion.save()

    return HttpResponse("Accion administrativa actualizada correctamente")


def eliminar_accion(request):
    accion = AccionAdministrativa.objects.get(
        administrador="Diego Arias",
        accion="Ocultar publicacion"
    )

    accion.delete()

    return HttpResponse("Accion administrativa eliminada correctamente")


def crear_reporte(request):
    ReporteContenido.objects.create(
        contenido="Fotografia reportada por la comunidad",
        tipo_contenido="Imagen",
        motivo="Contenido inapropiado",
        estado="Pendiente",
        reportado_por="Usuario123",
        fecha_reporte="2026-11-06 12:30:00"
    )

    return HttpResponse("Reporte creado correctamente")


def consultar_reportes(request):
    reportes = ReporteContenido.objects.all()

    return HttpResponse(str(reportes))


def actualizar_reporte(request):
    reporte = ReporteContenido.objects.get(
        contenido="Fotografia reportada por la comunidad",
        estado="Pendiente"
    )

    reporte.estado = "Revisado"
    reporte.motivo = "Contenido revisado por el moderador"

    reporte.save()

    return HttpResponse("Reporte actualizado correctamente")


def eliminar_reporte(request):
    reporte = ReporteContenido.objects.get(
        contenido="Fotografia reportada por la comunidad"
    )

    reporte.delete()

    return HttpResponse("Reporte eliminado correctamente")


def crear_control(request):
    ControlSistema.objects.create(
        fecha="2026-11-06",
        usuarios_activos=850,
        publicaciones=320,
        reportes=15,
        fecha_respaldo="2026-11-06 23:00:00",
        estado_respaldo="Exitoso"
    )

    return HttpResponse("Registro de control creado correctamente")


def consultar_controles(request):
    controles = ControlSistema.objects.all()

    return HttpResponse(str(controles))


def actualizar_control(request):
    control = ControlSistema.objects.get(
        fecha="2026-11-06"
    )

    control.usuarios_activos = 900
    control.publicaciones = 350
    control.reportes = 18
    control.estado_respaldo = "Exitoso"

    control.save()

    return HttpResponse("Registro de control actualizado correctamente")


def eliminar_control(request):
    control = ControlSistema.objects.get(
        fecha="2026-11-06"
    )

    control.delete()

    return HttpResponse("Registro de control eliminado correctamente")
