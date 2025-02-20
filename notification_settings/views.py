from django.shortcuts import render
import logging
from .service import *
from django.http import JsonResponse, HttpResponseNotAllowed

# Create your views here.

logger = logging.getLogger("error_logger")

def update_notification_settings(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = update_notification_settings_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    

def get_notification_settings(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_notification_settings_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
