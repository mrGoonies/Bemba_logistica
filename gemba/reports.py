from dataclasses import dataclass, field
from datetime import date, timedelta

from django.utils import timezone

from .models import Answer, Area, Question

OPEN_STATUSES = {Answer.ResponseStatus.NO_CONFORME, Answer.ResponseStatus.PARCIAL}


def week_bounds(for_date: date) -> tuple[date, date]:
    monday = for_date - timedelta(days=for_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


@dataclass
class AreaBreakdown:
    area: Area
    identified: int = 0
    resolved: int = 0


@dataclass
class OpenIncident:
    question: Question
    area: Area
    status: str
    since: date
    days_open: int


@dataclass
class Report:
    start: date
    end: date
    identified: int = 0
    resolved: int = 0
    breakdown: list = field(default_factory=list)
    open_incidents: list = field(default_factory=list)


def compute_report(start: date, end: date, area: Area | None = None) -> Report:
    """Calcula identificadas/solucionadas en [start, end] e incidencias abiertas a hoy.

    Una respuesta No conforme/Parcial se considera "solucionada" cuando, para la
    misma pregunta, la siguiente respuesta registrada (en orden cronológico) es
    Conforme. No existe un estado de resolución persistido: se infiere recorriendo
    la secuencia de respuestas de cada pregunta.
    """
    questions = Question.objects.select_related("area")
    if area is not None:
        questions = questions.filter(area=area)

    report = Report(start=start, end=end)
    breakdown_by_area = {}
    open_incidents = []
    today = timezone.localdate()

    for question in questions:
        answers = list(
            Answer.objects.filter(question=question)
            .select_related("walk")
            .order_by("walk__date")
        )
        area_breakdown = breakdown_by_area.setdefault(
            question.area_id, AreaBreakdown(area=question.area)
        )

        prev_status = None
        streak_start = None
        for answer in answers:
            answer_date = answer.walk.date
            if answer.status in OPEN_STATUSES:
                if prev_status not in OPEN_STATUSES:
                    streak_start = answer_date
                if start <= answer_date <= end:
                    report.identified += 1
                    area_breakdown.identified += 1
            else:
                if prev_status in OPEN_STATUSES and start <= answer_date <= end:
                    report.resolved += 1
                    area_breakdown.resolved += 1
            prev_status = answer.status

        if answers and answers[-1].status in OPEN_STATUSES:
            open_incidents.append(
                OpenIncident(
                    question=question,
                    area=question.area,
                    status=answers[-1].status,
                    since=streak_start,
                    days_open=(today - streak_start).days + 1,
                )
            )

    report.breakdown = sorted(breakdown_by_area.values(), key=lambda b: b.area.order)
    report.open_incidents = sorted(open_incidents, key=lambda i: -i.days_open)
    return report
