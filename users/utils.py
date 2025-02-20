import requests
from django.http import JsonResponse
import os
import logging
from .models import *
import firebase_admin
from firebase_admin import firestore
from datetime import datetime
import uuid
from pyfcm import FCMNotification
from django.db.models import Q
from notification_settings.models import *
from datetime import timedelta
import redis
from firebase_admin import messaging

# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))

logger = logging.getLogger("error_logger")

api_key = os.getenv("AUTH_KEY")

def connect(redis_db_instance=0):
    try:
        redis_connection_pool = redis.ConnectionPool(
            host = os.getenv("REDIS_HOST"),
            port = os.getenv("REDIS_PORT"),
            password = os.getenv("REDIS_PASSWORD"),
            db=redis_db_instance
        )
        redis_client = redis.Redis(connection_pool=redis_connection_pool)
        
        return redis_client
    except Exception as err:
        print("Error while connecting redis client >> ", str(err))
        return False

def send_otp(mobile_number, otp):
    # print(mobile_number, otp)
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:  
        url = "https://api.msg91.com/api/v5/otp"
        message = f"Dear Member, {otp} is your one time password (OTP) to authenticate your Medico Life Partner Account."
        
        payload={
            "authkey": api_key,
            "template_id":"60ccbb90d524b63e0b647ae3",
            "mobile":mobile_number,
            "otp":otp,
            "message":message
        }
        headers = {
        "accept": "application/json",
        "content-type": "application/json",
        
    }
        response = requests.post(
        url,
        json=payload,
        headers=headers,
        
        )
        # print(response.json())
        response = response.json()
        response_type = response.get("type")  
        
        return response_type
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

def registration_success(mobile_number):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        url = "https://control.msg91.com/api/v5/send"
        message = f"Hi, Welcome to medicolifepartner.com, Your account is successfully activated, Please login to complete your profile and start searching"
        
        payload = {
            "message": message,
            "mobile": mobile_number,
            "authkey": api_key,
            "route":4
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
        }
        response = requests.post(
        url,
        json=payload,
        headers=headers,
        
        )
        print(response.json())
        response = response.json()
        response_type = response.get("type")  
        
        return response_type
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
    
