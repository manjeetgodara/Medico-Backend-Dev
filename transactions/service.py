import json

from django.conf import settings
import requests
from MLP.services.utils.seswrapper import SesWrapper
from users.models import *
from .models import *
import logging
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from MLP.services.emails import email_services

logger = logging.getLogger("error_logger")
ses_wrapper = SesWrapper()
def execute_transaction(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        mihpayid = data.get('mihpayid')
        status = data.get('status')
        unmappedstatus = data.get('unmappedstatus')
        amount = float(data.get('amount')) if data.get('amount') else 0
        phone = data.get('udf3')
        coupon_code = data.get('udf1')
        subscription_id = data.get('udf2')
        mlp_id = data.get('udf4')
        user_obj = User.objects.filter(mobile_number=phone, mlp_id=mlp_id)
        if not user_obj.first():
            response['status_code'] = 404
            response['message'] = f'For mihpayid: {mihpayid}, user with phone number: {phone} and mlp id: {mlp_id} not found'
            return response
        user_obj = user_obj.first()
        if status == 'success' and unmappedstatus == 'captured':
            subscription_obj = Subscription.objects.filter(id=subscription_id)
            if not subscription_obj.first():
                response['status_code'] = 404
                response['message'] = f'For mihpayid: {mihpayid}, Payment was done for amount: "{amount}", not able to find correct subscription with this amount. current subscription id: {subscription_id}'
                return response
            subscription_obj = subscription_obj.first()
            coupon_obj = None
            if coupon_code:
                coupon_obj = Coupon.objects.filter(code__iexact=coupon_code, is_expired=False)
                if not coupon_obj.first():
                    response['status_code'] = 404
                    response["message"] = f'For mihpayid: {mihpayid}, Payment was done for amount: "{amount}", not able to find correct Coupon with this code'
                    return response
                coupon_obj = coupon_obj.first()
                if coupon_obj.one_user_only and coupon_obj.assigned_user and coupon_obj.assigned_user != user_obj:
                    response['status_code'] = 404
                    response["message"] = f'For mihpayid: {mihpayid}, Payment was done for amount: "{amount}", Coupon is not for this user as it is assigned for others'
                    return response
            with transaction.atomic():
                TransactionEntity.objects.create(
                    mihpayid = mihpayid,
                    status = status,
                    amount = amount,
                    user = user_obj,
                    subscription = subscription_obj,
                    coupon_code = coupon_obj,
                    payload = data,
                )
                if coupon_obj and coupon_obj.one_user_only:
                    coupon_obj.is_expired = True
                    coupon_obj.save()
                user_obj.can_upgrade_subscription = 1
                current_subscription = UserSubscription.objects.filter(user=user_obj, is_subscription_active=True).first()
                if current_subscription or not Subscription.objects.filter(amount__gt=subscription_obj.amount).exists():
                    user_obj.can_upgrade_subscription = 0
                UserSubscription.objects.filter(user=user_obj, is_subscription_active=True).update(is_subscription_active=False)
                user_obj.save(update_fields=['can_upgrade_subscription'])
                UserSubscription.objects.create(user=user_obj, subscription=subscription_obj,subscription_ios = None)
                if user_obj.email:
                    subject = "Successfull payment at medicolifepartner.com"
                    email_content = email_services.set_email_thank_you_payment(user_obj)
                    ses_wrapper.send_email(receiver_email_address=user_obj.email, subject=subject,
                                          html_body=email_content['message'])  
            response['status_code'] = 200
            response['message'] = f'Current user with phone number: {phone}, has purchased the subscription: "{subscription_obj.name}" at value: {amount}'
            return response
        response['status_code'] = 400
        response['message'] = f'For mihpayid: {mihpayid}, payment failed. Current status is "{status}" and unmappedstatus is "{unmappedstatus}"'
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def get_subscriptions_list():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        excluded_plan_ids = [8, 9, 10, 11, 12, 13, 14, 15, 16 , 17]

        subscription_objs = list(Subscription.objects.exclude(id__in=excluded_plan_ids).order_by('pk').values())
        response['status_code'] = 200
        response['message'] = 'Query processed successfully'
        response['data'] = subscription_objs
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response



def web_app_payment_post(data,logged_mlp_id) :
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id,is_active=True, is_wrong=False, mandatory_questions_completed=True).first()
        
        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
        
        transid=data.get('trnsId')
        amount = data.get('amount')
        coupon_code = data.get('couponCode')
        country_code = data.get('countryCode')
        subscription_id = data.get('subscriptionId')
        merchant_key = data.get('merchantKey')
        
        web_instance =WebAppTransaction(
            user = auth_user,
            amount = amount,
            trnsId = transid,
            couponCode = coupon_code,
            countryCode = country_code,
            subscriptionId = subscription_id,
            merchantKey = merchant_key
        )
        web_instance.save()

        response['status_code'] = 200
        response['message'] = "Web App Payment Data Added Successfully"
        return response            
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response       

