import json
from datetime import timedelta
from getpass import getpass
from urllib.parse import urlsplit
from bson import ObjectId
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from g_usuarios_perfiles.models import Usuario, Notificacion
from g_usuarios_perfiles.acceso import resumen_usuario
from publicacion_org_contenido.models import Categoria, Publicacion, Coleccion, Recomendacion
from int_social_comunidad.models import Mensaje, Grupo, Moderacion
from exploracion_inspiracion.models import ExploracionInspiracion
from admin_contrl_sys.models import Rol, ReporteContenido, AccionAdministrativa, ControlSistema
from photobook.consultas import documentos


class Command(BaseCommand):
    help = 'Carga fotografías y datos relacionados sin reemplazar los registros existentes.'

    def add_arguments(self, argumentos):
        argumentos.add_argument('--direccion', default='http://127.0.0.1:8000')

    def handle(self, *argumentos, **opciones):
        direccion = opciones['direccion'].rstrip('/')
        try:
            URLValidator(schemes=['http', 'https'])(direccion)
        except ValidationError:
            raise CommandError('Indica una dirección como http://127.0.0.1:8000.')
        partes = urlsplit(direccion)
        if partes.path or partes.query or partes.fragment or partes.username or partes.password:
            raise CommandError('La dirección debe contener solamente el protocolo, el servidor y el puerto.')
        administrador = Usuario.objects.filter(rol='administrador', activo__in=[True]).first()
        if administrador is None:
            raise CommandError('Primero ejecuta python manage.py crear_administrador.')
        carpeta = settings.BASE_DIR / 'estaticos' / 'ejemplos'
        imagenes = json.loads((settings.BASE_DIR / 'base_datos' / 'imagenes_ejemplo.json').read_text(encoding='utf-8'))
        for imagen in imagenes:
            archivo = carpeta / imagen['archivo']
            if not archivo.is_file() or archivo.stat().st_size != imagen['bytes']:
                raise CommandError('Falta una fotografía o está incompleta: ' + imagen['archivo'])
        nombres = ['ana_demo', 'luis_demo', 'maria_demo', 'carlos_demo']
        existentes = {nombre: Usuario.objects.filter(nombreUsuario=nombre).first() for nombre in nombres}
        for nombre, usuario in existentes.items():
            correo = nombre + '@example.org'
            if usuario and (usuario.correo != correo or not usuario.activo):
                raise CommandError('La cuenta ' + nombre + ' está ocupada o inactiva. No se modificó.')
            if usuario is None and Usuario.objects.filter(correo=correo).exists():
                raise CommandError('El correo de ejemplo ya pertenece a otra cuenta: ' + correo)
        nuevos = [nombre for nombre in nombres if existentes[nombre] is None]
        contrasena = None
        if nuevos:
            contrasena = getpass('Contraseña para las cuentas nuevas de ejemplo: ')
            if not 8 <= len(contrasena) <= 128:
                raise CommandError('La contraseña debe tener entre 8 y 128 caracteres.')
        fecha = timezone.now()
        usuarios = {}
        for numero, nombre in enumerate(nombres):
            usuario = existentes[nombre]
            if usuario is None:
                usuario = Usuario.objects.create(
                    nombreUsuario=nombre, correo=nombre + '@example.org',
                    contrasena=make_password(contrasena), rol='artista',
                    imagenPerfil=direccion + '/static/ejemplos/' + imagenes[numero]['archivo'],
                    biografia='Cuenta de demostración para compartir fotografías e ideas.',
                    privacidad={'perfilPublico': True, 'correoVisible': False},
                )
            usuarios[nombre] = usuario
        if len(nuevos) > 1:
            for numero, nombre in enumerate(nuevos):
                usuario = usuarios[nombre]
                usuario.siguiendo = [{'usuario': nuevos[(numero + 1) % len(nuevos)], 'inicioSeg': fecha}]
                usuario.seguidores = [{'usuario': nuevos[(numero - 1) % len(nuevos)], 'inicioSeg': fecha}]
                usuario.save()
        for nombre in ['artista', 'administrador']:
            if not Rol.objects.filter(nombre=nombre).exists():
                permiso = nombre == 'administrador'
                Rol.objects.create(nombre=nombre, descripcion='Rol de ' + nombre, permiso_usuarios=permiso, permiso_contenido=permiso, permiso_estadisticas=permiso)
        categorias = {}
        for nombre, ruta, descripcion in [
            ('Naturaleza', 'naturaleza', 'Paisajes, lagos y montañas.'),
            ('Viajes', 'viajes', 'Destinos para descubrir.'),
            ('Ciudad', 'ciudad', 'Arquitectura y espacios urbanos.'),
            ('Gastronomía', 'gastronomia', 'Comida, bebidas y detalles cotidianos.'),
            ('Flores', 'flores', 'Colores y pequeños detalles de la naturaleza.'),
        ]:
            categoria = Categoria.objects.filter(slug=ruta).first()
            if categoria is None:
                categoria = Categoria.objects.filter(nombre=nombre).first()
            if categoria is None:
                categoria = Categoria.objects.create(nombre=nombre, slug=ruta, descripcion=descripcion)
            categorias[ruta] = categoria
        publicaciones = []
        for numero, imagen in enumerate(imagenes):
            enlace = direccion + '/static/ejemplos/' + imagen['archivo']
            publicacion = Publicacion.objects.filter(pk=ObjectId(imagen['identificador'])).first()
            if publicacion is None:
                publicacion = Publicacion.objects.filter(archivoUrl=enlace).first()
            if publicacion is None:
                autor = usuarios[imagen['usuario']]
                categoria = categorias[imagen['categoria']]
                comentarista = usuarios[nombres[(nombres.index(imagen['usuario']) + 1) % len(nombres)]]
                comentario = {
                    'autor': resumen_usuario(comentarista),
                    'contenido': 'Me gusta cómo se ve la luz y el color en esta fotografía.',
                    'formato': 'texto', 'menciones': [], 'archivosAdjuntos': [], 'respuestas': [],
                    'estado': 'activo', 'conteoReacciones': {'meGusta': 0, 'amor': 0, 'aplauso': 0, 'sorpresa': 0, 'triste': 0, 'risa': 0},
                    'fechaCreacion': fecha - timedelta(days=1), 'fechaEdicion': None,
                }
                reacciones = [
                    {'usuario': resumen_usuario(usuario), 'tipoReaccion': 'meGusta' if posicion % 2 == 0 else 'aplauso', 'fecha': fecha - timedelta(hours=2)}
                    for posicion, usuario in enumerate(usuarios.values()) if usuario.nombreUsuario != autor.nombreUsuario
                ]
                publicacion = Publicacion.objects.create(
                    _id=ObjectId(imagen['identificador']), autor=resumen_usuario(autor), tipo='imagen',
                    titulo=imagen['titulo'], descripcion='Publicación de demostración. Fotografía: ' + imagen['fotografo'] + '. Licencia CC0 1.0. Fuente: ' + imagen['fuente'],
                    archivoUrl=enlace, formato='jpg', tamanioBytes=imagen['bytes'], ancho=imagen['ancho'], alto=imagen['alto'],
                    etiquetas=imagen['etiquetas'], categorias=[{'nombre': categoria.nombre, 'slug': categoria.slug}],
                    comentarios=[comentario], totalComentarios=1, reacciones=reacciones, totalReacciones=len(reacciones),
                    fechaPublicacion=fecha - timedelta(days=numero + 2),
                )
                categoria.totalPublicaciones += 1
                categoria.save()
            publicaciones.append(publicacion)
        for nombre, propietario, posiciones, tipo, privacidad in [
            ('Paisajes para recordar', 'ana_demo', [0, 2, 3], 'personal', 'publica'),
            ('Próximos destinos', 'luis_demo', [1, 5, 6], 'colaborativa', 'publica'),
            ('Colores y detalles', 'maria_demo', [4, 7], 'personal', 'publica'),
            ('Nuestro cuaderno privado', 'carlos_demo', [3, 5, 7], 'colaborativa', 'privada'),
        ]:
            if not documentos(Coleccion, {'creador.nombreUsuario': propietario, 'nombre': nombre}).exists():
                seleccion = [publicaciones[posicion] for posicion in posiciones]
                Coleccion.objects.create(
                    nombre=nombre, descripcion='Colección de ejemplo para organizar y compartir imágenes.',
                    creador=resumen_usuario(usuarios[propietario]), tipo=tipo, privacidad=privacidad, portadaUrl=seleccion[0].archivoUrl,
                    publicaciones=[{'orden': numero + 1, 'titulo': dato.titulo, 'tipo': dato.tipo, 'archivoUrl': dato.archivoUrl} for numero, dato in enumerate(seleccion)],
                    colaboradores=[resumen_usuario(usuarios[nombre_usuario]) for nombre_usuario in nombres if nombre_usuario != propietario] if tipo == 'colaborativa' else [],
                )
        for numero, (nombre, ruta, propietario) in enumerate([
            ('Paisajes de la comunidad', 'naturaleza', 'ana_demo'),
            ('Rutas y destinos', 'viajes', 'luis_demo'),
            ('Miradas cotidianas', 'ciudad', 'maria_demo'),
        ]):
            if not Grupo.objects.filter(nombre=nombre).exists():
                categoria = categorias[ruta]
                Grupo.objects.create(
                    nombre=nombre, descripcion='Grupo de demostración para compartir experiencias y fotografías.', tipo='publico',
                    imagenUrl=publicaciones[numero].archivoUrl, creador=resumen_usuario(usuarios[propietario]),
                    categoria={'nombre': categoria.nombre, 'slug': categoria.slug},
                    miembros=[{**resumen_usuario(usuario), 'rol': 'administrador' if usuario.nombreUsuario == propietario else 'miembro', 'fechaIngreso': fecha - timedelta(days=3)} for usuario in usuarios.values()],
                    totalMiembros=len(usuarios), reglas=['Respeta a los demás integrantes.', 'Comparte contenido relacionado con el grupo.'],
                    foros=[{'nombre': 'Presentaciones', 'descripcion': 'Cuéntanos qué te gusta fotografiar.', 'comentarios': [], 'fechaCreacion': fecha}, {'nombre': 'Ideas para la próxima salida', 'descripcion': 'Propón un destino o un tema para fotografiar.', 'comentarios': [], 'fechaCreacion': fecha}],
                )
        for numero, (emisor, receptor, contenido) in enumerate([
            ('ana_demo', 'luis_demo', '¿Organizamos una salida para fotografiar paisajes?'),
            ('luis_demo', 'ana_demo', 'Sí, podemos revisar los destinos de la colección compartida.'),
            ('maria_demo', 'carlos_demo', 'Me gustó la fotografía de la ciudad junto al mar.'),
            ('carlos_demo', 'maria_demo', 'Gracias. Podemos buscar detalles de arquitectura en la próxima salida.'),
            ('ana_demo', 'maria_demo', 'Agregué nuevas imágenes a la colección de paisajes.'),
            ('maria_demo', 'ana_demo', 'Ya las vi. Los colores de las montañas son muy bonitos.'),
            ('luis_demo', 'carlos_demo', '¿Qué te parece compartir ideas en el foro de viajes?'),
            ('carlos_demo', 'luis_demo', 'Voy a preparar algunas propuestas para el grupo.'),
        ]):
            if not documentos(Mensaje, {'emisor.nombreUsuario': emisor, 'receptor.nombreUsuario': receptor, 'contenido': contenido}).exists():
                Mensaje.objects.create(emisor=resumen_usuario(usuarios[emisor]), receptor=resumen_usuario(usuarios[receptor]), contenido=contenido, leido=numero % 2 == 0, fechaLectura=fecha - timedelta(hours=3) if numero % 2 == 0 else None, fechaEnvio=fecha - timedelta(days=1, minutes=numero))
        for numero, nombre in enumerate(nombres):
            for tipo, texto in [('sistema', 'Tu cuenta de ejemplo está lista para explorar Photobook.'), ('mensaje', 'Tienes conversaciones de ejemplo en la sección de mensajes.')]:
                if not Notificacion.objects.filter(usuarioNotificado=nombre, mensaje=texto).exists():
                    Notificacion.objects.create(usuarioNotificado=nombre, usuarioOrigen=nombres[(numero + 1) % len(nombres)], tipo=tipo, mensaje=texto)
            perfil = documentos(ExploracionInspiracion, {'usuario.nombreUsuario': nombre}).first()
            if perfil is None:
                ruta = ['naturaleza', 'viajes', 'flores', 'ciudad'][numero]
                perfil = ExploracionInspiracion.objects.create(usuario=resumen_usuario(usuarios[nombre]), preferencias={'categorias': [categorias[ruta].slug], 'etiquetas': ['naturaleza', 'viaje'], 'artistas': [nombres[(numero + 1) % len(nombres)]]})
            preferencias = perfil.preferencias
            for publicacion in publicaciones:
                if publicacion.autor['nombreUsuario'] == nombre or publicacion.estado != 'publicado':
                    continue
                factores = []
                if any(dato['slug'] in preferencias['categorias'] for dato in publicacion.categorias):
                    factores.append({'nombre': 'Categorías preferidas', 'peso': 1.0 / 3})
                if set(publicacion.etiquetas) & set(preferencias['etiquetas']):
                    factores.append({'nombre': 'Etiquetas preferidas', 'peso': 1.0 / 3})
                if publicacion.autor['nombreUsuario'] in preferencias['artistas']:
                    factores.append({'nombre': 'Artista preferido', 'peso': 1.0 / 3})
                if factores and not documentos(Recomendacion, {'usuario.nombreUsuario': nombre, 'publicacion.archivoUrl': publicacion.archivoUrl, 'criterio': 'preferencias'}).exists():
                    Recomendacion.objects.create(usuario=resumen_usuario(usuarios[nombre]), publicacion={'titulo': publicacion.titulo, 'tipo': publicacion.tipo, 'archivoUrl': publicacion.archivoUrl}, criterio='preferencias', puntuacion=len(factores) / 3, factores=factores)
        if not documentos(Moderacion, {'bloqueador.nombreUsuario': 'ana_demo', 'bloqueado.nombreUsuario': 'luis_demo', 'ambito': 'mensajes'}).exists():
            Moderacion.objects.create(bloqueador=resumen_usuario(usuarios['ana_demo']), bloqueado=resumen_usuario(usuarios['luis_demo']), ambito='mensajes', fechaExpiracion=fecha - timedelta(days=1))
        for numero in [0, 4]:
            motivo = 'Reporte de demostración: revisar la información y los créditos de la fotografía.'
            if not ReporteContenido.objects.filter(contenido=publicaciones[numero].archivoUrl, motivo=motivo).exists():
                ReporteContenido.objects.create(contenido=publicaciones[numero].archivoUrl, tipo_contenido='publicacion', motivo=motivo, reportado_por='luis_demo')
        if not AccionAdministrativa.objects.filter(accion='Carga de fotografías de ejemplo').exists():
            AccionAdministrativa.objects.create(administrador=administrador.nombreUsuario, rol_administrador=administrador.rol, accion='Carga de fotografías de ejemplo', entidad='Proyecto', detalle_entidad='Ocho fotografías y cuatro cuentas de demostración', descripcion='Se cargaron datos relacionados para recorrer las aplicaciones.', fecha=fecha)
        if not ControlSistema.objects.filter(fecha=timezone.localdate(), estado_respaldo='sin_registrar').exists():
            ControlSistema.objects.create(fecha=timezone.localdate(), usuarios_activos=Usuario.objects.filter(activo__in=[True]).count(), publicaciones=Publicacion.objects.count(), reportes=ReporteContenido.objects.count(), estado_respaldo='sin_registrar')
        self.stdout.write('Carga terminada. No se borraron ni reemplazaron los registros existentes.')
        self.stdout.write('Cuentas de ejemplo: ' + ', '.join(nombres))
        self.stdout.write('Las cuentas nuevas usan la contraseña que acabas de escribir; las anteriores conservan la suya.')
        self.stdout.write('Abre ' + direccion + ' para ver las fotografías.')
