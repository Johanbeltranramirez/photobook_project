import os,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p));os.environ['DJANGO_SETTINGS_MODULE']='photobook.settings'
import mongomock,djongo.database
cliente=mongomock.MongoClient()
djongo.database.MongoClient=lambda *a,**k:cliente
import django
django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS=['testserver','localhost','127.0.0.1']
import tempfile
carpeta_temporal=tempfile.TemporaryDirectory()
settings.SESSION_FILE_PATH=carpeta_temporal.name
from django.test import Client
from django.template.loader import get_template
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from g_usuarios_perfiles.models import Usuario
from admin_contrl_sys.models import Rol
from publicacion_org_contenido.models import Publicacion,Categoria,Coleccion,Recomendacion
from int_social_comunidad.models import Grupo,Mensaje,Moderacion
from exploracion_inspiracion.models import ExploracionInspiracion
from admin_contrl_sys.models import ReporteContenido,AccionAdministrativa,ControlSistema
resultados=[]
def comprobar(valor,nombre):
    assert valor,nombre
    resultados.append(nombre)
def pedir(navegador,metodo,ruta,datos=None,estado=200):
    respuesta=getattr(navegador,metodo)(ruta,datos or {})
    if respuesta.status_code!=estado:
        (Path(carpeta_temporal.name)/'error.html').write_bytes(respuesta.content)
        print(respuesta.content.decode()[:1800])
    comprobar(respuesta.status_code==estado,f'{metodo} {ruta}: {estado}')
    return respuesta
for f in list((p/'plantillas').rglob('*.html'))+list((p/'admin_contrl_sys/templates').rglob('*.html')):
    raiz=p/'plantillas' if (p/'plantillas') in f.parents else p/'admin_contrl_sys/templates'
    get_template(str(f.relative_to(raiz)))
comprobar(True,'Todas las plantillas compilan')
admin=Usuario.objects.create(nombreUsuario='administrador',correo='admin@example.org',contrasena=make_password('ClavePrueba963!'),rol='administrador',privacidad={'perfilPublico':True,'correoVisible':False})
Rol.objects.create(nombre='administrador',descripcion='Administración',permiso_usuarios=True,permiso_contenido=True,permiso_estadisticas=True)
Rol.objects.create(nombre='artista',descripcion='Artistas')
administrador=Client();ana=Client();luis=Client();extra=Client()
pedir(administrador,'post',reverse('iniciar_sesion'),{'nombreUsuario':'administrador','contrasena':'ClavePrueba963!'},302)
for navegador,nombre in [(ana,'ana'),(luis,'luis'),(extra,'otro')]:
    pedir(navegador,'post',reverse('registrar_usuario'),{'nombreUsuario':nombre,'correo':nombre+'@example.org','contrasena':'ClavePrueba963!','confirmacion':'ClavePrueba963!'},302)
pedir(administrador,'post',reverse('categoria_crear'),{'nombre':'Paisajes','descripcion':'Fotografía de paisajes'},302)
publicacion={'titulo':'Bosque de niebla','descripcion':'Una fotografía del bosque','tipo':'imagen','archivoUrl':'https://example.org/bosque.jpg','formato':'jpg','tamanioBytes':'2048','ancho':'800','alto':'600','etiquetas':'bosque, naturaleza','categorias':['paisajes'],'estado':'publicado'}
pedir(ana,'post',reverse('publicacion_crear'),publicacion,302)
foto=Publicacion.objects.first()
print('Foto',foto.pk)
for nombre in ['inicio','usuarios_listar','categorias_listar','publicaciones_listar','colecciones_listar','mensajes_listar','grupos_listar','moderaciones_listar','exploracion_inicio','preferencias_detalle','tendencias_listar','destacados_listar','notificaciones_listar','reportes_listar','recomendaciones_listar']:
    pedir(ana,'get',reverse(nombre))
for nombre in ['consultar_roles','consultar_acciones','consultar_controles']:
    pedir(administrador,'get',reverse(nombre))
for nombre in ['publicacion_detalle','publicacion_actualizar','publicacion_eliminar']:
    pedir(ana,'get',reverse(nombre,args=[foto.pk]))
