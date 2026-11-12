import mimetypes
import re
import struct
import uuid
from pathlib import Path
from urllib.parse import urlparse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.urls import reverse
from .opciones import EXTENSIONES_IMAGEN, EXTENSIONES_VIDEO, TAMANIO_MAXIMO_IMAGEN, TAMANIO_MAXIMO_VIDEO

PATRON_NOMBRE_ARCHIVO = re.compile(r'^[0-9a-f]{32}\.[a-z0-9]{3,4}$')
PATRON_RANGO = re.compile(r'^bytes=(\d*)-(\d*)$')


def carpeta_archivos():
    carpeta = Path(settings.CARPETA_ARCHIVOS_SUBIDOS)
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def firma_valida(extension, cabecera):
    if extension in ('jpg', 'jpeg'):
        return cabecera[:3] == b'\xff\xd8\xff'
    if extension == 'png':
        return cabecera[:8] == b'\x89PNG\r\n\x1a\n'
    if extension == 'gif':
        return cabecera[:6] in (b'GIF87a', b'GIF89a')
    if extension in ('mp4', 'mov'):
        return cabecera[4:8] in (b'ftyp', b'moov', b'mdat', b'free', b'wide', b'skip')
    if extension == 'webm':
        return cabecera[:4] == b'\x1a\x45\xdf\xa3'
    return False


def dimensiones_imagen(archivo, extension):
    archivo.seek(0)
    cabecera = archivo.read(32)
    if extension == 'png' and len(cabecera) >= 24:
        return struct.unpack('>II', cabecera[16:24])
    if extension == 'gif' and len(cabecera) >= 10:
        return struct.unpack('<HH', cabecera[6:10])
    if extension in ('jpg', 'jpeg'):
        archivo.seek(2)
        while True:
            byte = archivo.read(1)
            if not byte:
                return None
            if byte != b'\xff':
                continue
            marcador = archivo.read(1)
            while marcador == b'\xff':
                marcador = archivo.read(1)
            if not marcador:
                return None
            codigo = marcador[0]
            if codigo == 0xd9:
                return None
            if codigo in (0xd8, 0x01) or 0xd0 <= codigo <= 0xd7:
                continue
            texto = archivo.read(2)
            if len(texto) < 2:
                return None
            longitud = struct.unpack('>H', texto)[0]
            if 0xc0 <= codigo <= 0xcf and codigo not in (0xc4, 0xc8, 0xcc):
                datos = archivo.read(5)
                if len(datos) < 5:
                    return None
                alto, ancho = struct.unpack('>xHH', datos)
                return ancho, alto
            archivo.seek(longitud - 2, 1)
    return None


def duracion_en_moov(archivo, inicio, fin):
    posicion = inicio
    while posicion + 8 <= fin:
        archivo.seek(posicion)
        cabecera = archivo.read(8)
        if len(cabecera) < 8:
            return None
        tamanio, tipo = struct.unpack('>I4s', cabecera)
        if tamanio < 8:
            return None
        if tipo == b'mvhd':
            datos = archivo.read(32)
            if len(datos) < 32:
                return None
            if datos[0] == 1:
                escala, duracion = struct.unpack('>IQ', datos[20:32])
            else:
                escala, duracion = struct.unpack('>II', datos[12:20])
            if not escala or not duracion:
                return None
            return max(1, round(duracion / escala))
        posicion += tamanio
    return None


def duracion_mp4(archivo):
    archivo.seek(0, 2)
    final = archivo.tell()
    posicion = 0
    while posicion + 8 <= final:
        archivo.seek(posicion)
        cabecera = archivo.read(8)
        if len(cabecera) < 8:
            return None
        tamanio, tipo = struct.unpack('>I4s', cabecera)
        inicio_datos = posicion + 8
        if tamanio == 1:
            extendido = archivo.read(8)
            if len(extendido) < 8:
                return None
            tamanio = struct.unpack('>Q', extendido)[0]
            inicio_datos += 8
        elif tamanio == 0:
            tamanio = final - posicion
        if tamanio < 8:
            return None
        if tipo == b'moov':
            return duracion_en_moov(archivo, inicio_datos, posicion + tamanio)
        posicion += tamanio
    return None


