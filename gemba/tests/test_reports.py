from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from gemba.models import Answer, Area, Question, Walk
from gemba.reports import compute_report, week_bounds

User = get_user_model()


class ReportsTestCase(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name="Área Test", slug="area-test", order=1)
        self.other_area = Area.objects.create(name="Otra Área", slug="otra-area", order=2)
        self.question = Question.objects.create(
            area=self.area, text="¿Extintores señalizados?", criterio="Deben estar visibles.", order=1
        )
        self.other_question = Question.objects.create(
            area=self.other_area, text="¿Pasillos despejados?", criterio="Sin obstrucciones.", order=1
        )
        self.operator = User.objects.create_user(
            email="operador@empresa.com", password="clave-segura-123", role=User.Role.OPERADOR, area=self.area
        )

    def make_answer(self, question, day, status):
        walk, _ = Walk.objects.get_or_create(
            area=question.area, date=day, defaults={"operator": self.operator}
        )
        return Answer.objects.create(
            walk=walk,
            question=question,
            status=status,
            photo="fake.jpg" if status == Answer.ResponseStatus.NO_CONFORME else "",
        )

    def test_week_bounds_returns_monday_to_sunday(self):
        wednesday = date(2026, 7, 8)
        start, end = week_bounds(wednesday)
        self.assertEqual(start, date(2026, 7, 6))
        self.assertEqual(end, date(2026, 7, 12))

    def test_identifies_non_conforme_within_range(self):
        monday = date(2026, 7, 6)
        self.make_answer(self.question, monday, Answer.ResponseStatus.NO_CONFORME)

        report = compute_report(*week_bounds(monday))

        self.assertEqual(report.identified, 1)
        self.assertEqual(report.resolved, 0)

    def test_resolved_when_next_answer_is_conforme(self):
        day1 = date(2026, 7, 6)
        day2 = date(2026, 7, 7)
        self.make_answer(self.question, day1, Answer.ResponseStatus.NO_CONFORME)
        self.make_answer(self.question, day2, Answer.ResponseStatus.CONFORME)

        report = compute_report(*week_bounds(day2))

        self.assertEqual(report.resolved, 1)
        self.assertEqual(len(report.open_incidents), 0)

    def test_conforme_without_prior_incident_does_not_count_as_resolved(self):
        day = date(2026, 7, 6)
        self.make_answer(self.question, day, Answer.ResponseStatus.CONFORME)

        report = compute_report(*week_bounds(day))

        self.assertEqual(report.resolved, 0)
        self.assertEqual(report.identified, 0)

    def test_open_incident_tracks_days_since_it_started(self):
        today = date.today()
        started = today - timedelta(days=3)
        self.make_answer(self.question, started, Answer.ResponseStatus.NO_CONFORME)

        report = compute_report(*week_bounds(started))

        self.assertEqual(len(report.open_incidents), 1)
        incident = report.open_incidents[0]
        self.assertEqual(incident.since, started)
        self.assertEqual(incident.days_open, 4)

    def test_breakdown_separates_areas(self):
        day = date(2026, 7, 6)
        self.make_answer(self.question, day, Answer.ResponseStatus.NO_CONFORME)
        self.make_answer(self.other_question, day, Answer.ResponseStatus.PARCIAL)

        report = compute_report(*week_bounds(day))

        by_area = {b.area.id: b for b in report.breakdown}
        self.assertEqual(by_area[self.area.id].identified, 1)
        self.assertEqual(by_area[self.other_area.id].identified, 1)

    def test_area_filter_scopes_report(self):
        day = date(2026, 7, 6)
        self.make_answer(self.question, day, Answer.ResponseStatus.NO_CONFORME)
        self.make_answer(self.other_question, day, Answer.ResponseStatus.NO_CONFORME)

        report = compute_report(*week_bounds(day), area=self.area)

        self.assertEqual(report.identified, 1)
        self.assertEqual(len(report.breakdown), 1)
