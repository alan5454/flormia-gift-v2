from django.contrib import messages
from django.contrib.auth import login, logout
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Contacto, Favorito, ItemPedido, Pedido, Ramo, TipoFlor

MAX_POR_RAMO = 50

# Valores por defecto si la fila de Contacto aún no los tiene.
DIRECCION = "C. Mexicali 9021, Magisterial, 22470 Tijuana, B.C."
FACEBOOK = "https://www.facebook.com/share/18A2WsrtXo/?mibextid=wwXIfr"
INSTAGRAM = "https://www.instagram.com/flormia_gift?evlk=MWF1ZjA5bnFwbHp0bA=="


# ---------- Utilidades ----------
def _siguiente(request, defecto):
    """URL de retorno segura (campo 'next' del formulario)."""
    destino = request.POST.get("next") or request.GET.get("next") or ""
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return destino
    return defecto


def _catalogo_ramos():
    return f"{reverse('catalogo:catalogo')}#ramos"


def _exigir_sesion(request):
    """Si no hay sesión: redirige a /cuenta/ sin tocar la base de datos."""
    if request.user.is_authenticated:
        return None
    messages.info(request, "Inicia sesión o crea tu cuenta para guardar tus ramos.")
    return redirect(f"{reverse('catalogo:cuenta')}?next={reverse('catalogo:catalogo')}")


def _volver_a_pedidos(request):
    """Tras +1/−1/eliminar: vuelve a donde se hizo la acción (por defecto, Mi cuenta)."""
    return redirect(_siguiente(request, f"{reverse('catalogo:cuenta')}?tab=pedidos"))


def _pedido(usuario):
    return Pedido.objects.get_or_create(usuario=usuario)[0]


def _tocar_pedido(pedido):
    """Cualquier cambio deja el pedido pendiente de confirmar de nuevo."""
    pedido.estado = Pedido.PENDIENTE
    pedido.confirmado_en = None
    pedido.save()


def _agregar_al_pedido(usuario, ramo):
    with transaction.atomic():
        pedido = _pedido(usuario)
        item, creado = ItemPedido.objects.get_or_create(pedido=pedido, ramo=ramo)
        if not creado and item.cantidad < MAX_POR_RAMO:
            ItemPedido.objects.filter(pk=item.pk).update(cantidad=F("cantidad") + 1)
        _tocar_pedido(pedido)


def _volver(request, defecto):
    return redirect(_siguiente(request, defecto))


def _ramo_activo(ramo_id):
    return get_object_or_404(Ramo, pk=ramo_id, activo=True)


def _item_propio(request, item_id):
    return get_object_or_404(ItemPedido, pk=item_id, pedido__usuario=request.user)


# ---------- Pantallas ----------
def inicio(request):
    return render(request, "catalogo/inicio.html", {"seccion": "inicio"})


def catalogo(request):
    favoritos, cantidades = set(), {}
    if request.user.is_authenticated:
        favoritos = set(request.user.favoritos.values_list("ramo_id", flat=True))
        cantidades = dict(
            ItemPedido.objects.filter(pedido__usuario=request.user).values_list("ramo_id", "cantidad")
        )
    ramos = list(Ramo.objects.filter(activo=True))
    for r in ramos:
        r.es_favorito = r.pk in favoritos
        r.en_pedido = cantidades.get(r.pk, 0)
    pedido = Pedido.objects.filter(usuario=request.user).first() if request.user.is_authenticated else None
    items = list(pedido.items.select_related("ramo")) if pedido else []
    return render(request, "catalogo/catalogo.html", {
        "seccion": "catalogo",
        "ramos": ramos,
        "pedido": pedido,
        "items": items,
        "total": sum((i.subtotal for i in items), 0),
        "cantidad_total": sum(i.cantidad for i in items),
        "flores": TipoFlor.objects.filter(activo=True),
    })


def contacto(request):
    datos = Contacto.objects.first()
    return render(request, "catalogo/contacto.html", {
        "seccion": "contacto",
        "contacto": datos,
        "direccion": (datos and datos.direccion) or DIRECCION,
        "facebook": (datos and datos.facebook) or FACEBOOK,
        "instagram": (datos and datos.instagram) or INSTAGRAM,
    })


def cuenta(request):
    if request.user.is_authenticated:
        tab = "pedidos" if request.GET.get("tab") == "pedidos" else "favoritos"
        pedido = Pedido.objects.filter(usuario=request.user).first()
        items = list(pedido.items.select_related("ramo")) if pedido else []
        return render(request, "catalogo/cuenta.html", {
            "seccion": "cuenta",
            "tab": tab,
            "favoritos": request.user.favoritos.select_related("ramo"),
            "pedido": pedido,
            "items": items,
            "total": sum((i.subtotal for i in items), 0),
            "cantidad_total": sum(i.cantidad for i in items),
        })

    form_login, form_registro = AuthenticationForm(request), UserCreationForm()
    if request.method == "POST":
        if request.POST.get("accion") == "registro":
            form_registro = UserCreationForm(request.POST)
            if form_registro.is_valid():
                login(request, form_registro.save())
                messages.success(request, "¡Cuenta creada! Bienvenida a Flormia Gift.")
                return redirect(_siguiente(request, reverse("catalogo:cuenta")))
        else:
            form_login = AuthenticationForm(request, data=request.POST)
            if form_login.is_valid():
                login(request, form_login.get_user())
                return redirect(_siguiente(request, reverse("catalogo:cuenta")))
    return render(request, "catalogo/cuenta.html", {
        "seccion": "cuenta",
        "form_login": form_login,
        "form_registro": form_registro,
        "next": _siguiente(request, ""),
    })