def analizar_archivo(archivo):
    nombre = (archivo.name or '').lower()
    extension = nombre.rsplit('.', 1)[-1] if '.' in nombre else ''
    if extension not in EXTENSIONES_IMAGEN + EXTENSIONES_VIDEO:
        raise ValidationError('Sube una imagen (JPG, PNG o GIF) o un video (MP4, MOV o WEBM).')
    tipo = 'imagen' if extension in EXTENSIONES_IMAGEN else 'video'
    limite = TAMANIO_MAXIMO_IMAGEN if tipo == 'imagen' else TAMANIO_MAXIMO_VIDEO
    if archivo.size == 0:
        raise ValidationError('El archivo está vacío.')
    if archivo.size > limite:
        raise ValidationError('El archivo pesa demasiado. El máximo para %s es de %d MB.' % ('imágenes' if tipo == 'imagen' else 'videos', limite // (1024 * 1024)))
    archivo.seek(0)
    if not firma_valida(extension, archivo.read(12)):
        raise ValidationError('El contenido del archivo no corresponde a su formato.')
    ancho = alto = duracion = None
    if tipo == 'imagen':
        medidas = dimensiones_imagen(archivo, extension)
        if not medidas or min(medidas) < 1:
            raise ValidationError('No pudimos leer la imagen. Prueba con otro archivo.')
        ancho, alto = medidas
    elif extension in ('mp4', 'mov'):
        duracion = duracion_mp4(archivo)
    archivo.seek(0)
    return {'tipo': tipo, 'formato': extension, 'tamanioBytes': archivo.size, 'ancho': ancho, 'alto': alto, 'duracionSegundos': duracion}


def guardar_archivo(archivo, extension):
    nombre = '%s.%s' % (uuid.uuid4().hex, extension)
    with open(carpeta_archivos() / nombre, 'wb') as salida:
        for fragmento in archivo.chunks():
            salida.write(fragmento)
    return nombre


def url_archivo(solicitud, nombre):
    return solicitud.build_absolute_uri(reverse('archivo_publicacion', args=[nombre]))


def nombre_local(url):
    if not url:
        return None
    prefijo = reverse('archivo_publicacion', args=['x'])[:-1]
    ruta = urlparse(url).path
    if ruta.startswith(prefijo):
        nombre = ruta[len(prefijo):]
        if PATRON_NOMBRE_ARCHIVO.match(nombre):
            return nombre
    return None


def eliminar_archivo(url):
    nombre = nombre_local(url)
    if nombre:
        (carpeta_archivos() / nombre).unlink(missing_ok=True)


def fragmentos(archivo, restante, bloque=65536):
    try:
        while restante > 0:
            datos = archivo.read(min(bloque, restante))
            if not datos:
                break
            restante -= len(datos)
            yield datos
    finally:
        archivo.close()


def responder_archivo(solicitud, nombre):
    if not PATRON_NOMBRE_ARCHIVO.match(nombre):
        raise Http404
    ruta = carpeta_archivos() / nombre
    if not ruta.is_file():
        raise Http404
    tamanio = ruta.stat().st_size
    tipo = mimetypes.guess_type(nombre)[0] or 'application/octet-stream'
    rango = PATRON_RANGO.match(solicitud.META.get('HTTP_RANGE', ''))
    if rango and (rango.group(1) or rango.group(2)) and tamanio:
        if rango.group(1):
            inicio = int(rango.group(1))
            final = min(int(rango.group(2)), tamanio - 1) if rango.group(2) else tamanio - 1
        else:
            inicio = max(tamanio - int(rango.group(2)), 0)
            final = tamanio - 1
        if inicio >= tamanio or inicio > final:
            respuesta = HttpResponse(status=416)
            respuesta['Content-Range'] = 'bytes */%d' % tamanio
            return respuesta
        archivo = open(ruta, 'rb')
        archivo.seek(inicio)
        respuesta = StreamingHttpResponse(fragmentos(archivo, final - inicio + 1), status=206, content_type=tipo)
        respuesta['Content-Range'] = 'bytes %d-%d/%d' % (inicio, final, tamanio)
        respuesta['Content-Length'] = str(final - inicio + 1)
    else:
        respuesta = FileResponse(open(ruta, 'rb'), content_type=tipo)
        respuesta['Content-Length'] = str(tamanio)
    respuesta['Accept-Ranges'] = 'bytes'
    respuesta['Cache-Control'] = 'public, max-age=86400'
    respuesta['X-Content-Type-Options'] = 'nosniff'
    return respuesta