def get_web_app_payment_data(logged_mlp_id):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id,is_active=True, is_wrong=False, mandatory_questions_completed=True).first()
        
        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
        
        web_data = WebAppTransaction.objects.filter(user=auth_user).order_by('-created_date').first()

        if web_data is None:
            response['status_code'] = 300
            response['message'] = 'No web app payment data available for that user'
            return response 

        data ={}
        
        data['name'] = web_data.user.name
        data['mlp_id'] = web_data.user.mlp_id
        data['phone'] = web_data.user.mobile_number
        data['trnsId'] = web_data.trnsId
        data['merchantKey'] = web_data.merchantKey
        data['email'] = web_data.user.email
        data['amount'] = web_data.amount
        data['couponCode'] = web_data.couponCode
        data['countryCode'] = web_data.countryCode
        data['subscriptionId'] = web_data.subscriptionId

        response['status_code'] = 200
        response['message'] = "Web App Payment Data Added Successfully"
        response['data'] = data
        return response            
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response  


def get_ios_subscriptions_list():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        excluded_plan_ids = [8, 9, 10, 11, 12, 13, 14, 15, 16]

        subscription_objs = list(AppleSubscription.objects.exclude(id__in=excluded_plan_ids).order_by('pk').values())
        response['status_code'] = 200
        response['message'] = 'Query processed successfully'
        response['data'] = subscription_objs
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response        

