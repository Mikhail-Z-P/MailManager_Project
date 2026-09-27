from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from mailing.forms import ClientForm, MailingForm, MessageForm
from mailing.models import Attempt, Client, Mailing, Message
from mailing.services import send_mailing


class OwnerQuerySetMixin(LoginRequiredMixin):
    """Фильтрует queryset: пользователь видит свои объекты, менеджер — все."""

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.groups.filter(name="Managers").exists():
            return qs
        return qs.filter(owner=user)


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Доступ: владелец объекта или менеджер (просмотр чужих, редактирование своих)."""

    def test_func(self):
        obj = self.get_object()
        user = self.request.user
        if user.groups.filter(name="Managers").exists():
            if self.request.method in ("POST",):
                return obj.owner == user
            return True
        return obj.owner == user


@method_decorator(cache_page(60), name="dispatch")
class HomeView(View):
    """Главная страница со статистикой (кешируется: серверное + клиентское)."""

    def get(self, request):
        cache_key = "home_stats"
        stats = cache.get(cache_key)
        if stats is None:
            stats = {
                "total_mailings": Mailing.objects.count(),
                "active_mailings": Mailing.objects.filter(
                    status=Mailing.STATUS_RUNNING
                ).count(),
                "unique_clients": Client.objects.count(),
            }
            cache.set(cache_key, stats, timeout=60)
        return render(request, "mailing/home.html", stats)


# === Клиенты ===

class ClientListView(OwnerQuerySetMixin, ListView):
    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"


class ClientDetailView(OwnerRequiredMixin, DetailView):
    model = Client
    template_name = "mailing/client_detail.html"
    context_object_name = "client"


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(OwnerRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")


class ClientDeleteView(OwnerRequiredMixin, DeleteView):
    model = Client
    template_name = "mailing/client_confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")


# === Сообщения ===

class MessageListView(OwnerQuerySetMixin, ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "message_list"


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(OwnerRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


# === Рассылки ===

class MailingListView(OwnerQuerySetMixin, ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        qs = super().get_queryset()
        for m in qs:
            m.update_status()
        return qs


class MailingDetailView(OwnerRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["attempts"] = self.object.attempts.all()[:20]
        return ctx


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MailingDeleteView(OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingSendView(LoginRequiredMixin, View):
    """Ручной запуск рассылки по требованию."""

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        user = request.user
        is_manager = user.groups.filter(name="Managers").exists()
        if not is_manager and mailing.owner != user:
            messages.error(request, "Нет прав на отправку этой рассылки.")
            return redirect("mailing:mailing_detail", pk=pk)
        success, msg = send_mailing(mailing)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        return redirect("mailing:mailing_detail", pk=pk)


# === Попытки ===

class AttemptListView(LoginRequiredMixin, ListView):
    model = Attempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"
    paginate_by = 20

    def get_queryset(self):
        qs = Attempt.objects.select_related("mailing__owner")
        user = self.request.user
        if not user.groups.filter(name="Managers").exists():
            qs = qs.filter(mailing__owner=user)
        return qs


# === Статистика ===

class StatisticsView(LoginRequiredMixin, View):
    def get(self, request):
        cache_key = f"stats_{request.user.pk}"
        stats = cache.get(cache_key)
        if stats is None:
            user = request.user
            if user.groups.filter(name="Managers").exists():
                attempts = Attempt.objects.all()
            else:
                attempts = Attempt.objects.filter(mailing__owner=user)
            stats = {
                "total_success": attempts.filter(
                    status=Attempt.STATUS_SUCCESS
                ).count(),
                "total_failed": attempts.filter(
                    status=Attempt.STATUS_FAILED
                ).count(),
                "total_sent": attempts.count(),
            }
            cache.set(cache_key, stats, timeout=60)
        return render(request, "mailing/statistics.html", stats)


# === Менеджер: отключение рассылок ===

class MailingToggleView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.groups.filter(name="Managers").exists()

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.is_active = not mailing.is_active
        mailing.save(update_fields=["is_active"])
        status_text = "включена" if mailing.is_active else "отключена"
        messages.info(request, f"Рассылка #{pk} {status_text}.")
        return redirect("mailing:mailing_list")
