import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from misc.models import ChangeLog
from transactions.models import AppleTransactionEntity, Coupon, TransactionEntity, WebAppTransaction
from users.service import calculate_match_percentage
from .models import *
from .utils import *
import time
from MLP.services.emails import email_services
from pyfcm import FCMNotification
from django.db.models.signals import post_save , post_delete
from dateutil.relativedelta import relativedelta


@receiver(post_save, sender=User)
def send_notification_profilepercentage(sender, instance,created, **kwargs):
    if not created and instance.calculate_profile_percentage() <= 80:
        # Check if a notification with the same user, message, and type already exists
        notification, created = Notifications.objects.get_or_create(
            user=instance,
            message="Complete your profile to gain visibility on the app and find your perfect Medico match.",
            type="profile_completion"
        )
        # Optionally, handle the case where the notification already exists
        if not created:
            # The notification already exists, you might want to update or ignore
            pass


# @receiver(post_save, sender=User)
# def send_notification_on_high_match(sender, instance, created, **kwargs):
#     if created:
#         logged_user = instance  
#         logged_user_gender = logged_user.gender  

#         all_users = User.objects.exclude(mlp_id=logged_user.mlp_id).filter(Q(is_active=True) & Q(mandatory_questions_completed=True))
        
#         for user in all_users:
#             match_data = calculate_match_percentage(logged_user.mlp_id, user.mlp_id)
#             match_percentage = match_data.get('match_percentage', 0)
            
#             # Check if the match percentage is high and genders are different
#             if match_percentage >= 70 and logged_user_gender != user.gender:
#                 Notifications.objects.create(
#                     user=user,
#                     sender=logged_user,
#                     message=f"Your compatibility score with {logged_user.mlp_id} is high. Explore your potential connection!",
#                     type="match_percentage"
#                 )

#                 if user.notification_token:
#                     custom_data = {
#                         "screen": "match_percentage",
#                         "user_id":user.mlp_id 
#                     }
#                     push_service.notify_single_device(
#                         registration_id=user.notification_token,
#                         message_title="High Compatibility",
#                         message_body=f"Your compatibility score with {logged_user.mlp_id} is high. Explore your potential connection!",
#                         data_message=custom_data
#                     )  

                # all_linked_users=LinkedAccount.objects.filter(primary_user=logged_user).all()
                # notificationtokens = []
                # for i in all_linked_users:
                #     if i.linked_user.notification_token:
                #         notificationtokens.append(i.linked_user.notification_token) 

                # if notificationtokens:
                #     message_body = f"Your compatibility score with {logged_user.mlp_id} is high. Explore your potential connection!"
                #     push_service.notify_multiple_devices(
                #         registration_ids=notificationtokens,
                #         message_title="High Compatibility",
                #         message_body=message_body,
                #         data_message=custom_data
                #     )     


#Signals for syncing data with website 

