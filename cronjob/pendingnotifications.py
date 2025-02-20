from pyfcm import FCMNotification
from users.models import *
from django.db.models import Q
from celery import shared_task
from firebase_admin import messaging

# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))

@shared_task
def pending_notify(mlp_id,notification_token):
    try:
            unseennotifications = True 
            if unseennotifications: 
                custom_data={
                    "screen":"notifications",
                    "userid":mlp_id
                    }
                if notification_token!=None:
                    message = messaging.Message(
                        token=notification_token,  # FCM registration token
                        notification=messaging.Notification(
                            title="Missed Notifications! ⏰",
                            body="You've missed some notifications. Dive back in to see new stories, interests, and connections waiting for you. Your next great match might be just a tap away! 📲"
                        ),
                        data=custom_data  # Custom data payload
                    )

                    res= messaging.send(message)

                    # push_service.notify_single_device(registration_id=notification_token,message_title="Missed Notifications! ⏰",message_body="You've missed some notifications. Dive back in to see new stories, interests, and connections waiting for you. Your next great match might be just a tap away! 📲",data_message=custom_data)
                
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')