@require_POST
def salir(request):
    logout(request)
    return redirect("catalogo:inicio")


# ---------- Acciones (solo POST) ----------
@require_POST
def favorito_alternar(request, ramo_id):
    if (r := _exigir_sesion(request)):
        return r
    ramo = _ramo_activo(ramo_id)
    favorito, creado = Favorito.objects.get_or_create(usuario=request.user, ramo=ramo)
    if creado:
        messages.success(request, f"{ramo.nombre} se guardó en tus favoritos.")
    else:
        favorito.delete()
        messages.info(request, f"{ramo.nombre} se quitó de tus favoritos.")
    return _volver(request, _catalogo_ramos())


@require_POST
def favorito_quitar(request, ramo_id):
    if (r := _exigir_sesion(request)):
        return r
    Favorito.objects.filter(usuario=request.user, ramo_id=ramo_id).delete()
    messages.info(request, "Ramo quitado de tus favoritos.")
    return _volver(request, reverse("catalogo:cuenta"))


@require_POST
def favorito_a_pedido(request, ramo_id):
    if (r := _exigir_sesion(request)):
        return r
    ramo = _ramo_activo(ramo_id)
    with transaction.atomic():
        _agregar_al_pedido(request.user, ramo)
        Favorito.objects.filter(usuario=request.user, ramo=ramo).delete()
    messages.success(request, f"{ramo.nombre} pasó a tus pedidos.")
    return redirect(f"{reverse('catalogo:cuenta')}?tab=pedidos")


@require_POST
def pedido_agregar(request, ramo_id):
    if (r := _exigir_sesion(request)):
        return r
    ramo = _ramo_activo(ramo_id)
    _agregar_al_pedido(request.user, ramo)
    messages.success(request, f"{ramo.nombre} se añadió a tus pedidos.")
    return _volver(request, _catalogo_ramos())


@require_POST
def item_sumar(request, item_id):
    if (r := _exigir_sesion(request)):
        return r
    item = _item_propio(request, item_id)
    if item.cantidad < MAX_POR_RAMO:
        ItemPedido.objects.filter(pk=item.pk).update(cantidad=F("cantidad") + 1)
        _tocar_pedido(item.pedido)
    return _volver_a_pedidos(request)


@require_POST
def item_restar(request, item_id):
    if (r := _exigir_sesion(request)):
        return r
    item = _item_propio(request, item_id)
    if item.cantidad > 1:
        ItemPedido.objects.filter(pk=item.pk).update(cantidad=F("cantidad") - 1)
    else:
        item.delete()
    _tocar_pedido(item.pedido)
    return _volver_a_pedidos(request)


@require_POST
def item_quitar(request, item_id):
    if (r := _exigir_sesion(request)):
        return r
    item = _item_propio(request, item_id)
    pedido = item.pedido
    item.delete()
    _tocar_pedido(pedido)
    messages.info(request, "Ramo quitado de tus pedidos.")
    return _volver_a_pedidos(request)


class PagoForm(forms.ModelForm):
    forma_pago = forms.ChoiceField(label="Forma de pago", choices=Pedido.FORMAS_PAGO, widget=forms.RadioSelect)
    entrega = forms.ChoiceField(label="Entrega", choices=Pedido.ENTREGAS, widget=forms.RadioSelect)
    direccion_entrega = forms.CharField(
        label="Dirección de entrega", max_length=250, required=False,
        widget=forms.TextInput(attrs={"placeholder": "Calle, número, colonia"}),
    )

    class Meta:
        model = Pedido
        fields = ["forma_pago", "entrega", "direccion_entrega"]

    def clean(self):
        datos = super().clean()
        if datos.get("entrega") == "domicilio" and not (datos.get("direccion_entrega") or "").strip():
            self.add_error("direccion_entrega", "Escribe la dirección para la entrega a domicilio.")
        if datos.get("entrega") == "recoger":
            datos["direccion_entrega"] = ""
        return datos


def pago(request):
    """Espacio de pagos: desglose, forma de pago/entrega y confirmación del pedido."""
    if (r := _exigir_sesion(request)):
        return r
    pedido = Pedido.objects.filter(usuario=request.user).first()
    items = list(pedido.items.select_related("ramo")) if pedido else []
    if not items:
        messages.info(request, "Añade al menos un ramo para ir al espacio de pagos.")
        return redirect(_catalogo_ramos())

    if request.method == "POST":
        form = PagoForm(request.POST, instance=pedido)
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.estado = Pedido.CONFIRMADO
            pedido.confirmado_en = timezone.now()
            pedido.save()
            messages.success(request, "¡Pedido confirmado y guardado!")
            return redirect(f"{reverse('catalogo:cuenta')}?tab=pedidos")
    else:
        form = PagoForm(instance=pedido)
    return render(request, "catalogo/pago.html", {
        "seccion": "catalogo",
        "pedido": pedido,
        "items": items,
        "total": sum((i.subtotal for i in items), 0),
        "cantidad_total": sum(i.cantidad for i in items),
        "form": form,
    })
