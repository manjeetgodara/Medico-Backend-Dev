from functools import wraps
from .models import *
from django.http import JsonResponse
import json
import logging

logger = logging.getLogger("error_logger")

def user_validation(required_subscription=False):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            try:
                data = {}
                if request and request.body:
                    data = json.loads(request.body)
                mlp_id = data.get('mlp_id', '')
                if not mlp_id:
                    response = {
                        'status_code': 301,
                        'message': 'MLP id missing'
                    }
                    return JsonResponse(response)

                user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False).first()
                
                if not user_obj:
                    response = {
                        'status_code': 404,
                        'message': 'User not found'
                    }
                    return JsonResponse(response)

                # Check for subscription only if required_subscription is True
                if required_subscription and not user_obj.usersubscription.filter(is_subscription_active=True).exists():
                    response = {
                        'status_code': 403,
                        'message': 'User does not have a active subscription'
                    }
                    return JsonResponse(response)

                request.user_obj = user_obj  # Store user_obj in the request for later use
                return view_func(request, *args, **kwargs)
            except Exception as e:
                logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
                response = {
                    'status_code': 500,
                    'message': 'Internal server error'
                }
                return JsonResponse(response)

        return _wrapped_view

    return decorator
