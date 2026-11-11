from getpass import getpass
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from g_usuarios_perfiles.forms import FormularioRegistro
from g_usuarios_perfiles.models import Usuario
from admin_contrl_sys.models import Rol

class Command(BaseCommand):
    help = 'Crea una cuenta administradora desde la terminal.'

    def handle(self, *argumentos, **opciones):
        nombre = input('Nombre de usuario: ').strip()
        correo = input('Correo: ').strip()
        contrasena = getpass('Contraseña: ')
        confirmacion = getpass('Confirmar contraseña: ')
        formulario = FormularioRegistro({'nombreUsuario': nombre, 'correo': correo, 'contrasena': contrasena, 'confirmacion': confirmacion})
        if not formulario.is_valid():
            raise CommandError(str(formulario.errors.as_text()))
        for nombre_rol in ['administrador', 'artista']:
            if not Rol.objects.filter(nombre=nombre_rol).exists():
                administrador = nombre_rol == 'administrador'
                Rol.objects.create(nombre=nombre_rol, descripcion='Rol de ' + nombre_rol, permiso_usuarios=administrador, permiso_contenido=administrador, permiso_estadisticas=administrador)
        datos = formulario.cleaned_data
        Usuario.objects.create(nombreUsuario=datos['nombreUsuario'], correo=datos['correo'], contrasena=make_password(contrasena), rol='administrador', privacidad={'perfilPublico': True, 'correoVisible': False})
        self.stdout.write('Administrador creado.')
