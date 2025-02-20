from datetime import date, datetime
from django.utils import timezone
from cronjob.interestpending_notification import interest_pending
from cronjob.pendingnotifications import pending_notify
from cronjob.stories_notification import story_notify
from cronjob.subscription_expiry import subscription_expiry_notify
from cronjob.bachelor import find_bachelor_of_each_religion
from cronjob.coupons_expiry import coupon_expiry_notify            
from cronjob.inactiveusers import inactive
from misc.service import send_notifications_promotion, sync_data, sync_payment_data
from promotions.models import Promotions
from transactions.models import Coupon
from django.db.models import OuterRef, Subquery,Prefetch,Q
from cronjob.shortlisted_notification import shortlisted_notify
from users.models import Intrest, Notifications, SavedUser, Stories, User, UserSubscription
from django.db.models.signals import post_save
from django.dispatch import receiver


def main_cronjob():
    try:
        
        print(f"Started Cron job. Date: {date.today()}")
        find_bachelor_of_each_religion.apply_async(queue="push_notification")
        print("Successfully ran bachelor of the day at midnight")
        
        print("Running Cron to expire Coupons")
        coupon_expiry_notify.apply_async(queue="push_notification")
        print("Successfully completed cron to expire Coupons")
       
        inactive.apply_async(queue="push_notification") 
        print("Successfully Notify all inactive users")
        

        saved_profiles_prefetch = Prefetch(
            'saving_user',
            queryset=SavedUser.objects.select_related('saved_profile'),
            to_attr='saved_profiles'
        )
        active_subscriptions_prefetch = Prefetch(
                'usersubscription', 
                queryset=UserSubscription.objects.filter(is_subscription_active=True),
                to_attr='active_subscription'
            )
        pending_interest_prefetch =  Prefetch('invitation_to', queryset=Intrest.objects.filter(status="Pending"))
        
        all_users = User.objects.filter( mandatory_questions_completed=True, is_wrong=False,
                                         is_active=True).prefetch_related(
                                            active_subscriptions_prefetch).prefetch_related(
                                                pending_interest_prefetch 
                                            ).prefetch_related(saved_profiles_prefetch)

        print("Running Cron to expire subscription , notify shortlisted and so on")
        for user in all_users:
            #For subscription expiry
            if hasattr(user,"active_subscription"):
                if user.active_subscription:
                  active_subscription = user.active_subscription[0]
                  subscription_expiry_notify.apply_async(args=[user.id,active_subscription.id],queue="push_notification")

            #For shortlisted notify
            if hasattr(user, 'saved_profiles'):
               for saved_data in user.saved_profiles:
                  profile_mlp_id = saved_data.saved_profile.mlp_id
                  #print(f"{user} has saved profiles {saved_data}")
                  shortlisted_notify.apply_async(args=[user.mlp_id, user.notification_token, profile_mlp_id],queue="push_notification")
            
            #To notify interest pending users
            if hasattr(user, 'invitation_to'):
                for interest in user.invitation_to.all():
                   # print(f"{user} has interest profiles {interest}")
                    interest_pending.apply_async(args=[user.mlp_id,user.notification_token,interest.id],queue="push_notification") 

            # Access pending notifications status
            has_pending_notifications = user.user_notifications.filter(is_seen=False).exists()
            # print(f"{user} has notification {has_pending_notifications}")
            if has_pending_notifications:
                pending_notify.apply_async(args=[user.mlp_id,user.notification_token],queue="push_notification") 

            # twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            current_datetime = timezone.now()
            twenty_four_hours_ago = current_datetime - timezone.timedelta(hours=24)

            all_stories_exists = Stories.objects.filter(
                created_at__gte=twenty_four_hours_ago).exclude( Q(user=user) | 
                                                                Q(user__gender=user.gender) |
                                                                 Q(user__blocked_user__user=user)|
                                                                 Q(user__blocking_user__blocked_user=user)).exists()
            #print(f"{user} has stories {all_stories_exists}")
            if all_stories_exists:
               story_notify.apply_async(args=[user.mlp_id,user.notification_token],queue="push_notification")

        print("Successfully Ran Cron to expire subscription , notify shortlisted and so on at midnight")       
                
        print(f"All Crons completed. Date: {date.today()}")
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')


def sync_cronjob():
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Sync Cronjob started on: {start_time}")

        sync_data.apply_async(queue="push_notification")
        # sync_data()

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Sync Cronjob ended on: {end_time}")
    except Exception as e:
        print(f"{e.__traceback__.tb_lineno} - {str(e)}")  


def sync_payment_cronjob():
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Sync payment Cronjob started on: {start_time}")

        # sync_data.apply_async(queue="push_notification")
        sync_payment_data()

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Sync payment Cronjob ended on: {end_time}")
    except Exception as e:
        print(f"{e.__traceback__.tb_lineno} - {str(e)}")


def schedule_promotion_notification():
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Schedule promotion notify cronjob started on: {start_time}")
        
        # Get all promotions that haven't been sent
        instances = Promotions.objects.filter(sent=False)
        
        for instance in instances:
            try:
                scheduled_time = instance.scheduled_time
                
                if scheduled_time:
                    scheduled_time = timezone.make_aware(scheduled_time)
                    # Check if the scheduled time is in the future
                    if scheduled_time >= timezone.now():
                        send_notifications_promotion.apply_async(args=[instance.id], queue="push_notification")
                else:
                    send_notifications_promotion.apply_async(args=[instance.id], queue="push_notification")
               
            except Exception as inner_exception:
                print(f"Error processing promotion ID {instance.id}: {inner_exception}")
                # Ensure that sent is marked as True even if there's an error
                instance.sent = True
                instance.save()

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Scheduled promotion notify cronjob ended on: {end_time}")

    except Exception as e:
        print(f"Error in schedule_promotion_notification: {e}")  