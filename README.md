# Photobook

Photobook es una aplicación web de alcance artístico, concebida como una plataforma de libre expresión para aquellas personas que desean compartir su manera de ver el arte. Está diseñada para inspirar, descubrir y conectar a artistas, creadores y apasionados del arte en un mismo espacio digital, fomentando la creatividad y la interacción visual.

Alcance del sistema:
La aplicación se estructura en 5 módulos (aplicaciones Django):

1. Gestión de Usuarios y Perfiles:
   - Registro, autenticación y personalización de perfiles.
   - Seguimiento entre usuarios, configuración de privacidad y notificaciones en tiempo real.

2. Publicación y Organización de Contenido:
   - Subida de imágenes y videos con metadatos.
   - Herramientas de edición básica y organización en colecciones temáticas.
   - Búsqueda avanzada y sistema de recomendaciones.

3. Interacción Social y Comunidad:
   - Comentarios enriquecidos, reacciones múltiples y mensajería privada.
   - Grupos temáticos y foros de discusión artística.
   - Moderación de contenido con reportes y bloqueos.

4. Exploración e Inspiración:
   - Feed dinámico con contenido sugerido según preferencias.
   - Sección de tendencias y destacados.
   - Algoritmos de descubrimiento y colecciones colaborativas.

5. Administración y Control del Sistema:
   - Panel de administración para moderadores.
   - Gestión de roles, permisos y estadísticas de uso.
   - Herramientas de curaduría y respaldo de datos.

## Preparación en Windows

Usar Python 3.10 y un servidor MongoDB en ejecución. Abre PowerShell en la carpeta que contiene `manage.py`.

```powershell
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
python manage.py check
python manage.py preparar_base
python manage.py crear_administrador
python manage.py cargar_ejemplos
python manage.py runserver
```

## Equipo de Trabajo

- DIEGO ARMANDO ARIAS ALVEAR
- JUDY NATALIA CORREA LOPEZ
- NELSON MAURICIO GARZON BERNAL
- ANDREA ESTEFANIA PARRA QUIMBAY
- JOHAN FELIPE RAMIREZ BELTRAN