from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path("catalogo/ramo/<int:ramo_id>/", views.detalle_ramo, name="detalle_ramo"),
    path("contacto/", views.contacto, name="contacto"),
    path("cuenta/", views.cuenta, name="cuenta"),
    path("cuenta/salir/", views.salir, name="salir"),
    path("favoritos/<int:ramo_id>/alternar/", views.favorito_alternar, name="favorito_alternar"),
    path("favoritos/<int:ramo_id>/quitar/", views.favorito_quitar, name="favorito_quitar"),
    path("favoritos/<int:ramo_id>/pedir/", views.favorito_a_pedido, name="favorito_a_pedido"),
    path("pedido/<int:ramo_id>/agregar/", views.pedido_agregar, name="pedido_agregar"),
    path("pedido/item/<int:item_id>/sumar/", views.item_sumar, name="item_sumar"),
    path("pedido/item/<int:item_id>/restar/", views.item_restar, name="item_restar"),
    path("pedido/item/<int:item_id>/quitar/", views.item_quitar, name="item_quitar"),
    path("pago/", views.pago, name="pago"),
]
