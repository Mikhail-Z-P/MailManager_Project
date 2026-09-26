from django.contrib import admin

from mailing.models import Attempt, Client, Mailing, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Админка получателей рассылки."""

    list_display = ("email", "full_name", "comment", "owner")
    search_fields = ("email", "full_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админка сообщений."""

    list_display = ("subject", "owner")
    search_fields = ("subject",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Админка рассылок."""

    list_display = ("id", "start_time", "end_time", "status", "is_active", "owner")
    list_filter = ("status", "is_active")
    filter_horizontal = ("recipients",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    """Админка попыток отправки."""

    list_display = ("attempt_time", "status", "mailing")
    list_filter = ("status",)
    readonly_fields = ("attempt_time", "status", "server_response", "mailing")
