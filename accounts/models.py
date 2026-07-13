from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.OPERADOR)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.JEFATURA)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        OPERADOR = "OPERADOR", "Operador"
        JEFATURA = "JEFATURA", "Jefatura"

    username = None
    email = models.EmailField("correo electrónico", unique=True)
    role = models.CharField(
        "rol", max_length=20, choices=Role.choices, default=Role.OPERADOR
    )
    area = models.ForeignKey(
        "gemba.Area",
        verbose_name="área asignada",
        related_name="operadores",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["email"]

    def __str__(self):
        return self.get_full_name() or self.email

    def clean(self):
        super().clean()
        if self.role == self.Role.OPERADOR and self.area_id is None:
            raise ValidationError(
                {"area": "Un operador debe tener un área asignada."}
            )
        if self.role == self.Role.JEFATURA:
            self.area = None

    @property
    def is_operador(self):
        return self.role == self.Role.OPERADOR

    @property
    def is_jefatura(self):
        return self.role == self.Role.JEFATURA
