from django.core.management.base import BaseCommand
from django.utils import timezone

from mailing.models import Mailing
from mailing.services import send_mailing


class Command(BaseCommand):
    """Отправляет все активные рассылки, попавшие в временное окно."""

    def handle(self, *args, **options):
        now = timezone.now()
        mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            is_active=True,
        )
        for mailing in mailings:
            success, msg = send_mailing(mailing)
            self.stdout.write(f"Рассылка #{mailing.pk}: {msg}")
