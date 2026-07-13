from django.contrib.auth.views import LoginView

from .forms import EmailAuthenticationForm


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True