pedir(luis,'post',reverse('publicacion_comentar',args=[foto.pk]),{'contenido':'Me gusta el paisaje'},302)
pedir(luis,'post',reverse('publicacion_reaccionar',args=[foto.pk]),{'tipoReaccion':'meGusta'},302)
pedir(ana,'post',reverse('coleccion_crear'),{'nombre':'Naturaleza','descripcion':'Fotos','tipo':'colaborativa','privacidad':'privada'},302)
coleccion=Coleccion.objects.first()
pedir(ana,'post',reverse('coleccion_guardar_publicacion',args=[coleccion.pk]),{'archivoUrl':foto.archivoUrl},302)
pedir(ana,'post',reverse('coleccion_colaboradores',args=[coleccion.pk]),{'usuario':'luis'},302)
pedir(luis,'get',reverse('coleccion_detalle',args=[coleccion.pk]))
pedir(extra,'get',reverse('coleccion_detalle',args=[coleccion.pk]),estado=403)
pedir(luis,'post',reverse('preferencias_crear'),{'categorias':['paisajes'],'etiquetas':'bosque','artistas':['ana']},302)
comprobar(Recomendacion.objects.count()==1,'Recomendación según preferencias')
pedir(luis,'post',reverse('recomendaciones_generar'),{},302)
comprobar(Recomendacion.objects.count()==1,'Recomendaciones sin duplicados')
pedir(ana,'post',reverse('mensaje_crear'),{'receptor':'luis','contenido':'Hola','tipo':'texto'},302)
mensaje=Mensaje.objects.first()
pedir(luis,'get',reverse('mensaje_detalle',args=[mensaje.pk]))
pedir(extra,'get',reverse('mensaje_detalle',args=[mensaje.pk]),estado=403)
pedir(ana,'post',reverse('mensaje_actualizar',args=[mensaje.pk]),{'contenido':'Hola, Luis'},302)
pedir(luis,'post',reverse('mensaje_marcar_leido',args=[mensaje.pk]),{},302)
pedir(ana,'post',reverse('grupo_crear'),{'nombre':'Fotografía','descripcion':'Grupo','tipo':'publico','categoria':'paisajes','estado':'activo'},302)
grupo=Grupo.objects.first()
pedir(ana,'get',reverse('grupo_detalle',args=[grupo.pk]))
pedir(luis,'post',reverse('grupo_unirse',args=[grupo.pk]),{},302)
pedir(ana,'post',reverse('foro_crear',args=[grupo.pk]),{'nombre':'Presentaciones'},302)
pedir(luis,'post',reverse('foro_comentar',args=[grupo.pk,0]),{'contenido':'Hola a todos'},302)
pedir(ana,'post',reverse('grupo_cambiar_rol',args=[grupo.pk]),{'usuario':'luis','rol':'moderador'},302)
pedir(ana,'get',reverse('grupo_detalle',args=[grupo.pk]))
pedir(luis,'post',reverse('bloqueo_crear'),{'bloqueado':'otro','ambito':'mensajes'},302)
pedir(extra,'post',reverse('mensaje_crear'),{'receptor':'luis','contenido':'Bloqueado','tipo':'texto'})
comprobar(Mensaje.objects.count()==1,'El bloqueo impide enviar el mensaje')
pedir(luis,'post',reverse('social_reporte_crear'),{'contenido':foto.archivoUrl,'tipo_contenido':'publicacion','motivo':'Solicito revisión'},302)
reporte=ReporteContenido.objects.first()
pedir(administrador,'post',reverse('reporte_resolver',args=[reporte.pk]),{'estado':'resuelto','accion_tomada':'Contenido revisado'},302)
pedir(luis,'get',reverse('reporte_detalle',args=[reporte.pk]))
comprobar(AccionAdministrativa.objects.count()==1,'Reporte y actuación unidos')
print('PASARON',len(resultados))
(p/'pruebas/resultado.json').write_text(json.dumps(resultados,ensure_ascii=False,indent=2))

from jsonschema import Draft4Validator,validators,ValidationError
from bson import ObjectId
from datetime import datetime
esquemas=json.loads((p/'base_datos/esquemas.json').read_text())
def tipo_bson(validador,tipos,valor,esquema):
    tipos=tipos if isinstance(tipos,list) else [tipos]
    clases={'objectId':lambda v:isinstance(v,ObjectId),'date':lambda v:isinstance(v,datetime),'null':lambda v:v is None,'string':lambda v:isinstance(v,str),'object':lambda v:isinstance(v,dict),'array':lambda v:isinstance(v,list),'bool':lambda v:isinstance(v,bool),'int':lambda v:isinstance(v,int) and not isinstance(v,bool),'long':lambda v:isinstance(v,int) and not isinstance(v,bool),'double':lambda v:isinstance(v,float)}
    if not any(clases[t](valor) for t in tipos):yield ValidationError('Tipo BSON incorrecto: '+str(tipos))
