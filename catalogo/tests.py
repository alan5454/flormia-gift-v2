from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Contacto, Favorito, ItemPedido, Pedido, Ramo, TipoFlor

User = get_user_model()


class Base(TestCase):
    def get(self, nombre, **kw):
        return self.client.get(reverse(f"catalogo:{nombre}"), secure=True, **kw)

    def post(self, nombre, args=None, data=None):
        return self.client.post(reverse(f"catalogo:{nombre}", args=args), data or {}, secure=True)


class PantallasTests(Base):
    def test_carga_idempotente(self):
        call_command("cargar_datos")
        call_command("cargar_datos")
        self.assertEqual((TipoFlor.objects.count(), Ramo.objects.count(), Contacto.objects.count()), (9, 7, 1))

    def test_pantallas_individuales(self):
        call_command("cargar_datos")
        r = self.get("inicio")
        self.assertContains(r, "Convierte un día ordinario")
        self.assertNotContains(r, "Ramo Dulce Amanecer")
        r = self.get("catalogo")
        for t in ("Ramo Dulce Amanecer", "Ramo Ternura", "Gerberas", "Ramos disponibles", "Flores disponibles"):
            self.assertContains(r, t)
        r = self.get("contacto")
        for t in ("C. Mexicali 9021, Magisterial, 22470 Tijuana, B.C.", "facebook.com/share/18A2WsrtXo", "instagram.com/flormia_gift"):
            self.assertContains(r, t)
        self.assertContains(self.get("cuenta"), "Crear cuenta nueva")

    def test_nav_cambia_con_sesion(self):
        self.assertContains(self.get("inicio"), "Iniciar sesión")
        User.objects.create_user("ana", password="x-Segura-123")
        self.client.login(username="ana", password="x-Segura-123")
        self.assertContains(self.get("inicio"), "Mi cuenta")


class SesionTests(Base):
    def setUp(self):
        call_command("cargar_datos")
        self.ramo = Ramo.objects.first()

    def test_anonimo_redirige_y_no_guarda(self):
        for nombre in ("favorito_alternar", "pedido_agregar"):
            r = self.post(nombre, [self.ramo.pk])
            self.assertEqual(r.status_code, 302)
            self.assertTrue(r["Location"].startswith(reverse("catalogo:cuenta")))
        self.assertEqual((Favorito.objects.count(), Pedido.objects.count(), ItemPedido.objects.count()), (0, 0, 0))

    def test_registro_y_login(self):
        r = self.post("cuenta", data={"accion": "registro", "username": "luz",
                                      "password1": "Flor-segura-2026", "password2": "Flor-segura-2026"})
        self.assertEqual(r.status_code, 302)
        self.assertContains(self.get("cuenta"), "Hola, luz")
        self.post("salir")
        r = self.post("cuenta", data={"accion": "login", "username": "luz", "password": "Flor-segura-2026"})
        self.assertEqual(r.status_code, 302)

    def test_login_incorrecto(self):
        r = self.post("cuenta", data={"accion": "login", "username": "no", "password": "no"})
        self.assertEqual(r.status_code, 200)


class UsuarioTests(Base):
    def setUp(self):
        call_command("cargar_datos")
        self.user = User.objects.create_user("ana", password="x-Segura-123")
        self.client.login(username="ana", password="x-Segura-123")
        self.ramo = Ramo.objects.first()

    def test_favoritos(self):
        self.post("favorito_alternar", [self.ramo.pk])
        self.assertEqual(Favorito.objects.filter(usuario=self.user).count(), 1)
        self.assertContains(self.get("cuenta"), self.ramo.nombre)
        self.post("favorito_alternar", [self.ramo.pk])
        self.assertEqual(Favorito.objects.count(), 0)

    def test_pedido_sumar_restar_quitar_confirmar(self):
        self.post("pedido_agregar", [self.ramo.pk])
        self.post("pedido_agregar", [self.ramo.pk])
        item = ItemPedido.objects.get()
        self.assertEqual(item.cantidad, 2)
        self.post("item_sumar", [item.pk])
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 3)
        self.post("item_restar", [item.pk])
        item.refresh_from_db()
        self.assertEqual(item.cantidad, 2)
        r = self.client.get(reverse("catalogo:cuenta") + "?tab=pedidos", secure=True)
        self.assertContains(r, "Ir al espacio de pagos")
        self.post("pago", data={"forma_pago": "efectivo", "entrega": "recoger"})
        self.assertEqual(Pedido.objects.get().estado, Pedido.CONFIRMADO)
        self.post("item_sumar", [item.pk])
        self.assertEqual(Pedido.objects.get().estado, Pedido.PENDIENTE)
        self.post("item_quitar", [item.pk])
        self.assertEqual(ItemPedido.objects.count(), 0)

    def test_restar_a_cero_elimina(self):
        self.post("pedido_agregar", [self.ramo.pk])
        self.post("item_restar", [ItemPedido.objects.get().pk])
        self.assertEqual(ItemPedido.objects.count(), 0)

    def test_favorito_a_pedido(self):
        self.post("favorito_alternar", [self.ramo.pk])
        self.post("favorito_a_pedido", [self.ramo.pk])
        self.assertEqual((Favorito.objects.count(), ItemPedido.objects.count()), (0, 1))

    def test_no_toca_items_ajenos(self):
        otro = User.objects.create_user("otro", password="x-Segura-123")
        p = Pedido.objects.create(usuario=otro)
        item = ItemPedido.objects.create(pedido=p, ramo=self.ramo)
        self.assertEqual(self.post("item_sumar", [item.pk]).status_code, 404)

    def test_get_no_permitido(self):
        r = self.client.get(reverse("catalogo:pedido_agregar", args=[self.ramo.pk]), secure=True)
        self.assertEqual(r.status_code, 405)


