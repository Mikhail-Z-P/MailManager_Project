from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import CreateView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from users.forms import UserRegisterForm, UserUpdateForm
from users.models import User
from users.tokens import email_verification_token


class RegisterView(CreateView):
    """Регистрация нового пользователя с подтверждением email."""
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")


class UserLoginView(LoginView):
    """Вход в систему по email."""
    template_name = "users/login.html"


class UserLogoutView(LogoutView):
    """Выход из системы."""


class EmailVerifyView(View):
    """Подтверждение email по ссылке из письма."""

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and email_verification_token.check_token(user, token):
            user.is_verified = True
            user.is_active = True
            user.save()
            messages.success(request, "Email подтверждён. Можете войти.")
            return redirect("users:login")
        messages.error(request, "Ссылка недействительна.")
        return redirect("home")


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Редактирование профиля пользователя."""
    model = User
    form_class = UserUpdateForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")
    success_message = "Профиль успешно обновлён!"

    def get_object(self, queryset=None):
        """Возвращает текущего авторизованного пользователя."""
        return self.request.user

    def form_valid(self, form):
        """Обрабатывает сохранение формы и очистку аватара."""
        if self.request.POST.get("_clear_avatar"):
            if form.instance.avatar:
                form.instance.avatar.delete(save=False)
            form.instance.avatar = None
        return super().form_valid(form)
