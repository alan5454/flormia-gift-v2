from decimal import Decimal

from django.conf import settings
from django.db import models
from django.templatetags.static import static

IMAGEN_POR_DEFECTO = "catalogo/img/flor-rosa.svg"


class Ordenable(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    orden = models.PositiveSmallIntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class ConImagen(Ordenable):
    descripcion = models.CharField(max_length=200, blank=True)
    # Ruta dentro de static/ (ej. "catalogo/img/flor-rosa.svg") o URL completa.
    imagen = models.CharField(max_length=300, blank=True)

    class Meta(Ordenable.Meta):
        abstract = True

    @property
    def imagen_url(self):
        """URL de la imagen; si falta o no existe, usa la imagen por defecto."""
        ruta = self.imagen or IMAGEN_POR_DEFECTO
        if ruta.startswith(("http://", "https://")):
            return ruta
        try:
            return static(ruta)
        except ValueError:
            return static(IMAGEN_POR_DEFECTO)


class TipoFlor(ConImagen):
    class Meta(ConImagen.Meta):
        verbose_name = "tipo de flor"
        verbose_name_plural = "tipos de flores"


class Ramo(ConImagen):
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    flores = models.ManyToManyField(TipoFlor, blank=True, related_name="ramos", verbose_name="flores que contiene")


class Contacto(models.Model):
    """Una sola fila con los datos de la florería."""
    telefono = models.CharField(max_length=40, blank=True)
    whatsapp = models.CharField("WhatsApp (con lada, ej. 5216640000000)", max_length=40, blank=True)
    redes = models.CharField("redes sociales", max_length=200, blank=True)
    direccion = models.CharField("dirección", max_length=250, blank=True)
    facebook = models.URLField(max_length=300, blank=True)
    instagram = models.URLField(max_length=300, blank=True)

    def __str__(self):
        return "Datos de contacto"


class Favorito(models.Model):
    """Ramo que le gustó a un usuario."""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favoritos")
    ramo = models.ForeignKey(Ramo, on_delete=models.CASCADE, related_name="favoritos")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        constraints = [models.UniqueConstraint(fields=["usuario", "ramo"], name="favorito_unico")]

    def __str__(self):
        return f"{self.usuario} ♥ {self.ramo}"


class Pedido(models.Model):
    """Lista de ramos pedidos por un usuario (una por usuario)."""
    PENDIENTE, CONFIRMADO = "pendiente", "confirmado"
    ESTADOS = [(PENDIENTE, "Pendiente de confirmar"), (CONFIRMADO, "Confirmado")]
    FORMAS_PAGO = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia bancaria"),
        ("tarjeta", "Tarjeta (terminal al recoger o entregar)"),
    ]
    ENTREGAS = [("recoger", "Recoger en la florería"), ("domicilio", "Entrega a domicilio")]

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedido")
    estado = models.CharField(max_length=10, choices=ESTADOS, default=PENDIENTE)
    actualizado = models.DateTimeField(auto_now=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)
    forma_pago = models.CharField("forma de pago", max_length=15, choices=FORMAS_PAGO, blank=True)
    entrega = models.CharField(max_length=10, choices=ENTREGAS, blank=True)
    direccion_entrega = models.CharField("dirección de entrega", max_length=250, blank=True)

    def __str__(self):
        return f"Pedido de {self.usuario} ({self.get_estado_display()})"

    @property
    def total(self):
        return sum((i.subtotal for i in self.items.all()), Decimal("0"))

    @property
    def cantidad_total(self):
        return sum(i.cantidad for i in self.items.all())


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    ramo = models.ForeignKey(Ramo, on_delete=models.CASCADE, related_name="items_pedido")
    cantidad = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["pedido", "ramo"], name="item_unico_por_pedido")]

    def __str__(self):
        return f"{self.cantidad} × {self.ramo}"

    @property
    def subtotal(self):
        return self.ramo.precio * self.cantidad