Validador=validators.extend(Draft4Validator,{'bsonType':tipo_bson})
base=cliente[settings.DATABASES['default']['NAME']]
def validar_documentos():
    for nombre,esquema in esquemas.items():
        for documento in base[nombre].find():
            errores=list(Validador(esquema).iter_errors(documento))
            comprobar(not errores,'Esquema '+nombre+(' '+str(errores[0]) if errores else ''))
validar_documentos()

pedir(ana,'post',reverse('perfil_actualizar',args=['ana']),{'biografia':'Mi perfil actualizado','perfilPublico':'on'},302)
pedir(luis,'post',reverse('seguir_usuario',args=['ana']),{},302)
comprobar(Usuario.objects.get(nombreUsuario='ana').seguidores[0]['usuario']=='luis','Seguimiento compartido entre perfiles')
pedir(luis,'post',reverse('publicacion_actualizar',args=[foto.pk]),publicacion,403)
pedir(extra,'post',reverse('comentario_actualizar',args=[foto.pk,0]),{'contenido':'No soy autor'},403)
pedir(extra,'post',reverse('foro_comentario_actualizar',args=[grupo.pk,0,0]),{'contenido':'No soy autor'},403)
pedir(luis,'post',reverse('categoria_crear'),{'nombre':'No permitido'},403)
pedir(luis,'post',reverse('reporte_resolver',args=[reporte.pk]),{'estado':'descartado','accion_tomada':'No permitido'},403)
pedir(extra,'get',reverse('reporte_detalle',args=[reporte.pk]),estado=403)
pedir(extra,'get',reverse('recomendacion_detalle',args=[Recomendacion.objects.first().pk]),estado=403)
publicacion.update(titulo='Bosque actualizado',archivoUrl='https://example.org/bosque-nuevo.jpg')
pedir(ana,'post',reverse('publicacion_actualizar',args=[foto.pk]),publicacion,302)
foto=Publicacion.objects.get(pk=foto.pk)
comprobar(Coleccion.objects.get(pk=coleccion.pk).publicaciones[0]['archivoUrl']==foto.archivoUrl,'Actualizar colección al editar publicación')
comprobar(Recomendacion.objects.first().publicacion['titulo']==foto.titulo,'Actualizar recomendación al editar publicación')
pedir(administrador,'post',reverse('categoria_actualizar',args=['paisajes']),{'nombre':'Paisaje natural','descripcion':'Nueva descripción'},302)
comprobar(Grupo.objects.get(pk=grupo.pk).categoria['nombre']=='Paisaje natural','Categoría actualizada en grupos')
comprobar(Publicacion.objects.get(pk=foto.pk).categorias[0]['nombre']=='Paisaje natural','Categoría actualizada en publicaciones')
pedir(ana,'post',reverse('coleccion_actualizar',args=[coleccion.pk]),{'nombre':'Colección editada','descripcion':'Fotos','tipo':'colaborativa','privacidad':'privada'},302)
pedir(ana,'post',reverse('grupo_actualizar',args=[grupo.pk]),{'nombre':'Fotógrafos','descripcion':'Grupo editado','tipo':'publico','categoria':'paisajes','estado':'activo'},302)
pedir(luis,'post',reverse('foro_comentario_actualizar',args=[grupo.pk,0,0]),{'contenido':'Comentario editado'},302)
pedir(luis,'post',reverse('foro_comentario_moderar',args=[grupo.pk,0,0]),{'accion':'fijar'},302)
pedir(luis,'post',reverse('mensaje_reaccionar',args=[mensaje.pk]),{'tipoReaccion':'aplauso'},302)
for nombre,argumentos in [('grupo_actualizar',[grupo.pk]),('mensaje_actualizar',[mensaje.pk]),('bloqueo_crear',[]),('preferencias_actualizar',[]),('recomendacion_actualizar',[Recomendacion.objects.first().pk]),('crear_accion',[]),('crear_control',[]),('crear_rol',[])]:
    if nombre=='mensaje_actualizar':continue
    navegador=administrador if nombre.startswith('crear_') or nombre.startswith('recomendacion_') else ana
    pedir(navegador,'get',reverse(nombre,args=argumentos))
