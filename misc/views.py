from django.http import JsonResponse, HttpResponseNotAllowed
from .service import *
import json
import logging
logger = logging.getLogger("error_logger")

# Create your views here.

def sync(request):
    if request.method == 'GET':
        try:
            response = sync_data()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])



def user_data_sync(request):
    response = {
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method == 'GET':
        try:
            response = fetch_and_store_data()
            return JsonResponse(response)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])    


def reterieve_sync_data(request):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            response= get_change_log_data()
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])     
    