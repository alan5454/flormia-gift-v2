"""Carga el catálogo inicial. Idempotente: no duplica ni pisa cambios del admin."""
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogo.models import Arreglo, Contacto, Extra, Ramo, TipoFlor

I = "catalogo/img/"
FLORES = [
    ("Rosas", "clásicas y llenas de cariño", "flor-rosa.svg"),
    ("Tulipanes", "frescos y llenos de alegría", "flor-durazno.svg"),
    ("Girasoles", "luminosos y optimistas", "flor-amarillo.svg"),
    ("Lirios", "elegantes y serenos", "flor-blanco.svg"),
    ("Peonías", "románticas y exuberantes", "flor-magenta.svg"),
    ("Orquídeas", "sofisticadas y delicadas", "flor-lavanda.svg"),
]
RAMOS = [  # nombre, descripción, precio, categoría, imagen
    ("Ramo Dulce Amanecer", "12 rosas rosadas", 450, Ramo.CLASICO, "flor-rosa.svg"),
    ("Ramo Pureza", "lirios blancos y follaje verde", 520, Ramo.CLASICO, "flor-blanco.svg"),
    ("Ramo Campo Fresco", "girasoles y margaritas", 380, Ramo.CLASICO, "flor-amarillo.svg"),
    ("Ramo Primavera", "tulipanes y peonías", 680, Ramo.TEMPORADA, "flor-durazno.svg"),
    ("Ramo Lavanda y Luz", "flores en tonos lila", 590, Ramo.TEMPORADA, "flor-lavanda.svg"),
    ("Ramo Gran Detalle", "24 rosas premium", 890, Ramo.TEMPORADA, "flor-magenta.svg"),
]
ARREGLOS = [
    ("Caja Floral Suave", "arreglo floral en caja", 650, "flor-rosa.svg"),
    ("Florero de Cristal", "flores frescas en florero de cristal", 720, "flor-durazno.svg"),
    ("Centro de Mesa Elegante", "composición floral para mesa", 950, "flor-blanco.svg"),
    ("Orquídea en Maceta", "orquídea delicada en maceta", 480, "flor-lavanda.svg"),
]
EXTRAS = [
    ("Tarjeta con mensaje personalizado", "💌", 40),
    ("Globo", "🎈", 90),
    ("Peluche pequeño", "🧸", 150),
    ("Chocolates", "🍫", 120),
    ("Envío a domicilio", "🚚", 80),
]


class Command(BaseCommand):
    help = "Carga los datos iniciales sin duplicar (se puede ejecutar varias veces)."

    @transaction.atomic
    def handle(self, *args, **options):
        nuevos = 0

        def crear(modelo, nombre, **defaults):
            nonlocal nuevos
            _, creado = modelo.objects.get_or_create(nombre=nombre, defaults=defaults)
            nuevos += creado

        for n, (nombre, desc, img) in enumerate(FLORES, 1):
            crear(TipoFlor, nombre, descripcion=desc, imagen=I + img, orden=n)
        for n, (nombre, desc, precio, cat, img) in enumerate(RAMOS, 1):
            crear(Ramo, nombre, descripcion=desc, precio=precio, categoria=cat, imagen=I + img, orden=n)
        for n, (nombre, desc, precio, img) in enumerate(ARREGLOS, 1):
            crear(Arreglo, nombre, descripcion=desc, precio=precio, imagen=I + img, orden=n)
        for n, (nombre, icono, precio) in enumerate(EXTRAS, 1):
            crear(Extra, nombre, icono=icono, precio=precio, orden=n)
        _, creado = Contacto.objects.get_or_create(pk=1)
        nuevos += creado

        self.stdout.write(self.style.SUCCESS(f"Listo: {nuevos} registro(s) nuevo(s)."))