pedir(administrador,'post',reverse('crear_rol'),{'nombre':'moderador','descripcion':'Revisa contenido','activo':'on','permiso_contenido':'on'},302)
pedir(administrador,'post',reverse('asignar_rol',args=['otro']),{'rol':'moderador'},302)
pedir(extra,'get',reverse('consultar_acciones'))
pedir(extra,'get',reverse('consultar_roles'),estado=403)
pedir(extra,'get',reverse('consultar_controles'),estado=403)
pedir(administrador,'post',reverse('crear_accion'),{'accion':'Revisión','entidad':'Grupo','detalle_entidad':'Fotógrafos','descripcion':'Sin observaciones'},302)
pedir(administrador,'post',reverse('crear_control'),{'fecha':'2026-11-08','usuarios_activos':4,'publicaciones':1,'reportes':1,'estado_respaldo':'sin_registrar'},302)
control=ControlSistema.objects.first()
pedir(administrador,'get',reverse('actualizar_control',args=[control.pk]))
pedir(administrador,'post',reverse('actualizar_control',args=[control.pk]),{'fecha':'2026-11-08','usuarios_activos':4,'publicaciones':2,'reportes':1,'estado_respaldo':'sin_registrar'},302)
validar_documentos()

incorrecto=dict(base['publicaciones'].find_one());incorrecto['tamanioBytes']=-1
comprobar(not Validador(esquemas['publicaciones']).is_valid(incorrecto),'Esquema rechaza tamaño inválido')
incorrecto=dict(base['usuarios'].find_one());incorrecto['contrasena']='texto plano'
comprobar(not Validador(esquemas['usuarios']).is_valid(incorrecto),'Esquema rechaza contraseña sin hash')
incorrecto=dict(base['moderacion'].find_one());incorrecto['tipo']='reporte'
comprobar(not Validador(esquemas['moderacion']).is_valid(incorrecto),'Esquema excluye reportes de bloqueos')

antes=Publicacion.objects.count()
pedir(ana,'get',reverse('publicacion_eliminar',args=[foto.pk]))
comprobar(Publicacion.objects.count()==antes,'GET no elimina publicaciones')
pedir(ana,'get',reverse('publicacion_comentar',args=[foto.pk]),estado=405)
pedir(Client(),'get',reverse('usuarios_listar'),estado=302)
protegido=Client(enforce_csrf_checks=True)
pedir(protegido,'post',reverse('registrar_usuario'),{},403)
pedir(ana,'get','/publicacion-contenido/publicaciones/no-valido/',estado=404)
pedir(ana,'post',reverse('publicacion_eliminar',args=[foto.pk]),{},302)
comprobar(Publicacion.objects.count()==0 and len(Coleccion.objects.first().publicaciones)==0 and Recomendacion.objects.count()==0,'Eliminar publicación limpia sus copias activas')
pedir(ana,'post',reverse('coleccion_eliminar',args=[coleccion.pk]),{},302)
pedir(luis,'post',reverse('preferencias_eliminar'),{},302)
pedir(luis,'post',reverse('mensaje_eliminar',args=[mensaje.pk]),{},302)
pedir(ana,'post',reverse('mensaje_eliminar',args=[mensaje.pk]),{},302)
comprobar(Mensaje.objects.count()==0,'Mensaje desaparece cuando ambos lo eliminan')
pedir(ana,'post',reverse('grupo_expulsar',args=[grupo.pk]),{'usuario':'luis'},302)
pedir(ana,'post',reverse('grupo_eliminar',args=[grupo.pk]),{},302)
pedir(luis,'post',reverse('bloqueo_eliminar',args=[Moderacion.objects.first().pk]),{},302)
pedir(administrador,'post',reverse('reporte_eliminar',args=[reporte.pk]),{},302)
comprobar(AccionAdministrativa.objects.count()==2,'Eliminar reporte conserva actuación')
pedir(administrador,'post',reverse('eliminar_control',args=[control.pk]),{},302)
pedir(luis,'post',reverse('perfil_eliminar',args=['luis']),{},302)
comprobar(not Usuario.objects.get(nombreUsuario='luis').activo,'Cuenta desactivada')
validar_documentos()
print('PASARON',len(resultados))
(p/'pruebas/resultado.json').write_text(json.dumps(resultados,ensure_ascii=False,indent=2))

