from django.contrib import admin
from .models import *

# Register your models here.

class PromotionsAdmin(admin.ModelAdmin):
    list_display=('id','users','message_title','created_date')

admin.site.register(Promotions, PromotionsAdmin)