import io
import random
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from gemba.models import Answer, Area, Question, Walk

QUESTIONS_BY_AREA_SLUG = {
    "patio-exterior-bodega-1": [
        (
            "¿El patio exterior está libre de obstáculos y residuos?",
            "Los pasillos de circulación de vehículos y peatones deben estar despejados, sin material acumulado ni charcos.",
        ),
        (
            "¿La mercadería está apilada y estibada correctamente?",
            "Las estibas no deben superar la altura máxima permitida ni presentar riesgo de volcamiento.",
        ),
        (
            "¿La señalización de tránsito interno es visible?",
            "Líneas de circulación, topes y señaléticas de velocidad máxima deben estar pintadas y legibles.",
        ),
        (
            "¿Los operadores usan el EPP correspondiente?",
            "Chaleco reflectante, casco y calzado de seguridad son obligatorios en el patio.",
        ),
        (
            "¿La iluminación exterior funciona correctamente?",
            "Todos los focos del patio y bodega 1 deben estar operativos, sin zonas oscuras.",
        ),
    ],
    "seguridad": [
        (
            "¿Los extintores están señalizados, vigentes y accesibles?",
            "Deben tener carga vigente, estar despejados en un radio de 1 metro y con señalética visible.",
        ),
        (
            "¿Las vías de evacuación están despejadas?",
            "Pasillos, salidas de emergencia y puntos de encuentro no deben tener obstrucciones.",
        ),
        (
            "¿El control de acceso registra correctamente a visitas y personal?",
            "Todo ingreso debe quedar registrado con nombre, hora y motivo de la visita.",
        ),
        (
            "¿Las cámaras de vigilancia están operativas?",
            "Todas las cámaras del circuito cerrado deben estar grabando y con buena visibilidad.",
        ),
        (
            "¿El personal de seguridad cuenta con su equipo de comunicación?",
            "Radios cargadas y operativas para cada turno de guardia.",
        ),
    ],
    "bodega-principal-despacho": [
        (
            "¿Los productos están almacenados según su clasificación?",
            "Debe respetarse la zonificación por tipo de producto, rotación FIFO y compatibilidad de almacenaje.",
        ),
        (
            "¿El área de despacho está ordenada y libre de obstrucciones?",
            "Los pallets en tránsito no deben bloquear pasillos ni zonas de carga.",
        ),
        (
            "¿La documentación de despacho está completa y visible?",
            "Guías de despacho, checklists de carga y rotulados deben estar disponibles antes de cada envío.",
        ),
        (
            "¿Los equipos de manejo de materiales están en buen estado?",
            "Grúas horquilla y transpaletas deben tener mantención vigente y sin daños visibles.",
        ),
        (
            "¿Se respeta la segregación de residuos en bodega?",
            "Contenedores de reciclaje, cartón y residuos generales deben estar rotulados y sin mezclar.",
        ),
    ],
}

STATUS_WEIGHTS = [
    (Answer.ResponseStatus.CONFORME, 0.72),
    (Answer.ResponseStatus.PARCIAL, 0.18),
    (Answer.ResponseStatus.NO_CONFORME, 0.10),
]


class Command(BaseCommand):
    help = "Crea usuarios, preguntas y caminatas de ejemplo para probar la app."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias-historial",
            type=int,
            default=21,
            help="Cantidad de días hacia atrás para generar caminatas de ejemplo.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)

        supervisor = self._create_user(
            email="jefatura@caminata.demo",
            password="jefatura123",
            first_name="Jefatura",
            last_name="Logística",
            role=User.Role.JEFATURA,
            area=None,
        )

        operators = {}
        for area in Area.objects.all():
            local_part = area.slug.replace("-", ".")
            operator = self._create_user(
                email=f"{local_part}@caminata.demo",
                password="operador123",
                first_name="Operador",
                last_name=area.name,
                role=User.Role.OPERADOR,
                area=area,
            )
            operators[area.slug] = operator
            self._seed_questions(area)

        self._seed_history(operators, days=options["dias_historial"])

        self.stdout.write(self.style.SUCCESS("Datos de ejemplo creados."))
        self.stdout.write("\nCredenciales de acceso:")
        self.stdout.write(f"  Jefatura:  {supervisor.email} / jefatura123")
        for slug, operator in operators.items():
            self.stdout.write(f"  Operador ({operator.area.name}): {operator.email} / operador123")

    def _create_user(self, email, password, **fields):
        user, created = User.objects.get_or_create(email=email, defaults=fields)
        if created:
            user.set_password(password)
            user.save()
        return user

    def _seed_questions(self, area):
        for order, (text, criterio) in enumerate(QUESTIONS_BY_AREA_SLUG.get(area.slug, []), start=1):
            Question.objects.get_or_create(
                area=area,
                text=text,
                defaults={"criterio": criterio, "order": order},
            )

    def _placeholder_photo(self, label):
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (480, 320), color="#00694C")
        draw = ImageDraw.Draw(image)
        draw.rectangle([10, 10, 470, 310], outline="#FFFFFF", width=3)
        draw.multiline_text((30, 140), f"Evidencia demo\n{label}", fill="#FFFFFF")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        return ContentFile(buffer.getvalue(), name=f"demo_{label}.jpg")

    def _seed_history(self, operators, days):
        today = timezone.localdate()
        for area_slug, operator in operators.items():
            area = operator.area
            questions = list(area.questions.filter(is_active=True))
            if not questions:
                continue
            for offset in range(days, 0, -1):
                day = today - timedelta(days=offset)
                walk, _ = Walk.objects.get_or_create(
                    area=area, date=day, defaults={"operator": operator}
                )
                for question in questions:
                    status = random.choices(
                        [s for s, _ in STATUS_WEIGHTS],
                        weights=[w for _, w in STATUS_WEIGHTS],
                    )[0]
                    photo = None
                    if status == Answer.ResponseStatus.NO_CONFORME:
                        photo = self._placeholder_photo(f"{question.id}_{day}")
                    elif status == Answer.ResponseStatus.PARCIAL and random.random() < 0.4:
                        photo = self._placeholder_photo(f"{question.id}_{day}")

                    answer, _ = Answer.objects.get_or_create(
                        walk=walk,
                        question=question,
                        defaults={"status": status},
                    )
                    if photo:
                        answer.photo.save(photo.name, photo, save=False)
                    answer.save()
                walk.mark_complete_if_ready()