def upgrade_subscriptions_list(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "Fields missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False).first()
        if not user_obj:
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        current_subscription = user_obj.usersubscription.filter(is_subscription_active=True).first()
        if user_obj.can_upgrade_subscription != 1 or not Subscription.objects.filter(amount__gt=current_subscription.subscription.amount).exists():
            response['status_code'] = 301
            response["message"] = "User cannot upgrade its subscription"
            return response
        if current_subscription.subscription.id in range(8, 17):
            # User has a subscription belonging to IDs 8 to 16, show them plans 1 to 7 for upgrade
            subscription_objs = list(Subscription.objects.filter(id__range=(1, 7)).order_by('pk').values())
        else:
            subscription_objs = list(Subscription.objects.filter(amount__gt=current_subscription.subscription.amount).exclude(id__range=(8, 17)).order_by('pk').values())
            subscription_objs = [{key: (value - current_subscription.subscription.amount) if key == "amount" else value for key, value in item.items() } for item in subscription_objs]
        response['status_code'] = 200
        response['message'] = 'Query processed successfully'
        response['data'] = subscription_objs
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def check_coupon(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        mlp_id = data.get('mlp_id', '')
        coupon_code = data.get('coupon_code', '')
        subscription_id = data.get('subscription_id', '')
        if not mlp_id or not coupon_code:
            response["status_code"] = 301
            response["message"] = "Fields missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()
        coupon_obj = Coupon.objects.filter(Q(code__iexact=coupon_code, is_expired=False) & (Q(one_user_only=True, assigned_user=user_obj) | Q(one_user_only=True, assigned_user__isnull=True) | Q(one_user_only=False)))
        if subscription_id:
           coupon_obj = coupon_obj.filter(Q(assigned_subscription__id=subscription_id) | Q(assigned_subscription__isnull=True))
        else:
           coupon_obj = coupon_obj.filter(assigned_subscription__isnull=True)
        if not coupon_obj.first():
            response['status_code'] = 404
            response["message"] = "Invalid Coupon Code"
            return response
        coupon_obj = coupon_obj.first()
        if coupon_obj.expire_after_days and (timezone.now() - coupon_obj.created_date).days > coupon_obj.expire_after_days:
            coupon_obj.is_expired = True
            coupon_obj.save()
            response['status_code'] = 404
            response["message"] = "Invalid Coupon Code"
            return response
        if TransactionEntity.objects.filter(coupon_code=coupon_obj, user=user_obj).exists():
            response['status_code'] = 304
            response["message"] = "Coupon already used"
            return response

        response['status_code'] = 200
        response['message'] = 'Query processed successfully'
        response['coupon_id'] = coupon_obj.id
        response['coupon_code'] = coupon_obj.code
        response['discount_percent'] = coupon_obj.discount_percent
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    

def get_coupons(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        mlp_id = data.get('mlp_id', '')
        subscription_id = data.get('subscription_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id is missing missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False).first()
        if not user_obj:
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        data = []
        coupons_objs = Coupon.objects.filter((Q(one_user_only=True) & Q(assigned_user=user_obj)) | Q(one_user_only=False) )
        if subscription_id:
            coupons_objs = coupons_objs.filter(Q(assigned_subscription__id=subscription_id) | Q(assigned_subscription__isnull=True))
        else:
            coupons_objs = coupons_objs.filter(assigned_subscription__isnull=True)
        coupons_objs = list(coupons_objs.values('id', 'one_user_only', 'code', 'discount_percent', 'is_expired'))
        
        for coupon_obj in coupons_objs:
            if not coupon_obj['one_user_only'] and TransactionEntity.objects.filter(coupon_code__id=coupon_obj['id'], user=user_obj).exists():
                coupon_obj['is_expired'] = True

        coupons_objs = [el for el in coupons_objs if not el['is_expired']]
        response['status_code'] = 200
        response['message'] = 'Query processed successfully'
        response['data'] = coupons_objs
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def verify_ios_receipt(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        subscription_id = data.get('subscription_id')
        mlp_id = data.get('mlp_id')
        status = data.get('status')
        user_obj = User.objects.filter(mlp_id=mlp_id)
        if not user_obj.exists():
            response['status_code'] = 404
            response['message'] = f'User with mlp id: {mlp_id} not found'
            return response

        user_obj = user_obj.first()

        if status == "success":
            subscription_obj = AppleSubscription.objects.filter(id=subscription_id)
            if not subscription_obj.exists():
                response['status_code'] = 404
                response['message'] = f'Cannot find subscription with ID: {subscription_id}'
                return response

            subscription_obj = subscription_obj.first()
            amount = subscription_obj.amount
            coupon_obj = None
    
            AppleTransactionEntity.objects.create(
                status=status,
                amount=amount,
                user=user_obj,
                subscription=subscription_obj,
                coupon_code=coupon_obj,
            )
            # if coupon_obj and coupon_obj.one_user_only:
            #     coupon_obj.is_expired = True
            #     coupon_obj.save()
            # user_obj.can_upgrade_subscription = 1
            # current_subscription = UserSubscription.objects.filter(user=user_obj, is_subscription_active=True).first()
            # if current_subscription or not Subscription.objects.filter(amount__gt=subscription_obj.amount).exists():
            user_obj.can_upgrade_subscription = 0
            UserSubscription.objects.filter(user=user_obj, is_subscription_active=True).update(is_subscription_active=False)
            user_obj.save(update_fields=['can_upgrade_subscription'])
            UserSubscription.objects.create(user=user_obj, subscription=None,subscription_ios=subscription_obj)
            if user_obj.email:
                subject = "Successful payment at medicolifepartner.com"
                email_content = email_services.set_email_thank_you_payment(user_obj)
                ses_wrapper.send_email(receiver_email_address=user_obj.email, subject=subject, html_body=email_content['message'])

            response['status_code'] = 200
            response['message'] = f'User has purchased the subscription: "{subscription_obj.name}" at value: {amount}'
            return response
        
        response['status_code'] = 400
        response['message'] = f'Payment failed. Status is "{status}"'
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


# def verify_ios_receipt(receipt_data, transaction_data):
#     response = {
#         "status_code": 500,
#         "message": "Internal server error"
#     }
#     try:
#         verify_receipt_url = 'https://buy.itunes.apple.com/verifyReceipt' if settings.DEBUG else 'https://sandbox.itunes.apple.com/verifyReceipt'
#         request_data = json.dumps({
#             'receipt-data': receipt_data,
#             'password': settings.APPLE_SHARED_SECRET
#         })
#         result = requests.post(verify_receipt_url, data=request_data, headers={'Content-Type': 'application/json'})
#         result_data = result.json()

#         if result_data.get('status') != 0:
#             response['status_code'] = 400
#             response['message'] = f'Receipt verification failed with status: {result_data.get("status")}'
#             return response

#         receipt = result_data['receipt']
#         transaction_id = receipt.get('transaction_id')
#         product_id = receipt.get('product_id')
#         purchase_date = receipt.get('purchase_date')
#         status = transaction_data.get('status')
#         phone = transaction_data.get('phone')
#        # coupon_code = transaction_data.get('coupon_code')
#         subscription_id = transaction_data.get('subscription_id')
#         mlp_id = transaction_data.get('mlp_id')
#         amount = float(transaction_data.get('amount')) if transaction_data.get('amount') else 0

#         user_obj = User.objects.filter(mobile_number=phone, mlp_id=mlp_id)
#         if not user_obj.exists():
#             response['status_code'] = 404
#             response['message'] = f'User with phone number: {phone} and mlp id: {mlp_id} not found'
#             return response

#         user_obj = user_obj.first()

#         if status == 'success':
#             # change product_id
#             subscription_obj = Subscription.objects.filter(id=subscription_id)
#             if not subscription_obj.exists():
#                 response['status_code'] = 404
#                 response['message'] = f'Cannot find subscription with ID: {subscription_id}'
#                 return response

#             subscription_obj = subscription_obj.first()
#             coupon_obj = None

#             # if coupon_code:
#             #     coupon_obj = Coupon.objects.filter(code__iexact=coupon_code, is_expired=False)
#             #     if not coupon_obj.exists():
#             #         response['status_code'] = 404
#             #         response['message'] = f'Cannot find valid coupon with code: {coupon_code}'
#             #         return response

#             #     coupon_obj = coupon_obj.first()
#             #     if coupon_obj.one_user_only and coupon_obj.assigned_user and coupon_obj.assigned_user != user_obj:
#             #         response['status_code'] = 404
#             #         response['message'] = f'This coupon is not assigned to this user'
#             #         return response

#             with transaction.atomic():
#                 TransactionEntity.objects.create(
#                     transaction_id=transaction_id,
#                     status=status,
#                     amount=amount,
#                     user=user_obj,
#                     subscription=subscription_obj,
#                     coupon_code=coupon_obj,
#                     payload=transaction_data,
#                 )
#                 # if coupon_obj and coupon_obj.one_user_only:
#                 #     coupon_obj.is_expired = True
#                 #     coupon_obj.save()
#                 user_obj.can_upgrade_subscription = 1
#                 current_subscription = UserSubscription.objects.filter(user=user_obj, is_subscription_active=True).first()
#                 if current_subscription or not Subscription.objects.filter(amount__gt=subscription_obj.amount).exists():
#                     user_obj.can_upgrade_subscription = 0
#                 UserSubscription.objects.filter(user=user_obj, is_subscription_active=True).update(is_subscription_active=False)
#                 user_obj.save(update_fields=['can_upgrade_subscription'])
#                 UserSubscription.objects.create(user=user_obj, subscription=subscription_obj)
#                 if user_obj.email:
#                     subject = "Successful payment at medicolifepartner.com"
#                     email_content = email_services.set_email_thank_you_payment(user_obj, amount, subscription_obj.name, subscription_obj.timeframe)
#                     ses_wrapper.send_email(receiver_email_address=user_obj.email, subject=subject, html_body=email_content['message'])

#             response['status_code'] = 200
#             response['message'] = f'User with phone number: {phone} has purchased the subscription: "{subscription_obj.name}" at value: {amount}'
#             return response

#         response['status_code'] = 400
#         response['message'] = f'Payment failed. Status is "{status}"'
#         return response
#     except Exception as e:
#         logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
#         return response
