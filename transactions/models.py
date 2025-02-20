from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from users.models import *

# Create your models here.
class Coupon(models.Model):
    code = models.CharField(max_length=100)
    discount_percent = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], help_text='Discont must be integer between 1 to 100 percent', null=False, blank=False)
    is_expired = models.BooleanField(default=False)
    expire_after_days = models.PositiveIntegerField(null=True, blank=True)
    one_user_only = models.BooleanField(default=True, help_text='Code is applicable for any one user only one time if True else one time per user')
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    assigned_subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code
    
    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)
    

class TransactionEntity(models.Model):
    mihpayid = models.CharField(max_length=100, unique=True, null=False, blank=False)
    status = models.CharField(max_length=100)
    amount = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, null=True, blank=False)
    coupon_code = models.ForeignKey(Coupon, on_delete=models.SET_DEFAULT, default=None, null=True, blank=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_DEFAULT, default=None, null=True, blank=False)
    payload = models.JSONField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mihpayid


class AppleTransactionEntity(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, null=True, blank=False, related_name="userapplesubscription")
    status = models.CharField(max_length=100)
    amount = models.PositiveIntegerField()
    coupon_code = models.ForeignKey(Coupon, on_delete=models.SET_DEFAULT, default=None, null=True, blank=False)
    subscription = models.ForeignKey(AppleSubscription, on_delete=models.SET_DEFAULT, default=None, null=True, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.subscription}"


class WebAppTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, null=True, blank=False, related_name="webapptransaction")
    amount = models.PositiveIntegerField()
    trnsId = models.CharField(max_length=255, null=True, blank=False)
    couponCode = models.CharField(max_length=50, null=True, blank=False)
    countryCode = models.CharField(max_length=10, null=True, blank=False)
    subscriptionId = models.CharField(max_length=255, null=True, blank=False)
    merchantKey = models.CharField(max_length=255, null=True, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Transaction by {self.name}"  

