from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import EmailLoginView

app_name = "accounts"

urlpatterns = [
    path("ingresar/", EmailLoginView.as_view(), name="login"),
    path("salir/", LogoutView.as_view(), name="logout"),
]
