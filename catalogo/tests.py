from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Arreglo, Contacto, Extra, Ramo, TipoFlor


class CatalogoTests(TestCase):
    def pagina(self):
        return self.client.get(reverse("catalogo:inicio"), secure=True)

    def test_pagina_con_base_vacia(self):
        r = self.pagina()
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Convierte un día ordinario")

    def test_carga_idempotente_y_pagina(self):
        call_command("cargar_datos")
        call_command("cargar_datos")
        self.assertEqual(
            (TipoFlor.objects.count(), Ramo.objects.count(), Arreglo.objects.count(),
             Extra.objects.count(), Contacto.objects.count()),
            (6, 6, 4, 5, 1),
        )
        r = self.pagina()
        for texto in ("Ramo Dulce Amanecer", "Caja Floral Suave", 'data-precio="450.00"'):
            self.assertContains(r, texto)

    def test_imagen_inexistente_no_rompe(self):
        Ramo.objects.create(nombre="X", precio=10, imagen="catalogo/img/no-existe.png")
        self.assertEqual(self.pagina().status_code, 200)
