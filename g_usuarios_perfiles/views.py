from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
from .models import Usuario
from .arrays import PATRON_URL, PATRON_CORREO, ROLES_USUARIO



def usuarios_listar(request):
    texto = request.GET.get('q')
    rol = request.GET.get('rol')
    orden = request.GET.get('orden')
    sentido = '-creacionCuenta' if orden == 'recientes' else 'nombreUsuario'
    condicion = Q()
    if texto:
        condicion &= Q(nombreUsuario__contains=texto) | Q(biografia__contains=texto)
    if rol in ROLES_USUARIO:
        condicion &= Q(rol=rol)
    usuarios = Usuario.objects.filter(condicion).order_by(sentido)
    data = {'usuarios': usuarios[:50], 'total': usuarios.count()}
    return render(request, 'usuarios_lista.html', {'data': data})


def usuario_detalle(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    return render(request, 'usuario_detalle.html', {'data': {'usuario': usuario}})


def usuario_crear(request):
    contexto = {'accion': 'crear'}
    if request.method == 'GET':
        return render(request, 'usuario_form.html', {'data': contexto})
    errores = []
    datos = {
        'nombreUsuario': request.POST.get('nombreUsuario', '').strip(),
        'correo': request.POST.get('correo', '').strip().lower(),
        'contrasena': request.POST.get('contrasena', ''),
        'imagenPerfil': request.POST.get('imagenPerfil') or None,
        'biografia': request.POST.get('biografia') or None,
        'rol': request.POST.get('rol') or 'artista',
    }
   
    if not 3 <= len(datos['nombreUsuario']) <= 30:
        errores.append('El nombre de usuario debe tener entre 3 y 30 caracteres.')
    if Usuario.objects.filter(nombreUsuario=datos['nombreUsuario']).exists():
        errores.append('Ya existe un usuario con ese nombre.')
    if not datos['correo'] or not PATRON_CORREO.match(datos['correo']):
        errores.append('El correo no es válido.')
    if Usuario.objects.filter(correo=datos['correo']).exists():
        errores.append('Ya existe un usuario con ese correo.')
    if not 6 <= len(datos['contrasena']) <= 255:
        errores.append('La contraseña debe tener entre 6 y 255 caracteres.')
    if datos['imagenPerfil'] and not PATRON_URL.match(datos['imagenPerfil']):
        errores.append('La imagen de perfil debe ser un link válido.')
    if datos['biografia'] and len(datos['biografia']) > 255:
        errores.append('La biografía admite máximo 255 caracteres.')
    if datos['rol'] not in ROLES_USUARIO:
        errores.append('El rol debe ser artista o administrador.')
    if not errores:
        
        usuario = Usuario(**datos)
        try:
            usuario.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(request, 'usuario_form.html', {'data': contexto})
    usuario.save()
    return redirect('usuario_detalle', pk=usuario.pk)


def usuario_actualizar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    contexto = {'accion': 'actualizar', 'usuario': usuario}
    if request.method == 'GET':
        return render(request, 'usuario_form.html', {'data': contexto})
    errores = []
    datos = {
        'nombreUsuario': request.POST.get('nombreUsuario', '').strip(),
        'correo': request.POST.get('correo', '').strip().lower(),
        'imagenPerfil': request.POST.get('imagenPerfil') or None,
        'biografia': request.POST.get('biografia') or None,
        'rol': request.POST.get('rol') or 'artista',
    }
    contrasena = request.POST.get('contrasena', '')
    
    if not 3 <= len(datos['nombreUsuario']) <= 30:
        errores.append('El nombre de usuario debe tener entre 3 y 30 caracteres.')
    if Usuario.objects.filter(nombreUsuario=datos['nombreUsuario']).exclude(pk=usuario.pk).exists():
        errores.append('Ya existe otro usuario con ese nombre.')
    if not datos['correo'] or not PATRON_CORREO.match(datos['correo']):
        errores.append('El correo no es válido.')
    if Usuario.objects.filter(correo=datos['correo']).exclude(pk=usuario.pk).exists():
        errores.append('Ya existe otro usuario con ese correo.')
    if contrasena and not 6 <= len(contrasena) <= 255:
        errores.append('La contraseña debe tener entre 6 y 255 caracteres.')
    if datos['imagenPerfil'] and not PATRON_URL.match(datos['imagenPerfil']):
        errores.append('La imagen de perfil debe ser un link válido.')
    if datos['biografia'] and len(datos['biografia']) > 255:
        errores.append('La biografía admite máximo 255 caracteres.')
    if datos['rol'] not in ROLES_USUARIO:
        errores.append('El rol debe ser artista o administrador.')
    if not errores:
        for campo, valor in datos.items():
            setattr(usuario, campo, valor)
        if contrasena:
            usuario.contrasena = contrasena  
        try:
            usuario.full_clean(validate_unique=False)
        except ValidationError as excepcion:
            errores = excepcion.messages
    if errores:
        contexto['errores'] = errores
        return render(request, 'usuario_form.html', {'data': contexto})
    usuario.save()
    return redirect('usuario_detalle', pk=usuario.pk)


def usuario_eliminar(_request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.delete()
    return redirect('usuarios_listar')


def usuario_seguir(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    errores = []
    seguidor_nombre = request.POST.get('seguidor', '')
    if not 3 <= len(seguidor_nombre) <= 30:
        errores.append('El seguidor debe tener un nombre de 3 a 30 caracteres.')
    if seguidor_nombre == usuario.nombreUsuario:
        errores.append('No puedes seguirte a ti mismo.')
    if any(s.usuario == seguidor_nombre for s in usuario.seguidores.all()):
        errores.append('Ya sigues a este usuario.')
    if errores:
        return render(request, 'usuario_detalle.html', {'data': {'usuario': usuario, 'errores': errores}}, status=400)
    
    usuario.seguidores.create(usuario=seguidor_nombre, inicioSeg=timezone.now())
    
    seguidor = Usuario.objects.filter(nombreUsuario=seguidor_nombre).first()
    if seguidor:
        seguidor.siguiendo.create(usuario=usuario.nombreUsuario, inicioSeg=timezone.now())
        seguidor.save()
    usuario.save()
    return redirect('usuario_detalle', pk=usuario.pk)


def usuario_dejar_seguir(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    seguidor_nombre = request.POST.get('seguidor', '')
    seguidor_rel = usuario.seguidores.filter(usuario=seguidor_nombre).first()
    if seguidor_rel is None:
        errores = ['No sigues a este usuario.']
        return render(request, 'usuario_detalle.html', {'data': {'usuario': usuario, 'errores': errores}}, status=400)
    seguidor_rel.delete()
    seguidor = Usuario.objects.filter(nombreUsuario=seguidor_nombre).first()
    if seguidor:
        siguiendo_rel = seguidor.siguiendo.filter(usuario=usuario.nombreUsuario).first()
        if siguiendo_rel:
            siguiendo_rel.delete()
        seguidor.save()
    usuario.save()
    return redirect('usuario_detalle', pk=usuario.pk)