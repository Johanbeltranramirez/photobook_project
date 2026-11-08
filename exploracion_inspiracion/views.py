from django.shortcuts import render
from django.http import JsonResponse
from bson import ObjectId
from django.views.decorators.csrf import csrf_exempt
import json

from .db import coleccion, comprobar_conexion


def inicio(request):
    return render(request, "exploracion/pagina.html", {
        "seccion": "Explorar",
        "descripcion": "Descubre fotografías e inspiración."
    })


def categorias(request):
    return render(request, "exploracion/pagina.html", {
        "seccion": "Categorías",
        "descripcion": "Explora fotografías por categorías."
    })


def tendencias(request):
    return render(request, "exploracion/pagina.html", {
        "seccion": "Tendencias",
        "descripcion": "Descubre las publicaciones más populares."
    })


def destacados(request):
    return render(request, "exploracion/pagina.html", {
        "seccion": "Destacados",
        "descripcion": "Descubre el contenido seleccionado de Photobook."
    })


def para_ti(request):
    return render(request, "exploracion/pagina.html", {
        "seccion": "Para ti",
        "descripcion": "Contenido recomendado según tus preferencias."
    })


def colecciones(request):
    return render(request, "exploracion/pagina.html", {
        "seccion": "Colecciones",
        "descripcion": "Explora tus colecciones de inspiración."
    })


def estado(request):
    return JsonResponse({
        "mongodb": "Conectado" if comprobar_conexion() else "Desconectado",
        "modulo": "Exploración e Inspiración"
    })


@csrf_exempt
def crear(request):

    if request.method == "POST":

        try:
            datos = json.loads(request.body)

            documento = {
                "usuarioId": ObjectId(datos["usuarioId"]),
                "preferencias": datos.get("preferencias", {
                    "categorias": [],
                    "etiquetas": [],
                    "artistasSeguidos": []
                }),
                "feed": datos.get("feed", []),
                "tendencias": datos.get("tendencias", []),
                "destacados": datos.get("destacados", [])
            }

            resultado = coleccion.insert_one(documento)

            return JsonResponse({
                "mensaje": "Registro creado correctamente",
                "id": str(resultado.inserted_id)
            })

        except Exception as error:
            return JsonResponse({
                "error": str(error)
            }, status=400)

    return JsonResponse({"error": "Use POST"}, status=405)


def consultar(request):

    datos = list(coleccion.find())

    for dato in datos:
        dato["_id"] = str(dato["_id"])
        dato["usuarioId"] = str(dato["usuarioId"])

    return JsonResponse(datos, safe=False)


@csrf_exempt
def eliminar(request, id):

    if request.method == "POST":

        try:
            resultado = coleccion.delete_one({
                "_id": ObjectId(id)
            })

            return JsonResponse({
                "mensaje": "Registro eliminado",
                "eliminados": resultado.deleted_count
            })

        except Exception as error:
            return JsonResponse({
                "error": str(error)
            }, status=400)

    return JsonResponse({"error": "Use POST"}, status=405)