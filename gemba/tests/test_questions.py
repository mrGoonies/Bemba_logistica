from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from gemba.models import Answer, Area, Question, Walk

User = get_user_model()


class QuestionManagementTestCase(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name="Área Test", slug="area-test", order=1)
        self.question = Question.objects.create(
            area=self.area, text="¿Extintores señalizados?", criterio="Deben estar visibles.", order=1
        )
        self.jefatura = User.objects.create_user(
            email="jefatura@empresa.com", password="clave-segura-123", role=User.Role.JEFATURA
        )
        self.operator = User.objects.create_user(
            email="operador@empresa.com", password="clave-segura-123", role=User.Role.OPERADOR, area=self.area
        )

    def test_operador_cannot_access_question_list(self):
        self.client.force_login(self.operator)
        response = self.client.get(reverse("gemba:preguntas"))
        self.assertEqual(response.status_code, 403)

    def test_jefatura_can_list_questions(self):
        self.client.force_login(self.jefatura)
        response = self.client.get(reverse("gemba:preguntas"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "¿Extintores señalizados?")

    def test_jefatura_can_create_question(self):
        self.client.force_login(self.jefatura)
        response = self.client.post(
            reverse("gemba:pregunta_nueva"),
            {
                "area": self.area.id,
                "text": "¿Pasillos despejados?",
                "criterio": "Sin obstrucciones.",
                "order": 2,
            },
        )
        self.assertRedirects(response, reverse("gemba:preguntas"))
        self.assertTrue(Question.objects.filter(text="¿Pasillos despejados?").exists())

    def test_jefatura_can_edit_question(self):
        self.client.force_login(self.jefatura)
        response = self.client.post(
            reverse("gemba:pregunta_editar", args=[self.question.id]),
            {
                "area": self.area.id,
                "text": "¿Extintores señalizados y vigentes?",
                "criterio": self.question.criterio,
                "order": self.question.order,
            },
        )
        self.assertRedirects(response, reverse("gemba:preguntas"))
        self.question.refresh_from_db()
        self.assertEqual(self.question.text, "¿Extintores señalizados y vigentes?")

    def test_delete_without_answers_removes_question(self):
        self.client.force_login(self.jefatura)
        response = self.client.post(reverse("gemba:pregunta_eliminar", args=[self.question.id]))
        self.assertRedirects(response, reverse("gemba:preguntas"))
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())

    def test_delete_with_answers_deactivates_instead_of_deleting(self):
        walk = Walk.objects.create(area=self.area, operator=self.operator)
        Answer.objects.create(walk=walk, question=self.question, status=Answer.ResponseStatus.CONFORME)

        self.client.force_login(self.jefatura)
        response = self.client.post(reverse("gemba:pregunta_eliminar", args=[self.question.id]))

        self.assertRedirects(response, reverse("gemba:preguntas"))
        self.question.refresh_from_db()
        self.assertFalse(self.question.is_active)

    def test_jefatura_can_reactivate_question(self):
        self.question.is_active = False
        self.question.save(update_fields=["is_active"])

        self.client.force_login(self.jefatura)
        response = self.client.post(reverse("gemba:pregunta_reactivar", args=[self.question.id]))

        self.assertRedirects(response, reverse("gemba:preguntas"))
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_active)

    def test_operador_cannot_delete_question(self):
        self.client.force_login(self.operator)
        response = self.client.post(reverse("gemba:pregunta_eliminar", args=[self.question.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Question.objects.filter(id=self.question.id).exists())
