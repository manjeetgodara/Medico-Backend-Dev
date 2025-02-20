from django.contrib import admin
from .models import *


class CouponAdmin(admin.ModelAdmin):
    autocomplete_fields = ['assigned_user']  # Enable autocomplete for assigned_user
    # list_display = ('code', 'discount_percent', 'is_expired', 'expire_after_days', 'one_user_only', 'assigned_user', 'assigned_subscription', 'created_date')
    search_fields = ('assigned_user__mlp_id',)  # Allow searching by mlp_id in Coupon admin

# Register your models here.
admin.site.register(TransactionEntity)
admin.site.register(Coupon,CouponAdmin)
admin.site.register(AppleTransactionEntity)
admin.site.register(WebAppTransaction)