from pyfcm import FCMNotification
from users.models import *
from django.db.models import Q
from celery import shared_task
from firebase_admin import messaging

# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))


# @shared_task
# def interest_pending(user_id,interest_id):
#     try:
#         user_obj = User.objects.get(id=user_id)
#         interest = Intrest.objects.get(id=interest_id)
#         if interest:
#             # print(interest)
#             custom_data={
#                 "screen":"received_request",
#                 "userid":user_obj.mlp_id
#                 }
#             if user_obj.notification_token!=None: 
#                 push_service.notify_single_device(registration_id=user_obj.notification_token,message_title="Don't Miss Out! 🌟",message_body="Someone's interested in connecting with you! Check your interests and respond to spark a potential connection. Your next meaningful connection might be just a tap away! 💬",data_message=custom_data)
              
                
#     except Exception as e:
#         print(f'{e.__traceback__.tb_lineno} - {str(e)}')

@shared_task
def interest_pending(mlp_id,notification_token,interest):
    try:
        print(f"{mlp_id} has interested profiles {interest}")
        if interest:
            # print(interest)
            custom_data={
                "screen":"received_request",
                "userid":mlp_id
                }
            if notification_token!=None: 
                message = messaging.Message(
                    token=notification_token,  # FCM registration token
                    notification=messaging.Notification(
                        title="Don't Miss Out! 🌟",
                        body="Someone's interested in connecting with you! Check your interests and respond to spark a potential connection. Your next meaningful connection might be just a tap away! 💬",
                    ),
                    data=custom_data  # Custom data payload
                )
                res = messaging.send(message)

                # push_service.notify_single_device(registration_id=notification_token,message_title="Don't Miss Out! 🌟",message_body="Someone's interested in connecting with you! Check your interests and respond to spark a potential connection. Your next meaningful connection might be just a tap away! 💬",data_message=custom_data)
              
                
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')