from unittest.mock import patch
from django.core.management import call_command
import io
with patch('g_usuarios_perfiles.management.commands.cargar_ejemplos.getpass',return_value='ClaveDemo963!'):
    call_command('cargar_ejemplos',stdout=io.StringIO())
    cantidades={nombre:base[nombre].count_documents({}) for nombre in esquemas}
    call_command('cargar_ejemplos',stdout=io.StringIO())
    comprobar(cantidades=={nombre:base[nombre].count_documents({}) for nombre in esquemas},'Carga de ejemplos repetible sin duplicados')
comprobar(all(base[nombre].count_documents({}) for nombre in esquemas),'Ejemplos para las 14 colecciones')
validar_documentos()
publicacion_demo=Publicacion.objects.first()
grupo_demo=Grupo.objects.first()
fecha=grupo_demo.miembros[0]['fechaIngreso']
for vuelta in range(3):
    grupo_demo=Grupo.objects.get(pk=grupo_demo.pk)
    grupo_demo.descripcion='Revisión de fecha '+str(vuelta)
    grupo_demo.save()
comprobar(Grupo.objects.get(pk=grupo_demo.pk).miembros[0]['fechaIngreso']==fecha,'Las fechas embebidas no cambian al guardar de nuevo')

from django.urls import get_resolver
nombres=[]
def recorrer(rutas):
    for ruta in rutas:
        if hasattr(ruta,'url_patterns'):recorrer(ruta.url_patterns)
        elif ruta.name:nombres.append(ruta.name)
recorrer(get_resolver().url_patterns)
comprobar(len(nombres)==len(set(nombres)),'Nombres de rutas sin duplicados')
print('PASARON',len(resultados))
(p/'pruebas/resultado.json').write_text(json.dumps(resultados,ensure_ascii=False,indent=2))

for ruta in ['publicaciones_listar','publicaciones_buscar','categorias_listar','grupos_listar','usuarios_listar']:
    pedir(administrador,'get',reverse(ruta),{'q':'naturaleza','buscar':'demo'})

from django.urls.resolvers import URLPattern
from g_usuarios_perfiles.models import Notificacion
modelo_por_nombre={'publicacion':Publicacion,'comentario':Publicacion,'coleccion':Coleccion,'recomendacion':Recomendacion,'exploracion_recomendacion':Recomendacion,'mensaje':Mensaje,'grupo':Grupo,'foro':Grupo,'moderacion':Moderacion,'bloqueo':Moderacion,'reporte':ReporteContenido,'rol':Rol,'accion':AccionAdministrativa,'control':ControlSistema,'notificacion':Notificacion}
comprobadas=0
def visitar(rutas):
    global comprobadas
    for ruta in rutas:
        if not isinstance(ruta,URLPattern):visitar(ruta.url_patterns);continue
        if not ruta.name:continue
        parametros={}
        for nombre in ruta.pattern.converters:
            if nombre=='slug':parametros[nombre]='naturaleza'
            elif nombre=='nombre':parametros[nombre]='ana_demo'
            elif nombre.startswith('indice'):parametros[nombre]=0
            elif nombre=='pk':
                if ruta.name.startswith('exploracion_recomendacion'):modelo=Recomendacion
                else:
                    partes=ruta.name.split('_')
                    modelo=next((modelo_por_nombre[parte] for parte in partes if parte in modelo_por_nombre),None)
                if modelo is None:raise AssertionError(ruta.name)
                registro=modelo.objects.first()
                if registro is None:raise AssertionError('Sin ejemplo '+ruta.name)
                parametros[nombre]=registro.pk
        respuesta=administrador.get(reverse(ruta.name,kwargs=parametros))
        comprobar(respuesta.status_code in [200,302,400,403,404,405],'Ruta '+ruta.name+': '+str(respuesta.status_code))
        comprobadas+=1
visitar(get_resolver().url_patterns)
from django.apps import apps
for aplicacion in ['g_usuarios_perfiles','publicacion_org_contenido','int_social_comunidad','exploracion_inspiracion','admin_contrl_sys']:
    for modelo in apps.get_app_config(aplicacion).get_models():
        comprobar(not any(campo.is_relation for campo in modelo._meta.fields),'Sin llaves foráneas: '+modelo.__name__)
print('PASARON',len(resultados),'RUTAS',comprobadas)
(p/'pruebas/resultado.json').write_text(json.dumps(resultados,ensure_ascii=False,indent=2))

carpeta_temporal.cleanup()
