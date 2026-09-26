from django.urls import path

from mailing import views

app_name = "mailing"

urlpatterns = [
    # Клиенты
    path("clients/", views.ClientListView.as_view(), name="client_list"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client_detail"),
    path("clients/create/", views.ClientCreateView.as_view(), name="client_create"),
    path("clients/<int:pk>/edit/", views.ClientUpdateView.as_view(), name="client_update"),
    path("clients/<int:pk>/delete/", views.ClientDeleteView.as_view(), name="client_delete"),
    # Сообщения
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/create/", views.MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/edit/", views.MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_delete"),
    # Рассылки
    path("", views.MailingListView.as_view(), name="mailing_list"),
    path("<int:pk>/", views.MailingDetailView.as_view(), name="mailing_detail"),
    path("create/", views.MailingCreateView.as_view(), name="mailing_create"),
    path("<int:pk>/edit/", views.MailingUpdateView.as_view(), name="mailing_update"),
    path("<int:pk>/delete/", views.MailingDeleteView.as_view(), name="mailing_delete"),
    path("<int:pk>/send/", views.MailingSendView.as_view(), name="mailing_send"),
    path("<int:pk>/toggle/", views.MailingToggleView.as_view(), name="mailing_toggle"),
    # Попытки
    path("attempts/", views.AttemptListView.as_view(), name="attempt_list"),
    # Статистика
    path("statistics/", views.StatisticsView.as_view(), name="statistics"),
]
