from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _


class EmailAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget.attrs.update(
            {
                "class": "input",
                "placeholder": "nombre@empresa.com",
                "autofocus": True,
                "autocomplete": "email",
            }
        )
        self.fields["password"].widget.attrs.update(
            {
                "class": "input",
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        )

    error_messages = {
        "invalid_login": _(
            "Correo electrónico o contraseña incorrectos. Verifica tus datos e intenta nuevamente."
        ),
        "inactive": _("Esta cuenta está inactiva."),
    }
