from django.db import models
from users.models import *

# Create your models here.

class NotificationSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notification_settings")
    email_notifications = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    photo = models.CharField(max_length=200, null=True, blank=True)
    salary = models.CharField(max_length=200, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        verbose_name_plural="Notification Settings"

