from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админка пользователя с действиями блокировки."""

    list_display = ("email", "username", "is_verified", "is_blocked", "is_active")
    list_filter = ("is_verified", "is_blocked", "is_active")
    actions = ["block_users", "unblock_users"]

    @admin.action(description="Заблокировать выбранных пользователей")
    def block_users(self, request, queryset):
        """Блокирует выбранных пользователей."""
        queryset.update(is_blocked=True, is_active=False)

    @admin.action(description="Разблокировать выбранных пользователей")
    def unblock_users(self, request, queryset):
        """Разблокирует выбранных пользователей."""
        queryset.update(is_blocked=False, is_active=True)
