from pyfcm import FCMNotification
from users.models import *
from django.db.models import Q
from celery import shared_task
from firebase_admin import messaging

# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))

# @shared_task
# def shortlisted_notify(user_id,profile_id):
#     try: 
#         user_obj = User.objects.get(id=user_id)
#         profile = SavedUser.objects.get(id=profile_id)      
#         if not Intrest.objects.filter(Q(invitation_by=user_obj, invitation_to=profile.saved_profile)|(Q(invitation_by=profile.saved_profile, invitation_to=user_obj))):
#             custom_data={
#                 "screen":"shortlisted_profiles",
#                 "userid":user_obj.mlp_id
#                 }
#             if user_obj.notification_token!=None:
#                 push_service.notify_single_device(registration_id=user_obj.notification_token,message_title="Seize the Moment! 💖",message_body="You've shortlisted a profile that caught your eye. Why not take the next step? Send an interest now and make a meaningful connection! 💌",data_message=custom_data)
                   
#     except Exception as e:
#         print(f'{e.__traceback__.tb_lineno} - {str(e)}')


@shared_task
def shortlisted_notify(mlp_id,notification_token,profile_mlp):
    try: 
        print(f"{mlp_id} has saved profiles {profile_mlp}")     
        if not Intrest.objects.filter(Q(invitation_by__mlp_id=mlp_id, invitation_to__mlp_id=profile_mlp)|(Q(invitation_by__mlp_id=profile_mlp, invitation_to__mlp_id=mlp_id))):
            custom_data={
                "screen":"shortlisted_profiles",
                "userid":mlp_id
                }
            if notification_token!=None:
                    message = messaging.Message(
                        token=notification_token,  # FCM registration token
                        notification=messaging.Notification(
                            title="Seize the Moment! 💖",
                            body="You've shortlisted a profile that caught your eye. Why not take the next step? Send an interest now and make a meaningful connection! 💌"
                        ),
                        data=custom_data  # Custom data payload
                    )

                    res= messaging.send(message)
                # push_service.notify_single_device(registration_id=notification_token,message_title="Seize the Moment! 💖",message_body="You've shortlisted a profile that caught your eye. Why not take the next step? Send an interest now and make a meaningful connection! 💌",data_message=custom_data)
                   
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')