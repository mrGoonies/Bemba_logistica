import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Area(models.Model):
    name = models.CharField("nombre", max_length=100, unique=True)
    slug = models.SlugField("slug", max_length=100, unique=True)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "área"
        verbose_name_plural = "áreas"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Question(models.Model):
    area = models.ForeignKey(
        Area, verbose_name="área", related_name="questions", on_delete=models.CASCADE
    )
    text = models.CharField("pregunta", max_length=255)
    criterio = models.TextField(
        "criterio",
        help_text="Contexto que explica al operador qué se evalúa en esta pregunta.",
    )
    order = models.PositiveSmallIntegerField("orden", default=0)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "pregunta"
        verbose_name_plural = "preguntas"
        ordering = ["area__order", "order", "id"]

    def __str__(self):
        return f"[{self.area.name}] {self.text}"


class Walk(models.Model):
    class Status(models.TextChoices):
        EN_PROGRESO = "EN_PROGRESO", "En progreso"
        COMPLETA = "COMPLETA", "Completa"

    area = models.ForeignKey(
        Area, verbose_name="área", related_name="walks", on_delete=models.PROTECT
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="operador",
        related_name="walks",
        on_delete=models.PROTECT,
    )
    date = models.DateField("fecha", default=timezone.localdate)
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.EN_PROGRESO
    )
    created_at = models.DateTimeField("creada", auto_now_add=True)
    completed_at = models.DateTimeField("completada", null=True, blank=True)

    class Meta:
        verbose_name = "caminata"
        verbose_name_plural = "caminatas"
        ordering = ["-date", "area__order"]
        constraints = [
            models.UniqueConstraint(fields=["area", "date"], name="una_caminata_por_area_dia")
        ]

    def __str__(self):
        return f"{self.area.name} - {self.date}"

    @property
    def is_complete(self):
        return self.status == self.Status.COMPLETA

    def active_questions(self):
        return self.area.questions.filter(is_active=True)

    def pending_questions_count(self):
        answered_ids = self.answers.values_list("question_id", flat=True)
        return self.active_questions().exclude(id__in=answered_ids).count()

    def mark_complete_if_ready(self):
        if self.pending_questions_count() == 0 and self.status != self.Status.COMPLETA:
            self.status = self.Status.COMPLETA
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at"])
            return True
        return False


def answer_photo_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    walk = instance.walk
    return (
        f"caminatas/{walk.area.slug}/{walk.date:%Y/%m}/"
        f"{walk.date:%d}_{instance.question_id}_{uuid.uuid4().hex[:8]}.{ext}"
    )


class Answer(models.Model):
    class ResponseStatus(models.TextChoices):
        CONFORME = "CONFORME", "Conforme"
        NO_CONFORME = "NO_CONFORME", "No conforme"
        PARCIAL = "PARCIAL", "Parcial"

    walk = models.ForeignKey(
        Walk, verbose_name="caminata", related_name="answers", on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        Question, verbose_name="pregunta", related_name="answers", on_delete=models.PROTECT
    )
    status = models.CharField(
        "respuesta", max_length=20, choices=ResponseStatus.choices
    )
    comment = models.TextField("comentario", blank=True)
    photo = models.ImageField(
        "fotografía", upload_to=answer_photo_path, null=True, blank=True
    )
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"
        ordering = ["question__order"]
        constraints = [
            models.UniqueConstraint(fields=["walk", "question"], name="una_respuesta_por_pregunta")
        ]

    def __str__(self):
        return f"{self.question} -> {self.get_status_display()}"

    def clean(self):
        super().clean()
        if self.status == self.ResponseStatus.NO_CONFORME and not self.photo:
            raise ValidationError(
                {"photo": "La fotografía es obligatoria cuando la respuesta es No conforme."}
            )