#For Blocked user model
@receiver(post_save, sender=BlockedUsers)
def log_model_changes_on_create(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_mlp_id': instance.user.mlp_id,  
            'blocked_user_mlp_id': instance.blocked_user.mlp_id,  
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_save, sender=BlockedUsers)
def log_model_changes_on_update(sender, instance, created, **kwargs):
    if not created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_mlp_id': instance.user.mlp_id,  
            'blocked_user_mlp_id': instance.blocked_user.mlp_id,  
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=BlockedUsers)
def log_model_changes_on_delete(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user_mlp_id': instance.user.mlp_id,  
        'blocked_user_mlp_id': instance.blocked_user.mlp_id, 
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


# #For seen user model
# @receiver(post_save, sender=SeenUser)
# def log_seen_user_changes_on_create(sender, instance, created, **kwargs):
#     if created:
#         app_name = instance._meta.app_label
#         model_name = instance._meta.model_name
#         fields = {
#             'user_mlp_id': instance.user.mlp_id,  
#             'seen_profile_mlp_id': instance.seen_profile.mlp_id,  
#             'times_visited': instance.times_visited,
#             'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"), 
#             'last_seen': instance.last_seen.strftime("%Y-%m-%d %H:%M:%S"),  
#         }
#         ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

# @receiver(post_save, sender=SeenUser)
# def log_seen_user_changes_on_update(sender, instance, created, **kwargs):
#     if not created:
#         app_name = instance._meta.app_label
#         model_name = instance._meta.model_name
#         fields = {
#             'user_mlp_id': instance.user.mlp_id,  
#             'seen_profile_mlp_id': instance.seen_profile.mlp_id,  
#             'times_visited': instance.times_visited,
#             'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
#             'last_seen': instance.last_seen.strftime("%Y-%m-%d %H:%M:%S"),  
#         }
#         ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

# @receiver(post_delete, sender=SeenUser)
# def log_seen_user_changes_on_delete(sender, instance, **kwargs):
#     app_name = instance._meta.app_label
#     model_name = instance._meta.model_name
#     fields = {
#         'user_mlp_id': instance.user.mlp_id,  
#         'seen_profile_mlp_id': instance.seen_profile.mlp_id,  
#     }
#     ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For User Subscription model
@receiver(post_save, sender=UserSubscription)
def log_user_subscription_changes_on_create(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        if instance.subscription:
            end_date = instance.created_date + relativedelta(months=instance.subscription.timeframe)    
        elif instance.subscription_ios:
            end_date = instance.created_date + relativedelta(months=instance.subscription_ios.timeframe)  
        else:
            end_date = None
        fields = {
            'user_mlp_id': instance.user.mlp_id,  
            'subscription_name': instance.subscription.name if instance.subscription else None,
            'subscription_ios' : instance.subscription_ios.name  if instance.subscription_ios else None,
            'is_subscription_active': instance.is_subscription_active,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),
            'end_date': end_date.strftime("%Y-%m-%d %H:%M:%S") if end_date else None,
            'amount': instance.subscription.amount if instance.subscription else (instance.subscription_ios.amount if instance.subscription_ios else None) ,  
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_save, sender=UserSubscription)
def log_user_subscription_changes_on_update(sender, instance, created, **kwargs):
    if not created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        if instance.subscription:
            end_date = instance.created_date + relativedelta(months=instance.subscription.timeframe)    
        elif instance.subscription_ios:
            end_date = instance.created_date + relativedelta(months=instance.subscription_ios.timeframe)  
        else:
            end_date = None
             
        fields = {
            'user_mlp_id': instance.user.mlp_id,  
            'subscription_name': instance.subscription.name if instance.subscription else None,
            'subscription_ios' : instance.subscription_ios.name if instance.subscription_ios else None,
            'is_subscription_active': instance.is_subscription_active,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),
            'end_date': end_date.strftime("%Y-%m-%d %H:%M:%S") if end_date else None,
            'amount': instance.subscription.amount if instance.subscription else (instance.subscription_ios.amount if instance.subscription_ios else None) , 
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=UserSubscription)
def log_user_subscription_changes_on_delete(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    if instance.subscription:
        end_date = instance.created_date + relativedelta(months=instance.subscription.timeframe)    
    elif instance.subscription_ios:
        end_date = instance.created_date + relativedelta(months=instance.subscription_ios.timeframe)  
    else:
        end_date = None
    fields = {
        'user_mlp_id': instance.user.mlp_id,  
        'subscription_name': instance.subscription.name if instance.subscription else None,
        'subscription_ios' : instance.subscription_ios.name  if instance.subscription_ios else None,
        'is_subscription_active': instance.is_subscription_active,
        'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"), 
        'end_date': end_date.strftime("%Y-%m-%d %H:%M:%S") if end_date else None,
        'amount': instance.subscription.amount if instance.subscription else (instance.subscription_ios.amount if instance.subscription_ios else None) ,  
        'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"), 
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Contact Viewed model
@receiver(post_save, sender=ContactViewed)
def log_contact_viewed_changes_on_create(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_mlp_id': instance.user.mlp_id if instance.user else None,  
            'seen_contact_mlp_id': instance.seen_contact.mlp_id if instance.seen_contact else None,  
            'contacts_viewed': instance.contactsviewed,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        if instance.user and instance.seen_contact :
           ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

# @receiver(post_save, sender=ContactViewed)
# def log_contact_viewed_changes_on_update(sender, instance, created, **kwargs):
#     if not created:
#         app_name = instance._meta.app_label
#         model_name = instance._meta.model_name
#         fields = {
#             'user_mlp_id': instance.user.mlp_id,  
#             'seen_contact_mlp_id': instance.seen_contact.mlp_id, 
#             'contacts_viewed': instance.contactsviewed,
#             'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
#             'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
#         }
#         ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)


@receiver(post_delete, sender=ContactViewed)
def log_contact_viewed_changes_on_delete(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user_mlp_id': instance.user.mlp_id if instance.user else None,  
        'seen_contact_mlp_id': instance.seen_contact.mlp_id if instance.seen_contact else None,  
    }
    if instance.user and instance.seen_contact :
        ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Saved User model
@receiver(post_save, sender=SavedUser)
def log_saved_user_changes_on_create(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_mlp_id': instance.user.mlp_id,  
            'saved_profile_mlp_id': instance.saved_profile.mlp_id,  
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"), 
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

# @receiver(post_save, sender=SavedUser)
# def log_saved_user_changes_on_update(sender, instance, created, **kwargs):
#     if not created:
#         app_name = instance._meta.app_label
#         model_name = instance._meta.model_name
#         fields = {
#             'user_mlp_id': instance.user.mlp_id,  
#             'saved_profile_mlp_id': instance.saved_profile.mlp_id,  
#             'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
#             'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"), 
#         }
#         ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=SavedUser)
def log_saved_user_changes_on_delete(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user_mlp_id': instance.user.mlp_id,  
        'saved_profile_mlp_id': instance.saved_profile.mlp_id,  
       
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Intrest model
@receiver(post_save, sender=Intrest)
def log_intrest_changes_on_create(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'invitation_by_mlp_id': instance.invitation_by.mlp_id,  
            'invitation_to_mlp_id': instance.invitation_to.mlp_id,  
            'status': instance.status,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_save, sender=Intrest)
def log_intrest_changes_on_update(sender, instance, created, **kwargs):
    if not created and instance.status != 'Pending':
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'invitation_by_mlp_id': instance.invitation_by.mlp_id, 
            'invitation_to_mlp_id': instance.invitation_to.mlp_id,  
            'status': instance.status,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=Intrest)
def log_intrest_changes_on_delete(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'invitation_by_mlp_id': instance.invitation_by.mlp_id, 
        'invitation_to_mlp_id': instance.invitation_to.mlp_id, 
        'status': instance.status, 
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Connection List model
@receiver(post_save, sender=ConnectionList)
def log_connection_list_changes_on_create(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_one_mlp_id': instance.user_one.mlp_id,  
            'user_two_mlp_id': instance.user_two.mlp_id,  
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"), 
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

# @receiver(post_save, sender=ConnectionList)
# def log_connection_list_changes_on_update(sender, instance, created, **kwargs):
#     if not created:
#         app_name = instance._meta.app_label
#         model_name = instance._meta.model_name
#         fields = {
#             'user_one_mlp_id': instance.user_one.mlp_id,  
#             'user_two_mlp_id': instance.user_two.mlp_id,  
#             'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
#             'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  
#         }
#         ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=ConnectionList)
def log_connection_list_changes_on_delete(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user_one_mlp_id': instance.user_one.mlp_id,  
        'user_two_mlp_id': instance.user_two.mlp_id,  
       
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Profile View Model
@receiver(post_save, sender=ProfileView)
def log_profile_view_changes(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'viewer_mlp_id': instance.viewer.mlp_id,  
            'viewed_user_mlp_id': instance.viewed_user.mlp_id,  
            'viewed_at': instance.viewed_at.strftime("%Y-%m-%d %H:%M:%S"),  
            'visited_at': instance.visited_at.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)


@receiver(post_delete, sender=ProfileView)
def log_profile_view_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'viewer_mlp_id': instance.viewer.mlp_id,  
        'viewed_user_mlp_id': instance.viewed_user.mlp_id,  
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Rating Review Model
@receiver(post_save, sender=RatingReview)
def log_rating_review_changes(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_mlp_id': instance.user.mlp_id,  
            'rating': instance.rating,
            'review_text': instance.review_text,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)
    else:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_mlp_id': instance.user.mlp_id, 
            'rating': instance.rating,
            'review_text': instance.review_text,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
        }
        ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)


@receiver(post_delete, sender=RatingReview)
def log_rating_review_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user_mlp_id': instance.user.mlp_id,  
        'rating': instance.rating,
        'review_text': instance.review_text,
        'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Success story
@receiver(post_save, sender=SuccessStory)
def log_success_story_changes(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name

        logged_user = instance.user
        partner_mlp_id = instance.partner_mlp_id
        
        all_users = User.objects.exclude(mlp_id=logged_user.mlp_id).filter(Q(is_active=True) & Q(mandatory_questions_completed=True))
        
        for user in all_users:
            Notifications.objects.create(
                user=user,
                sender=logged_user,
                message=f"Read our latest success story of {logged_user.mlp_id} and {partner_mlp_id}. Find your success here",
                type="success_stories"
            )

        fields = {
            'user_mlp_id': instance.user.mlp_id,  
            'partner_mlp_id': instance.partner_mlp_id,  
            'partner_name': instance.partner_name,
            'partner_mobile_number': instance.partner_mobile_number,
            'reason':instance.reason,
            'experience':instance.experience,
            'story': instance.story,
            'image': instance.image,
            'video': instance.video,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"), 
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=SuccessStory)
def log_success_story_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user_mlp_id': instance.user.mlp_id, 
        'partner_mlp_id': instance.partner_mlp_id,  
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

#For delete profile model
@receiver(post_save, sender=DeleteProfile)
def log_delete_profile_creation(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'mlp_id': instance.mlp_id,
            'reason': instance.reason,
            'experience': instance.experience,
            'deleted_at': instance.deleted_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=DeleteProfile)
def log_delete_profile_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'mlp_id': instance.mlp_id,
        'reason': instance.reason,
        'experience': instance.experience,
        'deleted_at': instance.deleted_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

#For Report User model
@receiver(post_save, sender=ReportUsers)
def log_report_users_changes(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user_mlp_id': instance.user.mlp_id,  # Include mlp_id of the user
            'report_user_mlp_id': instance.report_user.mlp_id,  # Include mlp_id of the report user
            'reason': instance.reason,
            'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  # Convert datetime to string
            'updated_date': instance.updated_date.strftime("%Y-%m-%d %H:%M:%S"),  # Convert datetime to string
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=ReportUsers)
def log_report_users_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user_mlp_id': instance.user.mlp_id,  # Include mlp_id of the user
        'report_user_mlp_id': instance.report_user.mlp_id,  # Include mlp_id of the report user
        'reason': instance.reason,
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

# # For Notifications model(confirm once)
# @receiver(post_save, sender=Notifications)
# def log_notifications_changes(sender, instance, created, **kwargs):
#     if created:
#         app_name = instance._meta.app_label
#         model_name = instance._meta.model_name
#         fields = {
#             'user_mlp_id': instance.user.mlp_id,
#             'sender_mlp_id': instance.sender.mlp_id if instance.sender else None, 
#             'message': instance.message,
#             'type': instance.type,
#             'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"),  
#             'is_seen': instance.is_seen,
#         }
#         ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)
#     else:
#         app_name = instance._meta.app_label
#         model_name = instance._meta.model_name
#         fields = {
#             'user_mlp_id': instance.user.mlp_id,  
#             'sender_mlp_id': instance.sender.mlp_id if instance.sender else None,  
#             'message': instance.message,
#             'type': instance.type,
#             'created_date': instance.created_date.strftime("%Y-%m-%d %H:%M:%S"), 
#             'is_seen': instance.is_seen,
#         }
#         ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

# @receiver(post_delete, sender=Notifications)
# def log_notifications_deletion(sender, instance, **kwargs):
#     app_name = instance._meta.app_label
#     model_name = instance._meta.model_name
#     fields = {
#         'user_mlp_id': instance.user.mlp_id,  
#         'sender_mlp_id': instance.sender.mlp_id if instance.sender else None,  
       
#     }
#     ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


# For User model
@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
     if not created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
       
        if isinstance(instance.dob, str):
            dob = datetime.strptime(instance.dob, "%Y-%m-%d")  # Convert string to datetime object
        else:
            dob = instance.dob

        dob_str = dob.strftime("%Y-%m-%d") if dob else None
        if isinstance(instance.time_birth, str):
            # Convert string to time object
            time_birth = datetime.strptime(instance.time_birth, "%H:%M:%S").time()
        else:
            time_birth = instance.time_birth

        time_birth_str = time_birth.strftime("%H:%M:%S") if time_birth else None
        fields = {
            'mlp_id': instance.mlp_id,
            'mobile_number': instance.mobile_number if instance.mobile_number else None,
            'name': instance.name if instance.name else None,
            'email': instance.email if instance.email else None,
            'gender': instance.gender if instance.gender else None,
            'dob': dob_str,
            'time_birth': time_birth_str,
            'birth_location': instance.birth_location if instance.birth_location else None,
            'horoscope_matching': instance.horoscope_matching if instance.horoscope_matching else None,
            'about': instance.about if instance.about else None,
            'future_aspirations': instance.future_aspirations if instance.future_aspirations else None,
            'is_primary_account': instance.is_primary_account if instance.is_primary_account else None,
            'religion': instance.religion.name if instance.religion else None,
            'profile_pictures': json.loads(instance.profile_pictures) if instance.profile_pictures else None,
            'video': json.loads(instance.video) if instance.video else None,
            'family_photos': json.loads(instance.family_photos) if instance.family_photos else None,
            'manglik': instance.manglik if instance.manglik else None,
            'height': instance.height if instance.height else None,
            'weight': instance.weight if instance.weight else None,
            'complexion': instance.complexion if instance.complexion else None,
            'body_build': instance.body_build if instance.body_build else None,
            'physical_status': instance.physical_status if instance.physical_status else None,
            'salary': instance.salary if instance.salary else None,
            'password': instance.password if instance.password else None,
            'whatsapp_number': instance.whatsapp_number if instance.whatsapp_number else None,
            'marital_status': instance.marital_status.name if instance.marital_status and instance.marital_status.name else None,
            'eating_habits': instance.eating_habits if instance.eating_habits else None,
            'smoking_habits': instance.smoking_habits if instance.smoking_habits else None,
            'drinking_habits': instance.drinking_habits if instance.drinking_habits else None,
            'hobbies': json.loads(instance.hobbies) if instance.hobbies else None,
            'other_hobbies': json.loads(instance.other_hobbies) if instance.other_hobbies else None,
            'activity_status': instance.activity_status if instance.activity_status else None,
            'city': instance.city if instance.city else None,
            'state': instance.state if instance.state else None,
            'country': instance.country if instance.country else None,
            'caste': instance.caste if instance.caste else None,
            'sub_caste': instance.sub_caste.name if instance.sub_caste else None,
            'mandatory_questions_completed': instance.mandatory_questions_completed,
            'profile_createdby': instance.profile_createdby if instance.profile_createdby else None,
            'disease_history': instance.disease_history if instance.disease_history else None,
            'blood_group': instance.blood_group if instance.blood_group else None,
            'graduation_status': instance.graduation_status if instance.graduation_status else None,
            'graduation_institute': instance.graduation_institute if instance.graduation_institute else None ,
            'post_graduation_status': instance.post_graduation_status if  instance.post_graduation_status else None,
            'post_graduation_institute': instance.post_graduation_institute if instance.post_graduation_institute else None ,
            'profession': instance.profession if instance.profession else None,
            'specialization': instance.specialization.name if instance.specialization else None,
            'profession_description': instance.profession_description if instance.profession_description else None,
            'schooling_details': instance.schooling_details if instance.schooling_details else None,
            'facebook_profile': instance.facebook_profile if instance.facebook_profile else None,
            'instagram_profile': instance.instagram_profile if instance.instagram_profile else None,
            'linkedin_profile': instance.linkedin_profile if instance.linkedin_profile else None,
            'mother_name': instance.mother_name if instance.mother_name else None,
            'mother_occupation': instance.mother_occupation if instance.mother_occupation else None,
            'mother_education': instance.mother_education if instance.mother_education else None,
            'father_name': instance.father_name if instance.father_name else None,
            'father_occupation': instance.father_occupation if instance.father_occupation else None,
            'father_education': instance.father_education if instance.father_education else None,
            'sibling': instance.sibling if instance.sibling else None,
            'family_financial_status': instance.family_financial_status if instance.family_financial_status else None,
            'family_environment': instance.family_environment if  instance.family_environment else None,
            'family_car': instance.family_car if  instance.family_car else None,
            'city_parents': instance.city_parents if instance.city_parents else None,
            'family_house': instance.family_house if instance.family_house else None,
            'own_car': instance.own_car if instance.own_car else None,
            'residence': instance.residence if instance.residence else None,
            'religious_practices': instance.religious_practices if instance.religious_practices else None,
            'interest_party': instance.interest_party if instance.interest_party else None,
            'interest_music': instance.interest_music if  instance.interest_music else None,
            'foodie': instance.foodie if instance.foodie else None,
            'nature': instance.nature  if instance.nature else None,
            'beauty_consciousness': instance.beauty_consciousness if  instance.beauty_consciousness else None,
            'work_out': instance.work_out if instance.work_out else None,
            'body_clock': instance.body_clock if instance.body_clock else None,
            'kids_choice': instance.kids_choice if instance.kids_choice else None,
            'registration_number': instance.registration_number if instance.registration_number else None,
            'eyesight': instance.eyesight if instance.eyesight else None,
            'preferred_time_connect': instance.preferred_time_connect if instance.preferred_time_connect else None,
            'phone_is_verified': instance.phone_is_verified if instance.phone_is_verified else None,
            'can_upgrade_subscription': instance.can_upgrade_subscription if instance.can_upgrade_subscription else None,
            'graduation_obj': instance.graduation_obj.name if instance.graduation_obj else None,
            'completed_post_grad': instance.completed_post_grad if instance.completed_post_grad else None,
            #'completed_post_grad': instance.completed_post_grad if instance.completed_post_grad else None,
            'partner_age_preference': instance.partner_age_preference if instance.partner_age_preference else None,
            'partner_age_from': instance.partner_age_from if instance.partner_age_from else None,
            'partner_age_to': instance.partner_age_to if instance.partner_age_to else None,
            'partner_height_preference': instance.partner_height_preference if instance.partner_height_preference else None,
            'partner_height_from': instance.partner_height_from if instance.partner_height_from else None,
            'partner_height_to': instance.partner_height_to if instance.partner_height_to else None,
            'partner_cities_preference': instance.partner_cities_preference if instance.partner_cities_preference else None,
            'partner_cities_from': json.loads(instance.partner_cities_from) if instance.partner_cities_from else None,
            'partner_state_preference': instance.partner_state_preference if instance.partner_state_preference else None,
            'partner_state_from': json.loads(instance.partner_state_from) if instance.partner_state_from else None,
            'partner_country_preference': instance.partner_country_preference if instance.partner_country_preference else None,
            'partner_country_from': json.loads(instance.partner_country_from) if instance.partner_country_from else None,
            'partner_caste_preference': instance.partner_caste_preference if instance.partner_caste_preference else None,
            'partner_caste_from': json.loads(instance.partner_caste_from) if instance.partner_caste_from else None,
            'partner_mother_tongue_preference': instance.partner_mothertongue_preference if instance.partner_mothertongue_preference else None,
            # 'partner_mothertongue_from': json.loads(instance.partner_mothertongue_from) if instance.partner_mothertongue_from else None,
            'partner_expertise_preference': instance.partner_expertise_preference if instance.partner_expertise_preference else None,
            'partner_religion_preference': instance.partner_religion_preference if instance.partner_religion_preference else None,
            'partner_marital_status_preference': instance.partner_marital_status_preference if instance.partner_marital_status_preference else None,
            'partner_specialization_preference': instance.partner_specialization_preference if instance.partner_specialization_preference else None,
            'partner_graduation_preference': instance.partner_graduation_preference if instance.partner_graduation_preference else None,
            'partner_postgraduation_preference': instance.partner_postgraduation_preference if instance.partner_postgraduation_preference else None,
            'partner_income_from': instance.partner_income_from if instance.partner_income_from else None,
            'partner_income_to': instance.partner_income_to if instance.partner_income_to else None,
            'is_active': instance.is_active,
            'is_wrong' : instance.is_wrong
        }
        existing_logs = ChangeLog.objects.filter(app_name=app_name, model_name=model_name, fields__mlp_id=instance.mlp_id)
        if not existing_logs.exists():
            action = 'create'
        else:
            action = 'update' 
        if instance.name and instance.gender and instance.mlp_id:       
            ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)
        # # If mandatory questions are completed, send data to external API
        # if instance.mandatory_questions_completed:
        #     send_user_data_to_external_api(fields)

        
@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'mlp_id': instance.mlp_id
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For User Post Graduation model
@receiver(post_save, sender=UserPostGraduation)
def log_user_postgraduation_changes(sender, instance, created, **kwargs):
    if created:     
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user': instance.user.mlp_id ,
            'post_graduation': instance.post_graduation.name
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)
    else:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user': instance.user.mlp_id,
            'post_graduation': instance.post_graduation.name
        }
        ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=UserPostGraduation)
def log_user_postgraduation_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id,
        'post_graduation': instance.post_graduation.name
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

#For Partner Expertise Preference
@receiver(post_save, sender=PartnerExpertisePreference)
def log_partner_expertise_preference_changes(sender, instance, created, **kwargs):
    if created:
        action = 'create'
    else:
        action = 'update'
        
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id,
        'expertise': instance.expertise.name
    }
    ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=PartnerExpertisePreference)
