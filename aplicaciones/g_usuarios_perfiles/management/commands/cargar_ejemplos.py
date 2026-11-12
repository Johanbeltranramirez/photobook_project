from getpass import getpass
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from aplicaciones.g_usuarios_perfiles.models import Usuario, Notificacion
from aplicaciones.g_usuarios_perfiles.acceso import resumen_usuario
from aplicaciones.publicacion_org_contenido.models import Categoria, Publicacion, Coleccion
from aplicaciones.int_social_comunidad.models import Mensaje, Grupo, Moderacion
from aplicaciones.exploracion_inspiracion.models import ExploracionInspiracion
from aplicaciones.exploracion_inspiracion.views import actualizar_recomendaciones
from aplicaciones.admin_contrl_sys.models import ReporteContenido, AccionAdministrativa, ControlSistema
from photobook.utilidades.consultas import documentos

class Command(BaseCommand):
    help = 'Inserta ejemplos sin borrar ni reemplazar los registros existentes.'

    def handle(self, *argumentos, **opciones):
        administrador = Usuario.objects.filter(rol='administrador', activo__in=[True]).first()
        if administrador is None:
            raise CommandError('Primero ejecuta crear_administrador.')
        contrasena = getpass('Contraseña para las cuentas nuevas ana_demo y luis_demo: ')
        if len(contrasena) < 8:
            raise CommandError('La contraseña debe tener al menos ocho caracteres.')
        usuarios = []
        for nombre in ['ana_demo', 'luis_demo']:
            usuario = Usuario.objects.filter(nombreUsuario=nombre).first()
            if usuario is None:
                usuario = Usuario.objects.create(nombreUsuario=nombre, correo=nombre + '@example.org', contrasena=make_password(contrasena), rol='artista', privacidad={'perfilPublico': True, 'correoVisible': False})
            usuarios.append(usuario)
        ana, luis = usuarios
        categoria = Categoria.objects.filter(slug='naturaleza').first()
        if categoria is None:
            categoria = Categoria.objects.create(nombre='Naturaleza', slug='naturaleza', descripcion='Paisajes y fotografía al aire libre')
        publicacion = Publicacion.objects.filter(archivoUrl='http://127.0.0.1:8000/static/paisaje.png').first()
        if publicacion is None:
            publicacion = Publicacion.objects.create(autor=resumen_usuario(ana), tipo='imagen', titulo='Un lugar para inspirarse', descripcion='Publicación de ejemplo para recorrer el proyecto.', archivoUrl='http://127.0.0.1:8000/static/paisaje.png', formato='png', tamanioBytes=9922, ancho=1000, alto=700, etiquetas=['naturaleza', 'paisaje'], categorias=[{'nombre': categoria.nombre, 'slug': categoria.slug}])
            categoria.totalPublicaciones += 1
            categoria.save()
        if not documentos(Coleccion, {'creador.nombreUsuario': ana.nombreUsuario, 'nombre': 'Mis paisajes'}).exists():
            Coleccion.objects.create(creador=resumen_usuario(ana), nombre='Mis paisajes', descripcion='Colección de ejemplo', tipo='colaborativa', privacidad='publica', publicaciones=[{'orden': 1, 'titulo': publicacion.titulo, 'tipo': publicacion.tipo, 'archivoUrl': publicacion.archivoUrl}], colaboradores=[resumen_usuario(luis)])
        if not Grupo.objects.filter(nombre='Fotografía de naturaleza').exists():
            Grupo.objects.create(nombre='Fotografía de naturaleza', descripcion='Un grupo para compartir ideas.', creador=resumen_usuario(ana), categoria={'nombre': categoria.nombre, 'slug': categoria.slug}, miembros=[{**resumen_usuario(ana), 'rol': 'administrador', 'fechaIngreso': timezone.now()}, {**resumen_usuario(luis), 'rol': 'miembro', 'fechaIngreso': timezone.now()}], totalMiembros=2, reglas=['Respeta a los demás integrantes.'], foros=[{'nombre': 'Presentaciones', 'descripcion': 'Cuéntanos qué te gusta fotografiar.', 'comentarios': [], 'fechaCreacion': timezone.now()}])
        if not documentos(Mensaje, {'emisor.nombreUsuario': ana.nombreUsuario, 'receptor.nombreUsuario': luis.nombreUsuario, 'contenido': 'Bienvenido a Photobook.'}).exists():
            Mensaje.objects.create(emisor=resumen_usuario(ana), receptor=resumen_usuario(luis), contenido='Bienvenido a Photobook.')
        perfil = documentos(ExploracionInspiracion, {'usuario.nombreUsuario': luis.nombreUsuario}).first()
        if perfil is None:
            perfil = ExploracionInspiracion.objects.create(usuario=resumen_usuario(luis), preferencias={'categorias': [categoria.slug], 'etiquetas': ['paisaje'], 'artistas': [ana.nombreUsuario]})
            actualizar_recomendaciones(luis, perfil)
        if not Notificacion.objects.filter(usuarioNotificado=luis.nombreUsuario, mensaje='Bienvenido a Photobook.').exists():
            Notificacion.objects.create(usuarioNotificado=luis.nombreUsuario, usuarioOrigen=ana.nombreUsuario, tipo='sistema', mensaje='Bienvenido a Photobook.')
        if not documentos(Moderacion, {'bloqueador.nombreUsuario': ana.nombreUsuario, 'bloqueado.nombreUsuario': luis.nombreUsuario, 'ambito': 'mensajes'}).exists():
            Moderacion.objects.create(bloqueador=resumen_usuario(ana), bloqueado=resumen_usuario(luis), ambito='mensajes', fechaExpiracion=timezone.now() - timezone.timedelta(days=1))
        if not ReporteContenido.objects.filter(contenido=publicacion.archivoUrl, motivo='Reporte de ejemplo para revisar desde administración.').exists():
            ReporteContenido.objects.create(contenido=publicacion.archivoUrl, tipo_contenido='publicacion', motivo='Reporte de ejemplo para revisar desde administración.', reportado_por=luis.nombreUsuario)
        if not AccionAdministrativa.objects.filter(accion='Carga de ejemplos').exists():
            AccionAdministrativa.objects.create(administrador=administrador.nombreUsuario, rol_administrador=administrador.rol, accion='Carga de ejemplos', entidad='Proyecto', detalle_entidad='Datos de demostración', descripcion='Se cargaron ejemplos para recorrer los módulos.', fecha=timezone.now())
        if not ControlSistema.objects.filter(estado_respaldo='sin_registrar').exists():
            ControlSistema.objects.create(fecha=timezone.localdate(), usuarios_activos=Usuario.objects.filter(activo__in=[True]).count(), publicaciones=Publicacion.objects.count(), reportes=ReporteContenido.objects.count(), fecha_respaldo=None, estado_respaldo='sin_registrar')
        self.stdout.write('Ejemplos preparados. Puedes ingresar con ana_demo o luis_demo.')
