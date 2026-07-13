from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import AnswerForm, QuestionForm
from .mixins import OperatorRequiredMixin, SupervisorRequiredMixin
from .models import Answer, Area, Question, Walk
from .reports import compute_report, week_bounds


def home_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.user.is_jefatura:
        return redirect("gemba:reportes")
    return redirect("gemba:hoy")


class WalkTodayView(OperatorRequiredMixin, TemplateView):
    template_name = "gemba/walk_today.html"

    def get_walk(self):
        walk, _ = Walk.objects.get_or_create(
            area=self.request.user.area,
            date=timezone.localdate(),
            defaults={"operator": self.request.user},
        )
        return walk

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        walk = self.get_walk()
        answers_by_question = {a.question_id: a for a in walk.answers.select_related("question")}
        items = [
            {"question": question, "form": AnswerForm(instance=answers_by_question.get(question.id))}
            for question in walk.active_questions().order_by("order")
        ]
        pending_count = walk.pending_questions_count()
        context.update(
            {
                "walk": walk,
                "items": items,
                "pending_count": pending_count,
                "answered_count": len(items) - pending_count,
            }
        )
        return context


@login_required
def save_answer(request, walk_id, question_id):
    walk = get_object_or_404(Walk, pk=walk_id)
    if not request.user.is_operador or walk.area_id != request.user.area_id:
        raise PermissionDenied
    if request.method != "POST":
        raise PermissionDenied

    question = get_object_or_404(walk.area.questions, pk=question_id, is_active=True)
    instance = Answer.objects.filter(walk=walk, question=question).first() or Answer(
        walk=walk, question=question
    )
    form = AnswerForm(request.POST, request.FILES, instance=instance)

    if form.is_valid():
        answer = form.save(commit=False)
        answer.walk = walk
        answer.question = question
        answer.save()

    walk.refresh_from_db()
    context = {"walk": walk, "question": question, "form": form}
    return render(request, "gemba/partials/_answer_card.html", context)


@login_required
def finalize_walk(request, walk_id):
    walk = get_object_or_404(Walk, pk=walk_id)
    if not request.user.is_operador or walk.area_id != request.user.area_id:
        raise PermissionDenied
    if request.method == "POST":
        if walk.pending_questions_count() == 0:
            walk.status = Walk.Status.COMPLETA
            walk.completed_at = timezone.now()
            walk.save(update_fields=["status", "completed_at"])
            messages.success(request, "Caminata finalizada correctamente.")
        else:
            messages.error(request, "Aún hay preguntas sin responder.")
    return redirect("gemba:hoy")


class WalkHistoryView(OperatorRequiredMixin, ListView):
    template_name = "gemba/walk_history.html"
    context_object_name = "walks"
    paginate_by = 20

    def get_queryset(self):
        return Walk.objects.filter(area=self.request.user.area).order_by("-date")


class WalkDetailView(OperatorRequiredMixin, DetailView):
    model = Walk
    template_name = "gemba/walk_detail.html"
    context_object_name = "walk"
    pk_url_kwarg = "walk_id"

    def get_queryset(self):
        return Walk.objects.filter(area=self.request.user.area)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answers_by_question = {a.question_id: a for a in self.object.answers.select_related("question")}
        context["items"] = [
            {"question": question, "answer": answers_by_question.get(question.id)}
            for question in self.object.active_questions().order_by("order")
        ]
        return context


class QuestionListView(SupervisorRequiredMixin, ListView):
    template_name = "gemba/questions_list.html"
    context_object_name = "areas"

    def get_queryset(self):
        return Area.objects.prefetch_related("questions").all()


class QuestionCreateView(SupervisorRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "gemba/question_form.html"
    success_url = reverse_lazy("gemba:preguntas")

    def get_initial(self):
        initial = super().get_initial()
        area_id = self.request.GET.get("area")
        if area_id:
            initial["area"] = area_id
        return initial


class QuestionUpdateView(SupervisorRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "gemba/question_form.html"
    success_url = reverse_lazy("gemba:preguntas")


@login_required
def question_delete(request, pk):
    if not request.user.is_jefatura:
        raise PermissionDenied
    question = get_object_or_404(Question, pk=pk)
    if request.method == "POST":
        try:
            question.delete()
            messages.success(request, "Pregunta eliminada definitivamente.")
        except ProtectedError:
            question.is_active = False
            question.save(update_fields=["is_active"])
            messages.success(
                request,
                "La pregunta tiene respuestas históricas, así que se desactivó en lugar de eliminarse.",
            )
    return redirect("gemba:preguntas")


@login_required
def question_reactivate(request, pk):
    if not request.user.is_jefatura:
        raise PermissionDenied
    question = get_object_or_404(Question, pk=pk)
    if request.method == "POST":
        question.is_active = True
        question.save(update_fields=["is_active"])
        messages.success(request, "Pregunta reactivada.")
    return redirect("gemba:preguntas")


class ReportDashboardView(SupervisorRequiredMixin, TemplateView):
    template_name = "gemba/reports_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ref_date_str = self.request.GET.get("semana")
        try:
            ref_date = date.fromisoformat(ref_date_str) if ref_date_str else timezone.localdate()
        except ValueError:
            ref_date = timezone.localdate()

        week_start, week_end = week_bounds(ref_date)
        report = compute_report(week_start, week_end)

        max_bar_value = max(
            [1] + [b.identified for b in report.breakdown] + [b.resolved for b in report.breakdown]
        )

        context.update(
            {
                "report": report,
                "week_start": week_start,
                "week_end": week_end,
                "is_current_week": week_bounds(timezone.localdate()) == (week_start, week_end),
                "prev_week": week_start - timedelta(days=7),
                "next_week": week_start + timedelta(days=7),
                "max_bar_value": max_bar_value,
                "total_open": len(report.open_incidents),
            }
        )
        return context