def log_partner_expertise_preference_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id ,
        'expertise': instance.expertise.name
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

#For Partner Pg Preference
@receiver(post_save, sender=PartnerPGPreference)
def log_partner_pg_preference_changes(sender, instance, created, **kwargs):
    if created:
        action = 'create'
    else:
        action = 'update'
        
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id,
        'post_graduation': instance.post_graduation.name
    }
    ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=PartnerPGPreference)
def log_partner_pg_preference_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id ,
        'post_graduation': instance.post_graduation.name
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Partner Graduation Preference
@receiver(post_save, sender=PartnerGraduationPreference)
def log_partner_graduation_preference_changes(sender, instance, created, **kwargs):
    if created:
        action = 'create'
    else:
        action = 'update'
        
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id ,
        'graduation': instance.graduation.name
    }
    ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=PartnerGraduationPreference)
def log_partner_graduation_preference_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id,
        'graduation': instance.graduation.name
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

#For Partner Specialization Preference
@receiver(post_save, sender=PartnerSpecializationPreference)
def log_partner_specialization_preference_changes(sender, instance, created, **kwargs):
    if created:
        action = 'create'
    else:
        action = 'update'
        
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id,
        'specialization': instance.specialization.name
    }
    ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=PartnerSpecializationPreference)
def log_partner_specialization_preference_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id ,
        'specialization': instance.specialization.name
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

