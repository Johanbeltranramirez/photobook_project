from bson import ObjectId
from django.http import HttpResponse, Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from g_usuarios_perfiles.acceso import sesion_requerida, administrador_requerido, comprobar_propietario, puede_administrar
from g_usuarios_perfiles.models import Usuario
from g_usuarios_perfiles.notificaciones import notificar
from publicacion_org_contenido.models import Publicacion
from .models import Rol, AccionAdministrativa, ReporteContenido, ControlSistema
from .forms import FormularioRol, FormularioAccion, FormularioReporte, FormularioResolucion, FormularioControl

@sesion_requerida
def crear_reporte(solicitud):
    if solicitud.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    formulario = FormularioReporte(solicitud.POST if solicitud.method == "POST" else None)
    if solicitud.method == "POST" and formulario.is_valid():
        reporte = ReporteContenido.objects.create(reportado_por=solicitud.usuario.nombreUsuario, **formulario.cleaned_data)
        return redirect("reporte_detalle", pk=str(reporte.pk))
    return render(solicitud, "reportes/formulario.html", {"formulario": formulario, "titulo": "Crear reporte"})


@sesion_requerida
def consultar_reportes(solicitud, pendientes=False):
    reportes = ReporteContenido.objects.all()
    if not puede_administrar(solicitud.usuario, 'permiso_contenido'):
        reportes = reportes.filter(reportado_por=solicitud.usuario.nombreUsuario)
    estado = "pendiente" if pendientes else solicitud.GET.get("estado")
    if estado in ("pendiente", "resuelto", "descartado"):
        reportes = reportes.filter(estado=estado)
    return render(solicitud, "reportes/lista.html", {"reportes": reportes.order_by("-fecha_reporte")})


@sesion_requerida
def detalle_reporte(solicitud, pk):
    if not ObjectId.is_valid(str(pk)):
        raise Http404("Reporte no encontrado")
    reporte = get_object_or_404(ReporteContenido, pk=ObjectId(pk))
    if not puede_administrar(solicitud.usuario, 'permiso_contenido'):
        comprobar_propietario(solicitud, reporte.reportado_por)
    return render(solicitud, "reportes/detalle.html", {"reporte": reporte})


@sesion_requerida
def actualizar_reporte(solicitud, pk):
    if solicitud.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    if not ObjectId.is_valid(str(pk)):
        raise Http404("Reporte no encontrado")
    reporte = get_object_or_404(ReporteContenido, pk=ObjectId(pk))
    if not puede_administrar(solicitud.usuario, 'permiso_contenido'):
        comprobar_propietario(solicitud, reporte.reportado_por)
    if reporte.estado != "pendiente":
        return HttpResponse("Solo se pueden editar reportes pendientes", status=400)
    datos = {
        "contenido": reporte.contenido,
        "tipo_contenido": reporte.tipo_contenido,
        "motivo": reporte.motivo,
    }
    formulario = FormularioReporte(solicitud.POST if solicitud.method == "POST" else None, initial=datos)
    if solicitud.method == "POST" and formulario.is_valid():
        reporte.contenido = formulario.cleaned_data["contenido"]
        reporte.tipo_contenido = formulario.cleaned_data["tipo_contenido"]
        reporte.motivo = formulario.cleaned_data["motivo"]
        reporte.save()
        return redirect("reporte_detalle", pk=str(reporte.pk))
    return render(solicitud, "reportes/formulario.html", {"formulario": formulario, "titulo": "Editar reporte"})


