from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotAllowed
from .service import *
from .decorators import *
# from django.views.decorators.csrf import csrf_exempt
import logging
import boto3
from uuid import uuid4
from MLP.services.utils.seswrapper import SesWrapper




logger = logging.getLogger("error_logger")

# Create your views here.
def update_user(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = update_user_details(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def get_choices(request):
    if request.method == 'GET':
        try:
            response = get_question_choices()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])
    

def get_expertise_choices(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_graduation_objs(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def get_sub_caste_choices(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_subcaste_objs(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def block_profile(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = block_user(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def unblock_profile(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = unblock_user(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def send_requests(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = send_intrests(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def update_mobile_number(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = update_mobile_request(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def verify_updated_mobile(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = update_mobile_OTP_verify(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def shortlist(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = save_profiles(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def unshortlist(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = unsave_profiles(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def unlinkuser(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = unlink_userfunc(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def get_about(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_self_profile(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

@user_validation()
def get_profile(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_user_profile(data, request.user_obj)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

  
@user_validation()
def remove_sibling(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = delete_sibling(data, request.user_obj)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

  
def user_recommendation(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_user_recommendation(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def most_viewed_profiles(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_most_viewed_profile(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def popular_profiles(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_popular_profiles(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

  
def discovery(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_feed(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def delete_profile(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = delete_user_profile(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def get_recieved_intrests_view(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_recieved_intrests(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def get_intrests(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_intrests_requests(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def get_blocked_users(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_blocked_profiles(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def get_shortlisted(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_saved_profiles(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])


def generate_presigned_url(request,file_extension=""):
    if request.method == "GET":
        try:
            folder = request.GET.get("folder") or "DoctorImages"
            
            bucketname = os.getenv('S3_BUCKET_NAME')
            accesskey = os.getenv("S3_ACCESS_KEY_ID")
            secretkey = os.getenv("S3_SECRET_KEY")
            s3 = boto3.client('s3', region_name='ap-south-1', aws_access_key_id=accesskey, aws_secret_access_key=secretkey)
            file_key = f"{folder}/{uuid4()}"
            presigned_url = s3.generate_presigned_url(
                'put_object',
                Params={'Bucket': bucketname, 'Key': file_key},
                ExpiresIn=3600
            )
            s3_location = presigned_url.split("?")[0]
            return JsonResponse({'status_code': 200, 'presigned_url': presigned_url, 'file_key': file_key,'s3_bucket' : bucketname,'s3_location':s3_location, 'error':False})
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])


def signup(request):
    if request.method == 'POST':
        try:
            print("Signup API got hit")
            body = json.loads(request.body)
            print("Signup API body fetched")
            print("Signup API entering function")
            res = signupfunc(body)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({"message":"Internal server error","status_code":500})
    else:
        return HttpResponseNotAllowed(['POST'])


def verify_otp(request):
    if request.method=="POST":
        try:
            body=json.loads(request.body)
            res = verifyotpfunc(body)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({"message":"Internal Server error","status_code":500})
          
    else:
        return HttpResponseNotAllowed(['POST'])

def verify_otpforlinked(request):
    if request.method=="POST":
        try:
            print(request.body)
            data=json.loads(request.body)
            res = verifyotpforlinkedfunc(data)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({"message":"Internal Server error","status_code":500})
          
    else:
        return HttpResponseNotAllowed(['POST'])

def add_linkeduser(request):
    if request.method=="POST":
        try:
            body=json.loads(request.body)
            res = addlinkeduserfunc(body)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            # print(e)
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({"message":"Internal Server error","status_code":500})
          
    else:
        return HttpResponseNotAllowed(['POST'])
    
def add_linkeduserforedit(request):
    if request.method=="POST":
        try:
            body=json.loads(request.body)
            res = addlinkeduserforeditfunc(body)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            # print(e)
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({"message":"Internal Server error","status_code":500})
          
    else:
        return HttpResponseNotAllowed(['POST'])

def respond_interestreceived(request):
    if request.method=="POST":
        try:
            body=json.loads(request.body)
            res = respond_interestsfunc(body)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def get_mutuallyaccepted(request):
    if request.method=="POST":
        try:
            body=json.loads(request.body)
            res = getmutuallyacceptedfunc(body)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def send_email_successfullregistration(request):
    if request.method=="POST":
        try:
            body=json.loads(request.body)
            res = send_email_successfulregistration(body)
            return JsonResponse(res,status=res["status_code"])
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def get_notifications(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_notifications_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def validate_email(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = validate_email_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def contact_viewed(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = contact_viewed_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    

def post_stories(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = post_stories_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def get_own_stories(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_stories_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def get_all_stories(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_all_stories_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])

def delete_own_stories(request):
    if request.method == 'DELETE':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = delete_stories_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['DELETE'])
# To find Match percentage
def match_percentage(request):
    response = {
        'status': 500,
        "message": "Internal Server Error"
    }
    try:
        user_mlp_id = request.GET.get('user_mlp_id')
        logged_user_mlp_id = request.GET.get('logged_user_mlp_id')

        if user_mlp_id is not None and logged_user_mlp_id is not None:
            if request.method == "GET":
                response_data = calculate_match_percentage(
                    user_mlp_id, logged_user_mlp_id)
                return JsonResponse(response_data)
        else:
            return HttpResponseNotAllowed(['GET'])
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response           

#view for getting online users
def online_users(request,mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":       
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response = get_online_users(mlp_id, page, page_size)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
         return HttpResponseNotAllowed(['GET'])    

#view for newly joined users last month(sorting check)
def newly_joined_users(request,mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":  
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response = get_newly_joined(mlp_id,page,page_size)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])    
             
#view for users_near me in the same city
def users_near_me(request,mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":
        try: 
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response=get_users_near_me(mlp_id,page,page_size)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])   

#View for users viewed my profile
def users_viewed_my_profile(request,logged_mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response=get_users_viewed_my_profile(logged_mlp_id,page,page_size)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)  
    else:
        return HttpResponseNotAllowed(['GET'])     

#View for users whose profile viewed by me
def profile_viewed_by_me(request,logged_mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response=get_profile_viewed_by_me(logged_mlp_id,page,page_size)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)  
    else:
        return HttpResponseNotAllowed(['GET'])     
        
#view for contact seen users
def contact_seen(request,logged_mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response=get_contact_seen(logged_mlp_id,page,page_size)
            return JsonResponse(response)
        except  Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)  
    else:
        return HttpResponseNotAllowed(['GET']) 
    
#view for similar eduaction data
def similar_education(request,logged_mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":
        try: 
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response=get_similar_education_users(logged_mlp_id,page,page_size)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)            
    else:
        return HttpResponseNotAllowed(['GET'])    

#view for getting other user's data
def tier4_profiles(request,logged_mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method=="GET":
        try:  
           page = int(request.GET.get('page', 1))
           page_size = int(request.GET.get('page_size', 10))
           response=get_tier4_profiles(logged_mlp_id,page,page_size)
           return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)            
    else:
        return HttpResponseNotAllowed(['GET']) 
    

def add_rating_review_view(request,logged_mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body) 
                
            response=add_rating_review(data,logged_mlp_id)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['POST'])

def get_rating_review_view(request):
    response={
        "status": 500,
        "message":"Internal Server Error"
    }   
    if request.method=="GET":
        try:   
            response=get_rating_review()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET']) 


def bachelor_of_the_day(request,logged_mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            response=calculate_bachelor_of_the_day(logged_mlp_id)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET']) 


def delete_image(url):
    try:
        delete_imagefunc(url)
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

def test_com(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            ses_wrapper = SesWrapper()
            send_email = ses_wrapper.send_email(receiver_email_address=data.get('email'), subject=data.get('subject'), html_body=data.get('body'))
            return JsonResponse({"response":send_email})
        except Exception as e:
            return JsonResponse({"error":str(e)})
    else:
        return HttpResponseNotAllowed(['POST'])


def add_success_stories_view(request,logged_mlp_id):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body) 
                
            response=add_success_stories(data,logged_mlp_id)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['POST'])

def get_success_stories_view(request):
    response={
        "status": 500,
        "message": "Internal Server Error"
    }
    if request.method == 'GET':
        try:
            response=get_success_stories()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET']) 
    

def top_ten_profiles_view(request,logged_mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            response=top_ten_profiles(logged_mlp_id)
            return JsonResponse(response)

        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])  


def premium_profiles_view(request,logged_mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response= premium_profiles(logged_mlp_id,page,page_size)
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])        
    

def get_all_chats(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_all_chats_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def get_all_chatrequests(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_all_chatrequests_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def get_all_mysentchats(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = get_all_mysentchats_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def report_profile(request):
    if request.method == 'POST':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = reportprofile_func(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['POST'])
    
def test_firebasedata(request):
    if request.method == 'GET':
        try:
            response = test_firebase()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])
    
def test_CRON(request):
    if request.method == 'GET':
        try:
            response = test_CRON_func()
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['GET'])
    
def delete_notificationtoken(request):
    if request.method == 'DELETE':
        try:
            data = {}
            if request and request.body:
                data = json.loads(request.body)
            response = deletenotificationtokenfunc(data)
            return JsonResponse(response)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse({'status_code': 500,'message': 'Internal server error'})
    else:
        return HttpResponseNotAllowed(['DELETE'])
#newly joined last week view
def get_newly_joined_last_week_view(request,mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response= get_newly_joined_last_week(mlp_id,page ,page_size)
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])  

#same religion profile views
def same_religion_profiles_view(request,logged_mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response= same_religion_profiles(logged_mlp_id,page,page_size)
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET']) 

#same caste profiles view
def same_caste_profiles_view(request,logged_mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response= same_caste_profiles(logged_mlp_id,page,page_size)
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])    
               
    
# same height and age profile view    
def same_height_and_age_profiles_view(request,logged_mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response= same_height_and_age_profiles(logged_mlp_id,page,page_size)
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET']) 

#Newly joined last month view
def get_newly_joined_last_month_view(request,mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response= get_newly_joined_last_month(mlp_id,page,page_size)
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET']) 


# matched preference view
def matched_preference_view(request,logged_mlp_id):
    response={
        "status":500,
        "message":"Internal Server Error"
    }
    if request.method == 'GET':
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            response= matched_preference_service(logged_mlp_id,page,page_size)
            return JsonResponse(response)
         
        except Exception as e :
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
    else:
        return HttpResponseNotAllowed(['GET'])   