class CatalogoPedidoYPagoTests(Base):
    def setUp(self):
        call_command("cargar_datos")
        self.user = User.objects.create_user("ana", password="x-Segura-123")
        self.ramo = Ramo.objects.first()

    def entrar(self):
        self.client.login(username="ana", password="x-Segura-123")

    def test_panel_sin_sesion_y_boton_pago_deshabilitado(self):
        r = self.get("catalogo")
        self.assertContains(r, "Tu pedido")
        self.assertContains(r, "Inicia sesión para añadir ramos")
        self.assertContains(r, "disabled>Ir al espacio de pagos")
        self.assertNotContains(r, reverse("catalogo:pago"))

    def test_nav_solo_cuatro_enlaces(self):
        r = self.get("catalogo")
        nav = r.content.decode().split("<nav")[1].split("</nav>")[0]
        self.assertEqual(nav.count("<a "), 4)

    def test_panel_en_catalogo_con_acciones_y_retorno(self):
        self.entrar()
        self.assertContains(self.get("catalogo"), "Aún no has añadido ramos")
        destino = reverse("catalogo:catalogo") + "#ramos"
        r = self.post("pedido_agregar", [self.ramo.pk])
        self.assertEqual(r["Location"], destino)
        r = self.get("catalogo")
        self.assertContains(r, "Eliminar")
        self.assertContains(r, 'href="%s">Ir al espacio de pagos' % reverse("catalogo:pago"))
        item = ItemPedido.objects.get()
        for nombre, cantidad in (("item_sumar", 2), ("item_restar", 1)):
            r = self.client.post(reverse(f"catalogo:{nombre}", args=[item.pk]), {"next": destino}, secure=True)
            self.assertEqual(r["Location"], destino)
            item.refresh_from_db()
            self.assertEqual(item.cantidad, cantidad)
        r = self.client.post(reverse("catalogo:item_quitar", args=[item.pk]), {"next": destino}, secure=True)
        self.assertEqual(r["Location"], destino)
        self.assertEqual(ItemPedido.objects.count(), 0)

    def test_next_externo_se_ignora(self):
        self.entrar()
        self.post("pedido_agregar", [self.ramo.pk])
        item = ItemPedido.objects.get()
        r = self.client.post(reverse("catalogo:item_sumar", args=[item.pk]), {"next": "https://malo.example/"}, secure=True)
        self.assertEqual(r["Location"], reverse("catalogo:cuenta") + "?tab=pedidos")

    def test_pago_sin_sesion_redirige_y_no_guarda(self):
        r = self.get("pago")
        self.assertTrue(r["Location"].startswith(reverse("catalogo:cuenta")))
        r = self.post("pago", data={"forma_pago": "efectivo", "entrega": "recoger"})
        self.assertTrue(r["Location"].startswith(reverse("catalogo:cuenta")))
        self.assertEqual(Pedido.objects.count(), 0)

    def test_pago_vacio_regresa_al_catalogo(self):
        self.entrar()
        r = self.get("pago")
        self.assertEqual(r["Location"], reverse("catalogo:catalogo") + "#ramos")

    def test_pago_desglose_y_confirmacion(self):
        self.entrar()
        self.post("pedido_agregar", [self.ramo.pk])
        self.post("pedido_agregar", [self.ramo.pk])
        r = self.get("pago")
        self.assertContains(r, "Espacio de pagos")
        self.assertContains(r, self.ramo.nombre)
        self.assertContains(r, "Total a pagar")
        self.assertContains(r, "Transferencia bancaria")
        self.assertContains(r, "Confirmar y guardar pedido")
        # Datos incompletos: no confirma.
        self.post("pago", data={"forma_pago": "efectivo"})
        self.assertEqual(Pedido.objects.get().estado, Pedido.PENDIENTE)
        # Domicilio exige dirección.
        r = self.post("pago", data={"forma_pago": "efectivo", "entrega": "domicilio"})
        self.assertContains(r, "Escribe la dirección")
        self.assertEqual(Pedido.objects.get().estado, Pedido.PENDIENTE)
        # Confirmación válida.
        r = self.post("pago", data={"forma_pago": "transferencia", "entrega": "domicilio",
                                    "direccion_entrega": "Calle 1, Centro"})
        self.assertEqual(r.status_code, 302)
        p = Pedido.objects.get()
        self.assertEqual((p.estado, p.forma_pago, p.entrega, p.direccion_entrega),
                         (Pedido.CONFIRMADO, "transferencia", "domicilio", "Calle 1, Centro"))
        self.assertIsNotNone(p.confirmado_en)
        self.assertEqual(p.total, self.ramo.precio * 2)