@administrador_requerido
def resolver_reporte(solicitud, pk):
    if solicitud.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    if not ObjectId.is_valid(str(pk)):
        raise Http404("Reporte no encontrado")
    reporte = get_object_or_404(ReporteContenido, pk=ObjectId(pk))
    if reporte.estado != "pendiente":
        return HttpResponse("El reporte ya fue atendido", status=400)
    formulario = FormularioResolucion(solicitud.POST if solicitud.method == "POST" else None)
    if solicitud.method == "POST" and formulario.is_valid():
        datos = formulario.cleaned_data
        if solicitud.usuario.nombreUsuario == reporte.reportado_por:
            formulario.add_error("moderador", "El reportante no puede resolver su propio reporte")
        else:
            fecha = timezone.now()
            accion = AccionAdministrativa.objects.filter(pk=reporte.pk).first()
            if accion is None:
                accion = AccionAdministrativa(_id=reporte.pk)
            accion.administrador = solicitud.usuario.nombreUsuario
            accion.rol_administrador = solicitud.usuario.rol
            accion.accion = "Atender reporte"
            accion.entidad = "reporteContenido"
            accion.detalle_entidad = str(reporte.pk)
            accion.descripcion = datos["accion_tomada"]
            accion.fecha = fecha
            accion.save()
            reporte.estado = datos["estado"]
            reporte.moderador = solicitud.usuario.nombreUsuario
            reporte.accion_tomada = datos["accion_tomada"]
            reporte.fecha_resolucion = fecha
            reporte.save()
            notificar(reporte.reportado_por, 'sistema', 'Tu reporte fue %s.' % ('resuelto' if reporte.estado == 'resuelto' else 'descartado'), origen=solicitud.usuario.nombreUsuario, categoria='avisos', asunto='Actualización de tu reporte', ruta=reverse('reporte_detalle', kwargs={'pk': str(reporte.pk)}), detalle=reporte.accion_tomada, boton='Ver el reporte')
            return redirect("reporte_detalle", pk=str(reporte.pk))
    return render(solicitud, "reportes/formulario.html", {"formulario": formulario, "titulo": "Resolver reporte"})


@sesion_requerida
def eliminar_reporte(solicitud, pk):
    if solicitud.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])
    if not ObjectId.is_valid(str(pk)):
        raise Http404("Reporte no encontrado")
    reporte = get_object_or_404(ReporteContenido, pk=ObjectId(pk))
    if not puede_administrar(solicitud.usuario, 'permiso_contenido'):
        comprobar_propietario(solicitud, reporte.reportado_por)
    if reporte.estado == "pendiente":
        return HttpResponse("Primero se debe resolver o descartar el reporte", status=400)
    if solicitud.method == "POST":
        reporte.delete()
        return redirect("reportes_listar")
    return render(solicitud, "reportes/eliminar.html", {"reporte": reporte})


@administrador_requerido
def consultar_roles(solicitud):
    registros = Rol.objects.all()
    return render(solicitud, 'administracion/roles.html', {'registros': registros, 'titulo': 'Roles'})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def crear_rol(solicitud):
    formulario = FormularioRol(solicitud.POST or None)
    if solicitud.method == 'POST' and formulario.is_valid():
        datos = formulario.cleaned_data
        if Rol.objects.filter(nombre=datos['nombre']).exists():
            formulario.add_error('nombre', 'Este rol ya existe.')
        else:
            Rol.objects.create(**datos)
            return redirect('consultar_roles')
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Crear rol', 'formulario': formulario})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def actualizar_rol(solicitud, pk):
    registro = get_object_or_404(Rol, pk=pk)
    valores = {campo: getattr(registro, campo) for campo in FormularioRol().fields}
    formulario = FormularioRol(solicitud.POST or None, initial=valores)
    formulario.fields['nombre'].disabled = True
    if solicitud.method == 'POST' and formulario.is_valid():
        registro.nombre = formulario.cleaned_data['nombre']
        registro.descripcion = formulario.cleaned_data['descripcion']
        registro.permiso_usuarios = formulario.cleaned_data['permiso_usuarios']
        registro.permiso_contenido = formulario.cleaned_data['permiso_contenido']
        registro.permiso_estadisticas = formulario.cleaned_data['permiso_estadisticas']
        registro.activo = formulario.cleaned_data['activo']
        if registro.nombre == 'administrador':
            registro.activo = True
            registro.permiso_usuarios = True
            registro.permiso_contenido = True
            registro.permiso_estadisticas = True
        registro.save()
        return redirect('consultar_roles')
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Editar rol', 'formulario': formulario})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def eliminar_rol(solicitud, pk):
    registro = get_object_or_404(Rol, pk=pk)
    if registro.nombre in ('administrador', 'artista') or Usuario.objects.filter(rol=registro.nombre).exists():
        raise PermissionDenied('Este rol está en uso o es necesario para el sistema.')
    if solicitud.method == 'POST':
        registro.delete()
        return redirect('consultar_roles')
    return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar rol', 'objeto': registro})

