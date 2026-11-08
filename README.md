# Photobook

Proyecto de fotografía con cinco aplicaciones Django y almacenamiento documental en MongoDB.

## Preparación en Windows

Usa Python 3.10 y un servidor MongoDB en ejecución. Abre PowerShell en la carpeta que contiene `manage.py`.

```powershell
py -3.10 -m venv venv310
.\venv310\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py check
python manage.py preparar_base
python manage.py crear_administrador
python manage.py cargar_ejemplos
python manage.py runserver
```

Abre http://127.0.0.1:8000/. El comando `crear_administrador` solicita el nombre, correo y contraseña de la cuenta administradora. `cargar_ejemplos` es opcional y solicita una contraseña para las cuentas nuevas `ana_demo`, `luis_demo`, `maria_demo` y `carlos_demo`. Las cuentas que ya existían conservan su contraseña.

En Linux puedes crear el entorno con `python3.10 -m venv venv310` y activarlo con `source venv310/bin/activate`.

## Conexión

La configuración predeterminada utiliza `mongodb://127.0.0.1:27017/` y la base `photobook_db`. Para usar otra conexión, define las variables antes de ejecutar los comandos:

```powershell
$env:PHOTOBOOK_MONGO = "mongodb://127.0.0.1:27017/"
$env:PHOTOBOOK_BASE = "photobook_db"
```

La conexión y las credenciales se configuran en el equipo; no se incluyen credenciales de una base externa en el proyecto. La clave local se genera al iniciar Django y las sesiones se guardan en la carpeta `sesiones`.

El proyecto conserva Django 3.1.12 y Djongo 1.3.7 para seguir la estructura recibida. La configuración incluida corresponde a la ejecución local del proyecto académico.

## Colecciones

`python manage.py preparar_base` aplica los esquemas de `base_datos/esquemas.json` y los índices de `base_datos/indices.json`. También se incluye `base_datos/crear_colecciones.js` para ejecutar la creación desde mongosh. Son dos formas de preparar la misma estructura: basta con usar una.

El comando primero revisa los documentos y las claves que deben ser únicas. Si encuentra datos incompatibles o duplicados, se detiene antes de aplicar los esquemas. No borra ni transforma los datos anteriores. No ejecutes además el archivo original de colecciones: contiene definiciones repetidas y estructuras que ya se consolidaron.

Las colecciones definitivas son:

| Aplicación | Colecciones |
| --- | --- |
| Usuarios y perfiles | usuarios, notificaciones |
| Publicación y organización | publicaciones, colecciones, categorias, recomendaciones |
| Interacción social | mensajes, grupos, moderacion |
| Exploración e inspiración | exploracion |
| Administración | roles, accionesAdministrativas, reporteContenido, controlSistema |

Los comentarios y las reacciones se guardan dentro de las publicaciones o los mensajes correspondientes. Los foros y sus comentarios están dentro de los grupos. Los seguidores están dentro del usuario. No se crean colecciones separadas con esos mismos datos ni relaciones `ForeignKey`.

No se requiere `migrate` para los modelos del proyecto: las colecciones y sus restricciones se preparan con el comando anterior. La administración es el módulo propio del grupo; no se utiliza el panel automático de Django.

## Recorrido para comprobar la integración

1. Crea la base y el administrador. Carga los ejemplos si deseas recorrer pantallas con datos.
2. Ingresa como administrador. Revisa categorías, roles y control del sistema.
3. Cierra sesión e ingresa como `ana_demo`, o registra una cuenta nueva. Crea una publicación usando una categoría existente.
4. Crea una colección y agrega esa publicación. Si es colaborativa, agrega un usuario ya registrado.
5. Ingresa como `luis_demo`. Configura categorías, etiquetas y artistas en Exploración. Actualiza las recomendaciones.
6. Envía un mensaje, entra a un grupo y escribe en su foro. Comprueba las notificaciones.
7. Crea un reporte. Ingresa como administrador y atiende el mismo reporte desde Administración.
8. Edita y elimina registros desde sus pantallas. Las operaciones de eliminación muestran confirmación y se ejecutan mediante POST; las acciones de comentarios y foros tienen botones específicos.

