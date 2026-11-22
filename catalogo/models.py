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
    CLASICO, TEMPORADA = "clasico", "temporada"
    CATEGORIAS = [(CLASICO, "Clásico"), (TEMPORADA, "De temporada / especial")]
    categoria = models.CharField(max_length=10, choices=CATEGORIAS, default=CLASICO)
    precio = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta(ConImagen.Meta):
        ordering = ["categoria", "orden", "nombre"]


class Arreglo(ConImagen):
    precio = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta(ConImagen.Meta):
        verbose_name = "arreglo / diseño"
        verbose_name_plural = "arreglos y diseños"


class Extra(Ordenable):
    """Complemento con precio adicional (tarjeta, globo, peluche...)."""
    icono = models.CharField(max_length=10, blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)


class Contacto(models.Model):
    """Una sola fila con los datos de la florería."""
    telefono = models.CharField(max_length=40, blank=True)
    whatsapp = models.CharField("WhatsApp (con lada, ej. 5216640000000)", max_length=40, blank=True)
    redes = models.CharField("redes sociales", max_length=200, blank=True)
    direccion = models.CharField("dirección", max_length=250, blank=True)

    def __str__(self):
        return "Datos de contacto"
