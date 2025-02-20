from pyfcm import FCMNotification
from users.models import *
from django.db.models import Q
from celery import shared_task
from firebase_admin import messaging

# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))

@shared_task
def story_notify(mlp_id,notification_token):
    try:
        custom_data={
            "screen":"home",
            "userid":mlp_id
            }
        if notification_token!=None:
                message = messaging.Message(
                        token=notification_token,  # FCM registration token
                        notification=messaging.Notification(
                            title="Matchmaking Moments: Explore New Stories 💖",
                            body="Check out the latest uploads and connect with potential matches. Don't miss out on the chance to meet someone special."
                        ),
                        data=custom_data  # Custom data payload
                    )

                res= messaging.send(message)
            # push_service.notify_single_device(registration_id=notification_token,message_title="Matchmaking Moments: Explore New Stories 💖",message_body="Check out the latest uploads and connect with potential matches. Don't miss out on the chance to meet someone special.",data_message=custom_data)
        
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')