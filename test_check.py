import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.urls import reverse

from mailing.models import Client, Message, Mailing, Attempt
from mailing.services import send_mailing
from users.models import User

print("=" * 60)
print("ПРОВЕРКА ПРОЕКТА")
print("=" * 60)

# 1. Модели
print("\n1. Модели:")
for m, name in [(Client, "Client"), (Message, "Message"), (Mailing, "Mailing"), (Attempt, "Attempt")]:
    fields = [f.name for f in m._meta.get_fields() if hasattr(f, "name") and f.name != "id"]
    print(f"   {name}: {fields}")
print("   OK")

# 2. Статусы
print("\n2. Статусы рассылки:")
print(f"   {Mailing.STATUS_CHOICES}")
print("   OK")

# 3. update_status
print(f"\n3. update_status(): {hasattr(Mailing, 'update_status')} — OK")

# 4. send_mailing
print(f"\n4. send_mailing(): {callable(send_mailing)} — OK")

# 5. bulk_create
print(f"\n5. bulk_create: {hasattr(Attempt.objects, 'bulk_create')} — OK")

# 6. Валидация
print("\n6. Валидация:")
m = Mailing(
    start_time=timezone.now() - timedelta(days=1),
    end_time=timezone.now() + timedelta(days=1),
)
try:
    m.clean()
    print("   ОШИБКА — валидация не сработала")
except ValidationError:
    print("   OK — start_time в прошлом вызывает ошибку")

# 7. Кеш
print("\n7. Кеш:")
cache.set("test", "ok", 30)
print(f"   cache.get('test') = {cache.get('test')} — OK")
cache.delete("test")

# 8. URL-маршруты
print("\n8. URL-маршруты:")
for name in ["home", "mailing:client_list", "mailing:message_list",
             "mailing:mailing_list", "mailing:attempt_list", "mailing:statistics",
             "users:login", "users:register", "users:profile"]:
    try:
        print(f"   {name}: {reverse(name)} — OK")
    except Exception as e:
        print(f"   {name}: ОШИБКА — {e}")

# 9. Шаблоны
print("\n9. Шаблоны:")
from django.conf import settings
tpl_dir = settings.TEMPLATES[0]["DIRS"][0]
for t in ["base.html", "mailing/home.html", "mailing/client_list.html",
          "mailing/mailing_detail.html", "mailing/statistics.html",
          "users/register.html", "users/login.html"]:
    exists = os.path.exists(os.path.join(tpl_dir, t))
    print(f"   {t}: {'OK' if exists else 'ОТСУТСТВУЕТ'}")

# 10. Middleware
print("\n10. Middleware кеширования:")
mw = settings.MIDDLEWARE
print(f"   UpdateCache: {'OK' if 'django.middleware.cache.UpdateCacheMiddleware' in mw else 'НЕТ'}")
print(f"   FetchFromCache: {'OK' if 'django.middleware.cache.FetchFromCacheMiddleware' in mw else 'НЕТ'}")

# 11. Кастомный User
print(f"\n11. AUTH_USER_MODEL = {settings.AUTH_USER_MODEL} — OK")

print("\n" + "=" * 60)
print("ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 60)