Las imágenes y los videos se proporcionan mediante un enlace, tal como estaba definido en los modelos originales. La carga incluye ocho fotografías guardadas en `estaticos/ejemplos`; sus enlaces apuntan al mismo servidor local de Django. No necesitan conexión a Internet para verse durante la presentación. Los autores y las fuentes están en `base_datos/FUENTES_IMAGENES.txt`.

La carga agrega ocho publicaciones, cinco categorías, cuatro colecciones, tres grupos, ocho mensajes y ocho notificaciones. También incluye comentarios, reacciones, preferencias, recomendaciones, reportes y registros administrativos. Puede repetirse sin duplicar los ejemplos ni reemplazar las contraseñas, publicaciones o preferencias existentes. Si ya cargaste la ilustración de la versión anterior, se conserva y se agregan las ocho fotografías.

Si vas a usar otro puerto, indícalo en la primera carga: `python manage.py cargar_ejemplos --direccion http://127.0.0.1:8001`, y después ejecuta `python manage.py runserver 8001`. Este parámetro se aplica a los enlaces nuevos; no cambia los que ya están guardados. Consulta `CARGAR_DATOS.txt` para el procedimiento completo.

## Reglas de funcionamiento

- El usuario se registra una sola vez. Las vistas toman su identidad de la sesión, y los destinatarios o colaboradores se eligen entre usuarios existentes.
- El nombre de usuario no cambia al editar el perfil. Así se conserva la identidad dentro de los documentos embebidos.
- La contraseña se guarda mediante las funciones de Django para contraseñas, nunca como texto plano.
- Desactivar una cuenta impide iniciar sesión y conserva la autoría de su contenido. No se permite desactivar al último administrador.
- Las copias embebidas conservan el nombre de usuario y la imagen disponibles cuando se creó el documento. Cambiar la imagen del perfil no reescribe el historial completo.
- Un usuario accede a sus propios mensajes y reportes. Solo los participantes ven una conversación. Las colecciones privadas requieren ser propietario o colaborador.
- Los bloqueos se aplican según su ámbito y expiración. Un bloqueo de mensajes no oculta por sí solo las publicaciones.
- Las recomendaciones automáticas se generan por coincidencias de categorías, etiquetas y artistas. Cada criterio aporta un tercio de la puntuación. Se conservan hasta veinte coincidencias, ordenadas por puntuación y después por fecha. Se actualizan al guardar las preferencias o pulsar el botón correspondiente.
- Los reportes se guardan únicamente en `reporteContenido`. Al atenderlos, se registra la decisión y una acción administrativa. Escribir una acción no elimina automáticamente publicaciones ni desactiva usuarios: esas operaciones se realizan en sus pantallas correspondientes.
- `moderacion` guarda exclusivamente bloqueos.
- Control del sistema toma los conteos actuales al crear un registro. La fecha y el estado de un respaldo se registran manualmente; el módulo no ejecuta copias de seguridad.
- Los nombres de las funciones propias y los textos están en español. Se conservan nombres exigidos por Django, MongoDB, HTML y CSS, además de términos técnicos como URL y slug.

## Archivos principales

- `models.py`: estructura de cada documento y de sus objetos embebidos.
- `forms.py`: campos y validaciones de los formularios.
- `views.py`: consulta, creación, edición y eliminación de registros.
- `urls.py`: conexión de las rutas con sus vistas.
- `plantillas/base.html`: estructura visual compartida.
- `plantillas/comunes`: cabecera, menú, pie, formularios y tarjetas reutilizables.
- `estaticos/estilos.css`: estilos compartidos. Los colores #FFA97B y #FFECCB se usan en componentes; el fondo de página es blanco.
- `base_datos`: esquemas, índices y script de creación.

Consulta `SUSTENTACION.txt` para explicar el funcionamiento y `VALIDACION.txt` para conocer qué se comprobó y qué falta verificar en el equipo de ejecución.

## Comprobaciones aisladas

```powershell
python -m pip install -r requirements_pruebas.txt
python pruebas/verificar_integracion.py
python pruebas/verificar_carga.py
```

Estas comprobaciones usan MongoDB simulado y guardan el resultado en `pruebas/resultado.json`. No se conectan a la base del usuario. No reemplazan la prueba final con MongoDB real.
