from django.urls import path

from . import views

app_name = "gemba"

urlpatterns = [
    path("caminata/", views.WalkTodayView.as_view(), name="hoy"),
    path("caminata/historial/", views.WalkHistoryView.as_view(), name="historial"),
    path("caminata/<int:walk_id>/", views.WalkDetailView.as_view(), name="detalle"),
    path("caminata/<int:walk_id>/finalizar/", views.finalize_walk, name="finalizar"),
    path(
        "caminata/<int:walk_id>/pregunta/<int:question_id>/guardar/",
        views.save_answer,
        name="guardar_respuesta",
    ),
    path("reportes/", views.ReportDashboardView.as_view(), name="reportes"),
    path("preguntas/", views.QuestionListView.as_view(), name="preguntas"),
    path("preguntas/nueva/", views.QuestionCreateView.as_view(), name="pregunta_nueva"),
    path("preguntas/<int:pk>/editar/", views.QuestionUpdateView.as_view(), name="pregunta_editar"),
    path("preguntas/<int:pk>/eliminar/", views.question_delete, name="pregunta_eliminar"),
    path("preguntas/<int:pk>/reactivar/", views.question_reactivate, name="pregunta_reactivar"),
]