#For Partner Religion Preference
@receiver(post_save, sender=PartnerReligionPreference)
def log_partner_religion_preference_changes(sender, instance, created, **kwargs):
    if created:
        action = 'create'
    else:
        action = 'update'
        
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id,
        'religion': instance.religion.name
    }
    ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=PartnerReligionPreference)
def log_partner_religion_preference_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id ,
        'religion': instance.religion.name
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)


#For Partner Marital Status Preference
@receiver(post_save, sender=PartnerMaritalStatusPreference)
def log_partner_marital_status_preference_changes(sender, instance, created, **kwargs):
    if created:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user': instance.user.mlp_id,
            'marital_status': instance.marital_status.name
        }
        ChangeLog.objects.create(action='create', app_name=app_name, model_name=model_name, fields=fields)
    else:
        app_name = instance._meta.app_label
        model_name = instance._meta.model_name
        fields = {
            'user': instance.user.mlp_id,
            'marital_status': instance.marital_status.name
        }
        ChangeLog.objects.create(action='update', app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=PartnerMaritalStatusPreference)
def log_partner_marital_status_preference_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id,
        'marital_status': instance.marital_status.name
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)



# # For Coupon model
# @receiver(post_save, sender=Coupon)
# def log_coupon_changes(sender, instance, created, **kwargs):
#     action = 'create' if created else 'update'
#     app_name = instance._meta.app_label
#     model_name = instance._meta.model_name
#     fields = {
#         'code': instance.code,
#         'discount_percent': instance.discount_percent,
#         'is_expired': instance.is_expired,
#         'expire_after_days': instance.expire_after_days,
#         'one_user_only': instance.one_user_only,
#         'assigned_user': instance.assigned_user.mlp_id if instance.assigned_user else None,
#         'assigned_subscription': instance.assigned_subscription.id if instance.assigned_subscription else None,
#     }
#     ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

