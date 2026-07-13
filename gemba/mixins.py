from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class OperatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_operador


class SupervisorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_jefatura
