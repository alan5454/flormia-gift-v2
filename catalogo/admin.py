from django.contrib import admin

from .models import Contacto, Favorito, ItemPedido, Pedido, Ramo, TipoFlor


@admin.register(TipoFlor)
class TipoFlorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion", "orden", "activo")
    list_editable = ("orden", "activo")


@admin.register(Ramo)
class RamoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio", "orden", "activo")
    list_editable = ("precio", "orden", "activo")
    list_filter = ("activo",)


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ("direccion", "telefono", "whatsapp", "facebook", "instagram")


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "ramo", "creado")
    list_filter = ("ramo",)
    search_fields = ("usuario__username", "ramo__nombre")


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "estado", "forma_pago", "entrega", "cantidad_total", "total", "actualizado")
    list_filter = ("estado", "forma_pago", "entrega")
    search_fields = ("usuario__username",)
    inlines = [ItemPedidoInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "ramo", "cantidad")