@administrador_requerido
def consultar_acciones(solicitud):
    registros = AccionAdministrativa.objects.all()
    return render(solicitud, 'administracion/acciones.html', {'registros': registros, 'titulo': 'Acciones'})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def crear_accion(solicitud):
    formulario = FormularioAccion(solicitud.POST or None)
    if solicitud.method == 'POST' and formulario.is_valid():
        datos = formulario.cleaned_data
        AccionAdministrativa.objects.create(**datos, administrador=solicitud.usuario.nombreUsuario, rol_administrador=solicitud.usuario.rol, fecha=timezone.now())
        return redirect('consultar_acciones')
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Crear accion', 'formulario': formulario})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def actualizar_accion(solicitud, pk):
    registro = get_object_or_404(AccionAdministrativa, pk=pk)
    valores = {campo: getattr(registro, campo) for campo in FormularioAccion().fields}
    formulario = FormularioAccion(solicitud.POST or None, initial=valores)
    if solicitud.method == 'POST' and formulario.is_valid():
        registro.accion = formulario.cleaned_data['accion']
        registro.entidad = formulario.cleaned_data['entidad']
        registro.detalle_entidad = formulario.cleaned_data['detalle_entidad']
        registro.descripcion = formulario.cleaned_data['descripcion']
        registro.save()
        return redirect('consultar_acciones')
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Editar accion', 'formulario': formulario})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def eliminar_accion(solicitud, pk):
    registro = get_object_or_404(AccionAdministrativa, pk=pk)
    if solicitud.method == 'POST':
        registro.delete()
        return redirect('consultar_acciones')
    return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar accion', 'objeto': registro})

@administrador_requerido
def consultar_controles(solicitud):
    registros = ControlSistema.objects.all()
    return render(solicitud, 'administracion/controles.html', {'registros': registros, 'titulo': 'Controles'})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def crear_control(solicitud):
    valores = {'usuarios_activos': Usuario.objects.filter(activo__in=[True]).count(), 'publicaciones': Publicacion.objects.count(), 'reportes': ReporteContenido.objects.count(), 'fecha': timezone.localdate(), 'estado_respaldo': 'sin_registrar'}
    formulario = FormularioControl(solicitud.POST or None, initial=valores)
    for campo in ('usuarios_activos', 'publicaciones', 'reportes'):
        formulario.fields[campo].disabled = True
    if solicitud.method == 'POST' and formulario.is_valid():
        datos = formulario.cleaned_data
        ControlSistema.objects.create(**datos)
        return redirect('consultar_controles')
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Crear control', 'formulario': formulario})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def actualizar_control(solicitud, pk):
    registro = get_object_or_404(ControlSistema, pk=pk)
    valores = {campo: getattr(registro, campo) for campo in FormularioControl().fields}
    formulario = FormularioControl(solicitud.POST or None, initial=valores)
    for campo in ('usuarios_activos', 'publicaciones', 'reportes'):
        formulario.fields[campo].disabled = True
    if solicitud.method == 'POST' and formulario.is_valid():
        registro.fecha = formulario.cleaned_data['fecha']
        registro.usuarios_activos = formulario.cleaned_data['usuarios_activos']
        registro.publicaciones = formulario.cleaned_data['publicaciones']
        registro.reportes = formulario.cleaned_data['reportes']
        registro.fecha_respaldo = formulario.cleaned_data['fecha_respaldo']
        registro.estado_respaldo = formulario.cleaned_data['estado_respaldo']
        registro.save()
        return redirect('consultar_controles')
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Editar control', 'formulario': formulario})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def eliminar_control(solicitud, pk):
    registro = get_object_or_404(ControlSistema, pk=pk)
    if solicitud.method == 'POST':
        registro.delete()
        return redirect('consultar_controles')
    return render(solicitud, 'comunes/eliminar.html', {'titulo': 'Eliminar control', 'objeto': registro})


@administrador_requerido
@require_http_methods(['GET', 'POST'])
def asignar_rol(solicitud, nombre):
    from django import forms
    usuario = get_object_or_404(Usuario, nombreUsuario=nombre, activo__in=[True])
    class FormularioAsignacion(forms.Form):
        rol = forms.ChoiceField(choices=[(dato.nombre, dato.nombre) for dato in Rol.objects.filter(activo__in=[True])])
    formulario = FormularioAsignacion(solicitud.POST or None, initial={'rol': usuario.rol})
    if solicitud.method == 'POST' and formulario.is_valid():
        if usuario.rol == 'administrador' and formulario.cleaned_data['rol'] != 'administrador' and Usuario.objects.filter(rol='administrador', activo__in=[True]).count() <= 1:
            formulario.add_error('rol', 'Debe conservarse al menos un administrador.')
        else:
            usuario.rol = formulario.cleaned_data['rol']
            usuario.save()
            return redirect('perfil_detalle', nombre=nombre)
    return render(solicitud, 'comunes/formulario.html', {'titulo': 'Asignar rol a ' + nombre, 'formulario': formulario})
