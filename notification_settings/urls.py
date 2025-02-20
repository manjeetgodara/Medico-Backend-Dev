from django.urls import path
from . import views

urlpatterns=[
    path("updatenotificationsettings/", views.update_notification_settings, name="update-notification-settings"),
    path("getnotificationsettings/", views.get_notification_settings, name="get-notification-settings")
]