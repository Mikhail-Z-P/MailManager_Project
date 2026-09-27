from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from users.forms import UserRegisterForm, UserUpdateForm
from users.models import User
from users.tokens import email_verification_token


class RegisterView(CreateView):
    """Регистрация нового пользователя с подтверждением email."""

    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.is_verified = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        verify_url = reverse_lazy(
            "users:verify", kwargs={"uidb64": uid, "token": token}
        )
        domain = self.request.get_host()
        protocol = "https" if self.request.is_secure() else "http"
        verify_link = f"{protocol}://{domain}{verify_url}"

        send_mail(
            subject="Подтверждение регистрации",
            message=(
                f"Для подтверждения email перейдите по ссылке:\n{verify_link}"
            ),
            from_email=settings.EMAIL_FROM,
            recipient_list=[user.email],
            fail_silently=False,
        )

        messages.success(
            self.request, "Письмо с подтверждением отправлено на ваш email."
        )
        return redirect(self.success_url)


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
        if user is not None and email_verification_token.check_token(
            user, token
        ):
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
        return self.request.user

    def form_valid(self, form):
        if self.request.POST.get("_clear_avatar"):
            if form.instance.avatar:
                form.instance.avatar.delete(save=False)
            form.instance.avatar = None
        return super().form_valid(form)



class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Доступ только для менеджеров."""

    def test_func(self):
        return self.request.user.groups.filter(name="Managers").exists()


class UserListView(ManagerRequiredMixin, ListView):
    """Список пользователей сервиса (только для менеджеров)."""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"


class UserBlockView(ManagerRequiredMixin, View):
    """Блокировка/разблокировка пользователя менеджером."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        status_text = "разблокирован" if user.is_active else "заблокирован"
        messages.info(request, f"Пользователь {user.email} {status_text}.")
        return redirect("users:user_list")
