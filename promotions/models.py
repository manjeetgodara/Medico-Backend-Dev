from django.db import models

# Create your models here.
USERS_SELECT=(
    ("all","ALL"),
    ("silverregular","SILVER_REGULAR"),
    ("goldregular","GOLD_REGULAR"),
    ("platinumregular","PLATINUM_REGULAR"),
    ("silver","SILVER"),
    ("gold","GOLD"),
    ("platinum","PLATINUM"),
    ("premium", "PREMIUM"),
    ("Noplans", "NOPLANS")
)
class Promotions(models.Model):
    users = models.CharField(max_length=80, choices=USERS_SELECT)
    message_title = models.CharField(max_length=100, null=True, blank=True)
    message_body = models.CharField(max_length=500, null=True, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True) 
    sent = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Promotions and Offers"