# @receiver(post_delete, sender=Coupon)
# def log_coupon_deletion(sender, instance, **kwargs):
#     app_name = instance._meta.app_label
#     model_name = instance._meta.model_name
#     fields = {
#         'code': instance.code,
#         'discount_percent': instance.discount_percent,
#         'is_expired': instance.is_expired,
#         'expire_after_days': instance.expire_after_days,
#         'one_user_only': instance.one_user_only,
#         'assigned_user': instance.assigned_user.mlp_id if instance.assigned_user else None,
#         'assigned_subscription': instance.assigned_subscription.id if instance.assigned_subscription else None,
#     }
#     ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

# For TransactionEntity model
@receiver(post_save, sender=TransactionEntity)
def log_transaction_entity_changes(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'mihpayid': instance.mihpayid,
        'status': instance.status,
        'amount': instance.amount,
        'user': instance.user.mlp_id if instance.user else None,
        'coupon_code': instance.coupon_code.code if instance.coupon_code else None,
        'subscription': instance.subscription.id if instance.subscription else None,
        'payload': instance.payload,
    }
    ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=TransactionEntity)
def log_transaction_entity_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'mihpayid': instance.mihpayid,
        'status': instance.status,
        'amount': instance.amount,
        'user': instance.user.mlp_id if instance.user else None,
        'coupon_code': instance.coupon_code.code if instance.coupon_code else None,
        'subscription': instance.subscription.id if instance.subscription else None,
        'payload': instance.payload,
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)

# For AppleTransactionEntity model
@receiver(post_save, sender=AppleTransactionEntity)
def log_apple_transaction_entity_changes(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id if instance.user else None,
        'status': instance.status,
        'amount': instance.amount,
        'coupon_code': instance.coupon_code.code if instance.coupon_code else None,
        'subscription': instance.subscription.id if instance.subscription else None,
    }
    ChangeLog.objects.create(action=action, app_name=app_name, model_name=model_name, fields=fields)

@receiver(post_delete, sender=AppleTransactionEntity)
def log_apple_transaction_entity_deletion(sender, instance, **kwargs):
    app_name = instance._meta.app_label
    model_name = instance._meta.model_name
    fields = {
        'user': instance.user.mlp_id if instance.user else None,
        'status': instance.status,
        'amount': instance.amount,
        'coupon_code': instance.coupon_code.code if instance.coupon_code else None,
        'subscription': instance.subscription.id if instance.subscription else None,
    }
    ChangeLog.objects.create(action='delete', app_name=app_name, model_name=model_name, fields=fields)
