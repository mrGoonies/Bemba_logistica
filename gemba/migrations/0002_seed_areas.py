from django.db import migrations

AREAS = [
    ("Patio exterior y Bodega 1", "patio-exterior-bodega-1", 1),
    ("Seguridad", "seguridad", 2),
    ("Bodega principal y Despacho", "bodega-principal-despacho", 3),
]


def seed_areas(apps, schema_editor):
    Area = apps.get_model("gemba", "Area")
    for name, slug, order in AREAS:
        Area.objects.get_or_create(slug=slug, defaults={"name": name, "order": order})


def remove_areas(apps, schema_editor):
    Area = apps.get_model("gemba", "Area")
    Area.objects.filter(slug__in=[slug for _, slug, _ in AREAS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("gemba", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_areas, remove_areas),
    ]
