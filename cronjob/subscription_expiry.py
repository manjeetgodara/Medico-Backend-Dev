from transactions.models import *
from users.models import *
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from pyfcm import FCMNotification
from MLP.services.utils.seswrapper import SesWrapper
from MLP.services.emails import email_services
from celery import shared_task
from firebase_admin import messaging

# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))
ses_wrapper= SesWrapper()

@shared_task
def subscription_expiry_notify(user_id, subscription_id):
    try:
        try:
            user_obj = User.objects.get(id=user_id)
            active_subscription = UserSubscription.objects.get(id=subscription_id)
            print(f"{user_obj} has active subscription {active_subscription}")
            if active_subscription:
                # Ensure created_date is timezone-aware
                created_date = active_subscription.created_date
                if timezone.is_naive(created_date):
                    created_date = timezone.make_aware(created_date, timezone.get_current_timezone())
                
                # Calculate subscription expiry date
                subscription_expiry = created_date + relativedelta(months=active_subscription.subscription.timeframe)
                subscription_expiry -= timedelta(days=1)

                # Ensure subscription_expiry is timezone-aware
                if timezone.is_naive(subscription_expiry):
                    subscription_expiry = timezone.make_aware(subscription_expiry, timezone.get_current_timezone())

                # Compare with the current date (timezone-aware)
                if subscription_expiry.date() < timezone.now().date():
                    Notifications.objects.create(
                        user=user_obj,
                        message="Your subscription has expired. Renew now for uninterrupted access",
                        type="reminder"
                    )
                    custom_data = {
                        "screen": "subscriptions",
                        "userid": user_obj.mlp_id
                    }
                    if user_obj.notification_token:
                        message = messaging.Message(
                        token=user_obj.notification_token,  # FCM registration token
                        notification=messaging.Notification(
                            title="Subscription Expired",
                            body="Your subscription has expired. Renew now for uninterrupted access"
                        ),
                        data=custom_data  # Custom data payload
                        )

                        res= messaging.send(message)
                        # push_service.notify_single_device(
                        #     registration_id=user_obj.notification_token,
                        #     message_title="Subscription Expired",
                        #     message_body="Your subscription has expired. Renew now for uninterrupted access",
                        #     data_message=custom_data
                        # )
                    all_linked_users = LinkedAccount.objects.filter(primary_user=user_obj)
                    notificationtokens = [i.linked_user.notification_token for i in all_linked_users if i.linked_user.notification_token]

                    if notificationtokens:
                        message_body = f"{user_obj.name}'s subscription has expired. Renew now for uninterrupted access"
                        # push_service.notify_multiple_devices(
                        #     registration_ids=notificationtokens,
                        #     message_title="Subscription Expired",
                        #     message_body=message_body,
                        #     data_message=custom_data
                        # )
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title="Subscription Expired",
                                body=message_body
                            ),
                            data = custom_data 
                        )
                        res= messaging.send_multicast(message)

                    active_subscription.is_subscription_active = False
                    active_subscription.save()
                    user_obj.can_upgrade_subscription = -1
                    user_obj.save(update_fields=['can_upgrade_subscription'])

                # Ensure one_month_after_creation is timezone-aware
                one_month_after_creation = created_date + relativedelta(months=1)
                if timezone.is_naive(one_month_after_creation):
                    one_month_after_creation = timezone.make_aware(one_month_after_creation, timezone.get_current_timezone())

                # Compare with the current date (timezone-aware)
                if one_month_after_creation.date() < timezone.now().date() and user_obj.can_upgrade_subscription == 1:
                    user_obj.can_upgrade_subscription = 0
                    user_obj.save(update_fields=['can_upgrade_subscription'])

                # Compare subscription_expiry with the current date plus 7 days (timezone-aware)
                if subscription_expiry.date() < (timezone.now() + timedelta(days=7)).date():
                    Notifications.objects.create(
                        user=user_obj,
                        message="Your subscription is going to expire soon. Renew now for uninterrupted access",
                        type="reminder"
                    )
                    custom_data = {
                        "screen": "subscriptions",
                        "userid": user_obj.mlp_id
                    }
                    if user_obj.notification_token:
                        # push_service.notify_single_device(
                        #     registration_id=user_obj.notification_token,
                        #     message_title="Subscription expiring soon!",
                        #     message_body="Your subscription is going to expire soon. Renew now for uninterrupted access",
                        #     data_message=custom_data
                        # )
                        message = messaging.Message(
                            token=user_obj.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title="Subscription expiring soon!",
                                body="Your subscription is going to expire soon. Renew now for uninterrupted access"
                            ),
                            data=custom_data  
                        )
                        res= messaging.send(message)

                    all_linked_users = LinkedAccount.objects.filter(primary_user=user_obj)
                    notificationtokens = [i.linked_user.notification_token for i in all_linked_users if i.linked_user.notification_token]

                    if notificationtokens:
                        message_body = f"{user_obj.name}'s subscription is going to expire soon. Renew now for uninterrupted access"
                        # push_service.notify_multiple_devices(
                        #     registration_ids=notificationtokens,
                        #     message_title="Subscription expiring soon!",
                        #     message_body=message_body,
                        #     data_message=custom_data
                        # )

                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title="Subscription expiring soon!",
                                body=message_body
                            ),
                            data = custom_data 
                        )
                        res= messaging.send_multicast(message)

                    if user_obj.email:
                        remaining_days = (subscription_expiry - timezone.now()).days
                       # expiry_end_date = subscription_expiry.date()
                        subject = "Plan Expire Reminder (Renew Plan)"
                        email_content = email_services.set_email_plan_expire_reminder(user_obj, remaining_days)
                        ses_wrapper.send_email(
                            receiver_email_address=user_obj.email,
                            subject=subject,
                            html_body=email_content['message']
                        )

            else:
                Notifications.objects.create(
                    user=user_obj,
                    message="You don't have any active subscriptions. Check out our membership plans for exclusive benefits",
                    type="reminder"
                )
                custom_data = {
                    "screen": "subscriptions",
                    "userid": user_obj.mlp_id
                }
                if user_obj.notification_token:
                    # push_service.notify_single_device(
                    #     registration_id=user_obj.notification_token,
                    #     message_title="Reminder",
                    #     message_body="You don't have any active subscriptions. Check out our membership plans for exclusive benefits",
                    #     data_message=custom_data
                    # )
                    message = messaging.Message(
                            token=user_obj.notification_token, 
                            notification=messaging.Notification(
                                title="Reminder",
                                body="You don't have any active subscriptions. Check out our membership plans for exclusive benefits"
                            ),
                            data=custom_data  
                        )
                    res= messaging.send(message)

                all_linked_users = LinkedAccount.objects.filter(primary_user=user_obj)
                notificationtokens = [i.linked_user.notification_token for i in all_linked_users if i.linked_user.notification_token]

                if notificationtokens:
                    message_body = f"{user_obj.name} doesn't have any active subscriptions. Check out our membership plans for exclusive benefits"
                    # push_service.notify_multiple_devices(
                    #     registration_ids=notificationtokens,
                    #     message_title="Reminder",
                    #     message_body=message_body,
                    #     data_message=custom_data
                    # )

                    message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title="Reminder",
                                body=message_body
                            ),
                            data = custom_data 
                        )
                    res= messaging.send_multicast(message)
                    

        except Exception as e:
            print(f'error for specific user "{user_obj.mlp_id}" while operations: {e.__traceback__.tb_lineno} - {str(e)}')
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')
