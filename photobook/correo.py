import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

registro = logging.getLogger('photobook.correo')


def url_base():
    return settings.URL_BASE_SITIO.rstrip('/')


def enlace(ruta):
    return url_base() + ruta


def enviar_correo(destinatario, asunto, contexto, en_segundo_plano=True):
    if not destinatario:
        return False
    asunto = ' '.join(str(asunto).split())[:120]
    contexto = {**contexto, 'url_base': url_base(), 'sitio': 'Photobook'}
    try:
        texto = render_to_string('correos/mensaje.txt', contexto)
        html = render_to_string('correos/mensaje.html', contexto)
    except Exception:
        registro.exception('No se pudo preparar el correo para %s', destinatario)
        return False

    def enviar():
        try:
            mensaje = EmailMultiAlternatives('[Photobook] ' + asunto, texto, settings.DEFAULT_FROM_EMAIL, [destinatario])
            mensaje.attach_alternative(html, 'text/html')
            mensaje.send()
        except Exception:
            registro.exception('No se pudo enviar el correo a %s', destinatario)

    if en_segundo_plano:
        threading.Thread(target=enviar, daemon=True).start()
    else:
        enviar()
    return True
