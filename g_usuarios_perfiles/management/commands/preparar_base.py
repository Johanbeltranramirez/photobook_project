import json
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pymongo import MongoClient

class Command(BaseCommand):
    help = 'Crea o valida las colecciones sin borrar documentos.'

    def handle(self, *argumentos, **opciones):
        configuracion = settings.DATABASES['default']
        cliente = MongoClient(**configuracion['CLIENT'])
        base = cliente[configuracion['NAME']]
        carpeta = settings.BASE_DIR / 'base_datos'
        esquemas = json.loads((carpeta / 'esquemas.json').read_text(encoding='utf-8'))
        indices = json.loads((carpeta / 'indices.json').read_text(encoding='utf-8'))
        existentes = base.list_collection_names()
        for nombre, esquema in esquemas.items():
            if nombre in existentes:
                incompatible = base[nombre].find_one({'$nor': [{'$jsonSchema': esquema}]}, {'_id': 1})
                if incompatible:
                    raise CommandError('Documento incompatible en ' + nombre + ': ' + str(incompatible['_id']))
            for campos in indices.get(nombre, []):
                clave = {campo.replace('.', '_'): '$' + campo for campo in campos}
                duplicados = list(base[nombre].aggregate([
                    {'$group': {'_id': clave, 'cantidad': {'$sum': 1}}},
                    {'$match': {'cantidad': {'$gt': 1}}}, {'$limit': 1},
                ]))
                if duplicados:
                    raise CommandError('Hay duplicados en ' + nombre + ': ' + ', '.join(campos))
        for nombre, esquema in esquemas.items():
            validacion = {'validator': {'$jsonSchema': esquema}, 'validationLevel': 'strict', 'validationAction': 'error'}
            if nombre in existentes:
                base.command('collMod', nombre, **validacion)
            else:
                base.create_collection(nombre, **validacion)
            for campos in indices.get(nombre, []):
                base[nombre].create_index([(campo, 1) for campo in campos], unique=True)
            self.stdout.write(nombre + ': preparada')
        cliente.close()
