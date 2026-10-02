# PhotoBook

Proyecto web desarrollado con **Django 6.1.1**, preparado para trabajar con **MongoDB mediante PyMongo**.

## 1. Requisitos previos

Antes de clonar y ejecutar el proyecto, cada colaborador debe tener instalado:

- Git
- Python compatible con Django 6.1.1
- MongoDB
- Un editor de código, recomendado: Visual Studio Code
- PowerShell, CMD o una terminal equivalente

Verificar Python:

```powershell
python --version
```

Verificar Git:

```powershell
git --version
```

Verificar MongoDB según la instalación disponible en el equipo.

---

## 2. Clonar el repositorio

Clonar el proyecto:

```powershell
git clone https://github.com/Johanbeltranramirez/photobook_project.git
```

Entrar al proyecto:

```powershell
cd photobook_project
```

> Reemplazar `<URL_DEL_REPOSITORIO>` por la URL real del repositorio Git.

---

## 3. Crear el entorno virtual

En Windows / PowerShell:

```powershell
python -m venv env
```

Activar el entorno:

```powershell
.\env\Scripts\Activate.ps1
```

La terminal debe mostrar algo similar a:

```text
(env) PS C:\...\photobook_project>
```

Si PowerShell impide la ejecución de scripts, puede ser necesario ajustar temporalmente la política de ejecución del usuario:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Después volver a activar:

```powershell
.\env\Scripts\Activate.ps1
```

---

## 4. Instalar las dependencias

Con el entorno virtual activo:

```powershell
python -m pip install --upgrade pip
```

Instalar las dependencias del proyecto:

```powershell
pip install -r requirements.txt
```

Si el archivo `requirements.txt` todavía no existe, instalar inicialmente:

```powershell
pip install django==6.1.1 pymongo djangorestframework python-dotenv
```

Y generar el archivo:

```powershell
pip freeze > requirements.txt
```

### Dependencias principales

| Paquete | Uso |
|---|---|
| Django 6.1.1 | Framework principal |
| PyMongo | Conexión directa con MongoDB |
| Django REST Framework | Desarrollo de APIs REST |
| python-dotenv | Lectura de variables desde `.env` |

> **Importante:** este proyecto no utiliza `Djongo`. No instalar `djongo`, ya que la versión utilizada anteriormente presenta incompatibilidades con Django 6.1.1.

---

## 5. Configuración de MongoDB

El proyecto utiliza MongoDB mediante PyMongo.

Crear un archivo llamado:

```text
.env
```

en la raíz del proyecto:

```text
photobook_project/
├── .env
├── manage.py
├── requirements.txt
├── photobook/
└── g_usuarios_perfiles/
...
```

Contenido inicial:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=photobook
```

Si MongoDB utiliza autenticación, **no colocar las credenciales directamente en el código fuente**. Utilizar variables de entorno.

Ejemplo:

```env
MONGO_URI=mongodb://usuario:contraseña@localhost:27017/
MONGO_DB=photobook
```

### Seguridad

El archivo `.env` debe estar incluido en `.gitignore`:

```gitignore
.env
env/
__pycache__/
*.pyc
```

**Nunca subir contraseñas, tokens, claves o credenciales al repositorio.**

---

## 6. Verificar MongoDB

Antes de ejecutar el proyecto, MongoDB debe estar disponible.

La configuración local esperada inicialmente es:

```text
mongodb://localhost:27017/
```

Base de datos:

```text
photobook
```

MongoDB crea la base de datos cuando se realiza la primera operación que genera datos, por lo que no necesariamente debe existir previamente.

---

## 7. Configuración de Django

El proyecto Django se denomina:

```text
photobook
```

La estructura principal es:

```text
photobook_project/
│
├── env/
│
├── photobook/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── photos/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   └── mongodb.py
│
├── .env
├── .gitignore
├── manage.py
└── requirements.txt
```

Las aplicaciones actualmente utilizadas incluyen:

```python
'rest_framework',
'photos',
```

en `INSTALLED_APPS`.

---

## 8. Migraciones de Django

Después de clonar el proyecto y configurar el entorno:

```powershell
python manage.py migrate
```

Esto crea las estructuras necesarias para los componentes de Django que utilizan base de datos relacional, como autenticación, sesiones y administración.

> MongoDB se maneja mediante PyMongo y no mediante `Djongo`.

---

## 9. Crear un superusuario

El proyecto requiere un usuario administrador de Django para acceder al panel administrativo.

Crear uno con:

```powershell
python manage.py createsuperuser
```

El usuario administrador configurado originalmente durante el desarrollo es:

```text
Username: johanrb
Email: johan.ramirez.beltran@gmail.com
```

### Seguridad de credenciales

**La contraseña del superusuario no se documenta en este README ni debe almacenarse en Git.**

Si un colaborador necesita acceso administrativo, debe crear su propio superusuario:

```powershell
python manage.py createsuperuser
```

Esto evita compartir credenciales personales entre integrantes del equipo.

---

## 10. Ejecutar el proyecto

Con el entorno virtual activo:

```powershell
python manage.py runserver
```

Por defecto estará disponible en:

```text
http://127.0.0.1:8000/
```

También puede utilizarse:

```text
http://localhost:8000/
```

Para acceder al administrador:

```text
http://127.0.0.1:8000/admin/
```

---

## 11. Verificación de instalación

Antes de comenzar a desarrollar, ejecutar:

```powershell
python manage.py check
```

Una instalación correcta debe finalizar sin errores.

También se recomienda comprobar Django:

```powershell
python -m django --version
```

La versión esperada es:

```text
6.1.1
```

---

## 12. Flujo recomendado para nuevos colaboradores

Cada vez que un colaborador descargue el proyecto:

```powershell
git clone <URL_DEL_REPOSITORIO>
cd photobook_project

