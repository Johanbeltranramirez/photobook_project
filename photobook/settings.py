import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CARPETA_DATOS = BASE_DIR / 'datos_locales'
CARPETA_DATOS.mkdir(exist_ok=True)


def leer_ajustes_locales(ruta):
    valores = {}
    if ruta.exists():
        for linea in ruta.read_text(encoding='utf-8').splitlines():
            linea = linea.strip()
            if linea and not linea.startswith('#') and '=' in linea:
                nombre, _, valor = linea.partition('=')
                valores[nombre.strip()] = valor.strip().strip('"').strip("'")
    return valores


AJUSTES_LOCALES = leer_ajustes_locales(CARPETA_DATOS / 'ajustes_locales.txt')


def obtener_ajuste(nombre, defecto=''):
    return os.environ.get(nombre) or AJUSTES_LOCALES.get(nombre) or defecto


archivo_clave = CARPETA_DATOS / 'clave_secreta.txt'
if not obtener_ajuste('PHOTOBOOK_CLAVE') and not archivo_clave.exists():
    archivo_clave.write_text(secrets.token_urlsafe(50))
SECRET_KEY = obtener_ajuste('PHOTOBOOK_CLAVE') or archivo_clave.read_text().strip()
DEBUG = obtener_ajuste('PHOTOBOOK_DEPURACION', '1') == '1'
ALLOWED_HOSTS = obtener_ajuste('PHOTOBOOK_SERVIDORES', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles',
    'aplicaciones.g_usuarios_perfiles', 'aplicaciones.publicacion_org_contenido',
    'aplicaciones.int_social_comunidad', 'aplicaciones.exploracion_inspiracion',
    'aplicaciones.admin_contrl_sys',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'aplicaciones.g_usuarios_perfiles.acceso.UsuarioActual',
]

ROOT_URLCONF = 'photobook.urls'
WSGI_APPLICATION = 'photobook.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'plantillas'], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.messages.context_processors.messages',
        'aplicaciones.g_usuarios_perfiles.acceso.contexto_usuario',
    ]},
}]

DATABASES = {'default': {
    'ENGINE': 'djongo',
    'NAME': obtener_ajuste('PHOTOBOOK_BASE', 'photobook_db'),
    'CLIENT': {'host': obtener_ajuste('PHOTOBOOK_MONGO', 'mongodb://127.0.0.1:27017/'), 'serverSelectionTimeoutMS': 5000},
}}

SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = str(CARPETA_DATOS / 'sesiones')
Path(SESSION_FILE_PATH).mkdir(parents=True, exist_ok=True)
SESSION_COOKIE_AGE = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CARPETA_ARCHIVOS_SUBIDOS = CARPETA_DATOS / 'archivos_subidos' / 'publicaciones'

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    ('css', BASE_DIR / 'estaticos' / 'css'),
    BASE_DIR / 'estaticos' / 'imagenes',
]
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

CORREO_USUARIO = obtener_ajuste(
    'PHOTOBOOK_CORREO_USUARIO',
    'johan.ramirez.beltran@gmail.com'
).strip()

CORREO_CLAVE = obtener_ajuste(
    'PHOTOBOOK_CORREO_CLAVE',
    'xccs vfua rsfm dkjz'
).replace(' ', '')

EMAIL_HOST = obtener_ajuste(
    'PHOTOBOOK_CORREO_SERVIDOR',
    'smtp.gmail.com'
)

EMAIL_PORT = int(obtener_ajuste(
    'PHOTOBOOK_CORREO_PUERTO',
    '587'
))

EMAIL_USE_SSL = False
EMAIL_USE_TLS = True

EMAIL_HOST_USER = CORREO_USUARIO
EMAIL_HOST_PASSWORD = CORREO_CLAVE

EMAIL_TIMEOUT = 20

EMAIL_BACKEND = (
    'photobook.utilidades.correo_smtp.EmailBackend'
    if CORREO_USUARIO and CORREO_CLAVE
    else 'django.core.mail.backends.console.EmailBackend'
)

DEFAULT_FROM_EMAIL = f'Photobook <{CORREO_USUARIO}>'

SERVER_EMAIL = DEFAULT_FROM_EMAIL

URL_BASE_SITIO = obtener_ajuste('PHOTOBOOK_URL_BASE', 'http://127.0.0.1:8000')
TIEMPO_TOKEN_RESTABLECER = int(obtener_ajuste('PHOTOBOOK_TOKEN_MINUTOS', '60')) * 60

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'consola': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'photobook': {'handlers': ['consola'], 'level': 'INFO', 'propagate': False},
    },
}
