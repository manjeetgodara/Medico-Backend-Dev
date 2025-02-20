import json
import logging
from users.models import *
from .models import *

logger = logging.getLogger("error_logger")

def update_notification_settings_func(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        mlp_id, email_notifications,name,phone, photo,salary, email = data.get("mlp_id",''), data.get("email_notifications",""),data.get("name",""), data.get("phone",""), data.get("photo",""), data.get("salary",""), data.get("email","")
        if not mlp_id:
            response['status_code'] = 301
            response['message'] = "mlp id missing"
            return response
        user = User.objects.filter(mlp_id=mlp_id)
        if user:
            user = user.first()
            existing_settings=NotificationSettings.objects.filter(user=user)
            if existing_settings:
                existing_settings = existing_settings.first()
                existing_settings.email_notifications = email_notifications
                existing_settings.name = name
                existing_settings.phone = phone
                existing_settings.photo = photo
                existing_settings.salary = salary
                existing_settings.email = email
                existing_settings.save()
            else:
                NotificationSettings.objects.get_or_create(user=user,email_notifications=email_notifications,name=name,phone=phone,photo=photo, salary=salary, email=email )
            response['status_code'] = 200
            response['message'] = "Settings updated successfully"
            return response
                
        else:
            response['status_code'] = 404
            response['message'] = "User not found"
            return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
def get_notification_settings_func(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        mlp_id = data.get("mlp_id","")
        if not mlp_id:
            response['status_code'] = 301
            response['message'] = "mlp id missing"
            return response
        user = User.objects.filter(mlp_id=mlp_id)
        if user:
            user = user.first()
            settings = NotificationSettings.objects.filter(user=user).all().values('user__mlp_id','email_notifications','name','phone','photo','salary','email')
            # print(list(settings))
            response['status_code'] = 200
            response['message'] = "Data sent successfully"
            response['data']=list(settings)
            return response
                
        else:
            response['status_code'] = 404
            response['message'] = "User not found"
            return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response