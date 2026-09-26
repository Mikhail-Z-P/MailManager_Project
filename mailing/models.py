from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Client(models.Model):
    """Получатель рассылки с email, ФИО и комментарием."""
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """Сообщение для рассылки: тема и тело письма."""
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["subject"]

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    """Рассылка с динамическим статусом и связями на сообщение и получателей."""
    STATUS_CREATED = "Создана"
    STATUS_RUNNING = "Запущена"
    STATUS_COMPLETED = "Завершена"
    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_COMPLETED, "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    recipients = models.ManyToManyField(
        Client,
        related_name="mailings",
        verbose_name="Получатели",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_time"]

    def __str__(self):
        return f"Рассылка #{self.pk} ({self.status})"

    def update_status(self):
        """Пересчитывает статус по текущему времени и сохраняет при изменении."""
        now = timezone.now()
        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_COMPLETED
        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=["status"])

    def clean(self):
        """Валидация: start_time не в прошлом, start_time раньше end_time."""
        now = timezone.now()
        if self.start_time and self.start_time < now:
            raise ValidationError(
                {"start_time": "Дата начала не может быть в прошлом."}
            )
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(
                {"end_time": "Дата окончания должна быть позже даты начала."}
            )


class Attempt(models.Model):
    """Попытка отправки письма в рамках рассылки."""
    STATUS_SUCCESS = "Успешно"
    STATUS_FAILED = "Не успешно"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    attempt_time = models.DateTimeField(
        auto_now_add=True, verbose_name="Время попытки"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Статус"
    )
    server_response = models.TextField(
        blank=True, verbose_name="Ответ сервера"
    )
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )

    class Meta:
        verbose_name = "Попытка"
        verbose_name_plural = "Попытки"
        ordering = ["-attempt_time"]

    def __str__(self):
        return f"{self.status} — {self.attempt_time}"
