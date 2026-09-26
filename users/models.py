from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь с email-логином, верификацией и блокировкой."""

    email = models.EmailField(unique=True, verbose_name="Email")
    is_verified = models.BooleanField(default=False, verbose_name="Email подтверждён")
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
