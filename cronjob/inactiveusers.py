from pyfcm import FCMNotification
from users.models import *
from django.db.models import Q
from celery import shared_task
from firebase_admin import messaging

# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))

@shared_task
def inactive():
    try:
       user_objs = User.objects.filter(mandatory_questions_completed=False, is_active=True, is_wrong=False).all()
        
       for user_obj in user_objs.iterator():
            print("inactive user notify successfully",user_obj)
            custom_data={
                "screen":"login",
                "userid":user_obj.mlp_id
                }
            if user_obj.notification_token!=None:
                message = messaging.Message(
                    token=user_obj.notification_token,  # FCM registration token
                    notification=messaging.Notification(
                        title="Unlock the Full Experience! 🔓",
                        body="Hey there! It looks like you haven't completed your registration. Complete it now to discover exciting stories, connect with potential matches, and make the most of our community. Your perfect match awaits! 🌟",
                    ),
                    data=custom_data  # Custom data payload
                )
                res = messaging.send(message)
                # push_service.notify_single_device(registration_id=user_obj.notification_token,message_title="Unlock the Full Experience! 🔓",message_body="Hey there! It looks like you haven't completed your registration. Complete it now to discover exciting stories, connect with potential matches, and make the most of our community. Your perfect match awaits! 🌟",data_message=custom_data)   
            
            
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')