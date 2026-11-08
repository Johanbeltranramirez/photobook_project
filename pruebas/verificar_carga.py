import hashlib
import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

carpeta = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(carpeta))
os.environ['DJANGO_SETTINGS_MODULE'] = 'photobook.settings'

import mongomock
import djongo.database

cliente = mongomock.MongoClient()
djongo.database.MongoClient = lambda *argumentos, **opciones: cliente

import django
django.setup()

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.staticfiles.views import serve
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory
from g_usuarios_perfiles.models import Usuario

base = cliente[settings.DATABASES['default']['NAME']]
resultados = []
contrasena = 'ClavePrueba963!'
entrada = 'g_usuarios_perfiles.management.commands.cargar_ejemplos.getpass'


def comprobar(condicion, nombre):
    assert condicion, nombre
    resultados.append(nombre)


def cargar(**opciones):
    call_command('cargar_ejemplos', stdout=StringIO(), **opciones)


def contenido():
    return {nombre: list(base[nombre].find().sort('_id')) for nombre in sorted(base.list_collection_names())}


def rechazar(nombre, **opciones):
    anterior = contenido()
    try:
        cargar(**opciones)
    except CommandError:
        comprobar(contenido() == anterior, nombre)
    else:
        raise AssertionError(nombre)


indices = json.loads((carpeta / 'base_datos' / 'indices.json').read_text(encoding='utf-8'))
for nombre, campos in indices.items():
    for claves in campos:
        base[nombre].create_index([(clave, 1) for clave in claves], unique=True)

rechazar('No inserta datos sin administrador')
Usuario.objects.create(nombreUsuario='administrador', correo='admin@example.org', contrasena=make_password(contrasena), rol='administrador', privacidad={'perfilPublico': True, 'correoVisible': False})
rechazar('Rechaza una dirección sin protocolo', direccion='127.0.0.1:8000')
rechazar('Rechaza una dirección con ruta', direccion='http://127.0.0.1:8000/fotos')
with patch(entrada, return_value='corta'):
    rechazar('Rechaza contraseñas cortas antes de insertar')
with patch('pathlib.Path.is_file', return_value=False):
    rechazar('No inserta datos si falta una fotografía')

with patch(entrada, return_value=contrasena) as pregunta:
    cargar()
comprobar(pregunta.call_count == 1, 'Solicita una sola contraseña para las cuentas nuevas')

cantidades = {
    'usuarios': 5, 'publicaciones': 8, 'categorias': 5, 'colecciones': 4,
    'grupos': 3, 'mensajes': 8, 'notificaciones': 8, 'exploracion': 4,
    'moderacion': 1, 'reporteContenido': 2, 'roles': 2,
    'accionesAdministrativas': 1, 'controlSistema': 1,
}
for nombre, cantidad in cantidades.items():
    comprobar(base[nombre].count_documents({}) == cantidad, 'Cantidad de ' + nombre)
comprobar(base.recomendaciones.count_documents({}) > 0, 'Hay recomendaciones personales')

for nombre in ['ana_demo', 'luis_demo', 'maria_demo', 'carlos_demo']:
    usuario = Usuario.objects.get(nombreUsuario=nombre)
    comprobar(check_password(contrasena, usuario.contrasena), 'Contraseña cifrada de ' + nombre)
    comprobar(usuario.contrasena != contrasena, 'No guarda la contraseña en texto plano de ' + nombre)

imagenes = json.loads((carpeta / 'base_datos' / 'imagenes_ejemplo.json').read_text(encoding='utf-8'))
solicitudes = RequestFactory()
for imagen in imagenes:
    ruta = 'ejemplos/' + imagen['archivo']
    respuesta = serve(solicitudes.get('/static/' + ruta), ruta)
    datos = b''.join(respuesta.streaming_content)
    respuesta.close()
    comprobar(respuesta.status_code == 200 and respuesta['Content-Type'] == 'image/jpeg', 'Sirve ' + imagen['archivo'])
    comprobar(len(datos) == imagen['bytes'] and hashlib.sha256(datos).hexdigest() == imagen['sha256'], 'Fotografía completa ' + imagen['archivo'])
    publicacion = base.publicaciones.find_one({'archivoUrl': 'http://127.0.0.1:8000/static/' + ruta})
    comprobar(publicacion is not None and publicacion['titulo'] == imagen['titulo'], 'Publicación enlazada con ' + imagen['archivo'])
    comprobar(len(publicacion['comentarios']) == 1 and len(publicacion['reacciones']) == 3, 'Comentarios y reacciones de ' + imagen['archivo'])

anterior = contenido()
with patch(entrada, side_effect=AssertionError('No debe volver a pedir la contraseña')):
    cargar()
comprobar(contenido() == anterior, 'Repetir la carga conserva todos los documentos')

base.usuarios.update_one({'nombreUsuario': 'ana_demo'}, {'$set': {'biografia': 'Mi biografía personal', 'contrasena': make_password('NuevaClave963!')}})
base.exploracion.update_one({'usuario.nombreUsuario': 'ana_demo'}, {'$set': {'preferencias': {'categorias': [], 'etiquetas': [], 'artistas': []}}})
anterior = contenido()
with patch(entrada, side_effect=AssertionError('No debe cambiar las contraseñas')):
    cargar()
comprobar(contenido() == anterior, 'Conserva la biografía, la contraseña y las preferencias editadas')

base.usuarios.update_one({'nombreUsuario': 'ana_demo'}, {'$set': {'correo': 'otra_persona@example.org'}})
rechazar('Se detiene si una cuenta de ejemplo corresponde a otro correo')

print('APROBADAS', len(resultados), 'comprobaciones de la carga de datos')
