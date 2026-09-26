from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from mailing.models import Client, Mailing, Message


class ClientForm(forms.ModelForm):
    """Форма создания и редактирования получателя рассылки."""

    class Meta:
        model = Client
        fields = ["email", "full_name", "comment"]


class MessageForm(forms.ModelForm):
    """Форма создания и редактирования сообщения."""

    class Meta:
        model = Message
        fields = ["subject", "body"]


class MailingForm(forms.ModelForm):
    """Форма создания и редактирования рассылки с валидацией времени."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["message"].queryset = Message.objects.filter(owner=user)
            self.fields["recipients"].queryset = Client.objects.filter(owner=user)

    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }

    def clean_start_time(self):
        """Проверяет, что дата начала не в прошлом."""
        start = self.cleaned_data.get("start_time")
        if start and start < timezone.now():
            raise ValidationError("Дата начала не может быть в прошлом.")
        return start

    def clean(self):
        """Проверяет, что start_time раньше end_time."""
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and start >= end:
            raise ValidationError(
                "Дата окончания должна быть позже даты начала."
            )
        return cleaned
