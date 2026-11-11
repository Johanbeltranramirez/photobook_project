import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
archivo_clave = BASE_DIR / '.clave_local'
if not os.environ.get('PHOTOBOOK_CLAVE') and not archivo_clave.exists():
    archivo_clave.write_text(secrets.token_urlsafe(50))
SECRET_KEY = os.environ.get('PHOTOBOOK_CLAVE') or archivo_clave.read_text().strip()
DEBUG = os.environ.get('PHOTOBOOK_DEPURACION', '1') == '1'
ALLOWED_HOSTS = os.environ.get('PHOTOBOOK_SERVIDORES', 'localhost,127.0.0.1').split(',')
INSTALLED_APPS = [
    'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles',
    'g_usuarios_perfiles', 'publicacion_org_contenido',
    'int_social_comunidad', 'exploracion_inspiracion', 'admin_contrl_sys',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'g_usuarios_perfiles.acceso.UsuarioActual',
]
ROOT_URLCONF = 'photobook.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'plantillas'], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.messages.context_processors.messages',
        'g_usuarios_perfiles.acceso.contexto_usuario',
    ]},
}]
WSGI_APPLICATION = 'photobook.wsgi.application'
DATABASES = {'default': {
    'ENGINE': 'djongo',
    'NAME': os.environ.get('PHOTOBOOK_BASE', 'photobook_db'),
    'CLIENT': {'host': os.environ.get('PHOTOBOOK_MONGO', 'mongodb://127.0.0.1:27017/'), 'serverSelectionTimeoutMS': 5000},
}}
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = str(BASE_DIR / 'sesiones')
Path(SESSION_FILE_PATH).mkdir(exist_ok=True)
SESSION_COOKIE_AGE = 28800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'estaticos']
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

CORREO_USUARIO = os.environ.get(
    'PHOTOBOOK_CORREO_USUARIO',
    'johan.ramirez.beltran@gmail.com'
).strip()

CORREO_CLAVE = os.environ.get(
    'PHOTOBOOK_CORREO_CLAVE',
    'xccs vfua rsfm dkjz'
).replace(' ', '')

EMAIL_HOST = os.environ.get(
    'PHOTOBOOK_CORREO_SERVIDOR',
    'smtp.gmail.com'
)

EMAIL_PORT = int(os.environ.get(
    'PHOTOBOOK_CORREO_PUERTO',
    '587'
))

EMAIL_USE_SSL = False
EMAIL_USE_TLS = True

EMAIL_HOST_USER = CORREO_USUARIO
EMAIL_HOST_PASSWORD = CORREO_CLAVE

EMAIL_TIMEOUT = 20

EMAIL_BACKEND = (
    'photobook.correo_smtp.EmailBackend'
    if CORREO_USUARIO and CORREO_CLAVE
    else 'django.core.mail.backends.console.EmailBackend'
)

DEFAULT_FROM_EMAIL = f'Photobook <{CORREO_USUARIO}>'

SERVER_EMAIL = DEFAULT_FROM_EMAIL

URL_BASE_SITIO = os.environ.get(
    'PHOTOBOOK_URL_BASE',
    'http://127.0.0.1:8000'
)

TIEMPO_TOKEN_RESTABLECER = int(
    os.environ.get('PHOTOBOOK_TOKEN_MINUTOS', '60')
) * 60

# Logs visibles de los errores de envío (antes se perdían en el hilo)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'consola': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'photobook.correo': {'handlers': ['consola'], 'level': 'INFO', 'propagate': False},
    },
}