def sms_send(phone,message,template_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        
        url = f"https://api.msg91.com/api/sendhttp.php?mobiles={phone}&authkey={api_key}&route=4&sender=EXLVEN&message={message}&country=0&template-id={template_id}"
        
        response = requests.get(url)
        return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

def check_contact_count(user, profile, subscription, allowed_contact_view):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try: 
        if subscription and user:
            # Check whether the contacts seen are within the created date of subscription
            created_date = subscription.created_date
            
            contacts_seen = ContactViewed.objects.filter(user=user).exclude(created_date__lte=created_date).count()
            print(contacts_seen, allowed_contact_view)
            if contacts_seen < allowed_contact_view:
               # ContactViewed.objects.get_or_create(user=user, seen_contact=profile)
                # if user.mlp_id:
                #     message = f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile"
                #     Notifications.objects.get_or_create(user=profile,sender=user,message=message, type="detailview")
                #     custom_data={
                #         "screen":"detailview",
                #         "userid":user.mlp_id
                #         }
                #     if profile.notification_token!=None:
                        
                #         push_service.notify_single_device(registration_id=profile.notification_token,message_title="Profile Visited",message_body=f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile",data_message=custom_data)
                #     all_linked_users=LinkedAccount.objects.filter(primary_user=profile).all()
                    
                #     notificationtokens=[]
                #     for i in all_linked_users:
                #         if i.linked_user.notification_token:
                #             notificationtokens.append(i.linked_user.notification_token) 
                    
                #     if notificationtokens:
                #         message_body = f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile"
                #         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title="Profile Visited",message_body=message_body,data_message=custom_data)
            
                response = {
                    'status_code': 200,
                    'message': 'Open',
                    "param":1
                }
                return response
            Notifications.objects.get_or_create(user=user,message=f"Oops! Contact limit reached. Upgrade your subscription to unlock more contacts.", type="reminder")
            custom_data={
                "screen":"subscriptions",
                "userid":user.mlp_id
                }
            if user.notification_token!=None:
                message = messaging.Message(
                token=user.notification_token,  # FCM registration token
                notification=messaging.Notification(
                    title="Contact limit reached",
                    body="Oops! Contact limit reached. Upgrade your subscription to unlock more contacts."
                ),
                data=custom_data 
                )

                messaging.send(message)
                
                # push_service.notify_single_device(registration_id=user.notification_token,message_title="Contact limit reached",message_body="Oops! Contact limit reached. Upgrade your subscription to unlock more contacts.",data_message=custom_data)
            all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
            
            notificationtokens=[]
            for i in all_linked_users:
                if i.linked_user.notification_token:
                    notificationtokens.append(i.linked_user.notification_token) 
            
            if notificationtokens:
                message_body = f"{user.name}'s contact limit has reached. Upgrade subscription to unlock more contacts."
                message = messaging.MulticastMessage(
                    tokens=notificationtokens,  # List of FCM registration tokens
                    notification=messaging.Notification(
                        title="Contact limit reached",
                        body=message_body,
                    ),
                    data = custom_data
                )

                messaging.send_multicast(message)
                # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title="Contact limit reached",message_body=message_body,data_message=custom_data)
            
            if timezone.now().date() - created_date.date() <= timedelta(days=30):
                response = {
                        'status_code': 404,
                        'message': 'Close',
                        'param':3
                    }
                return response
            else:
                response = {
                        'status_code': 404,
                        'message': 'Close',
                        'param':4
                    }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

def viewed_contacts(user, profile):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        print("Inside viewed contact api")
        contact_viewed_existing = ContactViewed.objects.filter(user=user, seen_contact=profile)
        print("contacts",contact_viewed_existing)
        # Contact already viewed in previous subscription plan
        if contact_viewed_existing:
            response={
                'status_code': 200,
                'message': "Open",
                "param":7
            }
            return response
        print("Before Existing subscription")
        existing_subscription = UserSubscription.objects.filter(user=user, is_subscription_active=True)
        # If no existing subscription then contact cannot be viewed
        print("existing_subscription", existing_subscription)
        if not existing_subscription:
            response={
                'status_code': 405,
                'message': "Close",
                "param":2
            }
            return response
        print("Before Notification setting")
        notification_settings = NotificationSettings.objects.filter(user=profile)
        print("notify",notification_settings)
        if notification_settings:
            notification_settings = notification_settings.first()
            if notification_settings.phone == "interests":
                
                exist_int=Intrest.objects.filter(Q(invitation_by=profile, invitation_to=user)|Q(invitation_by=user, invitation_to=profile, status="Accepted"))
                if exist_int:
                    response={
                        'status_code': 200,
                        'message': "Open",
                        "param":5
                    }
                    return response
                else:
                    response={
                        'status_code': 405,
                        'message': "Close",
                        "param":6
                    }
                    return response
        
        print("before existing subscription details")
        # If there is an active subscription (Only one)
        existing_subscription=existing_subscription.first()
        print("exists",existing_subscription)
        if not existing_subscription:
            response={
                'status_code': 405,
                'message': "Close",
                "param":2
            }
            return response
        
        existing_subscription_name = existing_subscription.subscription.name if existing_subscription else None
        print("Subscription Name:", existing_subscription_name)

        if existing_subscription_name == "Premium Plus":
            #ContactViewed.objects.get_or_create(user=user, seen_contact=profile)
            # if user.mlp_id:
            #     message = f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile"
            #     Notifications.objects.get_or_create(user=profile,sender=user,message=message, type="detailview")
            #     custom_data={
            #             "screen":"detailview",
            #             "userid":user.mlp_id
            #             }
            #     if profile.notification_token!=None:
                        
            #             push_service.notify_single_device(registration_id=profile.notification_token,message_title="Profile Visited",message_body=f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile",data_message=custom_data)
            #     all_linked_users=LinkedAccount.objects.filter(primary_user=profile).all()
                
            #     notificationtokens=[]
            #     for i in all_linked_users:
            #         if i.linked_user.notification_token:
            #             notificationtokens.append(i.linked_user.notification_token) 
                
            #     if notificationtokens:
            #         message_body = f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile"
            #         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title="Profile Visited",message_body=message_body,data_message=custom_data)
            
            response={
                'status_code': 200,
                'message': "Open",
                "param":1
            }
            return response
        elif existing_subscription_name=="Platinum":
            if existing_subscription.subscription.regular_plan:
                allowed_contacts = 150
                return check_contact_count(user,profile,existing_subscription,allowed_contacts)
        elif existing_subscription_name == "Platinum Plus":
            response={
                'status_code': 200,
                'message': "Open",
                "param":1
            }
            return response
        elif existing_subscription_name == "Silver":
            if existing_subscription.subscription.regular_plan:
                allowed_contacts = 35
                return check_contact_count(user,profile,existing_subscription,allowed_contacts)
        elif existing_subscription_name == "Silver Plus":
                allowed_contacts = 50
                return check_contact_count(user,profile,existing_subscription,allowed_contacts)
        elif existing_subscription_name == "Gold":
            if existing_subscription.subscription.regular_plan:
                allowed_contacts = 75
                return check_contact_count(user,profile,existing_subscription,allowed_contacts)
        elif existing_subscription_name == "Gold Plus" :
                allowed_contacts = 100
                return check_contact_count(user,profile,existing_subscription,allowed_contacts)
            
        elif existing_subscription_name == "Gold Plus Web":
            response={
                'status_code': 200,
                'message': "Open",
                'param' : 1
            }
            return response
        elif existing_subscription_name == "Premium Old":
            response={
                'status_code': 200,
                'message': "Open",
                'param' : 1
            }
            return response
        elif existing_subscription_name == "Gold Old":
                allowed_contacts = 300
                return check_contact_count(user, profile, existing_subscription, allowed_contacts)
        elif existing_subscription_name == "Diamond":
            response={
                'status_code': 200,
                'message': "Open",
                'param' : 1
            }
            return response
        elif existing_subscription_name == "Premium Plus Web":
            response={
                'status_code': 200,
                'message': "Open",
                'param' : 1
            }
            return response
        elif existing_subscription_name == "Super Value":
            response={
                'status_code': 200,
                'message': "Open",
                'param' : 1
            }
            return response
        elif existing_subscription_name == "Super Saver":
                allowed_contacts = 25
                return check_contact_count(user, profile, existing_subscription, allowed_contacts)
        elif existing_subscription_name == "Silver Old":
                allowed_contacts = 150
                return check_contact_count(user, profile, existing_subscription, allowed_contacts)
        elif existing_subscription_name == "Platinum Old":
            response={
                'status_code': 200,
                'message': "Open",
                'param' : 1
            }
            return response
        elif existing_subscription_name == "Classic":
            response={
                'status_code': 200,
                'message': "Open",
                'param' : 1
            }
            return response    
        else:
            response={
                'status_code': 405,
                'message': "Close",
                "param":2
            }
            return response   
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def show_photographs(user,profile):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        if user and profile:
            # existing_settings = NotificationSettings.objects.filter(user=profile)
            
            existing_settings = profile.notification_settings.first()
            if existing_settings:
                # existing_settings=existing_settings.first()
                if existing_settings.photo=="paid":
                    # usersubscription = UserSubscription.objects.filter(user=user,is_subscription_active=True)
                    usersubscription=user.usersubscription.filter(is_subscription_active=True).exists()
                    if usersubscription:
                        response={
                        'status_code': 200,
                        'message': "Open"
                        }
                        return response
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                elif existing_settings.photo=="interests":
                    exist_int=Intrest.objects.filter(Q(invitation_by=profile, invitation_to=user)|Q(invitation_by=user, invitation_to=profile, status="Accepted"))
                    if exist_int:
                        response={
                            'status_code': 200,
                            'message': "Open"
                        }
                        return response
                    
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                response={
                            'status_code': 200,
                            'message': "Open"
                        }
                return response
            else:
                response={
                'status_code': 200,
                'message': "Open"
            }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def show_photographs_data(userid,profileid):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        user = User.objects.filter(mlp_id=userid).first()
        profile = User.objects.filter(mlp_id=profileid).first()

        if user and profile:
            # existing_settings = NotificationSettings.objects.filter(user=profile)
            
            existing_settings = profile.notification_settings.first()
            if existing_settings:
                # existing_settings=existing_settings.first()
                if existing_settings.photo=="paid":
                    # usersubscription = UserSubscription.objects.filter(user=user,is_subscription_active=True)
                    usersubscription=user.usersubscription.filter(is_subscription_active=True).exists()
                    if usersubscription:
                        response={
                        'status_code': 200,
                        'message': "Open"
                        }
                        return response
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                elif existing_settings.photo=="interests":
                    exist_int=Intrest.objects.filter(Q(invitation_by=profile, invitation_to=user)|Q(invitation_by=user, invitation_to=profile, status="Accepted"))
                    if exist_int:
                        response={
                            'status_code': 200,
                            'message': "Open"
                        }
                        return response
                    
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                response={
                            'status_code': 200,
                            'message': "Open"
                        }
                return response
            else:
                response={
                'status_code': 200,
                'message': "Open"
            }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
        

def show_salary(user,profile):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        if user and profile:
            existing_settings = profile.notification_settings.first()
            if existing_settings:
                # existing_settings=existing_settings.first()
                if existing_settings.salary=="paid":
                    usersubscription = user.usersubscription.filter(is_subscription_active=True).exists()
                    if usersubscription:
                        response={
                        'status_code': 200,
                        'message': "Open"
                        }
                        return response
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                elif existing_settings.salary=="interests":
                    exist_int=Intrest.objects.filter(Q(invitation_by=profile, invitation_to=user)|Q(invitation_by=user, invitation_to=profile, status="Accepted"))
                    if exist_int:
                        response={
                            'status_code': 200,
                            'message': "Open"
                        }
                        return response
                    
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                response={
                            'status_code': 200,
                            'message': "Open"
                        }
                return response
            else:
                response={
                'status_code': 200,
                'message': "Open"
            }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def show_name(user,profile):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        if user and profile:
            usersubscription = user.usersubscription.filter(is_subscription_active=True).exists()
            if not usersubscription:
                response={
                        'status_code': 405,
                        'message': "Close"
                    }
                return response
            existing_settings = profile.notification_settings.first()
            if existing_settings:
                # existing_settings=existing_settings.first()
                if existing_settings.name=="paid":
                    
                    if usersubscription:
                        response={
                        'status_code': 200,
                        'message': "Open"
                        }
                        return response
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                elif existing_settings.name=="interests":
                    exist_int=Intrest.objects.filter(Q(invitation_by=profile, invitation_to=user)|Q(invitation_by=user, invitation_to=profile, status="Accepted"))
                    if exist_int:
                        response={
                            'status_code': 200,
                            'message': "Open"
                        }
                        return response
                    
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                response={
                            'status_code': 200,
                            'message': "Open"
                        }
                return response
            else:
                response={
                    'status_code': 200,
                    'message': "Open"
                }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def show_name_data(userid,profileid):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        user = User.objects.filter(mlp_id=userid).first()
        profile = User.objects.filter(mlp_id = profileid).first()

        if user and profile:
            usersubscription = user.usersubscription.filter(is_subscription_active=True).exists()
            if not usersubscription:
                response={
                        'status_code': 405,
                        'message': "Close"
                    }
                return response
            existing_settings = profile.notification_settings.first()
            if existing_settings:
                # existing_settings=existing_settings.first()
                if existing_settings.name=="paid":
                    
                    if usersubscription:
                        response={
                        'status_code': 200,
                        'message': "Open"
                        }
                        return response
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                elif existing_settings.name=="interests":
                    exist_int=Intrest.objects.filter(Q(invitation_by=profile, invitation_to=user)|Q(invitation_by=user, invitation_to=profile, status="Accepted"))
                    if exist_int:
                        response={
                            'status_code': 200,
                            'message': "Open"
                        }
                        return response
                    
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                response={
                            'status_code': 200,
                            'message': "Open"
                        }
                return response
            else:
                response={
                    'status_code': 200,
                    'message': "Open"
                }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

def show_data(user_subscription,notification_name,auth_mlp_id , user_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        if user_subscription and notification_name:
            usersubscription = user_subscription
            if not usersubscription:
                response={
                        'status_code': 405,
                        'message': "Close"
                    }
                return response
            existing_settings = notification_name
            if existing_settings:
                # existing_settings=existing_settings.first()
                if notification_name=="paid":
                    
                    if usersubscription:
                        response={
                        'status_code': 200,
                        'message': "Open"
                        }
                        return response
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                elif notification_name=="interests":
                    exist_int=Intrest.objects.filter(Q(invitation_by__mlp_id=user_id, invitation_to__mlp_id=auth_mlp_id)|Q(invitation_by__mlp_id=auth_mlp_id, invitation_to__mlp_id=user_id, status="Accepted"))
                    if exist_int:
                        response={
                            'status_code': 200,
                            'message': "Open"
                        }
                        return response
                    
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                response={
                            'status_code': 200,
                            'message': "Open"
                        }
                return response
            else:
                response={
                    'status_code': 200,
                    'message': "Open"
                }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response



def show_data_photo(user_subscription,notification_photo,auth_mlp_id , user_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        if user_subscription and notification_photo:
            # existing_settings = NotificationSettings.objects.filter(user=profile)
            
            existing_settings = notification_photo
            if existing_settings:
                # existing_settings=existing_settings.first()
                if notification_photo=="paid":
                    # usersubscription = UserSubscription.objects.filter(user=user,is_subscription_active=True)
                    usersubscription=user_subscription
                    if usersubscription:
                        response={
                        'status_code': 200,
                        'message': "Open"
                        }
                        return response
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                elif notification_photo=="interests":
                    exist_int=Intrest.objects.filter(Q(invitation_by__mlp_id=user_id, invitation_to__mlp_id=auth_mlp_id )|Q(invitation_by__mlp_id=auth_mlp_id , invitation_to__mlp_id=user_id, status="Accepted"))
                    if exist_int:
                        response={
                            'status_code': 200,
                            'message': "Open"
                        }
                        return response
                    
                    response={
                        'status_code': 405,
                        'message': "Close"
                    }
                    return response
                response={
                            'status_code': 200,
                            'message': "Open"
                        }
                return response
            else:
                response={
                'status_code': 200,
                'message': "Open"
            }
                return response
        else:
            response = {
                    'status_code': 400,
                    'message': 'Fields not provided'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    

def add_data_firebase(data,msgId):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        db=firestore.client()
        if db and data:
            
            # chats_ref = db.collection('chats').where('userIds', '==', data.get('allmlpids')).limit(1)
            # chats_ref_reverse = db.collection('chats').where('userIds', '==', data.get('allmlpids')[::-1]).limit(1)
            sorted_mlpids = sorted([data.get('mlpid1'), data.get('mlpid2')])
            document_id=f'chat_{sorted_mlpids[0]}_{sorted_mlpids[1]}'
            chat_ref = db.collection('chats').document(document_id)
            # if chats_ref.get() or chats_ref_reverse.get():
            if chat_ref.get().exists:
                # Add data in the existing
                # print(chats_ref)
                chat_ref.collection('messages').document().set({
                    'id': msgId,
                    'content': data.get('lastMessage'),
                    'timestamp': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    'senderId': data.get('lastMsgUserId'),
                    'isSeen': False,
                    'isDeliver':False,
                    'type': "text"
                })
                # existing_doc_ref = chats_ref.get()[0].reference if chats_ref.get() else chats_ref_reverse.get()[0].reference
                chat_ref.update({
                    'id': document_id,
                    'lastMessage':data.get('lastMessage'),
                    'lastMsgUserId':data.get('lastMsgUserId'),
                    # 'messages':firestore.ArrayUnion([{
                    #     'id':msgId,
                    #     'content': data.get('lastMessage'),
                    #     'timestamp': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    #     'senderId': data.get('lastMsgUserId'),
                    #     'type':"text"}
                    # ]),
                    'userIds': sorted_mlpids,
                    'timestamp':datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                })
                response={
                    'status_code': 200,
                    'message': 'Data updated successfully'
                }
                return response
            else:
                datatoadd={
                    'id': document_id,
                    'lastMessage':data.get('lastMessage'),
                    'lastMsgUserId':data.get('lastMsgUserId'),
                    # 'messages':[{
                    #     'id':msgId,
                    #     'content': data.get('lastMessage'),
                    #     'timestamp': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    #     'senderId': data.get('lastMsgUserId'),
                    #     'type':"text"}
                    # ],
                    'userIds': sorted_mlpids,
                    "onlineusers":[],
                    'timestamp':datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                }
                # doc_ref=db.collection('chats').document(document_id)
                chat_ref.set(datatoadd)
                chat_ref.collection('messages').document().set({
                    'id': msgId,
                    'content': data.get('lastMessage'),
                    'timestamp': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    'senderId': data.get('lastMsgUserId'),
                    'isSeen': False,
                    'isDeliver':False,
                    'type': "text"
                })
                response={
                    'status_code': 200,
                    'message': 'Data added successfully'
                }
                return response
        else:
            response={
                    'status_code': 400,
                    'message': 'Failed to connect to firebase'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
def delete_data_firebase(id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        db=firestore.client()
        if db and id:
            doc_ref = db.collection('chats').document(id)
            if doc_ref:
                doc_ref.delete()
                response={
                    'status_code': 200,
                    'message': 'Chat deleted successfully'
                }
                return response
            else:
                response={
                    'status_code': 404,
                    'message': 'No chat found'
                }
                return response
        else:
            response={
                    'status_code': 400,
                    'message': 'Failed to connect to firebase'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
def add_field_firebase(mlp_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        db=firestore.client()
        if db and mlp_id:
            chats_ref = db.collection('chats').where('userIds', 'array_contains', mlp_id).stream()
            
            for el in chats_ref:
                doc_reference = db.collection('chats').document(el.id)
                currentonlineusers=doc_reference.get().to_dict().get('onlineusers',[])
                if not currentonlineusers:
                    doc_reference.update({"onlineusers":[mlp_id]})
                elif mlp_id not in currentonlineusers:
                    doc_reference.update({"onlineusers":firestore.ArrayUnion([mlp_id])})
            response={
                    'status_code': 200,
                    'message': 'Data updated successfully'
                }
            return response
        else:
            response={
                    'status_code': 400,
                    'message': 'Failed to connect to firebase'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
def delete_field_firebase(mlp_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        db=firestore.client()
        if db and mlp_id:
            chats_ref = db.collection('chats').where('userIds', 'array_contains', mlp_id).stream()
            
            for el in chats_ref:
                doc_reference = db.collection('chats').document(el.id)
                currentonlineusers=doc_reference.get().to_dict().get('onlineusers',[])
                if currentonlineusers and mlp_id in currentonlineusers:
                    doc_reference.update({"onlineusers":firestore.ArrayRemove([mlp_id])})
            response={
                    'status_code': 200,
                    'message': 'Data updated successfully'
                }
            return response
        else:
            response={
                    'status_code': 400,
                    'message': 'Failed to connect to firebase'
                }
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response