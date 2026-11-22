from django.db import migrations


def ordenar_ramos(apps, schema_editor):
    """Orden de visualización de los ramos que ya existían (antes iban por categoría)."""
    Ramo = apps.get_model("catalogo", "Ramo")
    nombres = ["Ramo Dulce Amanecer", "Ramo Pureza", "Ramo Campo Fresco",
               "Ramo Primavera", "Ramo Lavanda y Luz", "Ramo Gran Detalle"]
    for n, nombre in enumerate(nombres, 1):
        Ramo.objects.filter(nombre=nombre).update(orden=n)


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0002_favoritos_pedidos"),
    ]

    operations = [
        migrations.RunPython(ordenar_ramos, migrations.RunPython.noop),
    ]
