from django.http import JsonResponse, HttpResponseNotAllowed
from .service import *
import json
from urllib.parse import parse_qs
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import hashlib
from django.conf import settings

logger = logging.getLogger("error_logger")
t_logger = logging.getLogger("transactional_logger")

# Create your views here.
def payU(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = parse_qs(request.body.decode('utf-8'))
                data = {key: value[0] if len(value) == 1 else value for key, value in data.items()}
            response = execute_transaction(data)
            t_logger.info(f'status_code: {response["status_code"]}, message: {response["message"]}')
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def ios_purchase(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:  
                data = json.loads(request.body)
            #     data = json.loads(request.body.decode('utf-8'))
            # receipt_data = data.get('receipt_data')
            # transaction_data = data.get('transaction_data')
            response = verify_ios_receipt(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500, 'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])  


def get_ios_subscriptions(request):
    if request.method == 'GET':
        try:
            response = get_ios_subscriptions_list()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])     

def get_subscriptions(request):
    if request.method == 'GET':
        try:
            response = get_subscriptions_list()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])


def upgrade_subscriptions(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = upgrade_subscriptions_list(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def apply_coupons(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = check_coupon(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def get_user_coupons(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_coupons(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def web_app_payment_post_view(request,logged_mlp_id):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = web_app_payment_post(data,logged_mlp_id)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def get_web_app_payment_data_view(request,logged_mlp_id):
    if request.method == 'GET':
        try:
            response = get_web_app_payment_data(logged_mlp_id)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])



class CreatePaymentLink(APIView):

    def generate_token(self):
        url = settings.PAYU_GENERATE_TOKEN_URL
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.PAYU_CLIENT_ID,
            "client_secret": settings.PAYU_CLIENT_SECRET,
            "scope": settings.PAYU_SCOPE
        }
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            logger.error(f"Failed to get token: {response.text}")
            return None

    def post(self, request):
        try:
            data = request.data

            required_fields = ["subAmount", "description", "source","transactionId", "couponCode","subscriptionId", "countryCode", "phone","mlp_id"]
            for field in required_fields:
                if field not in data:
                    return Response({"error": f"Missing {field}"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate token
            token = self.generate_token()
            if not token:
                return Response({"error": "Failed to generate token"}, status=status.HTTP_502_BAD_GATEWAY)

            # Prepare payload for the payment link API
            payload = {
                "subAmount": data["subAmount"],
                "isPartialPaymentAllowed": data.get("isPartialPaymentAllowed", False),
                "description": data["description"],
                "source": data["source"],
                "transactionId": data["transactionId"],
                "udf": {
                    "udf1": data["couponCode"],  
                    "udf2": data["subscriptionId"],  
                    "udf3": f"{data['countryCode']}{data['phone']}", 
                    "udf4": data["mlp_id"] 
                }
            }

            # URL and headers for the API call
            url = 'https://oneapi.payu.in/payment-links'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'merchantId': settings.PAYU_MERCHANT_ID  # Assuming this is defined in your settings
            }

            # Make the POST request
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                try:
                    response_data = response.json()
                except ValueError:
                    logger.error("Failed to parse JSON response from PayU")
                    return Response({"error": "Failed to parse JSON response from PayU"}, status=status.HTTP_502_BAD_GATEWAY)

                if 'result' in response_data and 'paymentLink' in response_data['result']:
                    print(response_data['result'])
                    res_data={
                        "payment_link": response_data['result']['paymentLink'],
                        "transactionId" :response_data['result']['transactionId'],
                        "udf":response_data['result']['udf']
                    }
                    return Response({"message": "Payment link created successfully", "payment_link": res_data}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Payment link not found in the response", "details": response_data}, status=status.HTTP_502_BAD_GATEWAY)
            else:
                return Response({"error": "Failed to create payment link", "details": response.text}, status=response.status_code)

        except requests.RequestException as e:
            logger.error(f"Request to PayU failed: {str(e)}")
            return Response({"error": "Request to payment gateway failed", "details": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

