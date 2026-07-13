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
]
