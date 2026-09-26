from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from users.models import User
from users.tokens import email_verification_token


class UserRegisterForm(UserCreationForm):
    """Форма регистрации с отправкой письма подтверждения."""

    class Meta:
        model = User
        fields = ["email", "username", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        if commit:
            user.save()
            self._send_verification_email(user)
        return user

    def _send_verification_email(self, user):
        """Отправляет письмо со ссылкой подтверждения email."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        verification_url = f"http://127.0.0.1:8000/users/verify/{uid}/{token}/"
        send_mail(
            subject="Подтвердите ваш email",
            message=f"Перейдите по ссылке для подтверждения: {verification_url}",
            from_email=settings.EMAIL_FROM,
            recipient_list=[user.email],
        )


class UserUpdateForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = User
        fields = ["username", "phone", "avatar"]
