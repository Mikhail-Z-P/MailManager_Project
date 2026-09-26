from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Создаёт группу Managers для ролевой модели доступа."""

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Managers")
        if created:
            self.stdout.write(self.style.SUCCESS("Группа 'Managers' создана."))
        else:
            self.stdout.write("Группа 'Managers' уже существует.")
