from django.contrib import admin
from .models import *

# Register your models here.

class NotificationsAdmin(admin.ModelAdmin):
    list_display=('id','user','phone','photo','salary','email')

admin.site.register(NotificationSettings, NotificationsAdmin)
