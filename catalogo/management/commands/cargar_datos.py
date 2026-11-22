"""Carga el catálogo inicial. Idempotente: no duplica ni pisa cambios del admin."""
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogo.models import Contacto, Ramo, TipoFlor

I = "catalogo/img/"
FLORES = [  # nombre, descripción, imagen
    ("Rosas", "clásicas y llenas de cariño", "flor-rosa.svg"),
    ("Tulipanes", "frescos y llenos de alegría", "flor-durazno.svg"),
    ("Girasoles", "luminosos y optimistas", "flor-amarillo.svg"),
    ("Lirios", "elegantes y serenos", "flor-blanco.svg"),
    ("Peonías", "románticas y exuberantes", "flor-magenta.svg"),
    ("Orquídeas", "sofisticadas y delicadas", "flor-lavanda.svg"),
    ("Margaritas", "sencillas, frescas y llenas de ternura", "flor-blanco.svg"),
    ("Claveles", "duraderos y de colores intensos", "flor-magenta.svg"),
    ("Gerberas", "alegres y coloridas", "flor-amarillo.svg"),
]
RAMOS = [  # nombre, descripción, precio, imagen
    ("Ramo Dulce Amanecer", "12 rosas rosadas", 450, "flor-rosa.svg"),
    ("Ramo Pureza", "lirios blancos y follaje verde", 520, "flor-blanco.svg"),
    ("Ramo Campo Fresco", "girasoles y margaritas", 380, "flor-amarillo.svg"),
    ("Ramo Primavera", "tulipanes y peonías", 680, "flor-durazno.svg"),
    ("Ramo Lavanda y Luz", "flores en tonos lila", 590, "flor-lavanda.svg"),
    ("Ramo Gran Detalle", "24 rosas premium", 890, "flor-magenta.svg"),
    ("Ramo Ternura", "claveles y gerberas en tonos suaves", 480, "flor-durazno.svg"),
]
FLORES_POR_RAMO = {
    "Ramo Dulce Amanecer": ["Rosas"],
    "Ramo Pureza": ["Lirios"],
    "Ramo Campo Fresco": ["Girasoles", "Margaritas"],
    "Ramo Primavera": ["Tulipanes", "Peonías"],
    "Ramo Lavanda y Luz": ["Orquídeas", "Lirios"],
    "Ramo Gran Detalle": ["Rosas"],
    "Ramo Ternura": ["Claveles", "Gerberas"],
}
CONTACTO = {
    "direccion": "C. Mexicali 9021, Magisterial, 22470 Tijuana, B.C.",
    "facebook": "https://www.facebook.com/share/18A2WsrtXo/?mibextid=wwXIfr",
    "instagram": "https://www.instagram.com/flormia_gift?evlk=MWF1ZjA5bnFwbHp0bA==",
}


class Command(BaseCommand):
    help = "Carga los datos iniciales sin duplicar (se puede ejecutar varias veces)."

    @transaction.atomic
    def handle(self, *args, **options):
        nuevos = 0
        for n, (nombre, desc, img) in enumerate(FLORES, 1):
            _, creado = TipoFlor.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": desc, "imagen": I + img, "orden": n})
            nuevos += creado
        for n, (nombre, desc, precio, img) in enumerate(RAMOS, 1):
            _, creado = Ramo.objects.get_or_create(
                nombre=nombre, defaults={"descripcion": desc, "precio": precio, "imagen": I + img, "orden": n})
            nuevos += creado

        # Solo asigna flores a ramos que aún no tienen ninguna (no pisa lo editado en el admin).
        for nombre, flores in FLORES_POR_RAMO.items():
            ramo = Ramo.objects.filter(nombre=nombre).first()
            if ramo and not ramo.flores.exists():
                ramo.flores.set(TipoFlor.objects.filter(nombre__in=flores))

        contacto, creado = Contacto.objects.get_or_create(pk=1, defaults=CONTACTO)
        nuevos += creado
        # Solo rellena campos vacíos; nunca pisa lo que se editó en el admin.
        vacios = [c for c, v in CONTACTO.items() if not getattr(contacto, c)]
        for campo in vacios:
            setattr(contacto, campo, CONTACTO[campo])
        if vacios:
            contacto.save(update_fields=vacios)

        self.stdout.write(self.style.SUCCESS(f"Listo: {nuevos} registro(s) nuevo(s)."))
