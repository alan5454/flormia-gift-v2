from django.shortcuts import render

from .models import Arreglo, Contacto, Extra, Ramo, TipoFlor

CATEGORIAS = [
    ("clasico", "Ramos clásicos"),
    ("temporada", "Ramos de temporada"),
    ("arreglo", "Arreglos y diseños"),
]


def _producto(obj, categoria):
    return {
        "nombre": obj.nombre,
        "descripcion": obj.descripcion,
        "precio": obj.precio,
        "imagen_url": obj.imagen_url,
        "categoria": categoria,
    }


def inicio(request):
    """Página única del catálogo. Variables que usa index.html:
    flores, productos, categorias, extras, contacto, whatsapp."""
    productos = [_producto(r, r.categoria) for r in Ramo.objects.filter(activo=True)]
    productos += [_producto(a, "arreglo") for a in Arreglo.objects.filter(activo=True)]
    presentes = {p["categoria"] for p in productos}
    contacto = Contacto.objects.first()
    whatsapp = "".join(c for c in (contacto.whatsapp if contacto else "") if c.isdigit())
    return render(request, "catalogo/index.html", {
        "flores": TipoFlor.objects.filter(activo=True),
        "productos": productos,
        "categorias": [c for c in CATEGORIAS if c[0] in presentes],
        "extras": Extra.objects.filter(activo=True),
        "contacto": contacto,
        "whatsapp": whatsapp,
    })
