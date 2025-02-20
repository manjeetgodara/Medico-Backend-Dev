from transactions.models import *
from datetime import date, timedelta
from celery import shared_task

@shared_task
def coupon_expiry_notify():
    try:
        coupons_objs = Coupon.objects.all()
        for coupons_obj in coupons_objs.iterator():
            print(f"updated coupons_obj  {coupons_obj}")
            if coupons_obj.expire_after_days:
                expiry_date = coupons_obj.created_date + timedelta(coupons_obj.expire_after_days)
                if expiry_date.date() < date.today():
                    coupons_obj.is_expired = True
                    coupons_obj.save()
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')