python -m venv env
.\env\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

# Crear/configurar .env

python manage.py migrate
python manage.py check
python manage.py runserver
```

Si necesita acceso al administrador:

```powershell
python manage.py createsuperuser
```

---

## 13. Flujo de trabajo con Git

Antes de comenzar a trabajar:

```powershell
git pull
```

Consultar el estado:

```powershell
git status
```

Crear una rama para una funcionalidad:

```powershell
git checkout -b feature/nombre-funcionalidad
```

Agregar cambios:

```powershell
git add .
```

Crear commit:

```powershell
git commit -m "feat: descripcion del cambio"
```

Subir la rama:

```powershell
git push -u origin feature/nombre-funcionalidad
```

Después, crear un Pull Request/Merge Request según la plataforma utilizada por el equipo.

---

## 14. Archivos que NO deben subirse al repositorio

El repositorio no debe contener:

```text
env/
.env
__pycache__/
*.pyc
db.sqlite3
```

Especialmente:

```text
.env
```

porque puede contener credenciales de MongoDB u otros secretos.

---

## 15. Buenas prácticas

### Entorno virtual

Cada desarrollador debe utilizar su propio entorno virtual:

```text
env/
```

El entorno no se comparte mediante Git.

### Dependencias

Cuando se agregue o actualice una dependencia:

```powershell
pip install nombre-paquete
pip freeze > requirements.txt
```

Luego debe incluirse el cambio de `requirements.txt` en el commit.

### Variables de entorno

No escribir secretos directamente en:

- `settings.py`
- `views.py`
- `mongodb.py`
- archivos JavaScript
- archivos JSON versionados
- README
- commits de Git

### Credenciales

Cada desarrollador debe utilizar sus propias credenciales para cuentas administrativas o servicios externos.

---

## 16. Comandos útiles

### Activar entorno virtual

```powershell
.\env\Scripts\Activate.ps1
```

### Desactivar entorno virtual

```powershell
deactivate
```

### Ver paquetes instalados

```powershell
pip list
```

### Actualizar requirements.txt

```powershell
pip freeze > requirements.txt
```

### Comprobar Django

```powershell
python manage.py check
```

### Crear migraciones

```powershell
python manage.py makemigrations
```

### Aplicar migraciones

```powershell
python manage.py migrate
```

### Crear aplicación Django

```powershell
python manage.py startapp nombre_app
```

### Ejecutar servidor

```powershell
python manage.py runserver
```

---

## 17. Problemas frecuentes

### Error: `No module named django`

Verificar que el entorno virtual esté activo:

```powershell
.\env\Scripts\Activate.ps1
```

Luego:

```powershell
pip install -r requirements.txt
```

### Error relacionado con `Djongo`

No instalar:

```powershell
pip install djongo
```

El proyecto utiliza PyMongo directamente.

### Error de conexión con MongoDB

Verificar:

1. Que MongoDB esté ejecutándose.
2. Que `MONGO_URI` sea correcto.
3. Que el puerto utilizado sea el esperado.
4. Que el nombre de la base de datos sea correcto.
5. Que las credenciales, si existen, sean válidas.

Configuración local inicial:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=photobook
```

### El archivo `.env` no existe

Crear uno en la raíz del proyecto:

```powershell
New-Item .env -ItemType File
```

Agregar:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=photobook
```

---

## 18. Arquitectura actual

La integración con MongoDB utiliza la siguiente estructura:

```text
                 ┌───────────────────┐
                 │      Cliente      │
                 │ Browser / Frontend│
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │      Django       │
                 │    Photobook      │
                 └─────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │      PyMongo      │
                 └─────────┬─────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │      MongoDB      │
                 │     photobook     │
                 └───────────────────┘
```

Django continúa utilizando sus mecanismos propios para funcionalidades como autenticación, administración y sesiones, mientras que las operaciones sobre MongoDB se realizan mediante PyMongo.

---

## 19. Estado inicial del proyecto

Tecnologías principales:

- Python
- Django 6.1.1
- PyMongo
- MongoDB
- Django REST Framework
- python-dotenv
- Git / GitHub

Proyecto:

```text
photobook
```

Aplicación:

```text
photos
```

Base de datos MongoDB:

```text
photobookdb
```

MongoDB local:

```text
localhost:27017
```

Usuario administrador inicial:

```text
johanrb
```

Correo administrativo:

```text
johan.ramirez.beltran@gmail.com
```

> La contraseña del usuario administrador no forma parte de este archivo por razones de seguridad. Los colaboradores deben crear sus propias credenciales mediante `createsuperuser`.

---

## 20. Contacto y colaboración

Para contribuir al proyecto:

1. Crear una rama específica para el cambio.
2. Mantener actualizada la rama respecto al repositorio principal.
3. No subir credenciales ni archivos sensibles.
4. Mantener actualizado `requirements.txt` cuando cambien las dependencias.
5. Ejecutar `python manage.py check` antes de realizar un commit.
6. Probar localmente los cambios antes de abrir un Pull Request.
7. Describir claramente los cambios realizados en el commit y Pull Request.
