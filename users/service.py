from .models import *
from django.db.models import Count
import math
import json
from datetime import datetime, timedelta, date
import time
import string
from dateutil.relativedelta import relativedelta
from django.db.models import Value, CharField, Case, When, F
from django.db.models.functions import Concat
import uuid
import jwt
from pyfcm import FCMNotification
from django.db.models import Q ,Exists, OuterRef
from django.contrib.postgres.aggregates import ArrayAgg
import logging
import random
from .utils import *
from MLP.services.emails import email_services
from search.serializers import UserSerializer
from django.conf import settings
from urllib.parse import urlparse
import boto3
from itertools import groupby
from MLP.services.utils.seswrapper import SesWrapper
from collections import defaultdict,Counter
from json.decoder import JSONDecodeError
from firebase_admin import firestore
from cronjob.main import main_cronjob
from django.core.paginator import Paginator
from django.core.cache import cache
import time
from users.constants import *
from django.db import transaction
from firebase_admin import messaging

logger = logging.getLogger("error_logger")
# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))
ses_wrapper = SesWrapper()
redis_client = connect()


def try_block_end_point(user_obj, endpoint, session):
    try:
        if user_obj and endpoint:
            one_minute_ago = timezone.now() - timezone.timedelta(seconds=35)
            BlockEndPoints.objects.filter(user=user_obj, endpoint=endpoint, created_date__lt=one_minute_ago).delete()
            if not BlockEndPoints.objects.filter(user=user_obj, endpoint=endpoint).exists():
                BlockEndPoints.objects.create(user=user_obj, endpoint=endpoint, session=session)
                return 1
        return 0
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return -1


def release_endpoint(user_obj, endpoint, session):
    try:
        if user_obj and endpoint:
            BlockEndPoints.objects.filter(user=user_obj, endpoint=endpoint, session=session).delete()
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')


def update_user_details(data):
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        expertise_obj = None
        religion_obj = None
        marital_status_obj = None
        if data.get('expertise_in') != None:
            expertise_obj = Expertise.objects.filter(id=data.get('expertise_in'))
        if data.get('religion') != None:
            religion_obj = Religion.objects.filter(id=data.get('religion'))
        if data.get('marital_status') != None:
            marital_status_obj = MaritalStatus.objects.filter(id=data.get('marital_status'))
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()

        if data.get('expertise_in') != None and not expertise_obj.first():
            response['status_code'] = 404
            response["message"] = "Expertise id not found"
            return response
        elif data.get('expertise_in') != None and expertise_obj.first():
            expertise_obj = expertise_obj.first()
        if data.get('religion') != None and not religion_obj.first():
            response['status_code'] = 404
            response["message"] = "Religion id not found"
            return response
        elif data.get('religion') != None and religion_obj.first():
            religion_obj = religion_obj.first()
        if data.get('marital_status') != None and not marital_status_obj.first():
            response['status_code'] = 404
            response["message"] = "Marital status id not found"
            return response
        elif data.get('marital_status') != None and marital_status_obj.first():
            marital_status_obj = marital_status_obj.first()
        elif data.get('unset_marital_status'):
            marital_status_obj = None
            user_obj.marital_status = marital_status_obj
            user_obj.save()
        
        updated_fields = []

        if data.get('name') != None:
            user_obj.name = data.get('name').title()
            updated_fields.append("name")
        if data.get('email') != None:
            user_obj.email = data.get('email').lower()
            updated_fields.append("email")
        if data.get('password') != None:
            user_obj.password = data.get('password')
            updated_fields.append("password")
        if data.get('whatsapp_number') != None:
            user_obj.whatsapp_number = data.get('whatsapp_number')
            updated_fields.append("whatsapp_number")
        if data.get('gender') != None:
            user_obj.gender = data.get('gender')
            updated_fields.append("gender")
        if data.get('dob') != None:
            try:
                if (datetime.strptime(data.get('dob'), '%d-%m-%Y').date() + relativedelta(years=18)) > datetime.now().date():
                    response["status_code"] = 302
                    response["message"] = "Invalid dob (less than 18 years)"
                    return response
                user_obj.dob = datetime.strptime(data.get('dob'), '%d-%m-%Y').date()
                updated_fields.append("dob")
            except ValueError:
                response['status_code'] = 302
                response["message"] = "Date is not in correct format i.e. dd-mm-yyyy"
                return response
        if religion_obj:
            user_obj.religion = religion_obj
            updated_fields.append("religion")
        if isinstance(data.get('profile_pictures'), list): 
            user_obj.profile_pictures = json.dumps(data.get('profile_pictures'))
            updated_fields.append("profile_pictures")
        if isinstance(data.get('video'), list): 
            user_obj.video = json.dumps(data.get('video'))
            updated_fields.append("video")
        if data.get('partner_age_preference') != None:
            if data.get('partner_age_from') == None:
                response['status_code'] = 301
                response["message"] = "preffered age from not found"
                return response
            if data.get('partner_age_to') == None:
                response['status_code'] = 301
                response["message"] = "preffered age to not found"
                return response
            user_obj.partner_age_from = data.get('partner_age_from')
            updated_fields.append("partner_age_from")
            user_obj.partner_age_to = data.get('partner_age_to')
            updated_fields.append("partner_age_to")
            user_obj.partner_age_preference = data.get('partner_age_preference')
            updated_fields.append("partner_age_preference")
        expertise_objs = None
        if data.get('partner_expertise_preference') != None:
            if data.get('partner_expertise_preference') and isinstance(data.get('partner_expertise_preference_ids'), list) and len(data.get('partner_expertise_preference_ids')):
                partner_expertise_preference_ids = data.get('partner_expertise_preference_ids')
                expertise_objs = Expertise.objects.filter(id__in=partner_expertise_preference_ids)
            elif data.get('partner_expertise_preference'):
                response['status_code'] = 301
                response["message"] = "Partner expertise preference not found"
                return response
            user_obj.partner_expertise_preference = data.get('partner_expertise_preference')
            updated_fields.append("partner_expertise_preference")
        if data.get('graduation_obj') != None:
            graduation_obj = Graduation.objects.filter(id=data.get('graduation_obj')).first()
            if not graduation_obj:
                response['status_code'] = 301
                response["message"] = "Graduation obj not found"
                return response
            user_obj.graduation_obj = graduation_obj
            updated_fields.append("graduation_obj")
        if data.get('completed_post_grad') != None:
            user_obj.completed_post_grad = data.get('completed_post_grad')
            updated_fields.append("completed_post_grad")

        post_graduation_objs = None
        if user_obj.completed_post_grad and isinstance(data.get('user_post_graduation'), list) and len(data.get('user_post_graduation')):
            user_post_graduation = list(set(data.get('user_post_graduation')))
            post_graduation_objs = PostGraduation.objects.filter(id__in=user_post_graduation)
            if len(set(post_graduation_objs.values_list('graduation_obj__id', flat=True))) > 1 or post_graduation_objs.first().graduation_obj != user_obj.graduation_obj:
                response['status_code'] = 304
                response["message"] = "Post graduation ids are incorrect"
                return response
            
        mandandatory_completed_after = completed_mandatory_questions(user_obj, expertise_objs, post_graduation_objs)
        if user_obj.mandatory_questions_completed == True and mandandatory_completed_after == False:
            response['status_code'] = 305
            response['message'] = 'Requered fields missing'
            return response
        elif user_obj.mandatory_questions_completed == False and mandandatory_completed_after == True:
            user_obj.mandatory_questions_completed = True
            updated_fields.append("mandatory_questions_completed")
            if user_obj.email:
                subject = f"About successfull registration at medicolifepartner.com"
                email_content = email_services.set_email_content_successfulregistration(user_obj)
                ses_wrapper.send_email(receiver_email_address=user_obj.email,subject=subject,html_body=email_content['message'])
            
        if expertise_objs:
            PartnerExpertisePreference.objects.filter(user=user_obj).exclude(expertise__in=expertise_objs).delete()
            for expertise_obj in expertise_objs:
                PartnerExpertisePreference.objects.get_or_create(user=user_obj, expertise=expertise_obj)

        if post_graduation_objs:
            UserPostGraduation.objects.filter(user=user_obj).exclude(post_graduation__in=post_graduation_objs).delete()
            for post_graduation_obj in post_graduation_objs:
                UserPostGraduation.objects.get_or_create(user=user_obj, post_graduation=post_graduation_obj)

        if marital_status_obj:
            user_obj.marital_status = marital_status_obj
            updated_fields.append("marital_status")
        if isinstance(data.get('family_photos'), list):
            user_obj.family_photos = json.dumps(data.get('family_photos'))
            updated_fields.append("family_photos")
        if data.get('manglik') != None:
            user_obj.manglik = data.get('manglik')
            updated_fields.append("manglik")
        if data.get('height') != None:
            user_obj.height = data.get('height')
            updated_fields.append("height")
        if data.get('weight') != None:
            user_obj.weight = data.get('weight')
            updated_fields.append("weight")
        if data.get('salary') != None:
            user_obj.salary = data.get('salary')
            updated_fields.append("salary")
        if data.get('eating_habits') != None:
            user_obj.eating_habits = data.get('eating_habits')
            updated_fields.append("eating_habits")
        if data.get('smoking_habits') != None:
            user_obj.smoking_habits = data.get('smoking_habits')
            updated_fields.append("smoking_habits")
        if data.get('drinking_habits') != None:
            user_obj.drinking_habits = data.get('drinking_habits')
            updated_fields.append("drinking_habits")
        if isinstance(data.get('hobbies'), list):
            user_obj.hobbies = json.dumps(data.get('hobbies'))
            updated_fields.append("hobbies")
        if isinstance(data.get('other_hobbies'), list):
            user_obj.other_hobbies = json.dumps(data.get('other_hobbies'))
            updated_fields.append("other_hobbies")
        if data.get('about') != None:
            user_obj.about = data.get('about')
            updated_fields.append("about")
        if data.get('future_aspirations') != None:
            user_obj.future_aspirations = data.get('future_aspirations')
            updated_fields.append("future_aspirations")
        if data.get('complexion') != None:
            user_obj.complexion = data.get('complexion')
            updated_fields.append("complexion")
        if data.get('body_build') != None:
            user_obj.body_build = data.get('body_build')
            updated_fields.append("body_build")
        if data.get('physical_status') != None:
            user_obj.physical_status = data.get('physical_status')
            updated_fields.append("physical_status")
        if data.get('eyesight') != None:
            user_obj.eyesight = data.get('eyesight')
            updated_fields.append("eyesight")
        if data.get('preferred_time_connect') != None:
            user_obj.preferred_time_connect = data.get('preferred_time_connect')
            updated_fields.append("preferred_time_connect")
        if data.get('mother_tongue')!= None:
            mother_tongue=data.get('mother_tongue')
            if isinstance(mother_tongue, list):
                new_list=MotherTongue.objects.filter(name__in=mother_tongue)
                if new_list:
                    user_obj.mother_tongue.set(new_list)
                else:
                    user_obj.mother_tongue.clear()
            else:
                response['status_code'] = 403
                response["message"] = "Invalid type for mother_tongue"
                return response
        if data.get('languagespoken')!= None:
            lang=data.get('languagespoken')
            if isinstance(lang, list):
                new_list=Languages.objects.filter(name__in=lang)
                if new_list:
                    user_obj.languages.set(new_list)
                else:
                    user_obj.languages.clear()
            else:
                response['status_code'] = 403
                response["message"] = "Invalid type for languagespoken"
                return response
        if data.get('city') != None:
            user_obj.city = data.get('city')
            updated_fields.append("city")
        if data.get('state') != None:
            user_obj.state = data.get('state')
            updated_fields.append("state")
        if data.get('country') != None:
            user_obj.country = data.get('country')
            updated_fields.append("country")
        if data.get('caste') != None:
            user_obj.caste = data.get('caste')
            updated_fields.append("caste")
        if data.get('subcaste') != None:
            if SubCaste.objects.filter(name=data.get('subcaste')).first():
                user_obj.sub_caste = SubCaste.objects.filter(name=data.get('subcaste')).first()
                updated_fields.append("sub_caste")
            else:
                response['status_code'] = 404
                response["message"] = "Subcaste not found"
                return response
            
        if data.get('profile_createdby') != None:
            user_obj.profile_createdby=data.get('profile_createdby')
            updated_fields.append("profile_createdby")
        if data.get('disease_history') != None:
            user_obj.disease_history=data.get('disease_history')
            updated_fields.append("disease_history")
        if data.get('blood_group') != None:
            user_obj.blood_group=data.get('blood_group')
            updated_fields.append("blood_group")
        if data.get('time_birth') != None:
            user_obj.time_birth=data.get('time_birth')
            updated_fields.append("time_birth")
        if data.get('birth_location') != None:
            user_obj.birth_location=data.get('birth_location')
            updated_fields.append("birth_location")  
        if data.get('horoscope_matching') != None:
            user_obj.horoscope_matching=data.get('horoscope_matching')
            updated_fields.append("horoscope_matching")  
        if data.get('graduation_status') != None:
            user_obj.graduation_status=data.get('graduation_status')
            updated_fields.append("graduation_status")  
        if data.get('graduation_institute') != None:
            user_obj.graduation_institute=data.get('graduation_institute')
            updated_fields.append("graduation_institute") 
        if data.get('post_graduation_status') != None:
            user_obj.post_graduation_status=data.get('post_graduation_status')
            updated_fields.append("post_graduation_status")  
        if data.get('post_graduation_institute') != None:
            user_obj.post_graduation_institute=data.get('post_graduation_institute')
            updated_fields.append("post_graduation_institute")  
        if isinstance(data.get('profession'), list):
            user_obj.profession = json.dumps(data.get('profession'))
            updated_fields.append("profession")
        if data.get('specialization') != None:
            if Specialization.objects.filter(name=data.get('specialization')).first():
                user_obj.specialization = Specialization.objects.filter(name=data.get('specialization')).first()
                updated_fields.append("specialization")
            else:
                response['status_code'] = 404
                response["message"] = "Specialization not found"
                return response
        else :
            user_obj.specialization = None 
            updated_fields.append("specialization")    
            
        if data.get('profession_description') != None:
            user_obj.profession_description=data.get('profession_description')
            updated_fields.append("profession_description")
        if data.get('schooling_details') != None:
            user_obj.schooling_details=data.get('schooling_details')
            updated_fields.append("schooling_details")
        if data.get('facebook_profile') != None:
            user_obj.facebook_profile=data.get('facebook_profile')
            updated_fields.append("facebook_profile")
        if data.get('instagram_profile') != None:
            user_obj.instagram_profile=data.get('instagram_profile')
            updated_fields.append("instagram_profile")
        if data.get('linkedin_profile') != None:
            user_obj.linkedin_profile=data.get('linkedin_profile')
            updated_fields.append("linkedin_profile")
        if data.get('mother_name') != None:
            user_obj.mother_name=data.get('mother_name')
            updated_fields.append("mother_name")
        if data.get('mother_occupation') != None:
            user_obj.mother_occupation=data.get('mother_occupation')
            updated_fields.append("mother_occupation")
        if data.get('mother_education') != None:
            user_obj.mother_education=data.get('mother_education')
            updated_fields.append("mother_education")
        if data.get('father_name') != None:
            user_obj.father_name=data.get('father_name')
            updated_fields.append("father_name")
        if data.get('father_occupation') != None:
            user_obj.father_occupation=data.get('father_occupation')
            updated_fields.append("father_occupation")
        if data.get('father_education') != None:
            user_obj.father_education=data.get('father_education')
            updated_fields.append("father_education")
        if data.get('sibling')!=None:
            user_obj.sibling=data.get('sibling')
            updated_fields.append("sibling")
        if data.get('siblingdata')!=None:
            siblingdata=data.get('siblingdata')
            for siblings in siblingdata:
                if siblings.get("id") is not None:
                    existingsibling = Siblings.objects.filter(id=siblings["id"]).first()
                    existingsibling.sibling_gender=siblings["gender"]
                    existingsibling.sibling_name=siblings["name"]
                    existingsibling.sibling_education=siblings["education"]
                    existingsibling.sibling_marital_status=siblings["marital_status"]
                    existingsibling.sibling_profession=siblings["profession"]
                    existingsibling.save()
                else:
                    newsibling=Siblings()
                    newsibling.user=user_obj
                    newsibling.sibling_gender=siblings["gender"]
                    newsibling.sibling_name=siblings["name"]
                    newsibling.sibling_education=siblings["education"]
                    newsibling.sibling_marital_status=siblings["marital_status"]
                    newsibling.sibling_profession=siblings["profession"]
                    newsibling.save()
        if data.get('linkedusers')!=None:
            for lu in data.get('linkedusers'):
                existing_user = User.objects.filter(mobile_number=lu["linkeduser_phone"]).first()
                existing_user.preferred_time_connect=lu["preferred_time_connect"]
                existing_user.save()
                if lu["relation"]!=None:
                    linkeduser=LinkedAccount.objects.filter(primary_user=user_obj,linked_user=existing_user)
                    if linkeduser.exists():
                        linkeduser=linkeduser.first()
                        linkeduser.relation = lu["relation"]
                        linkeduser.save()
                    else:
                        response['status_code'] = 404
                        response["message"] = "LinkedUser not found"
                        return response
        if data.get('family_financial_status')!=None:
            user_obj.family_financial_status=data.get('family_financial_status')
            updated_fields.append("family_financial_status")
        if data.get('family_environment')!=None:
            user_obj.family_environment=data.get('family_environment')
            updated_fields.append("family_environment")
        if data.get('family_car')!=None:
            user_obj.family_car=data.get('family_car')
            updated_fields.append("family_car")
        if data.get('city_parents')!=None:
            user_obj.city_parents=data.get('city_parents')
            updated_fields.append("city_parents")
        if data.get('family_house')!=None:
            user_obj.family_house=data.get('family_house')
            updated_fields.append("family_house")
        if data.get('own_car')!=None:
            user_obj.own_car=data.get('own_car')
            updated_fields.append("own_car")
        if data.get('residence')!=None:
            user_obj.residence=data.get('residence')
            updated_fields.append("residence")
        if data.get('religious_practices')!=None:
            user_obj.religious_practices=data.get('religious_practices')
            updated_fields.append("religious_practices")
        if data.get('interest_party')!=None:
            user_obj.interest_party=data.get('interest_party')
            updated_fields.append("interest_party")
        if data.get('interest_music')!=None:
            user_obj.interest_music=data.get('interest_music')
            updated_fields.append("interest_music")
        if data.get('foodie')!=None:
            user_obj.foodie=data.get('foodie')
            updated_fields.append("foodie")
        if data.get('nature')!=None:
            user_obj.nature=data.get('nature')
            updated_fields.append("nature")
        if data.get('beauty_consciousness')!=None:
            user_obj.beauty_consciousness=data.get('beauty_consciousness')
            updated_fields.append("beauty_consciousness")
        if data.get('work_out')!=None:
            user_obj.work_out=data.get('work_out')
            updated_fields.append("work_out")
        if data.get('body_clock')!=None:
            user_obj.body_clock=data.get('body_clock')
            updated_fields.append("body_clock")
        if data.get('kids_choice')!=None:
            user_obj.kids_choice=data.get('kids_choice')
            updated_fields.append("kids_choice")
        if data.get('registration_number')!=None:
            user_obj.registration_number=data.get('registration_number')
            updated_fields.append("registration_number")

        if data.get('partner_income_preference') is not None:
            if data.get('partner_income_from') is None:
                response['status_code'] = 301
                response["message"] = "preferred income from not found"
                return response
            if data.get('partner_income_to') is None:
                response['status_code'] = 301
                response["message"] = "preferred income to not found"
                return response
            user_obj.partner_income_from = data.get('partner_income_from')
            updated_fields.append("partner_income_from")
            user_obj.partner_income_to = data.get('partner_income_to')
            updated_fields.append("partner_income_to")
            user_obj.partner_income_preference = data.get('partner_income_preference')
            updated_fields.append("partner_income_preference")

        if data.get('partner_mothertongue_from')!= None:
            mt=data.get('partner_mothertongue_from')
            if isinstance(mt, list):
                new_list=MotherTongue.objects.filter(name__in=mt)
                if new_list:
                    user_obj.partner_mothertongue_from.set(new_list)
                else:
                    user_obj.partner_mothertongue_from.clear()
            else:
                response['status_code'] = 403
                response["message"] = "Invalid type for partner_mothertongue_from"
                return response
        if data.get('partner_physicalstatus')!=None:
            user_obj.partner_physicalstatus=data.get('partner_physicalstatus')
            updated_fields.append("partner_physicalstatus")
        
        if data.get('partner_height_preference') != None:
            if data.get('partner_height_from') == None:
                response['status_code'] = 301
                response["message"] = "preffered height from not found"
                return response
            if data.get('partner_height_to') == None:
                response['status_code'] = 301
                response["message"] = "preffered height from not found"
                return response
            user_obj.partner_height_from = data.get('partner_height_from')
            updated_fields.append("partner_height_from")
            user_obj.partner_height_to = data.get('partner_height_to')
            updated_fields.append("partner_height_to")
            user_obj.partner_height_preference = data.get('partner_height_preference')
            updated_fields.append("partner_height_preference")
        if data.get('partner_cities_preference') != None:
            if not isinstance(data.get('partner_cities_from'), list):
                response['status_code'] = 301
                response["message"] = "preffered Cities from list not found"
                return response
            user_obj.partner_cities_from = json.dumps(data.get('partner_cities_from'))
            updated_fields.append("partner_cities_from")
            user_obj.partner_cities_preference = data.get('partner_cities_preference')
            updated_fields.append("partner_cities_preference")
        if data.get('partner_state_preference') != None:
            if not isinstance(data.get('partner_state_from'), list):
                response['status_code'] = 301
                response["message"] = "preffered state from list not found"
                return response
            user_obj.partner_state_from = json.dumps(data.get('partner_state_from'))
            updated_fields.append("partner_state_from")
            user_obj.partner_state_preference = data.get('partner_state_preference')
            updated_fields.append("partner_state_preference")
        if data.get('partner_country_preference') != None:
            if not isinstance(data.get('partner_country_from'), list):
                response['status_code'] = 301
                response["message"] = "preffered country from list not found"
                return response
            user_obj.partner_country_from = json.dumps(data.get('partner_country_from'))
            updated_fields.append("partner_country_from")
            user_obj.partner_country_preference = data.get('partner_country_preference')
            updated_fields.append("partner_country_preference")
        if data.get('partner_caste_preference') != None:
            if not isinstance(data.get('partner_caste_from'), list):
                response['status_code'] = 301
                response["message"] = "preffered Caste from list not found"
                return response
            user_obj.partner_caste_from = json.dumps(data.get('partner_caste_from'))
            updated_fields.append("partner_caste_from")
            user_obj.partner_caste_preference = data.get('partner_caste_preference') if len(data.get('partner_caste_from')) else False
            updated_fields.append("partner_caste_preference")
        if data.get('partner_specialization_preference') != None:
            if data.get('partner_specialization_preference') and isinstance(data.get('partner_specialization_preference_ids'), list) and len(data.get('partner_specialization_preference_ids')):
                partner_specialization_preference_ids = data.get('partner_specialization_preference_ids')
                specialization_objs = Specialization.objects.filter(id__in=partner_specialization_preference_ids)
                PartnerSpecializationPreference.objects.filter(user=user_obj).exclude(specialization__in=specialization_objs).delete()
                for specialization_obj in specialization_objs:
                    PartnerSpecializationPreference.objects.get_or_create(user=user_obj, specialization=specialization_obj)
            elif data.get('partner_specialization_preference'):
                response['status_code'] = 301
                response["message"] = "Partner specialization preference not found"
                return response
            user_obj.partner_specialization_preference = data.get('partner_specialization_preference')
            updated_fields.append("partner_specialization_preference")    
        if data.get('partner_religion_preference') != None:
            if data.get('partner_religion_preference') and isinstance(data.get('partner_religion_preference_ids'), list) and len(data.get('partner_religion_preference_ids')):
                partner_religion_preference_ids = data.get('partner_religion_preference_ids')
                religion_objs = Religion.objects.filter(id__in=partner_religion_preference_ids)
                PartnerReligionPreference.objects.filter(user=user_obj).exclude(religion__in=religion_objs).delete()
                if not religion_objs.exists() and not user_obj.partnerexpertisepreference.all().exists():
                    user_obj.partner_religion_preference = False
                    updated_fields.append("partner_religion_preference")
                else:
                    for religion_obj in religion_objs:
                        PartnerReligionPreference.objects.get_or_create(user=user_obj, religion=religion_obj)
                    user_obj.partner_religion_preference = data.get('partner_religion_preference')
                    updated_fields.append("partner_religion_preference")
            elif data.get('partner_religion_preference'):
                response['status_code'] = 301
                response["message"] = "Partner religion preference not found"
                return response
            else:
                user_obj.partner_religion_preference = data.get('partner_religion_preference')
                updated_fields.append("partner_religion_preference")
        if data.get('partner_marital_status_preference') != None:
            if data.get('partner_marital_status_preference') and isinstance(data.get('partner_marital_status_preference_ids'), list) and len(data.get('partner_marital_status_preference_ids')):
                partner_marital_status_preference_ids = data.get('partner_marital_status_preference_ids')
                marital_status_objs = MaritalStatus.objects.filter(id__in=partner_marital_status_preference_ids)
                PartnerMaritalStatusPreference.objects.filter(user=user_obj).exclude(marital_status__in=marital_status_objs).delete()
                if not marital_status_objs.exists() and not user_obj.partnermaritalstatuspreference.all().exists():
                    user_obj.partner_marital_status_preference = False
                    updated_fields.append("partner_marital_status_preference")
                else:
                    for marital_status_obj in marital_status_objs:
                        PartnerMaritalStatusPreference.objects.get_or_create(user=user_obj, marital_status=marital_status_obj)
                    user_obj.partner_marital_status_preference = data.get('partner_marital_status_preference')
                    updated_fields.append("partner_marital_status_preference")
            elif data.get('partner_marital_status_preference'):
                response['status_code'] = 301
                response["message"] = "Partner marital preference not found"
                return response
            else:
                user_obj.partner_marital_status_preference = data.get('partner_marital_status_preference')
                updated_fields.append("partner_marital_status_preference")
        
        if user_obj.partner_expertise_preference:
            print("HERE")
            if data.get('partner_graduation_preference') != None:
                partner_graduation_preference_ids = data.get('partner_graduation_preference_ids')
                if user_obj.partner_expertise_preference and data.get('partner_graduation_preference') and isinstance(partner_graduation_preference_ids, list) and len(partner_graduation_preference_ids):
                    graduation_objs = Graduation.objects.filter(id__in=partner_graduation_preference_ids)
                    if not graduation_objs.exists():
                        response['status_code'] = 301
                        response["message"] = "Partner graduation preference not found"
                        return response
                    PartnerGraduationPreference.objects.filter(user=user_obj).exclude(graduation__in=graduation_objs).delete()
                    for graduation_obj in graduation_objs:
                        PartnerGraduationPreference.objects.get_or_create(user=user_obj, graduation=graduation_obj)
                elif user_obj.partner_expertise_preference and data.get('partner_graduation_preference'):
                    response['status_code'] = 301
                    response["message"] = "Partner graduation preference not found"
                    return response
                user_obj.partner_graduation_preference = data.get('partner_graduation_preference')
                updated_fields.append('partner_graduation_preference')
        else:
            user_obj.partner_graduation_preference = False
            updated_fields.append('partner_graduation_preference')
        
        if user_obj.partner_expertise_preference and user_obj.partner_graduation_preference:
            if data.get('partner_pg_preference') != None:
                partner_pg_preference_ids = data.get('partner_pg_preference_ids')
                if user_obj.partner_expertise_preference and user_obj.partner_graduation_preference and data.get('partner_pg_preference') and isinstance(partner_pg_preference_ids, list) and len(partner_pg_preference_ids):
                    pg_objs = PostGraduation.objects.filter(id__in=partner_pg_preference_ids)
                    if not pg_objs.exists():
                        response['status_code'] = 301
                        response["message"] = "Partner post graduation preference not found"
                        return response
                    PartnerPGPreference.objects.filter(user=user_obj).exclude(post_graduation__in=pg_objs).delete()
                    for pg_obj in pg_objs:
                        PartnerPGPreference.objects.get_or_create(user=user_obj, post_graduation=pg_obj)
                elif user_obj.partner_expertise_preference and user_obj.partner_graduation_preference and data.get('partner_pg_preference'):
                    response['status_code'] = 301
                    response["message"] = "Partner post graduation preference not found"
                    return response
                user_obj.partner_postgraduation_preference = data.get('partner_pg_preference')
                updated_fields.append('partner_postgraduation_preference')
        else:
            user_obj.partner_postgraduation_preference = False
            updated_fields.append('partner_postgraduation_preference')
        
        user_obj.save(update_fields=updated_fields)
        
        response['status_code'] = 200
        response['message'] = 'Request processed successfully'
        return response

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def get_graduation_objs(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        expertise_id = data.get('expertise_id', '')
        if not expertise_id:
            response['status_code'] = 301
            response['message'] = "expertise id missing"
            return response
        if not isinstance(expertise_id, list):
            expertise_id = [expertise_id]
        expertise_obj = Expertise.objects.filter(id__in=expertise_id)
        if not expertise_obj.exists():
            response['status_code'] = 404
            response['message'] = "expertise object not found"
            return response
        graduation_id = data.get('graduation_id', '')
        if not graduation_id:
            response['status_code'] = 201
            response['message'] = 'Graduation objects processed successfully'
            response['data'] = list(Graduation.objects.filter(expertise_obj__in=expertise_obj).values('id', 'name'))
            return response
        if not isinstance(graduation_id, list):
            graduation_id = [graduation_id]
        graduation_obj = Graduation.objects.filter(expertise_obj__in=expertise_obj, id__in=graduation_id)
        if not graduation_obj.exists():
            response['status_code'] = 404
            response['message'] = "Graduation object not found"
            return response
        response['status_code'] = 200
        response['message'] = "Post Graduation objects processed successfully"
        response['data'] = list(PostGraduation.objects.filter(graduation_obj__in=graduation_obj).values('id', 'name'))
        return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

def get_subcaste_objs(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        caste = data.get('caste', '')
        if not caste:
            response['status_code'] = 301
            response['message'] = "caste is missing"
            return response
        response['status_code'] = 200
        response['message'] = "Subcaste objects processed successfully"
        response['data'] = list(SubCaste.objects.all().values('id', 'name'))
        return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
def get_question_choices():
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        # expertise_objs = list(Expertise.objects.all().values())
        # graduation_objs = list(Graduation.objects.all().values())
        # post_graduation_objs = list(PostGraduation.objects.all().values())
        # religion_objs = list(Religion.objects.all().values())
        # marital_status_objs = list(MaritalStatus.objects.all().values())
        specialization_objs = list(Specialization.objects.all().order_by('name').values())
        mothertongue_objs = list(MotherTongue.objects.all().order_by('name').values())
        languages_objs = list(Languages.objects.all().order_by('name').values())
        caste = list(Caste.objects.all().order_by('name').values())
        
        data = {
            #'gender': [{"id": id, "name": ele} for id, ele in GENDER],
            # 'eating_habits': [{"id": id, "name": ele} for id, ele in EATING_HABITS],
            # 'smoking_habits': [{"id": id, "name": ele} for id, ele in SMOKING_HABITS],
            # 'drinking_habits': [{"id": id, "name": ele} for id, ele in DRINKING_HABITS],
            # 'expertise_objs': expertise_objs,
            # 'graduation_objs': graduation_objs,
            # 'post_graduation_objs': post_graduation_objs,
            # 'religion_objs': religion_objs,
            # 'marital_status_objs': marital_status_objs,
            "specialization_objs":specialization_objs,
            "mothertongue_objs":mothertongue_objs,
            "languages_objs":languages_objs,
            "caste":caste
        }
        response['status_code'] = 200
        response['message'] = 'Request processed successfully'
        response['data'] = data
        return response
        
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def send_email_successfulregistration(body):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id=body.get('mlp_id')
        if mlp_id:
            user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False).first()
            if user_obj:
                subject = f"About successfull registration at medicolifepartner.com"
                    
                email_content = email_services.set_email_content_successfulregistration(user_obj)
                ses_wrapper.send_email(receiver_email_address=user_obj.email,subject=subject,html_body=email_content['message'])
                # email_services.send_email(subject,email_content['message'],to_email=[user_obj.email])
                response['status_code']=200
                response['message']='Email sent successfully'
                return response
            else:
                response['status_code']=400
                response['message']='User not found'
                return response
        else:
            response['status_code']=400
            response['message']='MLP ID not provided'
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    

# def signupfunc(body):
#     response = {
#         'status_code': 500,
#         'message': 'Internal server error'
#     }
#     try:
#         print("Signupfunc got hit", body)
#         phone = body.get('phone')
#         res={}
#         # Generate OTP
#         starttime=time.time()
#         print("Beforesxistinguserquery")
#         existing_user = User.objects.filter(mobile_number=phone).first()
        
#         print(existing_user)
#         if existing_user and not existing_user.is_active:
#             response['status_code'] = 404
#             response['message'] = "The account is deleted. Please contact to admin"
#             return response
#         print("existingusertime", time.time()-starttime)

#         otp = str(random.randint(1000, 9999))
#         #otp="1234"
#         # Generate session ID
#         session_id = str(uuid.uuid4())
#         # Store OTP session in the database
#         expires_at = datetime.now() + timedelta(minutes=5)
#         if phone:
#             starttime1=time.time()
#             previous_session=OTPSession.objects.filter(identifier=phone)
#             if previous_session.exists():
#                 previous_session.delete()
#             otp_session = OTPSession(
#                 otp=otp, expires_at=expires_at, session_id=session_id, identifier=phone)
#             otp_session.save()
#             print("OTPSession time", time.time()-starttime1)
#             starttime2=time.time()
#             otp_response = send_otp(phone, otp)
#             print("SendOTP", time.time()-starttime2)
#             # otp_response = "success"
#             print("OTPResponse", otp_response)
#             if otp_response=="success":
#                 # user_obj = User.objects.filter(mobile_number__contains=phone).first()
#                 if existing_user is None:
#                     # Create a new user if none exists with the given phone number
#                     starttime3=time.time()
#                     print("Beforecreatinguser")
#                     mlp_id = "MLP00"+hashlib.shake_128(phone.encode('ASCII')).hexdigest(4)
#                     user_instance_arr=[User(mobile_number=phone, mlp_id=mlp_id)]
#                     User.objects.bulk_create(user_instance_arr)
#                     print("CreateUSer", time.time()-starttime3)
#                 # else:
#                 #     # User already exists, set 'created' flag to False
#                 #     created = False
#                 # user_obj, created = User.objects.get_or_create(mobile_number__contains=phone)
#                 # if not created and not existing_user.is_primary_account and not LinkedAccount.objects.filter(linked_user=existing_user).exists():
#                 #     User.objects.filter(mobile_number=phone).delete()
#                 #     User.objects.create(mobile_number=phone)
#                 response['status_code'] = 200
#                 response['message'] = "OTP sent Successfully"
#                 response['session_id'] = session_id
#                 return response
#             else:
#                 res={'message': 'Failed to send OTP',"status_code":403,"error":True}
#                 return res
#         else:
#             res={'message': 'Please enter phonenumber',"status_code":403,"error":True}
#             return res
#     except Exception as e:
#     # traceback.print_exc()
#         logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
#         return response

def signupfunc(body):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        print("Signupfunc got hit", body)
        phone = body.get('phone')
        res = {}
        # Generate OTP
        starttime = time.time()
        print("Before existing user query")
        existing_user = User.objects.filter(mobile_number=phone , is_active =True,is_wrong=False )
        print("all_users",existing_user)

        # if existing_user.exists():
        #     if existing_user.filter(Q(can_upgrade_subscription=1) | Q(can_upgrade_subscription=0) ).exists():
        #         if len(existing_user.filter(Q(can_upgrade_subscription=1) | Q(can_upgrade_subscription=0) )) >1:
        #             response['status_code'] = 300
        #             response['message'] = "From this number multiple accounts are present"
        #             return response
        #         existing_user = existing_user.filter(Q(can_upgrade_subscription=1) | Q(can_upgrade_subscription=0)).first()
        #         print("paid_or_unpaid_members", existing_user)
                
        #     else:
        #         existing_user = existing_user.first()
        #         print("first_member", existing_user)
        # else:
        #     existing_user = None   
        if existing_user.exists():
            upgradeable_users = existing_user.filter(Q(can_upgrade_subscription=1) | Q(can_upgrade_subscription=0))
            print("paid_accounts",upgradeable_users)
            if upgradeable_users.exists():
                if upgradeable_users.count() > 1:
                    response['status_code'] = 300
                    response['message'] = "Multiple active accounts are associated with this phone number."
                    return response
                selected_user = upgradeable_users.first()
                print("paid_login",selected_user)
            else:
                # existing_user = existing_user.first()
                # In the case of no accounts with can_upgrade_subscription
                # Check for mandatory_questions_completed preference
                selected_user = existing_user.filter(mandatory_questions_completed=True).first()
                
                if not selected_user:
                    # Step 3: If none completed mandatory questions, pick the first created user
                    selected_user = existing_user.order_by('created_date').first()
                print("preferred_user_based_on_mandatory_questions", selected_user)

                # print("unpaid",existing_user)
        else:
            selected_user = None

        
        print("users",selected_user)
        if selected_user and selected_user.is_wrong:
            response['status_code'] = 403
            response['message'] = "Account access restricted. Please contact support team."
            return response
        
        if selected_user and not selected_user.is_active:
            response['status_code'] = 404
            response['message'] = "The account is deleted. Please contact to admin"
            return response
        
        print("Existing user time", time.time() - starttime)
        
        otp = str(random.randint(1000, 9999))
        if phone == "919953462784":
            otp="1234"
        # otp = "1234"
        # Generate session ID
        session_id = str(uuid.uuid4())
        # Store OTP session in the database
        expires_at = datetime.now() + timedelta(minutes=5)
        if phone:
            starttime1 = time.time()
            previous_session = OTPSession.objects.filter(identifier=phone)
            if previous_session.exists():
                previous_session.delete()
            otp_session = OTPSession(
                otp=otp, expires_at=expires_at, session_id=session_id, identifier=phone)
            otp_session.save()
            print("OTPSession time", time.time() - starttime1)
            starttime2 = time.time()
            otp_response = send_otp(phone, otp)
            print("SendOTP", time.time() - starttime2)
            # otp_response = "success"
            print("OTPResponse", otp_response)
            if otp_response == "success":
                if selected_user is None:
                    # Create a new user if none exists with the given phone number
                    starttime3 = time.time()
                    print("Before creating user")
                    api_response = requests.post("https://www.medicolifepartner.com/index.php/api/get_reg_data", json={"mobile number": phone})
                    print(api_response.text)
                    if api_response.status_code == 200:
                        
                        mlp_id1 = api_response.json().get("mlp_id")
                        mlp_id = f"MLP00{mlp_id1}"
                        print(mlp_id)

                        user_instance_arr = [User(mobile_number=phone, mlp_id=mlp_id)]
                        User.objects.bulk_create(user_instance_arr)
                        print("CreateUser", time.time() - starttime3)
                    else:
                        response['status_code'] = 500
                        response['message'] = "Failed to generate mlp_id"
                        return response
                response['status_code'] = 200
                response['message'] = "OTP sent Successfully"
                response['session_id'] = session_id
                return response
            else:
                res = {'message': 'Failed to send OTP', "status_code": 403, "error": True}
                return res
        else:
            res = {'message': 'Please enter phone number', "status_code": 403, "error": True}
            return res
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response    

def completed_mandatory_questions(user, expertise_objs, post_graduation_objs):
    try:
        if (
            user.name and user.email and user.gender and user.dob and user.religion and 
            len(json.loads(user.profile_pictures)) and 
            (not user.completed_post_grad or UserPostGraduation.objects.filter(user=user).exists() or post_graduation_objs.exists()) and
            (not user.partner_age_preference or ( user.partner_age_from != None and user.partner_age_to != None))
            ):
            return True
        return False
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return False


def verifyotpfunc(body):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        otp, session_id, notification_token = body.get('otp'), body.get('session_id'), body.get('notification_token')
        if not otp or not session_id:
            response['status_code'] = 301
            response['message'] = "Fields missing"
            return response
        otp_session = OTPSession.objects.filter(session_id=session_id).first()
        res={}
        if otp_session is None:
            res={'message': 'Invalid session ID',"status_code":403,"error":True}
            return res
        if (otp_session.otp==otp) and otp_session.expires_at > timezone.now():
            print(otp_session.identifier)
            #user = User.objects.filter(mobile_number=otp_session.identifier).first()
            users = User.objects.filter(mobile_number=otp_session.identifier , is_active = True,is_wrong=False)
            print("Users",users)
            user = None
            
            # if users.exists():
            #     if users.filter(Q(can_upgrade_subscription=1) | Q(can_upgrade_subscription=0)).exists():
            #         user = users.filter(Q(can_upgrade_subscription=1) | Q(can_upgrade_subscription=0)).first()
            #     else:
            #         user = users.first()

            if users.exists():
                # Step 1: Filter users with can_upgrade_subscription=1 or 0
                upgradeable_users = users.filter(Q(can_upgrade_subscription=1) | Q(can_upgrade_subscription=0))

                if upgradeable_users.exists():
                    user = upgradeable_users.first()
                    print("paid_user",user)
                else:
                    # Step 2: If no upgradeable user, check for users who completed mandatory questions
                    user = users.filter(mandatory_questions_completed=True).first()
                    
                    
                    if not user:
                        # Step 3: If none completed mandatory questions, pick the first created user
                        user = users.order_by('created_date').first()
                    print("unpaid user",user)    
            else:
                user = users.first()

            
            otp_session.delete()
            if not user:
                response['status_code'] = 404
                response['message'] = "User not found"
                return response
            elif not user.is_active:
                response['status_code'] = 404
                response['message'] = "The account is deleted. Please contact admin to activate"
                return response
            elif user.is_primary_account:
                # if not user.email or user.is_active:
                #     print(otp_session.identifier)
                #     res=registration_success(otp_session.identifier)
                #     print(res)
                if notification_token:
                    user.notification_token=notification_token
                    user.save()
                user.is_active = True
                user.phone_is_verified=True
                user.save()
                # token = AuthToken.objects.get_or_create(user=user)[0]
                res={
                    'message':"OTP verified successfully",
                    'data':[{
                        # 'token':token.token,
                        'id':user.mlp_id,
                        'phone':user.mobile_number,
                    }],
                    "status_code":200,
                    "error":False
                }
                
                return res
            else:
                linkeduser = LinkedAccount.objects.filter(linked_user__mobile_number__contains=otp_session.identifier).all()
                data=[]
                for item in linkeduser:
                    item.primary_user.is_active = True
                    item.primary_user.save(update_fields=['is_active'])
                    # token = AuthToken.objects.get_or_create(user=item.primary_user)[0]
                    data.append({
                        # 'token':token.token,
                        'id':item.primary_user.mlp_id,
                        'phone':item.primary_user.mobile_number,
                        'name':item.primary_user.name
                    })
                response_data={
                    'message':"OTP verified successfully",
                    'data':data,
                    "status_code":200,
                    "error":False
                }
                
                return response_data
        else:
            res={'message': 'Invalid OTP','status_code':403,"error":True}
            return res
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    

def update_mobile_request(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        updated_mobile = data.get('updated_mobile_number', '')
        if not mlp_id or not updated_mobile:
            response["status_code"] = 301
            response["message"] = "Fields missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()
        if LinkedAccount.objects.filter(primary_user=user_obj, linked_user__mobile_number=updated_mobile).exists():
            response['status_code'] = 305
            response["message"] = "User already linked to your account please un-link it first"
            return response
        if User.objects.filter(mobile_number=updated_mobile).exclude(mlp_id=user_obj.mlp_id).exists():
            response['status_code'] = 306
            response["message"] = "Number already taken can't update to this number"
            return response
        OTP = str(random.randint(1000, 9999))
        otp_response = send_otp(updated_mobile, OTP)
       # OTP = "1234"
        # otp_response = "success"
        if otp_response != "success":
            response['status_code'] = 400
            response['message'] = 'Failed to send OTP'
            return response
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        payload={
            "exp": expires_at,
            'current_mlp_id': user_obj.mlp_id,
            'current_mobile': user_obj.mobile_number,
            'updated_mobile': updated_mobile,
            'OTP': OTP
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS512')
        response['status_code'] = 200
        response['message'] = 'OTP sent successfully'
        response['token'] = token
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def update_mobile_OTP_verify(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        token = data.get('token', '')
        OTP = data.get('OTP', '')
        payload = jwt.decode(token, settings.SECRET_KEY, leeway=10, algorithms='HS512')
        if not payload:
            response['status_code'] = 402
            response['message'] = "Invalid token"
            return response
        current_mlp_id, current_mobile, updated_mobile = payload['current_mlp_id'], payload['current_mobile'], payload['updated_mobile']
        if not current_mlp_id or not current_mobile or not updated_mobile:
            response['status_code'] = 402
            response['message'] = "Invalid token"
            return response
        user_obj = User.objects.filter(mlp_id=current_mlp_id, is_active=True, is_wrong=False,mobile_number=current_mobile)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()
        if LinkedAccount.objects.filter(primary_user=user_obj, linked_user__mobile_number=updated_mobile).exists():
            response['status_code'] = 305
            response["message"] = "User already linked to your account please un-link it first"
            return response
        if User.objects.filter(mobile_number=updated_mobile).exclude(mlp_id=user_obj.mlp_id).exists():
            response['status_code'] = 306
            response["message"] = "Number already taken can't update to this number"
            return response
        if payload['OTP'] and OTP != payload['OTP']:
            response['status_code'] = 302
            response["message"] = "OTP Invalid"
            return response
        user_obj.mobile_number = updated_mobile
        user_obj.save()
        response['status_code'] = 200
        response['mlp_id'] = user_obj.mlp_id
        response['message'] = "Mobile number updated successfully"
        return response
    except jwt.ExpiredSignatureError:
        response['status_code'] = 400
        response['message'] = "OTP expired"
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def verifyotpforlinkedfunc(body):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        otp = body.get('otp')
        session_id=body.get('session_id')
        primaryuser_id = body.get('primaryuser_id')
        relation = body.get('relation')

        if not otp or not session_id or not primaryuser_id or not relation:
            response['status_code'] = 301
            response['message'] = "Fields missing"
            return response
        otp_session = OTPSession.objects.filter(session_id=session_id)
        if not otp_session.first():
            response['status_code'] = 402
            response['message'] = "Invalid session ID"
            return response
        otp_session = otp_session.first()
        
        if (otp_session.otp==otp) and otp_session.expires_at > timezone.now():
            user = User.objects.filter(mlp_id=primaryuser_id)
            if not user.first():
                response['status_code'] = 404
                response['message'] = "User not found"
                return response
            user=user.first()
            
            new_user, created = User.objects.get_or_create(mobile_number=otp_session.identifier)
            if not created and not new_user.is_primary_account:
                response['status_code'] = 302
                response['message'] = "Cannot link your account to this account as it is not an primary account"
            
            new_user.phone_is_verified=True
            new_user.name = user.name
            new_user.gender = user.gender
            new_user.profile_createdby = user.profile_createdby
            new_user.save()
            LinkedAccount.objects.create(primary_user=new_user, linked_user=user, relation=relation)
            user.is_primary_account = False
            user.is_active = True
            user.phone_is_verified = True
            user.save()
            token = AuthToken.objects.get_or_create(user=new_user)[0]
            otp_session.delete()
            response['status_code'] = 201
            response['message'] = "OTP verified sucessfully"
            response['data'] = {
                'token': token.token,
                'id': new_user.mlp_id
            }
            if not created and new_user.mandatory_questions_completed:
                new_user.is_active=True
                new_user.save()
                response['status_code'] = 200
            return response
        else:
            response['status_code'] = 403
            response['message'] = "Invalid OTP"
            return response
    except Exception as e:
    # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def addlinkeduserfunc(body):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        linkeduserphone = body.get('linkeduser_phone')
        primaryuser_id = body.get('primaryuser_id')
        
        if not linkeduserphone or not primaryuser_id:
            response['status_code'] = 301
            response['message'] = "Fields missing"
        if User.objects.filter(mlp_id=primaryuser_id, is_primary_account=True, mandatory_questions_completed=True).exists():
            response['status_code'] = 302
            response['message'] = "This is an Primary account, please deactivate to link it to other users"
            return response
        if User.objects.filter(mobile_number=linkeduserphone, is_primary_account=False).exists():
            response['status_code'] = 303
            response['message'] = "The number is already registered as linked user"
            return response
        # Check if the linked user already has maximum linked users
        linked_users_count = User.objects.filter(mlp_id=primaryuser_id).count()
        if linked_users_count >= 2:
            response['status_code'] = 304
            response['message'] = "Maximum 2 linked users can be added"
            return response
        previous_session=OTPSession.objects.filter(identifier=linkeduserphone)
        if previous_session.exists():
            previous_session.delete()
        otp = str(random.randint(1000, 9999))
       # otp="1234"
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=5)
        otp_session = OTPSession(
            otp=otp, expires_at=expires_at, session_id=session_id, identifier=linkeduserphone)
        otp_response = send_otp(linkeduserphone, otp)
        # otp_response = "success"
        if otp_response != "success":
            response['status_code'] = 403
            response['message'] = "Failed to send OTP"
            return response
        otp_session.save()
        response['status_code'] = 200
        response['message'] = 'OTP sent successfully'
        response['session_id'] = session_id
        return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def addlinkeduserforeditfunc(body):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        linkeduserphone = body.get('linkeduser_phone')
        primaryuser_id = body.get('primaryuser_id')
        relation = body.get('relation')
        preferred_time = body.get('preferred_time_connect')
        
        if not linkeduserphone or not primaryuser_id:
            response['status_code'] = 301
            response['message'] = "Fields missing"
        if User.objects.filter(mobile_number=linkeduserphone, is_primary_account=True, mandatory_questions_completed=True).exists():
            response['status_code'] = 302
            response['message'] = "This is already a Primary account, cannot be linked to other primary accounts"
            return response
        primary_user=User.objects.filter(mlp_id=primaryuser_id).first()
        if primary_user:
            linked_users_count = LinkedAccount.objects.filter(primary_user=primary_user).count()
            if linked_users_count > 2:
                response['status_code'] = 303
                response['message'] = "Cannot add more than 2 linked users"
                return response

            if LinkedAccount.objects.filter(primary_user=primary_user, linked_user__mobile_number=linkeduserphone).exists():
                response['status_code'] = 200
                response['message'] = "The number already exists as linkeduser to this primary one"
                return response
        
            new_user, created = User.objects.get_or_create(mobile_number=linkeduserphone)
            if preferred_time:
                new_user.preferred_time_connect = preferred_time
                new_user.save()
            LinkedAccount.objects.get_or_create(primary_user=primary_user, linked_user=new_user, relation=relation)
            response['status_code'] = 200
            response['message'] = "The number saved successfully as linkeduser"
            return response
        # previous_session=OTPSession.objects.filter(identifier=linkeduserphone)
        # if previous_session.exists():
        #     previous_session.delete()
        # # otp = str(random.randint(1000, 9999))
        # otp="1234"
        # session_id = str(uuid.uuid4())
        # expires_at = datetime.now() + timedelta(minutes=5)
        # otp_session = OTPSession(
        #     otp=otp, expires_at=expires_at, session_id=session_id, identifier=linkeduserphone)
        # # otp_response = send_otp(linkeduserphone, otp)
        # otp_response = "success"
        # if otp_response != "success":
        #     response['status_code'] = 403
        #     response['message'] = "Failed to send OTP"
        #     return response
        # otp_session.save()
        # response['status_code'] = 200
        # response['message'] = 'Linked user saved successfully'
        # return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def block_user(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        block_mlp_id = data.get('block_mlp_id', '')
        if not block_mlp_id:
            response["status_code"] = 301
            response["message"] = "Block MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        block_user_obj = User.objects.filter(mlp_id=block_mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        if not block_user_obj.first() or not block_user_obj.first().mandatory_questions_completed:
            response['status_code'] = 404
            response["message"] = "Block User not found"
            return response
        else:
            block_user_obj = block_user_obj.first()
        if user_obj == block_user_obj:
            response['status_code'] = 303
            response['message'] = "User cannot block himself"
            return response
        if BlockedUsers.objects.filter(user=user_obj, blocked_user=block_user_obj).exists():
            response['status_code'] = 204
            response['message'] = "User is already blocked"
        else:
            BlockedUsers.objects.create(user=user_obj, blocked_user=block_user_obj)
            response['status_code'] = 200
            response['message'] = "User blocked Successfully"
        return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def unblock_user(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        block_mlp_id = data.get('block_mlp_id', '')
        if not block_mlp_id:
            response["status_code"] = 301
            response["message"] = "Block MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        blocked_obj = BlockedUsers.objects.filter(user=user_obj, blocked_user__mlp_id=block_mlp_id, blocked_user__mandatory_questions_completed=True, blocked_user__is_active=True,blocked_user__is_wrong=False)
        if not blocked_obj.first():
            response['status_code'] = 404
            response["message"] = "Blocked profile not found"
            return response
        else:
            blocked_obj = blocked_obj.first()

        blocked_obj.delete()
        response['status_code'] = 200
        response['message'] = "Profile unblocked successfully"
        return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def send_intrests(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        messagetosend = data.get('message','')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        recievers_mlp_id = data.get('recievers_mlp_id', '')
        undoaction=data.get('undoaction',False)
        if not recievers_mlp_id:
            response["status_code"] = 301
            response["message"] = "Receiver's MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        recievers_user_obj = User.objects.filter(mlp_id=recievers_mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        if not recievers_user_obj.first() or not recievers_user_obj.first().mandatory_questions_completed:
            response['status_code'] = 404
            response["message"] = "Receiver User not found"
            return response
        else:
            recievers_user_obj = recievers_user_obj.first()
        if user_obj == recievers_user_obj:
            response['status_code'] = 303
            response['message'] = "User cannot send interests to himself"
            return response
        intrest_obj = Intrest.objects.filter(invitation_by=user_obj, invitation_to=recievers_user_obj)
        interest_existing = Intrest.objects.filter(invitation_by=recievers_user_obj, invitation_to=user_obj)
        if BlockedUsers.objects.filter(user=user_obj, blocked_user=recievers_user_obj).exists():
            response['status_code'] = 301
            response['message'] = 'You have blocked the User'
            return response
        if BlockedUsers.objects.filter(user=recievers_user_obj, blocked_user=user_obj).exists():
            response['status_code'] = 302
            response['message'] = 'User has blocked you'
            return response
        if not intrest_obj.first() and not interest_existing.exists():
            Intrest.objects.create(invitation_by=user_obj, invitation_to=recievers_user_obj)
            result = calculate_match_percentage(user_obj.mlp_id , recievers_user_obj.mlp_id)
            match_percent ="NA"
            if result["status_code"] == 200:
                match_percent = str(result["match_percentage"])
                if "." in match_percent:
                    match_percent = match_percent.split(".")[0]
                    match_percent = f"{match_percent}%"
            user_post_graduation = UserPostGraduation.objects.filter(user=user_obj)
            pictures = json.loads(recievers_user_obj.profile_pictures) 
            receiver_pic = pictures[0] if pictures else "NA"
            post_grads = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first()  and user_obj.completed_post_grad else []
            graduation_id = user_obj.graduation_obj.name
            expertise_id = user_obj.graduation_obj.expertise_obj.name
            if post_grads:
                education = f"{graduation_id}, {post_grads[0]}"
            else:
                education = f"{graduation_id}"
            link="https://bit.ly/2JQ7u6i"
            
            if user_obj.city:
                
                template_id=1307161790205538529
                message=f"Hi {recievers_user_obj.name}, you have received an interest from ({user_obj.mlp_id}) who is {education}, Lives in {user_obj.city} on medicolifepartner.com(Exclusive Venture), please click to respond. {link}"
                
            else:
                template_id=1307161911050663508
                message=f"Hi {recievers_user_obj.name}, you have received an interest from ({user_obj.mlp_id}) who is {education} on medicolifepartner.com(Exclusive Venture), please click to respond. {link}"
                # message=f"Hi {recievers_user_obj.name}, you have received an interest from ({user_obj.mlp_id}) who is {education} on medicolifepartner.com (Exclusive Venture), please click to respond. {link}"
            sms_send(recievers_user_obj.mobile_number,message,template_id)
            custom_data={
                "screen":"received_request",
                "userid":recievers_user_obj.mlp_id
                }
            if recievers_user_obj.notification_token!=None:

                message = messaging.Message(
                    token=recievers_user_obj.notification_token,  # FCM registration token
                    notification=messaging.Notification(
                        title="Someone's Interested! 💌",
                        body="Exciting news! You've received an interest. Check it out now and see if a new connection is on the horizon. Don't miss the chance for something special! 💖"
                    ),
                    data=custom_data  # Custom data payload
                )

                res = messaging.send(message)
                # print(f'Successfully sent {res.success_count} messages')

                # push_service.notify_single_device(registration_id=recievers_user_obj.notification_token,message_title="Someone's Interested! 💌",message_body="Exciting news! You've received an interest. Check it out now and see if a new connection is on the horizon. Don't miss the chance for something special! 💖",data_message=custom_data)
            all_linked_users=LinkedAccount.objects.filter(primary_user=recievers_user_obj).all()
            
            notificationtokens=[]
            for i in all_linked_users:
                if i.linked_user.notification_token:
                    notificationtokens.append(i.linked_user.notification_token) 
            
            if notificationtokens:
                message_body = f"{recievers_user_obj.name} has received an interest. Check it out now and see if a new connection is on the horizon. Don't miss the chance for something special! 💖"

                message = messaging.MulticastMessage(
                    tokens=notificationtokens,  # List of FCM registration tokens
                    notification=messaging.Notification(
                        title="Someone's Interested! 💌",
                        body=message_body,
                    ),
                    data=custom_data  # Custom data payload
                )

                res = messaging.send_multicast(message)
                # print(f'Successfully sent {response.success_count} messages')
                # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title="Someone's Interested! 💌",message_body=message_body,data_message=custom_data)
            
            subject = f"Interest received at medicolifepartner.com"
            if post_grads:
                email_content = email_services.set_email_interestreceived(recievers_user_obj.name,user_obj,graduation_id,post_grads[0],receiver_pic,match_percent)
            else: 
                email_content = email_services.set_email_interestreceived(recievers_user_obj.name,user_obj,graduation_id,"NA",receiver_pic,match_percent)
            # email_services.send_email(subject,email_content['message'],to_email=[recievers_user_obj.email])
            ses_wrapper.send_email(receiver_email_address=recievers_user_obj.email,subject=subject,html_body=email_content['message'])
            Notifications.objects.create(user=recievers_user_obj,sender=user_obj, message="Exciting news! You've received an interest. Check it out now and see if a new connection is on the horizon. Don't miss the chance for something special! 💖",type="Interest_Received", created_date=timezone.now)
            if messagetosend:
                data={
                    "allmlpids":[recievers_mlp_id, mlp_id],
                    'mlpid1':mlp_id,
                    "mlpid2":recievers_mlp_id,
                    "lastMessage":messagetosend,
                    "lastMsgUserId":mlp_id
                }
                msgId = str(uuid.uuid4())
                res=add_data_firebase(data, msgId)
                if res["status_code"]!=200:
                    response['status_code'] = 400
                    response['message'] = 'Error in sending message'
                    return response
                if recievers_user_obj.notification_token!=None:
                    custom_data={
                "screen":"chat",
                "currentUserId":user_obj.mlp_id,
                "otherUserId":recievers_user_obj.mlp_id,
                "msgId":msgId
                }
                    message = messaging.Message(
                        token=recievers_user_obj.notification_token,  # FCM registration token
                        notification=messaging.Notification(
                            title=f"New Message from MLPID:{user_obj.mlp_id}",
                            body=messagetosend
                        ),
                        data=custom_data  # Custom data payload
                    )
                    res = messaging.send(message)
                    # print(f'Successfully sent {response.success_count} messages')

                    # push_service.notify_single_device(registration_id=recievers_user_obj.notification_token,message_title=f"New Message from MLPID:{user_obj.mlp_id} ",message_body=messagetosend,data_message=custom_data)
                    
            response['status_code'] = 200
            response['message'] = 'Interest sent successfully'
        elif interest_existing.exists():
            response['status_code'] = 409
            response['message'] = 'You already have an interest sent by this user.'
        elif undoaction:
            intrest_obj.delete()
            notification_exisitng = Notifications.objects.filter(user=recievers_user_obj,sender=user_obj,type="Interest_Received")
            if notification_exisitng:
                notification_exisitng.delete()
            response['status_code'] = 200
            response['message'] = 'Interest sent undone successfully'
        else:
            intrest_obj = intrest_obj.first()
            response['status_code'] = 409
            response['message'] = 'Already sent request'
            response['intrest_status'] = intrest_obj.status
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def save_profiles(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        save_mlp_id = data.get('save_mlp_id', '')
        if not save_mlp_id:
            response["status_code"] = 301
            response["message"] = "Save MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        save_user_obj = User.objects.filter(mlp_id=save_mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        if not save_user_obj.first() or not save_user_obj.first().mandatory_questions_completed:
            response['status_code'] = 404
            response["message"] = "Shortlisted User not found"
            return response
        else:
            save_user_obj = save_user_obj.first()
        if user_obj == save_user_obj:
            response['status_code'] = 303
            response['message'] = "User cannot save to himself"
            return response
        if SavedUser.objects.filter(user=user_obj,saved_profile=save_user_obj).exists():
            response['status_code'] = 204
            response['message'] = "User already shortlisted"
        else:
            SavedUser.objects.create(user=user_obj,saved_profile=save_user_obj)
            response['status_code'] = 200
            response['message'] = "User shortlisted"
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def unlink_userfunc(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        primary_mlp_id = data.get('primary_mlp_id', '')
        linkeduser_mlp_id = data.get('linkeduser_mlp_id','')
        if not primary_mlp_id and linkeduser_mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP ids missing"
            return response
        
        user_obj = User.objects.filter(mlp_id=primary_mlp_id, is_active=True,is_wrong=False).first()
        linkeduser = User.objects.filter(mlp_id=linkeduser_mlp_id, is_active=True,is_wrong=False).first()
        if not user_obj or not linkeduser:
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        exisitnglinkedaccount = LinkedAccount.objects.filter(primary_user=user_obj, linked_user=linkeduser)
        
        if exisitnglinkedaccount:
            exisitnglinkedaccount.delete()
            response['status_code'] = 200
            response["message"] = "Linked account unlinked successfully"
            return response
        else:
            response['status_code'] = 404
            response["message"] = "No linked accounts found"
            return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

def unsave_profiles(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        save_mlp_id = data.get('save_mlp_id', '')
        if not save_mlp_id:
            response["status_code"] = 301
            response["message"] = "Save MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        save_user_obj = SavedUser.objects.filter(user=user_obj, saved_profile__mlp_id=save_mlp_id, saved_profile__mandatory_questions_completed=True, saved_profile__is_active=True,saved_profile__is_wrong=False)
        if not save_user_obj.first():
            response['status_code'] = 404
            response["message"] = "Shortlisted User not found"
            return response
        else:
            save_user_obj = save_user_obj.first()
        save_user_obj.delete()
        response['status_code'] = 200
        response['message'] = "Profile unsaved successfully"
        return response
    except Exception as e:
        # traceback.print_exc()
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    

def get_self_profile(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_mm=user_obj.first()
            specialization_name = user_obj.first().specialization.name if user_obj.first().specialization else None
            user_obj = user_obj.values()[0]
            user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=user_obj['mlp_id'])
            user_subscription = UserSubscription.objects.filter(
            user=user_mm,
                is_subscription_active=True
            ).values(
                'subscription_id', 'subscription_id__name', 'subscription_id__timeframe', 
                'subscription_id__amount', 'subscription_id__description', 
                'subscription_id__regular_plan', 'subscription_ios_id', 
                'subscription_ios__name', 'subscription_ios__timeframe',
                'subscription_ios__amount', 'subscription_ios__description', 
                'subscription_ios__regular_plan', 'is_subscription_active', 
                'created_date', 'updated_date'
            ).order_by('-created_date').first()
            print(user_subscription)

            subscription_details = None
            if user_subscription:
                if user_subscription['subscription_id']:  # Use details from 'subscription'
                    subscription_details = {
                        "subscription_id": user_subscription['subscription_id'],
                        "subscription_id__name": user_subscription['subscription_id__name'],
                        "subscription_id__timeframe": user_subscription['subscription_id__timeframe'],
                        "subscription_id__amount": user_subscription['subscription_id__amount'],
                        "subscription_id__description": user_subscription['subscription_id__description'],
                        "subscription_id__regular_plan": user_subscription['subscription_id__regular_plan']
                    }
                    created_date = user_subscription['created_date']
                elif user_subscription['subscription_ios_id']:  # Use details from 'subscription_ios'
                    subscription_details = {
                        "subscription_id": user_subscription['subscription_ios_id'],
                        "subscription_id__name": user_subscription['subscription_ios__name'],
                        "subscription_id__timeframe": user_subscription['subscription_ios__timeframe'],
                        "subscription_id__amount": user_subscription['subscription_ios__amount'],
                        "subscription_id__description": user_subscription['subscription_ios__description'],
                        "subscription_id__regular_plan": user_subscription['subscription_ios__regular_plan']
                    }
                    created_date = user_subscription['created_date']
                
                print(subscription_details)
                contacts_seen = ContactViewed.objects.filter(user=user_mm).exclude(created_date__lte=created_date).count()
                dict={
                    "Platinum Plus" : [(False,"Unlimited")],
                    "Platinum":[(True,"150")],
                    "Silver Plus" : [(False,"50")],
                    "Silver":[(True,"35")],
                    "Gold Plus" :[(False,"100")],
                    "Gold":[(True,"75")],
                    "Premium Plus":[(False,"Unlimited")],
                    "Gold Plus Web":[(False,"Unlimited")],
                    "Premium Old":[(False,"Unlimited")],
                    "Super Value":[(False,"Unlimited")],
                    "Gold Old":[(False ,"300")],
                    "Diamond":[(False,"Unlimited")],
                    "Premium Plus Web":[(False,"Unlimited")],
                    "Super Saver":[(False,"25")],
                    "Silver Old":[(False,"150")],
                    "Platinum Old":[(False,"Unlimited")],
                    "Classic" :[(False,"Unlimited")]
                }
                name=  subscription_details.get('subscription_id__name') 
                regular_plan = subscription_details.get('subscription_id__regular_plan') 
                # regular_plan=user_subscription["subscription_id__regular_plan"]
                print(name)
                print(regular_plan)
                if name in dict:
                    purchased_plan = dict.get(name)
                    for i in purchased_plan:
                        is_regular, allowed_contacts=i
                        if is_regular == regular_plan:
                            if allowed_contacts!="Unlimited":
                                contacts_seen=f"{contacts_seen}/{allowed_contacts}"
                            else:
                                contacts_seen=f"{allowed_contacts}"
                            break
                    
                    if not contacts_seen:
                        contacts_seen = "Invalid subscription"
                else:
                    contacts_seen="No subscriptions found"
            else:
                contacts_seen="No active subscriptions"

            print("contact seen",contacts_seen)    
            linkedusers = LinkedAccount.objects.filter(primary_user=user_mm).all()
            linkedusersdata=[]
            for i in linkedusers:
                linkedusersdata.append({
                    "primaryuser_mlp_id":i.primary_user.mlp_id,
                    "linkeduser_mlp_id":i.linked_user.mlp_id,
                    "linkeduser_phone":i.linked_user.mobile_number,
                    "phone_is_verified":i.linked_user.phone_is_verified,
                    "preferred_time_connect":i.linked_user.preferred_time_connect,
                    "relation":i.relation
                })
            response['status_code'] = 200
            response['message'] = "Query processed successfully"
            response['data'] = user_obj
            response['data']['profile_pictures'] = json.loads(response['data']['profile_pictures'])
            response['data']['video'] = json.loads(response['data']['video'])
            response['data']['family_photos'] = json.loads(response['data']['family_photos'])
            response['data']['hobbies'] = json.loads(response['data']['hobbies'])
            response['data']['other_hobbies'] = json.loads(response['data']['other_hobbies'])
            response['data']['profession'] = json.loads(response['data']['profession'])
            response['data']['mother_tongue'] = [mt.name for mt in user_mm.mother_tongue.all()]
            response['data']['languages'] = [mt.name for mt in user_mm.languages.all()]
            response['data']['sub_caste_id'] = str(user_mm.sub_caste)
            response['data']['partner_cities_from'] = json.loads(response['data']['partner_cities_from'])
            response['data']['partner_state_from'] = json.loads(response['data']['partner_state_from'])
            response['data']['partner_country_from'] = json.loads(response['data']['partner_country_from'])
            response['data']['partner_caste_from'] = json.loads(response['data']['partner_caste_from'])
            response['data']['partnerExpertisePreference'] = list(PartnerExpertisePreference.objects.filter(user__mlp_id=user_obj['mlp_id']).values_list("expertise__name", flat=True))
            response['data']['partnerGraduationPreference'] = list(PartnerGraduationPreference.objects.filter(user__mlp_id=user_obj['mlp_id']).values_list("graduation__name", flat=True))
            response['data']['partnerPostGraduationPreference'] = list(PartnerPGPreference.objects.filter(user__mlp_id=user_obj['mlp_id']).values_list("post_graduation__name", flat=True))
            response['data']['partnerReligionPreference'] = list(PartnerReligionPreference.objects.filter(user__mlp_id=user_obj['mlp_id']).values_list("religion__name", flat=True))
            response['data']['partnerMaritalStatusPreference'] = list(PartnerMaritalStatusPreference.objects.filter(user__mlp_id=user_obj['mlp_id']).values_list("marital_status__name", flat=True))
            response['data']['partnerSpecializationPreference'] = list(PartnerSpecializationPreference.objects.filter(user__mlp_id=user_obj['mlp_id']).exclude(specialization=None).values_list("specialization__name", flat=True))
            response['data']['siblings'] = list(Siblings.objects.filter(user__mlp_id=user_obj['mlp_id']).values())    
            response['data']['user_post_graduation_ids'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first()  and user_mm.completed_post_grad else []
            response['data']['graduation_id'] = user_mm.graduation_obj.name
            response['data']['expertise_id'] = user_mm.graduation_obj.expertise_obj.name
            response['data']['partner_mothertongue_from'] = [mt.name for mt in user_mm.partner_mothertongue_from.all()]
            response['data']['linkedusers']=linkedusersdata
            response['data']['specialization_name']=specialization_name
            response['data']['percentage']=user_mm.calculate_profile_percentage()
            response['data']['subscription']=subscription_details
            #print(subscription_details.get('subscription_id__timeframe'))
            response['data']['subscription_expiry']= "Expires on {}".format(((created_date + relativedelta(months=subscription_details.get('subscription_id__timeframe'))) - timedelta(days=1)).strftime("%d %b %y")) if user_subscription and subscription_details.get('subscription_id__timeframe') < 14 else ""
            response['data']['contacts_seen']=contacts_seen
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response



# def get_self_profile(data):
#     response = {
#         'status_code': 500,
#         'message': 'Internal server error'
#     }
#     try:
#         mlp_id = data.get('mlp_id', '')
#         if not mlp_id:
#             response["status_code"] = 301
#             response["message"] = "MLP id missing"
#             return response
#         user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True)
#         if not user_obj.first():
#             response['status_code'] = 404
#             response["message"] = "User not found"
#             return response
#         else:
#             user_mm=user_obj.first()
#             specialization_name = user_obj.first().specialization.name if user_obj.first().specialization else None
#             user_obj = user_obj.values()[0]
#             user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=user_obj['mlp_id'])

#             # Fetch either subscription or subscription_ios
#             user_subscription = UserSubscription.objects.filter(
#                 user=user_mm,
#                 is_subscription_active=True
#             ).values(
#                 'subscription_id', 'subscription_id__name', 'subscription_id__timeframe', 
#                 'subscription_id__amount', 'subscription_id__description', 
#                 'subscription_id__regular_plan', 'subscription_ios_id', 
#                 'subscription_ios__name', 'subscription_ios__timeframe',
#                 'subscription_ios__amount', 'subscription_ios__description', 
#                 'subscription_ios__regular_plan', 'is_subscription_active', 
#                 'created_date', 'updated_date'
#             ).first()


#         subscription_details = {}
#         if user_subscription:
#             if user_subscription['subscription_id']:  # Use details from 'subscription'
#                 subscription_details = {
#                     "subscription_id": user_subscription['subscription_id'],
#                     "subscription_id__name": user_subscription['subscription_id__name'],
#                     "subscription_id__timeframe": user_subscription['subscription_id__timeframe'],
#                     "subscription_id__amount": user_subscription['subscription_id__amount'],
#                     "subscription_id__description": user_subscription['subscription_id__description'],
#                     "subscription_id_regular_plan": user_subscription['subscription_id__regular_plan']
#                 }
#                 created_date = user_subscription['created_date']
#             elif user_subscription['subscription_ios_id']:  # Use details from 'subscription_ios'
#                 subscription_details = {
#                     "subscription_id": user_subscription['subscription_ios_id'],
#                     "subscription_id__name": user_subscription['subscription_ios__name'],
#                     "subscription_id__timeframe": user_subscription['subscription_ios__timeframe'],
#                     "subscription_id__amount": user_subscription['subscription_ios__amount'],
#                     "subscription_id__description": user_subscription['subscription_ios__description'],
#                     "subscription_id__regular_plan": user_subscription['subscription_ios__regular_plan']
#                 }
#                 created_date = user_subscription['created_date']
           
#             contacts_seen = ContactViewed.objects.filter(
#                 user=user_mm
#             ).exclude(
#                 created_date__lte=created_date
#             ).count()

#             subscription_plans = {
#                 "Platinum": [(True, "150"), (False, "Unlimited")],
#                 "Silver": [(True, "35"), (False, "50")],
#                 "Gold": [(True, "75"), (False, "100")],
#                 "Premium": [(False, "Unlimited")],
#                 "Gold Plus": [(False, "Unlimited")],
#                 "Premium Old": [(False, "Unlimited")],
#                 "Super Value": [(False, "Unlimited")],
#                 "Gold Old": [(False, "300")],
#                 "Diamond": [(False, "Unlimited")],
#                 "Premium Plus": [(False, "Unlimited")],
#                 "Super Saver": [(False, "25")],
#                 "Silver Old": [(False, "150")],
#                 "Platinum Old": [(False, "Unlimited")]
#             }

#             subscription_name = subscription_details.get('subscription_id__name') or subscription_details.get('subscription_ios_name')
#             subscription_regular_plan = subscription_details.get('subscription_id__regular_plan') or subscription_details.get('subscription_ios_regular_plan')

#             if subscription_name in subscription_plans:
#                 for is_regular, allowed_contacts in subscription_plans[subscription_name]:
#                     if is_regular == subscription_regular_plan:
#                         if allowed_contacts != "Unlimited":
#                             contacts_seen = f"{contacts_seen}/{allowed_contacts}"
#                         else:
#                             contacts_seen = f"{allowed_contacts}"
#                         break
#             else:
#                 contacts_seen = "Invalid subscription"
#         else:
#             contacts_seen = "No active subscriptions"
        

#         linked_users = LinkedAccount.objects.filter(primary_user=user_mm)
#         linked_users_data = [
#             {
#                 "primaryuser_mlp_id": linked_user.primary_user.mlp_id,
#                 "linkeduser_mlp_id": linked_user.linked_user.mlp_id,
#                 "linkeduser_phone": linked_user.linked_user.mobile_number,
#                 "phone_is_verified": linked_user.linked_user.phone_is_verified,
#                 "preferred_time_connect": linked_user.linked_user.preferred_time_connect,
#                 "relation": linked_user.relation
#             }
#             for linked_user in linked_users
#         ]

#         subscription_timeframe = subscription_details.get('subscription_id__timeframe') or subscription_details.get('subscription_ios_timeframe')
           
#         response['status_code'] = 200
#         response['message'] = "Query processed successfully"
#         response['data'] = user_obj
#         response['data']['profile_pictures'] = json.loads(response['data']['profile_pictures'])
#         response['data']['video'] = json.loads(response['data']['video'])
#         response['data']['family_photos'] = json.loads(response['data']['family_photos'])
#         response['data']['hobbies'] = json.loads(response['data']['hobbies'])
#         response['data']['other_hobbies'] = json.loads(response['data']['other_hobbies'])
#         response['data']['profession'] = json.loads(response['data']['profession'])
#         response['data']['mother_tongue'] = [mt.name for mt in user_mm.mother_tongue.all()]
#         response['data']['languages'] = [mt.name for mt in user_mm.languages.all()]
#         response['data']['sub_caste_id'] = str(user_mm.sub_caste)
#         response['data']['partner_cities_from'] = json.loads(response['data']['partner_cities_from'])
#         response['data']['partner_state_from'] = json.loads(response['data']['partner_state_from'])
#         response['data']['partner_country_from'] = json.loads(response['data']['partner_country_from'])
#         response['data']['partner_caste_from'] = json.loads(response['data']['partner_caste_from'])
#         response['data']['partnerExpertisePreference'] = list(
#             PartnerExpertisePreference.objects.filter(user__mlp_id=user_mm.mlp_id).values_list("expertise__name", flat=True)
#         )
#         response['data']['partnerGraduationPreference'] = list(
#             PartnerGraduationPreference.objects.filter(user__mlp_id=user_mm.mlp_id).values_list("graduation__name", flat=True)
#         )
#         response['data']['partnerPostGraduationPreference'] = list(
#             PartnerPGPreference.objects.filter(user__mlp_id=user_mm.mlp_id).values_list("post_graduation__name", flat=True)
#         )
#         response['data']['partnerReligionPreference'] = list(
#             PartnerReligionPreference.objects.filter(user__mlp_id=user_mm.mlp_id).values_list("religion__name", flat=True)
#         )
#         response['data']['partnerMaritalStatusPreference'] = list(
#             PartnerMaritalStatusPreference.objects.filter(user__mlp_id=user_mm.mlp_id).values_list("marital_status__name", flat=True)
#         )
#         response['data']['partnerSpecializationPreference'] = list(
#             PartnerSpecializationPreference.objects.filter(user__mlp_id=user_mm.mlp_id).exclude(specialization=None).values_list("specialization__name", flat=True)
#         )
#         response['data']['siblings'] = list(Siblings.objects.filter(user__mlp_id=user_mm.mlp_id).values())
#         response['data']['user_post_graduation_ids'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.exists() and user_mm.completed_post_grad else []
#         response['data']['graduation_id'] = user_mm.graduation_obj.name
#         response['data']['expertise_id'] = user_mm.graduation_obj.expertise_obj.name
#         response['data']['partner_mothertongue_from'] = [mt.name for mt in user_mm.partner_mothertongue_from.all()]
#         response['data']['linkedusers'] = linked_users_data
#         response['data']['specialization_name'] = specialization_name
#         response['data']['percentage'] = user_mm.calculate_profile_percentage()
#         response['data']['subscription'] = subscription_details
#         if user_subscription and subscription_timeframe < 14:
#             response['data']['subscription_expiry'] = "Expires on {}".format(
#                 ((created_date + relativedelta(months=subscription_timeframe)) - timedelta(days=1)).strftime("%d %b %y")
#             )
#         else:
#             response['data']['subscription_expiry'] = ""
#         response['data']['contacts_seen'] = contacts_seen

#         return response
#     except Exception as e:
#         logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
#         return response


def delete_sibling(data, user_obj):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        sibling_id = data.get('sibling_id', '')
        Siblings.objects.filter(id=sibling_id, user=user_obj).delete()
        response['status_code'] = 200
        response["message"] = "Sibling successfully removed"
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


def get_user_profile(data, user_obj):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        profile_id = data.get('profile_id', '')
        if not profile_id:
            response["status_code"] = 301
            response["message"] = "Profile id missing"
            return response
        profile_user_obj = User.objects.filter(mlp_id=profile_id, is_active=True,is_wrong=False)
        if not profile_user_obj.first() or not profile_user_obj.first().mandatory_questions_completed:
            response['status_code'] = 404
            response["message"] = "Profile not found"
            return response
        
        profile_viewer=profile_user_obj.first()

        profile_user_mm = profile_user_obj.first()
        profile_user_obj = profile_user_obj.values()[0]

        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'
        
        if BlockedUsers.objects.filter(user__mlp_id=profile_user_obj['mlp_id'], blocked_user=user_obj).exists():
            response['status_code'] = 404
            response['message'] = 'Profile not found'
            return response
            
       
        res = show_photographs(user_obj,profile_user_mm)
        
        if res:
            if res["status_code"] == 200:
                photo_hidden = False
            else:
                photo_hidden = True
        
        res = show_salary(user_obj,profile_user_mm)
        
        if res:
            if res["status_code"] == 200:
                salary_hidden = False
            else:
                salary_hidden = True

        res = show_name(user_obj,profile_user_mm)
        
        if res:
            if res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True

        is_bachelor = False
        bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
        if bachelor_of_the_day and profile_user_mm.mlp_id == bachelor_of_the_day.user.mlp_id:
            is_bachelor = True


        user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=profile_user_obj['mlp_id'])
        response['status_code'] = 200
        response['message'] = "Query processed successfully"
        response['data'] = profile_user_obj
        response['data']['name'] = response['data']['mlp_id'] if name_hidden else response['data']['name']
        response['data']['profile_pictures'] = json.loads(response['data']['profile_pictures'])
        response['data']['family_photos'] = json.loads(response['data']['family_photos'])
        response['data']['video'] = json.loads(response['data']['video'])
        response['data']['hobbies'] = json.loads(response['data']['hobbies'])
        response['data']['other_hobbies'] = json.loads(response['data']['other_hobbies'])
        response['data']['profession'] = json.loads(response['data']['profession'])
        response['data']['mother_tongue'] = [mt.name for mt in profile_user_mm.mother_tongue.all()]
        response['data']['languages'] = [mt.name for mt in profile_user_mm.languages.all()]
        response['data']['sub_caste_id'] = str(profile_user_mm.sub_caste)
        response['data']['partner_cities_from'] = json.loads(response['data']['partner_cities_from'])
        response['data']['partner_state_from'] = json.loads(response['data']['partner_state_from'])
        response['data']['partner_country_from'] = json.loads(response['data']['partner_country_from'])
        response['data']['partner_caste_from'] = json.loads(response['data']['partner_caste_from'])
        response['data']['partnerExpertisePreference'] = list(PartnerExpertisePreference.objects.filter(user__mlp_id=profile_user_obj['mlp_id']).values_list("expertise__name", flat=True))
        response['data']['partnerGraduationPreference'] = list(PartnerGraduationPreference.objects.filter(user__mlp_id=profile_user_obj['mlp_id']).values_list("graduation__name", flat=True))
        response['data']['partnerPostGraduationPreference'] = list(PartnerPGPreference.objects.filter(user__mlp_id=profile_user_obj['mlp_id']).values_list("post_graduation__name", flat=True))
        response['data']['partnerReligionPreference'] = list(PartnerReligionPreference.objects.filter(user__mlp_id=profile_user_obj['mlp_id']).values_list("religion__name", flat=True))
        response['data']['partnerMaritalStatusPreference'] = list(PartnerMaritalStatusPreference.objects.filter(user__mlp_id=profile_user_obj['mlp_id']).values_list("marital_status__name", flat=True))
        response['data']['partnerSpecializationPreference'] = list(PartnerSpecializationPreference.objects.filter(user__mlp_id=profile_user_obj['mlp_id']).values_list("specialization__name", flat=True))
        response['data']['siblings'] = list(Siblings.objects.filter(user__mlp_id=profile_user_obj['mlp_id']).values())    
        response['data']['user_post_graduation_ids'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and profile_user_mm.completed_post_grad else []
        response['data']['graduation_id'] = profile_user_mm.graduation_obj.name 
        response['data']['expertise_id'] = profile_user_mm.graduation_obj.expertise_obj.name
        response['data']['specialization_name'] = profile_user_mm.specialization.name if profile_user_mm.specialization else None
        response['data']['partner_mothertongue_from'] = [mt.name for mt in profile_user_mm.partner_mothertongue_from.all()]
        response['data']['blocked_profile'] = BlockedUsers.objects.filter(blocked_user__mlp_id=profile_user_obj['mlp_id'], user=user_obj).exists()
        response['data']['intrests_sent'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=profile_user_obj['mlp_id']).exists()
        response['data']['shortlisted_profile'] = SavedUser.objects.filter(user=user_obj, saved_profile__mlp_id=profile_user_obj['mlp_id']).exists()
        response['data']['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=profile_user_obj['mlp_id'], invitation_to=user_obj).exists()
        response['data']['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=profile_user_obj['mlp_id']) | Q(user_two=user_obj, user_one__mlp_id=profile_user_obj['mlp_id'])).exists()
        response['data']['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=profile_user_obj['mlp_id'], status="Rejected").exists()
        response['data']['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=profile_user_obj['mlp_id'], invitation_to=user_obj, status="Rejected").exists() 
        response['data']['photo_hidden'] = photo_hidden
        response['data']['salary_hidden'] = salary_hidden
        response['data']['name_hidden'] = name_hidden
        response['data']['is_bachelor'] = is_bachelor
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response
    

def get_tier_recommended(user_obj, suggested_user):
    try:
        
        # if (
        #     not isinstance(suggested_user.dob, date) or
        #     not suggested_user.caste
        # ):
        #     return "skip"
        
        if not user_obj.partner_age_preference:
            dob = user_obj.dob
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if user_obj.gender == "f":
                lower = age
                upper = age + 5
            else:
                lower = age - 5
                upper = age
            
        preferences = {
            'age': (lower, upper) if not user_obj.partner_age_preference else (user_obj.partner_age_from, user_obj.partner_age_to),
            'religion_ids': set([el.religion.id for el in user_obj.partnerreligionpreference.all()]) if user_obj.partner_religion_preference else set(Religion.objects.all().values_list('id', flat=True)),
            # 'marital_status_ids': set([el.id for el in user_obj.partnermaritalstatuspreference.all()]) if user_obj.partner_marital_status_preference else set(MaritalStatus.objects.all().values_list('id', flat=True)),
            'caste': json.loads(user_obj.partner_caste_from) if user_obj.partner_caste_preference else "all",
            'expertise_ids': set([el.expertise.id for el in user_obj.partnerexpertisepreference.all()]) if user_obj.partner_expertise_preference else set(Expertise.objects.all().values_list('id', flat=True)),
            # 'cities': json.loads(user_obj.partner_cities_from) if user_obj.partner_cities_preference else "all",
            # 'height': (0, 150) if not user_obj.partner_height_preference else (user_obj.partner_height_from, user_obj.partner_height_to)
        }
        # print(preferences)
        today = date.today()
        current_age = today.year - suggested_user.dob.year - ((today.month, today.day) < (suggested_user.dob.month, suggested_user.dob.day))
        
        if user_obj.graduation_obj and user_obj:
            expertise_in = suggested_user.graduation_obj.expertise_obj.id
            print(suggested_user.name,preferences['age'][0] <= current_age <= preferences['age'][1],suggested_user.religion.id in preferences['religion_ids'])
            print(suggested_user.caste)
            if (
                preferences['age'][0] <= current_age <= preferences['age'][1] and
                suggested_user.religion.id in preferences['religion_ids'] and
                # suggested_user.marital_status.id in preferences['marital_status_ids'] and
                (preferences['caste'] == "all" or suggested_user.caste in preferences['caste']) and
                (not user_obj.partner_expertise_preference or expertise_in in preferences['expertise_ids'])
                # (preferences['cities'] == "all" or suggested_user.city in preferences['cities']) and
                # (not user_obj.partner_height_preference or preferences['height'][0] <= suggested_user.height <= preferences['height'][1])
            ):
                return "tier-1"
            
            if (
                preferences['age'][0] <= current_age <= preferences['age'][1] and
                suggested_user.religion.id in preferences['religion_ids'] and
                # suggested_user.marital_status.id in preferences['marital_status_ids'] and
                (preferences['caste'] == "all" or suggested_user.caste in preferences['caste'])
                # (not user_obj.partner_expertise_preference or expertise_in in preferences['expertise_ids']) and
                # (preferences['cities'] == "all" or suggested_user.city in preferences['cities'])
            ):
                return "tier-2"

            if (
                preferences['age'][0] <= current_age <= preferences['age'][1] and
                suggested_user.religion.id in preferences['religion_ids'] 
                # suggested_user.marital_status.id in preferences['marital_status_ids'] and
                # (preferences['caste'] == "all" or suggested_user.caste in preferences['caste']) and
                # (not user_obj.partner_expertise_preference or expertise_in in preferences['expertise_ids'])
            ):
                return "tier-3"

            if (
                preferences['age'][0] <= current_age <= preferences['age'][1]
                # suggested_user.religion.id in preferences['religion_ids'] and
                # suggested_user.marital_status.id in preferences['marital_status_ids'] and
                # (preferences['caste'] == "all" or suggested_user.caste in preferences['caste'])
            ):
                return "tier-4"
            
            return "other"

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return "error"


def get_tier(user_obj, suggested_user):
    try:

        if (
            not isinstance(suggested_user.dob, date) or
            suggested_user.religion == None or
            suggested_user.marital_status == None or
            not suggested_user.caste
        ):
            return "skip"
        
        preferences = {
            'age': (0, 200) if not user_obj.partner_age_preference else (user_obj.partner_age_from, user_obj.partner_age_to),
            'religion_ids': set([el.religion.id for el in user_obj.partnerreligionpreference.all()]) if user_obj.partner_religion_preference else set(Religion.objects.all().values_list('id', flat=True)),
            'marital_status_ids': set([el.id for el in user_obj.partnermaritalstatuspreference.all()]) if user_obj.partner_marital_status_preference else set(MaritalStatus.objects.all().values_list('id', flat=True)),
            'caste': json.loads(user_obj.partner_caste_from) if user_obj.partner_caste_preference else "all",
            'expertise_ids': set([el.expertise.id for el in user_obj.partnerexpertisepreference.all()]) if user_obj.partner_expertise_preference else set(Expertise.objects.all().values_list('id', flat=True)),
            'cities': json.loads(user_obj.partner_cities_from) if user_obj.partner_cities_preference else "all",
            'height': (0, 150) if not user_obj.partner_height_preference else (user_obj.partner_height_from, user_obj.partner_height_to)
        }
        
        today = date.today()
        current_age = today.year - suggested_user.dob.year - ((today.month, today.day) < (suggested_user.dob.month, suggested_user.dob.day))
        print("USERAGE", current_age)
        print(preferences['age'][0] <= current_age <= preferences['age'][1])
        if user_obj.graduation_obj and user_obj:
            expertise_in = user_obj.graduation_obj.expertise_obj.id
            if (
                preferences['age'][0] <= current_age <= preferences['age'][1] and
                suggested_user.religion.id in preferences['religion_ids'] and
                suggested_user.marital_status.id in preferences['marital_status_ids'] and
                (preferences['caste'] == "all" or suggested_user.caste in preferences['caste']) and
                (not user_obj.partner_expertise_preference or expertise_in in preferences['expertise_ids']) and
                (preferences['cities'] == "all" or suggested_user.city in preferences['cities']) and
                (not user_obj.partner_height_preference or preferences['height'][0] <= suggested_user.height <= preferences['height'][1])
            ):
                return "tier-1"
            
            if (
                preferences['age'][0] <= current_age <= preferences['age'][1] and
                suggested_user.religion.id in preferences['religion_ids'] and
                suggested_user.marital_status.id in preferences['marital_status_ids'] and
                (preferences['caste'] == "all" or suggested_user.caste in preferences['caste']) and
                (not user_obj.partner_expertise_preference or expertise_in in preferences['expertise_ids']) and
                (preferences['cities'] == "all" or suggested_user.city in preferences['cities'])
            ):
                return "tier-2"

            if (
                preferences['age'][0] <= current_age <= preferences['age'][1] and
                suggested_user.religion.id in preferences['religion_ids'] and
                suggested_user.marital_status.id in preferences['marital_status_ids'] and
                (preferences['caste'] == "all" or suggested_user.caste in preferences['caste']) and
                (not user_obj.partner_expertise_preference or expertise_in in preferences['expertise_ids'])
            ):
                return "tier-3"

            if (
                preferences['age'][0] <= current_age <= preferences['age'][1] and
                suggested_user.religion.id in preferences['religion_ids'] and
                suggested_user.marital_status.id in preferences['marital_status_ids'] and
                (preferences['caste'] == "all" or suggested_user.caste in preferences['caste'])
            ):
                return "tier-4"
            
            return "other"

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return "error"

def mark_user_seen(data, visit_count=0):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        seen_mlp_id = data.get('seen_mlp_id', '')
        if not seen_mlp_id:
            response["status_code"] = 301
            response["message"] = "Seen user MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()
        seen_user_obj = User.objects.filter(mlp_id=seen_mlp_id, is_active=True,is_wrong=False)
        if not seen_user_obj.first() or not seen_user_obj.first().mandatory_questions_completed:
            response['status_code'] = 404
            response["message"] = "Seen user not found"
            return response
        seen_user_obj = seen_user_obj.first()
        seen_user_relation = SeenUser.objects.filter(user=user_obj,seen_profile=seen_user_obj)
        if seen_user_relation.first():
            seen_user_relation = seen_user_relation.first()
            seen_user_relation.times_visited += visit_count
            seen_user_relation.save()
        else:
            SeenUser.objects.create(user=user_obj,seen_profile=seen_user_obj)
        response['status_code'] = 200
        response['message'] = 'Query processed successfully'
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response



def get_user_recommendation(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()
        
        opposite_gender = 'f' if user_obj.gender == 'm' else 'm'

        today = date.today()
        age = today.year - user_obj.dob.year - ((today.month, today.day) < (user_obj.dob.month, user_obj.dob.day))   
        blocked_users = BlockedUsers.objects.filter(user=user_obj).values_list('blocked_user__mlp_id', flat=True)
        if user_obj.gender == 'm':
            min_age = age - 5
            max_age = age
        else:
            min_age = age
            max_age = age + 5 
        
        recommended_data = User.objects.filter(is_active=True,is_wrong=False,
                                        mandatory_questions_completed=True,
                                        gender=opposite_gender).exclude(mlp_id__in=blocked_users).distinct()     
        
        if user_obj.partner_age_preference:
            partner_age_from = user_obj.partner_age_from
            partner_age_to = user_obj.partner_age_to

            recommended_data = recommended_data.filter(
                                        dob__year__gte=today.year - partner_age_to,
                                        dob__year__lte=today.year - partner_age_from)  
        else:
            recommended_data = recommended_data.filter(
                                        dob__year__gte=today.year - max_age,
                                        dob__year__lte=today.year - min_age)
        
        if user_obj.partner_religion_preference:
           religion_ids = set([el.religion.id for el in user_obj.partnerreligionpreference.all()]) 
           recommended_data = recommended_data.filter(religion__id__in = religion_ids)
        
        # if user_obj.partner_expertise_preference :
        #    expertise_ids= set([el.expertise.id for el in user_obj.partnerexpertisepreference.all()])   
        #    recommended_data = recommended_data.filter(graduation_obj__expertise_obj__id__in = expertise_ids)
        
        # if user_obj.partner_caste_preference:
        #     caste_pref = json.loads(user_obj.partner_caste_from)    
        #     recommended_data = recommended_data.filter(caste__in = caste_pref)
        
        recommended_data1= recommended_data
        recommendedID = redis_client.get(f"recommendedID_{user_obj.mlp_id}")
        if recommendedID:
            recommendedID_json = recommendedID.decode('utf-8')
            recommendedID = json.loads(recommendedID_json)
            recommended_data = recommended_data.exclude(mlp_id__in=recommendedID)
        else:
            recommendedID = []

        if len(recommended_data) < 10:
            recommended_data = recommended_data1
            redis_client.delete(f"recommendedID_{user_obj.mlp_id}")        

        random_profiles = recommended_data.order_by('?')[:3]
        final_recommendation =[] 
        for profile in random_profiles:
            if ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=profile.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=profile.mlp_id)).exists():
                continue

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and profile.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True


            res = show_name(user_obj,profile)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True
                
            res = show_photographs(user_obj,profile)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 
            age = today.year - profile.dob.year - ((today.month, today.day) < (profile.dob.month, profile.dob.day))   
            data = {
                'mlp_id':profile.mlp_id,
                'name': profile.mlp_id if name_hidden else profile.name,
                'email': profile.email,
                'gender': profile.gender,
                'dob': profile.dob,
                'age':age,
                'religion': profile.religion.name if profile.religion else None,
                'marital_status' : profile.marital_status.name if profile.marital_status else None,
                'profile_pictures': json.loads(profile.profile_pictures),
                'family_photos': json.loads(profile.family_photos),
                'activity_status':profile.activity_status,
                'last_seen':profile.last_seen,
                'completed_post_grad': profile.completed_post_grad,
                'height': profile.height,
                'weight': profile.weight,
                'eating_habits' : profile.eating_habits,
                'hobbies': json.loads(profile.hobbies),
                'other_hobbies': json.loads(profile.other_hobbies),
                'city': profile.city,
                'caste': profile.caste,
                'is_bachelor': is_bachelor,
                'shortlisted': SavedUser.objects.filter(user=user_obj, saved_profile=profile).exists(),
                'interest_sent': Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=profile.mlp_id).exists()
            }

           # data['shortlisted'] = SavedUser.objects.filter(user=auth_user, saved_profile=profile).exists()
           # data['interest_sent'] =  Intrest.objects.filter(Q(invitation_by=auth_user, invitation_to__mlp_id=profile.mlp_id) | Q(invitation_to=auth_user, invitation_by__mlp_id=profile.mlp_id)).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=profile.mlp_id, invitation_to=user_obj).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=profile.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=profile.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=profile.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=profile.mlp_id, invitation_to=user_obj , status="Rejected").exists()

            user_graduation = profile.graduation_obj.name if profile.graduation_obj else None

            if profile.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=profile).values_list('post_graduation__name', flat=True))
            else :
                user_post_graduation = set() 

            user_expertise =  profile.graduation_obj.expertise_obj.name if (profile.graduation_obj and profile.graduation_obj.expertise_obj) else None

            data['graduation_id'] = user_graduation
            data['user_post_graduation'] = list(user_post_graduation)
            data['expertise_id'] = user_expertise
            data['name_hidden']=name_hidden
            data['photo_hidden']=photo_hidden

            final_recommendation.append(data)
            recommendedID.append(data['mlp_id'])

            redis_client.set(f"recommendedID_{user_obj.mlp_id}", json.dumps(recommendedID))

        response['status_code'] = 200
        response['message'] = "Data Reterieved Successfully"
        response['data'] = final_recommendation
        return response     
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

# get most viewed profile
def get_most_viewed_profile(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()

        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'

        cache_key = f"seen_most_viewed_profiles_{user_obj.mlp_id}"

        popular_profiles = cache.get(cache_key)
    
        if popular_profiles is None:
            ids_to_skip = redis_client.get(f"Idstoskip_{user_obj.mlp_id}")
            if not ids_to_skip:
                queryset = ConnectionList.objects.filter(Q(user_one=user_obj) | Q(user_two=user_obj)).annotate(mlp_id=Case(When(user_one=user_obj, then=F('user_two__mlp_id')),
                            When(user_two=user_obj, then=F('user_one__mlp_id')),
                            output_field=CharField(),)).values_list('mlp_id', flat=True)
                
                ids_to_skip = list(BlockedUsers.objects.filter(Q(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True) |Q(blocked_user=user_obj, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)).values_list('blocked_user__mlp_id', 'user__mlp_id'))
                ids_to_skip += list(Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, invitation_to__is_wrong=False,status__in=["Pending", "Accepted"]).values_list('invitation_to__mlp_id',flat = True))
                ids_to_skip += list(queryset)
                
                redis_client.set(f"Idstoskip_{user_obj.mlp_id}",json.dumps(ids_to_skip),cache_timeout)
            else:
                ids_to_skip_json = ids_to_skip.decode('utf-8')  
                ids_to_skip = json.loads(ids_to_skip_json)
                
            # add a preprocessed column called total visit count (seen user: postsave)
            
            popular_profiles = SeenUser.objects.filter(
                seen_profile__is_active=True,
                seen_profile__is_wrong =False, 
                seen_profile__mandatory_questions_completed=True, 
                seen_profile__gender__isnull=False
            ).exclude(
                Q(seen_profile__mlp_id=user_obj.mlp_id) |  
                Q(seen_profile__gender=user_obj.gender) | 
                Q(seen_profile__gender__exact='') | 
                Q(seen_profile__mlp_id__in=ids_to_skip)
            ).values('seen_profile__mlp_id').annotate(
                field_count=Count('seen_profile__mlp_id')
            ).order_by('-field_count')

            cache.set(cache_key, popular_profiles, timeout=3600)

        most_viewed_profiles = []    
        for el in popular_profiles:
            data = {}
            suggested_user = User.objects.get(mlp_id=el['seen_profile__mlp_id'])

            # if ConnectionList.objects.filter(Q(user_one=user_obj, user_two=suggested_user) | Q(user_two=user_obj, user_one=suggested_user)).exists():
            #     continue

            res = show_name(user_obj, suggested_user)

            if res:
                name_hidden = res["status_code"] != 200

            res = show_photographs(user_obj, suggested_user)

            if res:
                photo_hidden = res["status_code"] != 200

            is_bachelor = False
            #Bachelor of the day in cache which will expire in 24 hrs
            #religion_gender
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True

            data['mlp_id'] = suggested_user.mlp_id
            data['mobile_number'] = suggested_user.mobile_number
            data['name'] = suggested_user.mlp_id if name_hidden else suggested_user.name
            data['email'] = suggested_user.email
            data['gender'] = suggested_user.gender
            data['dob'] = suggested_user.dob
            data['height'] = suggested_user.height
            data['city'] = suggested_user.city
            data['marital_status'] = suggested_user.marital_status.name if suggested_user.marital_status else None
            data['eating_habits'] = suggested_user.eating_habits
            data['ReligionId']= suggested_user.religion.name 
            data['expertiseId']= suggested_user.graduation_obj.expertise_obj.name
            data['graduationId']= suggested_user.graduation_obj.name
            #Arrayagg for postgrad
            data['userPostGraduationId']= UserPostGraduation.objects.filter(user=suggested_user).values_list('post_graduation__graduation_obj__name', flat=True).first()
            data['activity_status'] = suggested_user.activity_status
            data['last_seen'] = suggested_user.last_seen
            data['is_bachelor'] = is_bachelor
            data['shortlisted'] = SavedUser.objects.filter(user=user_obj, saved_profile=suggested_user).exists()
            data['interest_sent'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to=suggested_user).exists()
           # data['interest_received'] = Intrest.objects.filter(invitation_by=suggested_user, invitation_to=user_obj).exists()
           # data['interest_sent'] =  Intrest.objects.filter(Q(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id) | Q(invitation_to=user_obj, invitation_by__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user_obj).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user_obj , status="Rejected").exists()
            data['profile_pictures'] = json.loads(suggested_user.profile_pictures)
            data['photo_hidden'] = photo_hidden
            most_viewed_profiles.append(data)
            if len(most_viewed_profiles) >= 5:
                break

        response['status_code'] = 200
        response['message'] = "Query processed successfully"
        response['data'] =  most_viewed_profiles
        return response

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


# To get popular profile service
def get_popular_profiles(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        page = data.get('page', 1)
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response    
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()
        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'

        cache_key = f"popular_profiles_data_{user_obj.mlp_id}"

        popular_profiles = cache.get(cache_key)
        #Add cache variable common (24hrs)
        if popular_profiles is None:
            ids_to_skip = redis_client.get(f"Idstoskip_{user_obj.mlp_id}")
            if not ids_to_skip:
                queryset = ConnectionList.objects.filter(Q(user_one=user_obj) | Q(user_two=user_obj)).annotate(mlp_id=Case(When(user_one=user_obj, then=F('user_two__mlp_id')),
                            When(user_two=user_obj, then=F('user_one__mlp_id')),
                            output_field=CharField(),)).values_list('mlp_id', flat=True)
                ids_to_skip = list(BlockedUsers.objects.filter(Q(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True) |Q(blocked_user=user_obj, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)).values_list('blocked_user__mlp_id', 'user__mlp_id'))
                ids_to_skip += list(Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, invitation_to__is_wrong=False, status__in=["Pending", "Accepted"]).values_list('invitation_to__mlp_id',flat = True))
                ids_to_skip += list(queryset)
                
                redis_client.set(f"Idstoskip_{user_obj.mlp_id}",json.dumps(ids_to_skip),cache_timeout)
            else:
                ids_to_skip_json = ids_to_skip.decode('utf-8')  
                ids_to_skip = json.loads(ids_to_skip_json)

            # ids_to_skip = list(BlockedUsers.objects.filter( Q(user=user_obj, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True) |Q(blocked_user=user_obj, user__is_active=True, user__mandatory_questions_completed=True)).values_list('blocked_user__mlp_id', 'user__mlp_id'))
            # ids_to_skip += list(Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, status__in=["Pending", "Accepted"]).values_list('invitation_to__mlp_id', flat=True))
            # ids_to_skip += list( ConnectionList.objects.filter( Q(user_one=user_obj) | Q(user_two=user_obj)).values_list( 'user_two__mlp_id', 'user_one__mlp_id' ))
            popular_profiles = SeenUser.objects.filter(seen_profile__is_active=True, seen_profile__is_wrong=False,seen_profile__gender__isnull=False).exclude(Q(seen_profile__mlp_id=user_obj.mlp_id) |  Q(seen_profile__gender=user_obj.gender) | Q(seen_profile__gender__exact='') | Q(seen_profile__mlp_id__in=ids_to_skip)).values('seen_profile__mlp_id').annotate(field_count=Count('seen_profile__mlp_id')).order_by('-field_count')

            cache.set(cache_key, popular_profiles, timeout=cache_timeout)

        most_viewed_profiles = []
        possible_pages = math.ceil(len(popular_profiles)/3)
        if page > possible_pages:
            response['status_code'] = 302
            response["message"] = "Page is invalid"
            return response
        for el in popular_profiles:
            data = {}
            suggested_user = User.objects.get(mlp_id=el['seen_profile__mlp_id'])

            # if ConnectionList.objects.filter(Q(user_one=user_obj, user_two=suggested_user) | Q(user_two=user_obj, user_one=suggested_user)).exists():
            #    continue 

            res = show_name(user_obj,suggested_user)
        
            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True
            
            res = show_photographs(user_obj,suggested_user)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True


            data['mlp_id'] = suggested_user.mlp_id
            data['mobile_number'] = suggested_user.mobile_number
            data['name'] = suggested_user.mlp_id if name_hidden else suggested_user.name
            data['email'] = suggested_user.email
            data['gender'] = suggested_user.gender
            data['dob'] = suggested_user.dob
            data['height'] = suggested_user.height
            data['city'] = suggested_user.city
            data['marital_status'] = suggested_user.marital_status.name if suggested_user.marital_status else None
            data['eating_habits'] = suggested_user.eating_habits
            data['ReligionId']= suggested_user.religion.name 
            data['expertiseId']= suggested_user.graduation_obj.expertise_obj.name
            data['graduationId']= suggested_user.graduation_obj.name
            data['userPostGraduationId']= UserPostGraduation.objects.filter(user=suggested_user).values_list('post_graduation__graduation_obj__name', flat=True).first()
            data['activity_status'] = suggested_user.activity_status
            data['last_seen']=suggested_user.last_seen
            data['is_bachelor'] = is_bachelor
            data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=suggested_user).exists()
           # data['interest_sent']=Intrest.objects.filter(invitation_by=user_obj, invitation_to=suggested_user).exists()
           #Create a common fn for interest sent, received, and then use
            data['interest_received']=Intrest.objects.filter(invitation_by=suggested_user, invitation_to=user_obj).exists()
            data['interest_sent'] =  Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id).exists()
           # data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user_obj).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me']=Intrest.objects.filter(invitation_by=suggested_user, invitation_to=user_obj , status="Rejected").exists()
            data['profile_pictures'] = json.loads(suggested_user.profile_pictures)
            data['photo_hidden'] = photo_hidden
            most_viewed_profiles.append(data)
        response['status_code'] = 200
        response['message'] = "Query processed successfully"
        response['data'] = most_viewed_profiles[(page-1)*3:page*3]
        response['possible_pages'] = possible_pages
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response



def get_feed(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        print("start api")
        api_time = time.time()
        before_final_recom = time.time()

        mlp_id = data.get('mlp_id', '')
        page = data.get('page',1)
        page_size = data.get('page_size',3)
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response

        user_time = time.time()

        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()

        print("user fetch time >> ", time.time() - user_time)

        print("user fetched")

        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'

        # while_loop_time = time.time()
        
        session = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        # retry = 1
        # while retry <= 5:
        #     if try_block_end_point(user_obj, "get_feed", session) == 0:
        #         time.sleep(0.4*retry)
        #     elif try_block_end_point(user_obj, "get_feed", session) == -1:
        #         raise Exception('Error in blocking endpoint, check logs')
        #     else:
        #         break
        #     retry += 1
        # if retry > 10:
        #     response['status_code'] = 409
        #     response["message"] = "Can't process the request now, queue is full"
        #     return response
        # print("after retry fetched")

        #print("while loop exec time >> ", time.time() - while_loop_time)
        
        all_user_fetch_start = time.time()
        ids_to_skip = redis_client.get(f"Idstoskip_{user_obj.mlp_id}")
        if not ids_to_skip:
            queryset = ConnectionList.objects.filter(Q(user_one=user_obj) | Q(user_two=user_obj)).annotate(mlp_id=Case(When(user_one=user_obj, then=F('user_two__mlp_id')),
                            When(user_two=user_obj, then=F('user_one__mlp_id')),
                            output_field=CharField(),)).values_list('mlp_id', flat=True)
            ids_to_skip = list(BlockedUsers.objects.filter(Q(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False,blocked_user__mandatory_questions_completed=True) |Q(blocked_user=user_obj, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)).values_list('blocked_user__mlp_id', 'user__mlp_id'))
            ids_to_skip += list(Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, invitation_to__is_wrong=False, status__in=["Pending", "Accepted"]).values_list('invitation_to__mlp_id',flat = True))
            ids_to_skip += list(queryset)
            
            redis_client.set(f"Idstoskip_{user_obj.mlp_id}",json.dumps(ids_to_skip),cache_timeout)
        else:
            ids_to_skip_json = ids_to_skip.decode('utf-8')  
            ids_to_skip = json.loads(ids_to_skip_json)

        
        # ids_to_skip = list(BlockedUsers.objects.filter( Q(user=user_obj, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True) |Q(blocked_user=user_obj, user__is_active=True, user__mandatory_questions_completed=True)).values_list('blocked_user__mlp_id', 'user__mlp_id'))
        # ids_to_skip += list(Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, status__in=["Pending", "Accepted"]).values_list('invitation_to__mlp_id', flat=True))
        # ids_to_skip += list( ConnectionList.objects.filter( Q(user_one=user_obj) | Q(user_two=user_obj)).values_list( 'user_two__mlp_id', 'user_one__mlp_id' ))

        seen_users_objs = SeenUser.objects.filter(
            user=user_obj, seen_profile__mandatory_questions_completed=True, seen_profile__gender__isnull=False, seen_profile__is_active=True, seen_profile__is_wrong=False
        ).exclude(
            Q(seen_profile__gender=user_obj.gender) | Q(seen_profile__gender__exact='') | Q(seen_profile__mlp_id__in=ids_to_skip)
        ).order_by('times_visited')
        
        all_users = User.objects.filter(
            is_active=True, is_wrong=False, mandatory_questions_completed=True, gender__isnull=False
        ).exclude(
            Q(mlp_id=mlp_id) | Q(mlp_id__in=seen_users_objs.values_list('seen_profile__mlp_id', flat=True)) | 
            Q(gender=user_obj.gender) | Q(gender__exact='') | Q(mlp_id__in=ids_to_skip)
        ).order_by('updated_date')
        
        results = {
            "tier-1": [],
            "tier-2": [],
            "tier-3": [],
            "tier-4": [],
            "other": [],
            "skip": [],
            "error": [],
        }

        all_user_fetch_end = time.time()
        print("all_users_time",(all_user_fetch_end-all_user_fetch_start))
        
        print("pagination start")
        pagination_time_start = time.time()
        start_index = (page - 1) * page_size
        end_index = page * page_size
        paginated_queryset = all_users[start_index:end_index]
        pagination_time_end = time.time()
        print("pagination time",(pagination_time_end-pagination_time_start))

        print("serializing start")
        serializing_start = time.time()
        for suggested_user in paginated_queryset:
            data = {}

            # if ConnectionList.objects.filter(Q(user_one=user_obj, user_two=suggested_user) | Q(user_two=user_obj, user_one=suggested_user)).exists():
            #     continue

            res = show_name(user_obj,suggested_user)

            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True
            res = show_photographs(user_obj,suggested_user)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True
     
            data['mlp_id'] = suggested_user.mlp_id
            data['mobile_number'] = suggested_user.mobile_number
            data['name'] = suggested_user.mlp_id if name_hidden else suggested_user.name
            data['email'] = suggested_user.email
            data['gender'] = suggested_user.gender
            data['dob'] = suggested_user.dob
            data['height'] = suggested_user.height
            data['city'] = suggested_user.city
            data['marital_status'] = suggested_user.marital_status.name if suggested_user.marital_status else None
            data['eating_habits'] = suggested_user.eating_habits
            data['ReligionId']= suggested_user.religion.name if suggested_user.religion else None
            data['expertiseId']= suggested_user.graduation_obj.expertise_obj.name
            data['graduationId']= suggested_user.graduation_obj.name
            data['userPostGraduationId']= UserPostGraduation.objects.filter(user=suggested_user).values_list('post_graduation__graduation_obj__name', flat=True).first()
            data['activity_status'] = suggested_user.activity_status
            data['last_seen']=suggested_user.last_seen
            data['is_bachelor'] = is_bachelor
            data['profile_pictures'] = json.loads(suggested_user.profile_pictures)
            data['photo_hidden'] = photo_hidden
            data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=suggested_user).exists()
           # data['interest_sent']=Intrest.objects.filter(invitation_by=user_obj, invitation_to=suggested_user).exists()
            data['interest_received']=Intrest.objects.filter(invitation_by=suggested_user, invitation_to=user_obj).exists()
            data['interest_sent'] =  Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me']=Intrest.objects.filter(invitation_by=suggested_user, invitation_to=user_obj, status="Rejected").exists()
            tier = get_tier(user_obj, suggested_user)
            print("TIER is", tier)
            results[tier].append(data)

        serializing_end = time.time()    
        print("serializing_end",(serializing_end-serializing_start))

        print("Before final recom >> ", time.time() - before_final_recom)
        
        print("final recommendation start")

        final_recommendation_start = time.time()
        final_recommendation = []
        for tier in results:
            if tier == "error":
                continue
            final_recommendation += results[tier]
            if len(final_recommendation) >= 3:
                break

        print("final recomendation from all users >> ", len(final_recommendation))

        if len(final_recommendation) < 3:
            flag = False
            # times_visited = sorted(set(seen_users_objs.values_list('times_visited', flat=True)))
            for obj in seen_users_objs:
                current_obj = obj
                visit_count = obj.times_visited
                print(current_obj)
                seen_results = {
                    "tier-1": [],
                    "tier-2": [],
                    "tier-3": [],
                    "tier-4": [],
                    "other": [],
                    "skip": [],
                    "error": [],
                }
                data={}

                # current_objs = seen_users_objs.filter(times_visited=visit_count)
                # for current_obj in current_objs.iterator():
                    
                res = show_name(user_obj,current_obj.seen_profile)
    
                if res:
                    if res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True
                res = show_photographs(user_obj,current_obj.seen_profile)
    
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True


                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
                if bachelor_of_the_day and current_obj.seen_profile.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True

                data['mlp_id'] = current_obj.seen_profile.mlp_id
                data['mobile_number'] = current_obj.seen_profile.mobile_number
                data['name'] = current_obj.seen_profile.mlp_id if name_hidden else current_obj.seen_profile.name
                data['email'] = current_obj.seen_profile.email
                data['gender'] = current_obj.seen_profile.gender
                data['dob'] = current_obj.seen_profile.dob
                data['activity_status'] = current_obj.seen_profile.activity_status
                data['last_seen']=current_obj.seen_profile.last_seen
                data['profile_pictures'] = json.loads(current_obj.seen_profile.profile_pictures)
                data['photo_hidden'] = photo_hidden
                data['height'] =current_obj.seen_profile.height
                data['city'] =current_obj.seen_profile.city
                data['marital_status'] = current_obj.seen_profile.marital_status.name if current_obj.seen_profile.marital_status else None
                data['eating_habits'] =current_obj.seen_profile.eating_habits
                data['ReligionId']= current_obj.seen_profile.religion.name if current_obj.seen_profile.religion else None
                data['expertiseId']= current_obj.seen_profile.graduation_obj.expertise_obj.name
                data['graduationId']=current_obj.seen_profile.graduation_obj.name
                data['userPostGraduationId']= UserPostGraduation.objects.filter(user=current_obj.seen_profile).values_list('post_graduation__graduation_obj__name', flat=True).first()
                data['is_bachelor'] = is_bachelor
                data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=current_obj.seen_profile).exists()
                data['interest_sent']=Intrest.objects.filter(invitation_by=user_obj, invitation_to=current_obj.seen_profile).exists()
                data['interest_received']=Intrest.objects.filter(invitation_by=current_obj.seen_profile, invitation_to=user_obj).exists()
                data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=current_obj.seen_profile.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=current_obj.seen_profile.mlp_id)).exists()
                data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=current_obj.seen_profile.mlp_id, status="Rejected").exists()
                data['interest_rejected_by_me']=Intrest.objects.filter(invitation_by=current_obj.seen_profile, invitation_to=user_obj , status="Rejected").exists()

                tier = get_tier(user_obj, current_obj.seen_profile)
                
                seen_results[tier].append(data)
                for tier in seen_results:
                    if tier == "error":
                        continue
                    final_recommendation += seen_results[tier]
                    if len(final_recommendation) >=3:
                        flag = True
                        break
                if flag:
                    break
        final_recommendation = final_recommendation[:3]

        mark_seen_loop = time.time()

        for recommendation in final_recommendation:
            mark_user_seen(data={'mlp_id': user_obj.mlp_id, 'seen_mlp_id': recommendation['mlp_id']}, visit_count=1)

        print("mark seen loop time >> ", time.time() - mark_seen_loop)
        
        final_recommendation_end = time.time()  

        after_final_recom = time.time()

        print("final recommendation time",(final_recommendation_end-final_recommendation_start))  
        print("response start")
        response_start = time.time()
        response['status_code'] = 200
        response['message'] = 'Query processed successfully'

       # response['total_pages'] = (all_users.count() + page_size - 1) // page_size
        response['total_pages'] = 10 

        response['data'] = final_recommendation
        # release_endpoint(user_obj, "get_feed", session)
        response_end_time = time.time()
        print("response time",(response_end_time-response_start))
        print("after final recom >> ", time.time() - after_final_recom)
        print("api response time >> ", time.time() - api_time)
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        release_endpoint(user_obj, "get_feed", session)
        return response


def get_feed_recommended(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
       # print("start api")

        mlp_id = data.get('mlp_id', '')
        page = data.get('page',1)
        page_size = data.get('page_size',10)
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response


        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        user_obj = user_obj.first()


        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'

        # while_loop_time = time.time()
        
        session = ''.join(random.choices(string.ascii_letters + string.digits, k=4))
        # retry = 1
        # while retry <= 5:
        #     if try_block_end_point(user_obj, "get_feed", session) == 0:
        #         time.sleep(0.4*retry)
        #     elif try_block_end_point(user_obj, "get_feed", session) == -1:
        #         raise Exception('Error in blocking endpoint, check logs')
        #     else:
        #         break
        #     retry += 1
        # if retry > 10:
        #     response['status_code'] = 409
        #     response["message"] = "Can't process the request now, queue is full"
        #     return response
        # print("after retry fetched")

        #print("while loop exec time >> ", time.time() - while_loop_time)
        
        #all_user_fetch_start = time.time()
        ids_to_skip = redis_client.get(f"Idstoskip_{user_obj.mlp_id}")
        if not ids_to_skip:
            queryset = ConnectionList.objects.filter(Q(user_one=user_obj) | Q(user_two=user_obj)).annotate(mlp_id=Case(When(user_one=user_obj, then=F('user_two__mlp_id')),
                            When(user_two=user_obj, then=F('user_one__mlp_id')),
                            output_field=CharField(),)).values_list('mlp_id', flat=True)
            ids_to_skip = list(BlockedUsers.objects.filter(Q(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True) |Q(blocked_user=user_obj, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)).values_list('blocked_user__mlp_id', 'user__mlp_id'))
            ids_to_skip += list(Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, invitation_to__is_wrong=False, status__in=["Pending", "Accepted"]).values_list('invitation_to__mlp_id',flat = True))
            ids_to_skip += list(queryset)
            
            redis_client.set(f"Idstoskip_{user_obj.mlp_id}",json.dumps(ids_to_skip),cache_timeout)
        else:
            ids_to_skip_json = ids_to_skip.decode('utf-8')  
            ids_to_skip = json.loads(ids_to_skip_json)

        
        # ids_to_skip = list(BlockedUsers.objects.filter( Q(user=user_obj, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True) |Q(blocked_user=user_obj, user__is_active=True, user__mandatory_questions_completed=True)).values_list('blocked_user__mlp_id', 'user__mlp_id'))
        # ids_to_skip += list(Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, status__in=["Pending", "Accepted"]).values_list('invitation_to__mlp_id', flat=True))
        # ids_to_skip += list( ConnectionList.objects.filter( Q(user_one=user_obj) | Q(user_two=user_obj)).values_list( 'user_two__mlp_id', 'user_one__mlp_id' ))

        seen_users_objs = SeenUser.objects.filter(
            user=user_obj, seen_profile__mandatory_questions_completed=True, seen_profile__gender__isnull=False, seen_profile__is_active=True, seen_profile__is_wrong=False
        ).exclude(
            Q(seen_profile__gender=user_obj.gender) | Q(seen_profile__gender__exact='') | Q(seen_profile__mlp_id__in=ids_to_skip)
        ).order_by('times_visited')
        
        all_users = User.objects.filter(
            is_active=True, mandatory_questions_completed=True, gender__isnull=False,is_wrong=False
        ).exclude(
            Q(mlp_id=mlp_id) | Q(mlp_id__in=seen_users_objs.values_list('seen_profile__mlp_id', flat=True)) | 
            Q(gender=user_obj.gender) | Q(gender__exact='') | Q(mlp_id__in=ids_to_skip)
        ).order_by('updated_date')
        
        
        results = {
            "tier-1": [],
            "tier-2": [],
            "tier-3": [],
            "tier-4": [],
            "other": [],
            "skip": [],
            "error": [],
        }
     
        start_index = (page - 1) * page_size
        end_index = page * page_size
       # paginated_queryset = all_users
        paginated_queryset = all_users[start_index:end_index]

        # print(paginated_queryset)
        # count=0
        for suggested_user in paginated_queryset:
            data = {}
           
            tier = get_tier_recommended(user_obj, suggested_user)
            
            if tier == "other":
                continue
            
            res = show_name(user_obj,suggested_user)

            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True
            res = show_photographs(user_obj,suggested_user)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True
     
            data['mlp_id'] = suggested_user.mlp_id
            data['mobile_number'] = suggested_user.mobile_number
            data['name'] = suggested_user.mlp_id if name_hidden else suggested_user.name
            data['email'] = suggested_user.email
            data['gender'] = suggested_user.gender
            data['dob'] = suggested_user.dob
            data['height'] = suggested_user.height
            data['city'] = suggested_user.city
            data['marital_status'] = suggested_user.marital_status.name if suggested_user.marital_status else None
            data['eating_habits'] = suggested_user.eating_habits
            data['ReligionId']= suggested_user.religion.name if suggested_user.religion else None
            data['expertiseId']= suggested_user.graduation_obj.expertise_obj.name
            data['graduationId']= suggested_user.graduation_obj.name
            data['userPostGraduationId']= UserPostGraduation.objects.filter(user=suggested_user).values_list('post_graduation__graduation_obj__name', flat=True).first()
            data['activity_status'] = suggested_user.activity_status
            data['last_seen']=suggested_user.last_seen
            data['is_bachelor'] = is_bachelor
            data['profile_pictures'] = json.loads(suggested_user.profile_pictures)
            data['photo_hidden'] = photo_hidden
            data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=suggested_user).exists()
           # data['interest_sent']=Intrest.objects.filter(invitation_by=user_obj, invitation_to=suggested_user).exists()
            data['interest_received']=Intrest.objects.filter(invitation_by=suggested_user, invitation_to=user_obj).exists()
            data['interest_sent'] =  Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me']=Intrest.objects.filter(invitation_by=suggested_user, invitation_to=user_obj, status="Rejected").exists()
            # tier = get_tier_recommended(user_obj, suggested_user)
            results[tier].append(data)
  
    
        final_recommendation = []
        for tier in results:
            if tier == "error" or tier=="other":
                continue
            final_recommendation += results[tier]
            if len(final_recommendation) >= 3:
                break

        print("final recomendation from all users >> ", len(final_recommendation))

        if len(final_recommendation) < 3:
            flag = False
            # times_visited = sorted(set(seen_users_objs.values_list('times_visited', flat=True)))
            for obj in seen_users_objs:
                current_obj = obj
                visit_count = obj.times_visited
                print(current_obj)
                seen_results = {
                    "tier-1": [],
                    "tier-2": [],
                    "tier-3": [],
                    "tier-4": [],
                    "other": [],
                    "skip": [],
                    "error": [],
                }
                data={}

                # current_objs = seen_users_objs.filter(times_visited=visit_count)
                # for current_obj in current_objs.iterator():
                    
                res = show_name(user_obj,current_obj.seen_profile)
    
                if res:
                    if res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True
                res = show_photographs(user_obj,current_obj.seen_profile)
    
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True


                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
                if bachelor_of_the_day and current_obj.seen_profile.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True

                data['mlp_id'] = current_obj.seen_profile.mlp_id
                data['mobile_number'] = current_obj.seen_profile.mobile_number
                data['name'] = current_obj.seen_profile.mlp_id if name_hidden else current_obj.seen_profile.name
                data['email'] = current_obj.seen_profile.email
                data['gender'] = current_obj.seen_profile.gender
                data['dob'] = current_obj.seen_profile.dob
                data['activity_status'] = current_obj.seen_profile.activity_status
                data['last_seen']=current_obj.seen_profile.last_seen
                data['profile_pictures'] = json.loads(current_obj.seen_profile.profile_pictures)
                data['photo_hidden'] = photo_hidden
                data['height'] =current_obj.seen_profile.height
                data['city'] =current_obj.seen_profile.city
                data['marital_status'] = current_obj.seen_profile.marital_status.name if current_obj.seen_profile.marital_status else None
                data['eating_habits'] =current_obj.seen_profile.eating_habits
                data['ReligionId']= current_obj.seen_profile.religion.name if current_obj.seen_profile.religion else None
                data['expertiseId']= current_obj.seen_profile.graduation_obj.expertise_obj.name
                data['graduationId']=current_obj.seen_profile.graduation_obj.name
                data['userPostGraduationId']= UserPostGraduation.objects.filter(user=current_obj.seen_profile).values_list('post_graduation__graduation_obj__name', flat=True).first()
                data['is_bachelor'] = is_bachelor
                data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=current_obj.seen_profile).exists()
                data['interest_sent']=Intrest.objects.filter(invitation_by=user_obj, invitation_to=current_obj.seen_profile).exists()
                data['interest_received']=Intrest.objects.filter(invitation_by=current_obj.seen_profile, invitation_to=user_obj).exists()
                data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=current_obj.seen_profile.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=current_obj.seen_profile.mlp_id)).exists()
                data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=current_obj.seen_profile.mlp_id, status="Rejected").exists()
                data['interest_rejected_by_me']=Intrest.objects.filter(invitation_by=current_obj.seen_profile, invitation_to=user_obj , status="Rejected").exists()

                tier = get_tier(user_obj, current_obj.seen_profile)
                
                seen_results[tier].append(data)
                for tier in seen_results:
                    if tier == "error":
                        continue
                    final_recommendation += seen_results[tier]
                    if len(final_recommendation) >=3:
                        flag = True
                        break
                if flag:
                    break
        final_recommendation = final_recommendation[:3]

       

        for recommendation in final_recommendation:
            mark_user_seen(data={'mlp_id': user_obj.mlp_id, 'seen_mlp_id': recommendation['mlp_id']}, visit_count=1)

        response['status_code'] = 200
        response['message'] = 'Query processed successfully'

       # response['total_pages'] = (all_users.count() + page_size - 1) // page_size
       # response['total_pages'] = 10 

        response['data'] = final_recommendation
        # release_endpoint(user_obj, "get_feed", session)
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        release_endpoint(user_obj, "get_feed", session)
        return response


def delete_user_profile(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        reason = data.get('reason', '')
        experience = data.get('experience', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response

        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)

        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response

        user_obj = user_obj.first()

        # Create DeleteProfile instance and save it
        DeleteProfile.objects.create(
            mlp_id=mlp_id,
            reason=reason,
            experience=experience,
            deleted_at=timezone.now()
        )

        user_obj.delete()
    
        response['status_code'] = 200
        response['message'] = "User deleted successfully"
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def get_recieved_intrests(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        page = data.get('page',1)
        page_size = data.get('page_size',10)
        # sent_sort = data.get('sent_sort', 'default')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'

        # ids_to_skip = list(BlockedUsers.objects.filter(user=user_obj, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True).values_list('blocked_user__mlp_id', flat=True))        
        # ids_to_skip += list(BlockedUsers.objects.filter(blocked_user=user_obj, user__is_active=True, user__mandatory_questions_completed=True).values_list("user__mlp_id", flat=True))
        # print(ids_to_skip)
        blocked_users_query = Q(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True) | Q(blocked_user=user_obj, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)
        ids_to_skip = list(
            BlockedUsers.objects.filter(blocked_users_query).values_list(
                Case(
                    When(user=user_obj, then=F('blocked_user__mlp_id')),
                    When(blocked_user=user_obj, then=F('user__mlp_id')),
                    output_field=CharField(),
                ),
                flat=True
            )
        )
        
        recieved_intrests = Intrest.objects.filter(invitation_by__mandatory_questions_completed=True, invitation_by__is_active=True, invitation_by__is_wrong=False ,invitation_to=user_obj, status__in=['Pending', 'Rejected']).exclude(invitation_by__mlp_id__in=ids_to_skip).order_by('-id')

        paginator = Paginator(recieved_intrests, page_size)
        paginated_queryset = paginator.get_page(page) 

        recieved_requests = []
        for intrest_obj in paginated_queryset:
            data = {}
            res = show_name(user_obj,intrest_obj.invitation_by)
        
            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

            res = show_photographs(user_obj,intrest_obj.invitation_by)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and intrest_obj.invitation_by.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True
        
            user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=intrest_obj.invitation_by.mlp_id)
            data['mlp_id'] = intrest_obj.invitation_by.mlp_id
            data['mobile_number'] = intrest_obj.invitation_by.mobile_number
            data['name'] = intrest_obj.invitation_by.mlp_id if name_hidden else intrest_obj.invitation_by.name
            data['email'] = intrest_obj.invitation_by.email
            data['gender'] = intrest_obj.invitation_by.gender
            data['dob'] = intrest_obj.invitation_by.dob
            data['activity_status'] = intrest_obj.invitation_by.activity_status
            data['last_seen']=intrest_obj.invitation_by.last_seen
            data['profile_pictures'] = json.loads(intrest_obj.invitation_by.profile_pictures)
            data['photo_hidden'] = photo_hidden
            data['height'] = intrest_obj.invitation_by.height
            data['religion'] = intrest_obj.invitation_by.religion.name if intrest_obj.invitation_by.religion else None
            data['city'] = intrest_obj.invitation_by.city
            data['caste'] = intrest_obj.invitation_by.caste
            data['marital_status']= intrest_obj.invitation_by.marital_status.name if intrest_obj.invitation_by.marital_status else None
            data['eating_habits']=intrest_obj.invitation_by.eating_habits
            data['is_bachelor'] = is_bachelor
            data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and intrest_obj.invitation_by.completed_post_grad else []
            data['graduation_id'] = intrest_obj.invitation_by.graduation_obj.name
            data['expertise_id'] = intrest_obj.invitation_by.graduation_obj.expertise_obj.name
            data['created_date'] = intrest_obj.created_date
            data['updated_date'] = intrest_obj.updated_date
            data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=intrest_obj.invitation_by).exists()
            data['status'] = intrest_obj.status
            recieved_requests.append(data) 

        response['status_code'] = 200
        response['message'] = "Query executed successfully"
        response['total_pages_recieved_interest']=  paginator.num_pages
        # response['total_pages_sent_interest'] = paginator1.num_pages
        response['recieved_requests'] = recieved_requests
        return response    

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def get_intrests_requests(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        # page = data.get('page',1)
        # page_size = data.get('page_size',10)
        sent_sort = data.get('sent_sort', 'default')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'

        # ids_to_skip = list(BlockedUsers.objects.filter(user=user_obj, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True).values_list('blocked_user__mlp_id', flat=True))        
        # ids_to_skip += list(BlockedUsers.objects.filter(blocked_user=user_obj, user__is_active=True, user__mandatory_questions_completed=True).values_list("user__mlp_id", flat=True))
        # print(ids_to_skip)
        blocked_users_query = Q(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True) | Q(blocked_user=user_obj, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)
        ids_to_skip = list(
            BlockedUsers.objects.filter(blocked_users_query).values_list(
                Case(
                    When(user=user_obj, then=F('blocked_user__mlp_id')),
                    When(blocked_user=user_obj, then=F('user__mlp_id')),
                    output_field=CharField(),
                ),
                flat=True
            )
        )
        
        recieved_intrests = Intrest.objects.filter(invitation_by__mandatory_questions_completed=True, invitation_by__is_active=True, invitation_by__is_wrong=False, invitation_to=user_obj, status__in=['Pending', 'Rejected']).exclude(invitation_by__mlp_id__in=ids_to_skip).order_by('-id')
        sent_intrests = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True,  invitation_to__is_wrong=False, status__in=['Pending', 'Rejected']).exclude(invitation_to__mlp_id__in=ids_to_skip).order_by('-id')
        # paginator = Paginator(recieved_intrests, page_size)
        # paginated_queryset = paginator.get_page(page) 
        recieved_requests = []
        for intrest_obj in recieved_intrests:
            data = {}
            res = show_name(user_obj,intrest_obj.invitation_by)
        
            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

            res = show_photographs(user_obj,intrest_obj.invitation_by)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and intrest_obj.invitation_by.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True
        
            user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=intrest_obj.invitation_by.mlp_id)
            data['mlp_id'] = intrest_obj.invitation_by.mlp_id
            data['mobile_number'] = intrest_obj.invitation_by.mobile_number
            data['name'] = intrest_obj.invitation_by.mlp_id if name_hidden else intrest_obj.invitation_by.name
            data['email'] = intrest_obj.invitation_by.email
            data['gender'] = intrest_obj.invitation_by.gender
            data['dob'] = intrest_obj.invitation_by.dob
            data['activity_status'] = intrest_obj.invitation_by.activity_status
            data['last_seen']=intrest_obj.invitation_by.last_seen
            data['profile_pictures'] = json.loads(intrest_obj.invitation_by.profile_pictures)
            data['photo_hidden'] = photo_hidden
            data['height'] = intrest_obj.invitation_by.height
            data['religion'] = intrest_obj.invitation_by.religion.name if intrest_obj.invitation_by.religion else None
            data['city'] = intrest_obj.invitation_by.city
            data['caste'] = intrest_obj.invitation_by.caste
            data['marital_status']= intrest_obj.invitation_by.marital_status.name if intrest_obj.invitation_by.marital_status else None
            data['eating_habits']=intrest_obj.invitation_by.eating_habits
            data['is_bachelor'] = is_bachelor
            data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and intrest_obj.invitation_by.completed_post_grad else []
            data['graduation_id'] = intrest_obj.invitation_by.graduation_obj.name
            data['expertise_id'] = intrest_obj.invitation_by.graduation_obj.expertise_obj.name
            data['created_date'] = intrest_obj.created_date
            data['updated_date'] = intrest_obj.updated_date
            data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=intrest_obj.invitation_by).exists()
            data['status'] = intrest_obj.status
            recieved_requests.append(data)
        sent_requests = []
        # paginator1 = Paginator( sent_intrests, page_size)
        # paginated_queryset1 = paginator1.get_page(page)
        for intrest_obj in sent_intrests:
            data = {}
            res = show_name(user_obj,intrest_obj.invitation_to)
        
            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

            res = show_photographs(user_obj,intrest_obj.invitation_to)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and intrest_obj.invitation_to.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True


            user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=intrest_obj.invitation_to.mlp_id)
            data['mlp_id'] = intrest_obj.invitation_to.mlp_id
            data['mobile_number'] = intrest_obj.invitation_to.mobile_number
            data['name'] =intrest_obj.invitation_to.mlp_id if name_hidden else intrest_obj.invitation_to.name
            data['email'] = intrest_obj.invitation_to.email
            data['gender'] = intrest_obj.invitation_to.gender
            data['dob'] = intrest_obj.invitation_to.dob
            data['activity_status'] = intrest_obj.invitation_to.activity_status
            data['last_seen']=intrest_obj.invitation_to.last_seen
            data['profile_pictures'] = json.loads(intrest_obj.invitation_to.profile_pictures)
            data['photo_hidden'] = photo_hidden
            data['height'] = intrest_obj.invitation_to.height
            data['marital_status']= intrest_obj.invitation_to.marital_status.name if intrest_obj.invitation_to.marital_status else None
            data['eating_habits']=intrest_obj.invitation_to.eating_habits
            data['religion'] = intrest_obj.invitation_to.religion.name if intrest_obj.invitation_to.religion else None
            data['city'] = intrest_obj.invitation_to.city
            data['caste'] = intrest_obj.invitation_to.caste
            data['is_bachelor'] = is_bachelor
            data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=intrest_obj.invitation_to).exists()
            data['vp'] = 1 if SeenUser.objects.filter(user=intrest_obj.invitation_to, seen_profile=user_obj).exists() else 0
            data['rp'] = 1 if intrest_obj.status == "Rejected" else 0
            data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and intrest_obj.invitation_to.completed_post_grad else []
            data['graduation_id'] = intrest_obj.invitation_to.graduation_obj.name
            data['expertise_id'] = intrest_obj.invitation_to.graduation_obj.expertise_obj.name
            sent_requests.append(data)
        if sent_sort == "viewed profile":
            sent_requests = sorted(sent_requests, key=lambda x: x['vp'], reverse=True)
        elif sent_sort == "not viewed profile":
            sent_requests = sorted(sent_requests, key=lambda x: x['vp'])
        elif sent_sort == "rejected profile":
            sent_requests = sorted(sent_requests, key=lambda x: x['rp'], reverse=True)
        response['status_code'] = 200
        response['message'] = "Query executed successfully"
        # response['total_pages_recieved_interest']=  paginator.num_pages
        # response['total_pages_sent_interest'] = paginator1.num_pages
        response['recieved_requests'] = recieved_requests
        response['sent_requests'] = sent_requests
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

# def get_intrests_requests(data):
#     response = {
#         'status_code': 500,
#         'message': 'Internal server error'
#     }
#     try:
#         mlp_id = data.get('mlp_id', '')
#         page = data.get('page',1)
#         page_size = data.get('page_size',10)
#         sent_sort = data.get('sent_sort', 'default')
#         if not mlp_id:
#             response["status_code"] = 301
#             response["message"] = "MLP id missing"
#             return response
#         user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True)
#         if not user_obj.first():
#             response['status_code'] = 404
#             response["message"] = "User not found"
#             return response
#         else:
#             user_obj = user_obj.first()
#         opposite_gender = 'm' if user_obj.gender == 'f' else 'f'

#         blocked_users_query = Q(user=user_obj, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True) | Q(blocked_user=user_obj, user__is_active=True, user__mandatory_questions_completed=True)
#         ids_to_skip = list(
#             BlockedUsers.objects.filter(blocked_users_query).values_list(
#                 Case(
#                     When(user=user_obj, then=F('blocked_user__mlp_id')),
#                     When(blocked_user=user_obj, then=F('user__mlp_id')),
#                     output_field=CharField(),
#                 ),
#                 flat=True
#             )
#         )
        
#         sent_intrests = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mandatory_questions_completed=True, invitation_to__is_active=True, status__in=['Pending', 'Rejected']).exclude(invitation_to__mlp_id__in=ids_to_skip).order_by('-id')
      
#         sent_requests = []
#         paginator = Paginator(sent_intrests, page_size)
#         paginated_queryset = paginator.get_page(page)
#         for intrest_obj in paginated_queryset:
#             data = {}
#             res = show_name(user_obj,intrest_obj.invitation_to)
        
#             if res:
#                 if res["status_code"] == 200:
#                     name_hidden = False
#                 else:
#                     name_hidden = True

#             res = show_photographs(user_obj,intrest_obj.invitation_to)
        
#             if res:
#                 if res["status_code"] == 200:
#                     photo_hidden = False
#                 else:
#                     photo_hidden = True

#             is_bachelor = False
#             bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
#             if bachelor_of_the_day and intrest_obj.invitation_to.mlp_id == bachelor_of_the_day.user.mlp_id:
#                 is_bachelor = True


#             user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=intrest_obj.invitation_to.mlp_id)
#             data['mlp_id'] = intrest_obj.invitation_to.mlp_id
#             data['mobile_number'] = intrest_obj.invitation_to.mobile_number
#             data['name'] =intrest_obj.invitation_to.mlp_id if name_hidden else intrest_obj.invitation_to.name
#             data['email'] = intrest_obj.invitation_to.email
#             data['gender'] = intrest_obj.invitation_to.gender
#             data['dob'] = intrest_obj.invitation_to.dob
#             data['activity_status'] = intrest_obj.invitation_to.activity_status
#             data['last_seen']=intrest_obj.invitation_to.last_seen
#             data['profile_pictures'] = json.loads(intrest_obj.invitation_to.profile_pictures)
#             data['photo_hidden'] = photo_hidden
#             data['height'] = intrest_obj.invitation_to.height
#             data['marital_status']= intrest_obj.invitation_to.marital_status.name if intrest_obj.invitation_to.marital_status else None
#             data['eating_habits']=intrest_obj.invitation_to.eating_habits
#             data['religion'] = intrest_obj.invitation_to.religion.name if intrest_obj.invitation_to.religion else None
#             data['city'] = intrest_obj.invitation_to.city
#             data['caste'] = intrest_obj.invitation_to.caste
#             data['is_bachelor'] = is_bachelor
#             data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=intrest_obj.invitation_to).exists()
#             data['vp'] = 1 if SeenUser.objects.filter(user=intrest_obj.invitation_to, seen_profile=user_obj).exists() else 0
#             data['rp'] = 1 if intrest_obj.status == "Rejected" else 0
#             data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and intrest_obj.invitation_to.completed_post_grad else []
#             data['graduation_id'] = intrest_obj.invitation_to.graduation_obj.name
#             data['expertise_id'] = intrest_obj.invitation_to.graduation_obj.expertise_obj.name
#             sent_requests.append(data)
#         if sent_sort == "viewed profile":
#             sent_requests = sorted(sent_requests, key=lambda x: x['vp'], reverse=True)
#         elif sent_sort == "not viewed profile":
#             sent_requests = sorted(sent_requests, key=lambda x: x['vp'])
#         elif sent_sort == "rejected profile":
#             sent_requests = sorted(sent_requests, key=lambda x: x['rp'], reverse=True)
#         response['status_code'] = 200
#         response['message'] = "Query executed successfully"
#         response['total_pages_sent_interest'] = paginator.num_pages
#         response['sent_requests'] = sent_requests
#         return response
#     except Exception as e:
#         logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
#         # traceback.print_exc()
#         return response


def get_blocked_profiles(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        page = data.get('page',1)
        page_size = data.get('page_size',10)
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'    
        blocked_users = BlockedUsers.objects.filter(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True).order_by("-id")
        
        total_count = blocked_users.count()

        paginator = Paginator(blocked_users, page_size)
        paginated_queryset = paginator.get_page(page) 

        blocked_profiles = []
        for blocked_obj in paginated_queryset:
            data = {}
            res = show_name(user_obj,blocked_obj.blocked_user)
        
            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

            res = show_photographs(user_obj,blocked_obj.blocked_user)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and blocked_obj.blocked_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True


            user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=blocked_obj.blocked_user.mlp_id)
            data['mlp_id'] = blocked_obj.blocked_user.mlp_id
            data['mobile_number'] = blocked_obj.blocked_user.mobile_number
            data['name'] = blocked_obj.blocked_user.mlp_id if name_hidden else blocked_obj.blocked_user.name
            data['email'] = blocked_obj.blocked_user.email
            data['gender'] = blocked_obj.blocked_user.gender
            data['dob'] = blocked_obj.blocked_user.dob
            data['activity_status'] = blocked_obj.blocked_user.activity_status
            data['last_seen']=blocked_obj.blocked_user.last_seen
            data['height'] = blocked_obj.blocked_user.height
            data['religion'] = blocked_obj.blocked_user.religion.name if blocked_obj.blocked_user.religion else None
            data['city'] = blocked_obj.blocked_user.city
            data['caste'] = blocked_obj.blocked_user.caste
            data['profile_pictures'] = json.loads(blocked_obj.blocked_user.profile_pictures)
            data['photo_hidden'] = photo_hidden
            data['is_bachelor']= is_bachelor
            data['marital_status'] = blocked_obj.blocked_user.marital_status.name if blocked_obj.blocked_user.marital_status else None
            data['eating_habits']=blocked_obj.blocked_user.eating_habits
            data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and blocked_obj.blocked_user.completed_post_grad else []
            data['graduation_id'] = blocked_obj.blocked_user.graduation_obj.name
            data['expertise_id'] = blocked_obj.blocked_user.graduation_obj.expertise_obj.name
            data['created_date'] = blocked_obj.created_date
            data['updated_date'] = blocked_obj.updated_date
            blocked_profiles.append(data)
        response['status_code'] = 200
        response['message'] = "Query executed successfully"
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['blocked_profiles'] = blocked_profiles
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def get_saved_profiles(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id = data.get('mlp_id', '')
        page = data.get('page',1)
        page_size = data.get('page_size',10)
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True, is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'       
        # ids_to_skip = list(BlockedUsers.objects.filter(user=user_obj, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True).values_list('blocked_user__mlp_id', flat=True))        
        # ids_to_skip += list(BlockedUsers.objects.filter(blocked_user=user_obj, user__is_active=True, user__mandatory_questions_completed=True).values_list("user__mlp_id", flat=True))
        blocked_users_query = Q(user=user_obj, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True) | Q(blocked_user=user_obj, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)
        ids_to_skip = list(
            BlockedUsers.objects.filter(blocked_users_query).values_list(
                Case(
                    When(user=user_obj, then=F('blocked_user__mlp_id')),
                    When(blocked_user=user_obj, then=F('user__mlp_id')),
                    output_field=CharField(),
                ),
                flat=True
            )
        )
        saved_users = SavedUser.objects.filter(user=user_obj, saved_profile__is_active=True, saved_profile__is_wrong=False,saved_profile__mandatory_questions_completed=True).exclude(saved_profile__mlp_id__in=ids_to_skip).order_by("-id")
        
        paginator = Paginator(saved_users, page_size)
        paginated_queryset = paginator.get_page(page) 

        saved_profiles = []
        for saved_obj in paginated_queryset:
            data = {}
            
            if ConnectionList.objects.filter(Q(user_one=user_obj, user_two=saved_obj.saved_profile) | Q(user_two=user_obj, user_one=saved_obj.saved_profile)).exists():
                continue

            res = show_name(user_obj,saved_obj.saved_profile)
        
            if res:
                if res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True
            
            res = show_photographs(user_obj,saved_obj.saved_profile)
        
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True
            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and saved_obj.saved_profile.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True
    
            user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=saved_obj.saved_profile.mlp_id)
            data['mlp_id'] = saved_obj.saved_profile.mlp_id
            data['mobile_number'] = saved_obj.saved_profile.mobile_number
            data['name'] = saved_obj.saved_profile.mlp_id if name_hidden else saved_obj.saved_profile.name
            data['email'] = saved_obj.saved_profile.email
            data['gender'] = saved_obj.saved_profile.gender
            data['dob'] = saved_obj.saved_profile.dob
            data['activity_status'] = saved_obj.saved_profile.activity_status
            data['last_seen']=saved_obj.saved_profile.last_seen
            data['profile_pictures'] = json.loads(saved_obj.saved_profile.profile_pictures)
            data['photo_hidden'] = photo_hidden
            data['name_hidden'] = name_hidden
            data['is_bachelor'] = is_bachelor
            data['connection_status'] = True if Intrest.objects.filter(invitation_by=user_obj,invitation_to=saved_obj.saved_profile, status__in=["Accepted"]).exists() or Intrest.objects.filter(invitation_by=saved_obj.saved_profile, invitation_to=user_obj, status__in=["Accepted"]).exists() else False
            data['height'] = saved_obj.saved_profile.height
            data['religion'] = saved_obj.saved_profile.religion.name if saved_obj.saved_profile.religion else None
            data['city'] = saved_obj.saved_profile.city
            data['eating_habits'] = saved_obj.saved_profile.eating_habits
            data['marital_status'] = saved_obj.saved_profile.marital_status.name if saved_obj.saved_profile.marital_status else None
            data['caste'] = saved_obj.saved_profile.caste
            data['interest_sent'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to=saved_obj.saved_profile).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by=saved_obj.saved_profile, invitation_to=user_obj).exists()
            data['shortlisted']=SavedUser.objects.filter(user=user_obj,saved_profile=saved_obj.saved_profile).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=saved_obj.saved_profile.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=saved_obj.saved_profile.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=saved_obj.saved_profile.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by=saved_obj.saved_profile, invitation_to=user_obj , status="Rejected").exists()
            data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first()  and saved_obj.saved_profile.completed_post_grad else []
            data['graduation_id'] = saved_obj.saved_profile.graduation_obj.name
            data['expertise_id'] = saved_obj.saved_profile.graduation_obj.expertise_obj.name
            data['created_date'] = saved_obj.created_date
            data['updated_date'] = saved_obj.updated_date
            saved_profiles.append(data)
        response['status_code'] = 200
        response['message'] = "Query executed successfully"
        response['total_pages'] = paginator.num_pages
        response['saved_profiles'] = saved_profiles
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def get_notifications_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        seen_ids = data.get('seen_ids','')
        marked_seen = data.get('marked_seen','')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP id missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            notifications_all=Notifications.objects.filter(user__mlp_id=mlp_id).all().values()
            if seen_ids:
                Notifications.objects.filter(id__in=seen_ids).delete()
            if marked_seen:
                notifications=Notifications.objects.filter(id__in=marked_seen)
                for i in notifications:
                    i.is_seen=True
                    i.save()
        response['status_code'] = 200
        response['message'] = "Notifications sent successfully"
        response['all_notifications'] = list(notifications_all)
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def post_stories_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        url = data.get('url','')
        type = data.get('type','')
        if not data:
            response["status_code"] = 301
            response["message"] = "Fields missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
            Stories.objects.create(user=user_obj, url=url,type=type)
            response['status_code'] = 200
            response['message'] = "Story added successfully"
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response
    
def get_stories_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP ID is missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
            twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            all_stories = Stories.objects.filter(user=user_obj,created_at__gte=twenty_four_hours_ago).all().values()
            #who all viewed my story
            for story in all_stories:
                viewed_stories = ViewedStories.objects.filter(story=story.get("id")).all().values('id','story','viewed_by__mlp_id','viewed_by__name','viewed_by__profile_pictures','is_viewed','viewed_datetime').order_by('-viewed_datetime')
                for i in viewed_stories:
                    i["viewed_by__profile_pictures"]=json.loads(i["viewed_by__profile_pictures"])
                story["viewed_stories"]=list(viewed_stories)
            
            all_stories = sorted(all_stories, key=lambda x: x['created_at'])
            response['status_code'] = 200
            response['data']=list(all_stories)
            response['message'] = "Stories sent successfully"
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def delete_stories_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        story_id = data.get('story_id','')
        if not mlp_id and story_id:
            response["status_code"] = 301
            response["message"] = "MLP ID and story ID is missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
            existing_story=Stories.objects.filter(user=user_obj, id=story_id)
            if existing_story:
                delete_imagefunc(existing_story.first().url)
                existing_story.delete()
                
                response['status_code'] = 200
                response['message'] = "Story deleted successfully"
                return response
            else:
                response['status_code'] = 404
                response['message'] = "Story not found"
                return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def get_all_stories_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        viewedstories_id = data.get('viewedstories_id',[])
        
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP ID is missing"
            return response
        user_obj = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False)
        if not user_obj.first():
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        else:
            user_obj = user_obj.first()
            opposite_gender = 'm' if user_obj.gender == 'f' else 'f'   
            if viewedstories_id:
                for i in viewedstories_id:
                    ViewedStories.objects.get_or_create(story_id=i,viewed_by=user_obj)
            twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
            all_stories = Stories.objects.filter(created_at__gte=twenty_four_hours_ago,user__is_active=True,user__is_wrong=False).exclude(Q(user=user_obj) | Q(user__gender=user_obj.gender) | Q(user__blocked_user__user=user_obj) | Q(user__blocking_user__blocked_user=user_obj)).values('id','url', 'type', 'created_at', 'user__mlp_id','user__name','user__profile_pictures', 'user__activity_status',"user__dob", "user__religion__id", "user__marital_status__id")
            all_stories = sorted(all_stories, key=lambda x: x['created_at'])
            # for stories in all_stories:
            #     stories['user__profile_pictures']=json.loads(stories.get('user__profile_pictures'))
            #     viewed_by_me = ViewedStories.objects.filter(story__id=stories.get("id"),viewed_by=user_obj).exists()
            #     interest_sent = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=stories.get("user__mlp_id")).exists()
            #     interest_received = Intrest.objects.filter(invitation_by__mlp_id=stories.get("user__mlp_id"), invitation_to=user_obj).exists()
            #     mutually_accepted = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=stories.get("user__mlp_id"))|Q(user_two=user_obj, user_one__mlp_id=stories.get("user__mlp_id"))).exists()
            #     interest_rejected = Intrest.objects.filter(invitation_by__mlp_id=stories.get("user__mlp_id"), invitation_to=user_obj,status="Rejected").exists()
            #     shortlisted = SavedUser.objects.filter(user=user_obj, saved_profile__mlp_id=stories.get("user__mlp_id")).exists()
            #     stories['viewed_by_me']=viewed_by_me
            #     stories['interest_sent']=interest_sent
            #     stories['interest_received']=interest_received
            #     stories['mutually_accepted']=mutually_accepted
            #     stories["interest_rejected"]=interest_rejected
            #     stories['shortlisted']=shortlisted
                
            
            # final_response=[]
            # user_stories_dict={}
            # for story in list(all_stories):
            #     user_stories_dict.setdefault(story['user__mlp_id'],[]).append(story)
            
            
            # for user_id, stories_list in user_stories_dict.items():
            #     final_response.append({user_id: stories_list})

            # response['status_code'] = 200
            # response['data']=final_response
            # response['message'] = "Stories sent successfully"
            # return response
            user_stories_dict = {}
            for story in list(all_stories):
                user_stories_dict.setdefault(story['user__mlp_id'], []).append(story)

            final_response = []
            
            for user_id, stories_list in user_stories_dict.items():
                res = show_name(user_obj,User.objects.filter(mlp_id=user_id).first())
                # print(res)
                if res:
                    if res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True
                res = show_photographs(user_obj,User.objects.filter(mlp_id=user_id).first())
        
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True
                
                saved_obj=User.objects.filter(mlp_id=user_id).first()
                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
                if bachelor_of_the_day and saved_obj.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True

                user_data = {
                    'user__mlp_id': user_id,
                    'user__name': user_id if name_hidden else stories_list[0]['user__name'],
                    'user__profile_pictures': json.loads(stories_list[0]['user__profile_pictures']),
                    'photo_hidden':photo_hidden,
                    'name_hidden': name_hidden,
                    'user__dob': stories_list[0]['user__dob'],
                    'user__activity_status': stories_list[0]['user__activity_status'],
                    'user__religion__id': stories_list[0]['user__religion__id'],
                    'user__marital_status__id': stories_list[0]['user__marital_status__id'],
                    # 'viewed_by_me': ViewedStories.objects.filter(story__id__in=[s['id'] for s in stories_list], viewed_by=user_obj).exists(),
                    'interest_sent': Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=user_id).exists(),
                    'interest_received': Intrest.objects.filter(invitation_by__mlp_id=user_id, invitation_to=user_obj).exists(),
                    'mutually_accepted': ConnectionList.objects.filter(
                        Q(user_one=user_obj, user_two__mlp_id=user_id)
                        | Q(user_two=user_obj, user_one__mlp_id=user_id)
                    ).exists(),
                    'is_bachelor': is_bachelor,
                    'interest_rejected': Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=user_id, status="Rejected").exists(),
                    'interest_rejected_by_me': Intrest.objects.filter(invitation_by__mlp_id=user_id, invitation_to=user_obj , status="Rejected").exists(),
                    'shortlisted': SavedUser.objects.filter(user=user_obj, saved_profile__mlp_id=user_id).exists(),
                    'stories': [
                        {
                            'id': s['id'],
                            'url': s['url'],
                            'type': s['type'],
                            'created_at': s['created_at'],
                            'viewed_by_me': ViewedStories.objects.filter(story__id=s['id'], viewed_by=user_obj).exists()
                        }
                        for s in stories_list
                    ]
                }
                final_response.append(user_data)

            response['status_code'] = 200
            response['data'] = final_response
            response['message'] = "Stories sent successfully"
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def validate_email_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        email = data.get('email','')
        if not mlp_id and not email:
            response["status_code"] = 301
            response["message"] = "Fields missing"
            return response
        existinguser = User.objects.filter(mlp_id=mlp_id)
        existingemail = User.objects.filter(email=email).first()
        if existinguser:
            existinguser=existinguser.first()
            if existinguser.email == email:
                response["status_code"] = 200
                response["message"] = "Email ID is available"
                return response
            elif existingemail:
                response["status_code"] = 404
                response["message"] = "Email ID already in use"
                return response
            else:
                response["status_code"] = 200
                response["message"] = "Email ID is available"
                return response
        response["status_code"] = 404
        response["message"] = "User not found"
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def respond_interestsfunc(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id=data.get('mlp_id')
        receiver_mlp_id = data.get('receiver_mlp_id')
        status=data.get('status')
        if not mlp_id and receiver_mlp_id:
            response["status_code"] = 301
            response["message"] = "Id for sender and receiver are missing"
            return response
        sender = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False).first()
        receiver = User.objects.filter(mlp_id=receiver_mlp_id, is_active=True,is_wrong=False).first()
        if not sender or not receiver:
            response["status_code"] = 301
            response["message"] = "User not found"
            return response
        if BlockedUsers.objects.filter(user=sender, blocked_user=receiver).exists():
                response['status_code'] = 301
                response['message'] = 'You have blocked the User'
                return response
        if BlockedUsers.objects.filter(user=receiver, blocked_user=sender).exists():
            response['status_code'] = 302
            response['message'] = 'User has blocked you'
            return response
        
        existing_interest=Intrest.objects.filter(invitation_by=receiver, invitation_to=sender).first()
        
        if not existing_interest:
            response["status_code"] = 301
            response["message"] = "No interest found to accept or reject"
            return response
        else:
            existing_interest.status=status
            existing_interest.updated_date=datetime.now()
            existing_interest.save()
            existing_connectionlist=ConnectionList.objects.filter(Q(user_one=sender, user_two=receiver)|Q(user_one=receiver, user_two=sender))
            if existing_interest.status=="Accepted":
                if not existing_connectionlist.exists():
                    ConnectionList.objects.create(user_one=receiver, user_two=sender)
                    link="https://bit.ly/2JQ7u6i"
                    template_id=1307161911414085583
                    message = f"Hi {receiver.name}, {sender.name} ({sender.mlp_id}) has accepted your interest on medicolifepartner.com(Exclusive Venture)! Would you like to initiate conversation with them? {link}"
                    sms_send(receiver.mobile_number,message, template_id)
                    custom_data={
                        "screen":"Mutualconnection",
                        "userid":receiver.mlp_id
                        }
                    if receiver.notification_token!=None:
                        message =messaging.Message(
                            token=receiver.notification_token,  
                            notification=messaging.Notification(
                                title="It's a Match! 💑",
                                body="Great news! Your interest has been accepted. Start the conversation and explore the possibilities of a new connection! 🎉",
                            ),
                            data=custom_data  
                        )

                        res = messaging.send(message)


                        # push_service.notify_single_device(registration_id=receiver.notification_token,message_title="It's a Match! 💑",message_body="Great news! Your interest has been accepted. Start the conversation and explore the possibilities of a new connection! 🎉",data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=receiver).all()
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message_body = f"{receiver.name} interest has been accepted. Start the conversation and explore the possibilities of a new connection! 🎉"
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title="It's a Match! 💑",
                                body=message_body,
                            ),
                              data=custom_data  
                        ) 

                        res = messaging.send_multicast(message)
                        #push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title="It's a Match! 💑",message_body=message_body,data_message=custom_data)
                    
                    result = calculate_match_percentage(sender.mlp_id , receiver.mlp_id)
                    match_percent ="NA"
                    if result["status_code"] == 200:
                        match_percent = str(result["match_percentage"])
                        if "." in match_percent:
                            match_percent = match_percent.split(".")[0]
                            match_percent = f"{match_percent}%"
                    user_post_graduation = UserPostGraduation.objects.filter(user=sender)
                    pictures = json.loads(receiver.profile_pictures) 
                    receiver_pic = pictures[0] if pictures else "NA"
                    post_grads = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() else []
                    graduation_id = sender.graduation_obj.name
                    subject = f"New Connection at medicolifepartner.com"
                    if post_grads:
                        email_content = email_services.set_email_interestaccepted(sender,receiver.name,graduation_id,post_grads[0],receiver_pic,match_percent)
                    else:
                        email_content = email_services.set_email_interestaccepted(sender,receiver.name,graduation_id,"NA",receiver_pic,match_percent)
                    ses_wrapper.send_email(receiver_email_address=receiver.email,subject=subject,html_body=email_content['message'])
                    Notifications.objects.create(user=receiver,sender=sender, message="Great news! Your interest has been accepted. Start the conversation and explore the possibilities of a new connection! 🎉",type="Interest_Accepted", created_date=timezone.now)
                else:
                    existing_connectionlist=existing_connectionlist.first()
                    existing_connectionlist.updated_date=datetime.now()
                    existing_connectionlist.save()
            elif existing_interest.status=="Rejected" or existing_interest.status=="Pending":
                if existing_interest.status=="Rejected":
                    custom_data={
                        "screen":"InterestRejected",
                        "userid":receiver.mlp_id
                        }
                    if receiver.notification_token!=None:
                        message = messaging.Message(
                            token=receiver.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title="On to the Next Chapter 🚀",
                                body=f"Your interest to MLP Id: {sender.mlp_id} has been rejected. No worries! If it's not the right match, there are plenty more opportunities. Keep exploring and find the perfect match. Happy connecting! 😊"
                            ),
                            data=custom_data  # Custom data payload
                        )

                        res = messaging.send(message)
                        
                        # push_service.notify_single_device(registration_id=receiver.notification_token,message_title="On to the Next Chapter 🚀",message_body=f"Your interest to MLP Id: {sender.mlp_id} has been rejected. No worries! If it's not the right match, there are plenty more opportunities. Keep exploring and find the perfect match. Happy connecting! 😊",data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=receiver).all()
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message_body = f"{receiver.name} interest has been rejected by MLP Id: {sender.mlp_id}. No worries! If it's not the right match, there are plenty more opportunities. Keep exploring and find the perfect match. Happy connecting! 😊"
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title="On to the Next Chapter 🚀",
                                body=message_body,
                            ),
                              data=custom_data  
                        ) 

                        res = messaging.send_multicast(message)
                       # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title="On to the Next Chapter 🚀",message_body=message_body,data_message=custom_data)
                    
                    result = calculate_match_percentage(sender.mlp_id , receiver.mlp_id)
                    match_percent ="NA"
                    if result["status_code"] == 200:
                        match_percent = str(result["match_percentage"])
                        if "." in match_percent:
                            match_percent = match_percent.split(".")[0]
                            match_percent = f"{match_percent}%"
                    user_post_graduation = UserPostGraduation.objects.filter(user=sender)
                    pictures = json.loads(receiver.profile_pictures) 
                    receiver_pic = pictures[0] if pictures else "NA"
                    post_grads = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() else []
                    graduation_id = sender.graduation_obj.name
                    subject = f"Interest Rejected at medicolifepartner.com"
                    if post_grads:
                        email_content = email_services.set_email_interestrejected(sender,receiver.name,graduation_id,post_grads[0],receiver_pic,match_percent)
                    else:
                        email_content = email_services.set_email_interestrejected(sender,receiver.name,graduation_id,"NA",receiver_pic,match_percent)
                    ses_wrapper.send_email(receiver_email_address=receiver.email,subject=subject,html_body=email_content['message'])
                    email_services.send_email(subject,email_content['message'],to_email=[receiver.email])
                    Notifications.objects.create(user=receiver,sender=sender, message=f"Your interest to MLP Id: {sender.mlp_id} has been rejected. No worries! If it's not the right match, there are plenty more opportunities. Keep exploring and find the perfect match. Happy connecting! 😊",type="Interest_Rejected", created_date=timezone.now)
                if existing_connectionlist.exists():
                    existing_connectionlist.delete()
                exiting_notifications = Notifications.objects.filter(user=receiver,sender=sender,type="Interest_Accepted")
                if exiting_notifications:
                    exiting_notifications.delete()
            else:
                pass
            
            response["status_code"] = 200
            response["message"] = "Interest status changed successfully"
            response['interest_status'] = existing_interest.status

            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response
    

def getmutuallyacceptedfunc(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id=data.get('mlp_id')
        page = data.get('page',1)
        page_size = data.get('page_size',10)
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "Id is missing"
            return response
        user = User.objects.filter(mlp_id=mlp_id, is_active=True, is_wrong=False).first()
        opposite_gender = 'm' if user.gender == 'f' else 'f'   
        if not user:
            response["status_code"] = 301
            response["message"] = "User not found"
            return response
        blocked_users_query = Q(user=user, blocked_user__is_active=True, blocked_user__is_wrong=False, blocked_user__mandatory_questions_completed=True) | Q(blocked_user=user, user__is_active=True, user__is_wrong=False, user__mandatory_questions_completed=True)
        ids_to_skip = list(
            BlockedUsers.objects.filter(blocked_users_query).values_list(
                Case(
                    When(user=user, then=F('blocked_user__mlp_id')),
                    When(blocked_user=user, then=F('user__mlp_id')),
                    output_field=CharField(),
                ),
                flat=True
            )
        )
        # ids_to_skip = list(BlockedUsers.objects.filter(user=user, blocked_user__is_active=True, blocked_user__mandatory_questions_completed=True).values_list('blocked_user__mlp_id', flat=True))        
        # ids_to_skip += list(BlockedUsers.objects.filter(blocked_user=user, user__is_active=True, user__mandatory_questions_completed=True).values_list("user__mlp_id", flat=True))
        mutualmatches = ConnectionList.objects.filter(
            Q(user_one=user) | Q(user_two=user)
        ).exclude(
            Q(user_one__mlp_id__in=ids_to_skip)|
            Q(user_two__mlp_id__in=ids_to_skip)
        ).order_by('updated_date').all()
       
        paginator = Paginator(mutualmatches, page_size)
        paginated_queryset = paginator.get_page(page) 

        mutuallymatcheddata = []
        for intrest_obj in paginated_queryset:
            data = {}
            if intrest_obj.user_one==user:
                if not intrest_obj.user_two.mandatory_questions_completed:
                    continue
                
                res = show_name(user,intrest_obj.user_two)
        
                if res:
                    if res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True

                res = show_photographs(user,intrest_obj.user_two)
        
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True

                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
                if bachelor_of_the_day and intrest_obj.user_two.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True
        
                user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=intrest_obj.user_two.mlp_id)
                data['mlp_id'] = intrest_obj.user_two.mlp_id
                data['mobile_number'] = intrest_obj.user_two.mobile_number
                data['name'] =intrest_obj.user_two.mlp_id if name_hidden else intrest_obj.user_two.name
                data['email'] = intrest_obj.user_two.email
                data['gender'] = intrest_obj.user_two.gender
                data['dob'] = intrest_obj.user_two.dob
                data['activity_status'] = intrest_obj.user_two.activity_status
                data['last_seen']=intrest_obj.user_two.last_seen
                data['profile_pictures'] = json.loads(intrest_obj.user_two.profile_pictures)
                data['photo_hidden'] = photo_hidden
                data['name_hidden'] = name_hidden
                data['is_bachelor'] = is_bachelor
                data['eating_habits'] = intrest_obj.user_two.eating_habits
                data['height'] = intrest_obj.user_two.height
                data['marital_status'] = intrest_obj.user_two.marital_status.name if  intrest_obj.user_two.marital_status else None
                data['religion'] = intrest_obj.user_two.religion.name if intrest_obj.user_two.religion else None
                data['city'] = intrest_obj.user_two.city
                data['caste'] = intrest_obj.user_two.caste
                data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and intrest_obj.user_two.completed_post_grad else []
                data['graduation_id'] = intrest_obj.user_two.graduation_obj.name
                data['expertise_id'] = intrest_obj.user_two.graduation_obj.expertise_obj.name
            
                mutuallymatcheddata.append(data)
            else:
                if not intrest_obj.user_one.mandatory_questions_completed:
                    continue 

                res = show_name(user,intrest_obj.user_one)
        
                if res:
                    if res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True
                res = show_photographs(user,intrest_obj.user_one)
        
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True

                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
                if bachelor_of_the_day and intrest_obj.user_one.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True


                user_post_graduation = UserPostGraduation.objects.filter(user__mlp_id=intrest_obj.user_one.mlp_id)
                data['mlp_id'] = intrest_obj.user_one.mlp_id
                data['mobile_number'] = intrest_obj.user_one.mobile_number
                data['name'] = intrest_obj.user_one.mlp_id if name_hidden else intrest_obj.user_one.name
                data['email'] = intrest_obj.user_one.email
                data['gender'] = intrest_obj.user_one.gender
                data['dob'] = intrest_obj.user_one.dob
                data['activity_status'] = intrest_obj.user_one.activity_status
                data['last_seen']=intrest_obj.user_one.last_seen
                data['profile_pictures'] = json.loads(intrest_obj.user_one.profile_pictures)
                data['photo_hidden'] = photo_hidden
                data['name_hidden'] =name_hidden
                data['city'] = intrest_obj.user_one.city
                data['caste'] = intrest_obj.user_one.caste
                data['height'] = intrest_obj.user_one.height
                data['eating_habits'] = intrest_obj.user_one.eating_habits
                data['marital_status'] = intrest_obj.user_one.marital_status.name if  intrest_obj.user_one.marital_status else None
                data['religion'] = intrest_obj.user_one.religion.name if intrest_obj.user_one.religion else None
                data['is_bachelor'] = is_bachelor
                data['user_post_graduations'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and intrest_obj.user_one.completed_post_grad else []
                data['graduation_id'] = intrest_obj.user_one.graduation_obj.name
                data['expertise_id'] = intrest_obj.user_one.graduation_obj.expertise_obj.name
            
                mutuallymatcheddata.append(data)
        response['status_code'] = 200
        response['message'] = "Query executed successfully"
        response['total_pages'] = paginator.num_pages
        response['data'] = {
            "mutually_accepted":mutuallymatcheddata,
            "total_count":len(mutuallymatcheddata)
            }
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def deletenotificationtokenfunc(data):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        mlp_id=data.get('mlp_id')
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "Id is missing"
            return response
        user = User.objects.filter(mlp_id=mlp_id, is_active=True,is_wrong=False).first()
        
        if not user:
            response["status_code"] = 301
            response["message"] = "User not found"
            return response
        user.notification_token=None
        user.save()
        
        response['status_code'] = 200
        response['message'] = "Token deleted successfully"
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response
    
# service for  calculating match percentage 
def calculate_match_percentage(user_mlp_id, logged_user_mlp_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try: 
        user = User.objects.filter(mlp_id=user_mlp_id,is_active=True, is_wrong=False,mandatory_questions_completed=True).first()
        logged_user = User.objects.filter(mlp_id=logged_user_mlp_id,is_active=True,is_wrong=False,mandatory_questions_completed=True).first()
        if not user or not logged_user:
            response['status_code'] = 301
            response["message"] = "User/logged user not found"
            return response
        print(user.name , logged_user.name)
        if user and logged_user:
            res = viewed_contacts(logged_user,user)
            print("res" , res)
            if res:
                contact_hidden = res["param"]
                # if res["status_code"] == 200:
                #     contact_hidden = False
                # else:
                #     contact_hidden = True
                print('contact_hidden', contact_hidden)   
        previous_view = ProfileView.objects.filter(viewer=logged_user, viewed_user=user).first()

        if previous_view:
            # Update the visited_at field if the viewer has seen the same viewed_user again
            previous_view.visited_at = timezone.now()
            previous_view.save()
        else:
            # Create a new entry if there is no previous view
            ProfileView.objects.create(
                viewer=logged_user,
                viewed_user=user,
                visited_at=timezone.now(),
                viewed_at=timezone.now()
            )
        # cache_key = f"match_percentage_{user_mlp_id}_{logged_user_mlp_id}"
        # cached_data = cache.get(cache_key)
        # if cached_data:
        #     print("data from cache")
        #     return cached_data
        
        partner_preferences = {
           'partner_age_preference': logged_user.partner_age_preference,
            'age_range': {
                'min': logged_user.partner_age_from if logged_user.partner_age_from else 0,
                'max': logged_user.partner_age_to if logged_user.partner_age_to else 0
            },
            'partner_height_preference': logged_user.partner_height_preference,
            'height_range': {
                'min': logged_user.partner_height_from if logged_user.partner_height_from else 0,
                'max': logged_user.partner_height_to if logged_user.partner_height_to else 0
            },
            'partner_caste_preference': logged_user.partner_caste_preference,
            'caste': json.loads(logged_user.partner_caste_from) if logged_user.partner_caste_from else [],
            'partner_expertise_preference': logged_user.partner_expertise_preference,
            'expertise': list(logged_user.partnerexpertisepreference.values_list('expertise__name', flat=True)) if logged_user.partnerexpertisepreference.exists() else [],
            'partner_religion_preference': logged_user.partner_religion_preference,
            'religion': list(logged_user.partnerreligionpreference.values_list('religion__name', flat=True)) if logged_user.partnerreligionpreference.exists() else [],
            'partner_marital_status_preference': logged_user.partner_marital_status_preference,
            'marital_status': list(logged_user.partnermaritalstatuspreference.values_list('marital_status__name', flat=True)) if logged_user.partnermaritalstatuspreference.exists() else [],
            'partner_physical_status': logged_user.partner_physicalstatus if logged_user.partner_physicalstatus else None,
            'partner_graduation_preference': logged_user.partner_graduation_preference,
            'partner_graduation': list(PartnerGraduationPreference.objects.filter(user=logged_user).values_list('graduation__name', flat=True)) if logged_user.partner_graduation_preference else [],
            'partner_postgraduation_preference': logged_user.partner_postgraduation_preference,
            'partner_postgraduation': list(PartnerPGPreference.objects.filter(user=logged_user).values_list('post_graduation__name', flat=True)) if logged_user.partner_postgraduation_preference else [],
            'partner_mothertongue_preference': logged_user.partner_mothertongue_preference,
            'partner_mothertongue_from': list(logged_user.partner_mothertongue_from.values_list('name', flat=True)) if logged_user.partner_mothertongue_from.exists() else [],
            'partner_specialization_preference': logged_user.partner_specialization_preference,
            'specialization': list(PartnerSpecializationPreference.objects.filter(user=logged_user).values_list('specialization__name', flat=True)) if logged_user.partner_specialization_preference else [],
        }

        print("partner_pref", partner_preferences) 

        matches = {}
        match_count = 0
        total_criteria = 0
        
        #Check for age preference
        if partner_preferences['partner_age_preference']:
            if user.dob is not None: 
                if partner_preferences['age_range']['min'] <= (date.today().year - user.dob.year) <= partner_preferences['age_range']['max']:
                    matches['age_range'] = True
                    match_count += 1
                else:
                    matches['age_range'] = False
                total_criteria += 1
            else:
                matches['age_range'] = False
                total_criteria += 1    
        else:
            matches['age_range'] = True   
            match_count += 1
            total_criteria += 1  

        
        #Check for Height preference    
        if partner_preferences['partner_height_preference']:
            if user.height is not None:
                if partner_preferences['height_range']['min'] <= user.height <= partner_preferences['height_range']['max']:
                    matches['height_range'] = True
                    match_count += 1
                else:
                    matches['height_range'] = False
                total_criteria += 1
            else:
                matches['height_range'] = False
                total_criteria += 1    
        else:
            matches['height_range'] = True
            match_count += 1
            total_criteria += 1


        #Check for mother tongue preference
        if partner_preferences['partner_mothertongue_preference']:
            user_mother_tongue = set(user.mother_tongue.values_list('name', flat=True))
            partner_mother_tongue = set(partner_preferences['partner_mothertongue_from'])
            if user_mother_tongue and partner_mother_tongue:
                if user_mother_tongue.intersection(partner_mother_tongue):
                    matches['partner_mothertongue_from'] = True
                    match_count += 1
                else:
                    matches['partner_mothertongue_from'] = False
                total_criteria += 1
            else:
                matches['partner_mothertongue_from']=False
                total_criteria +=1
        else:
            matches['partner_mothertongue_from']=True
            match_count+=1
            total_criteria +=1            

        # Check for Physical Status Preference
        if partner_preferences['partner_physical_status']:
            user_physical_status = user.physical_status if user.physical_status else None
            partner_physical= partner_preferences['partner_physical_status']
            if user_physical_status and partner_physical:
                if user_physical_status == partner_preferences['partner_physical_status']:
                    matches['partner_physical_status'] = True
                    match_count += 1
                else:
                    matches['partner_physical_status'] = False
                total_criteria += 1    
            else:
                matches['partner_physical_status'] = False
                total_criteria +=1
        else:
            matches['partner_physical_status'] = True
            match_count+=1
            total_criteria +=1        

        
        # Check for Caste Preference
        if partner_preferences['partner_caste_preference']:
            user_caste = user.caste if user.caste else None
            partner_caste = partner_preferences['caste']
            if user_caste in partner_caste:
                matches['partner_caste_preference'] = True
                match_count += 1
            else:
                matches['partner_caste_preference'] = False
            total_criteria += 1
        else:
            matches['partner_caste_preference'] = True
            match_count+=1
            total_criteria +=1        
    
        
        
        # Check for Religion Preference
        if partner_preferences['partner_religion_preference']:
            user_religion = user.religion.name if user.religion else None
            if user_religion in partner_preferences['religion']:
                matches['partner_religion_preference'] = True
                match_count += 1
            else:
                matches['partner_religion_preference'] = False
            total_criteria += 1
        else:
            matches['partner_religion_preference']=True
            match_count += 1
            total_criteria +=1      
        
        
        # Check for Marital Status Preference
        if partner_preferences['partner_marital_status_preference']:
            user_marital_status = user.marital_status.name if user.marital_status else None
            if user_marital_status in partner_preferences['marital_status']:
                matches['partner_marital_status_preference'] = True
                match_count += 1
            else:
                matches['partner_marital_status_preference'] = False
            total_criteria += 1
        else:
            matches['partner_marital_status_preference']=True
            match_count +=1
            total_criteria +=1  

  

        #  Check for Expertise Preference
        if partner_preferences['partner_expertise_preference']:
            user_expertise = set(user.graduation_obj.expertise_obj.name if user.graduation_obj and user.graduation_obj.expertise_obj else "")
            if set(partner_preferences['expertise']).intersection(user_expertise):
                matches['partner_expertise_preference'] = True
                match_count += 1
            else:
                matches['partner_expertise_preference'] = False
            total_criteria += 1
        else:
            matches['partner_expertise_preference']=True
            match_count +=1
            total_criteria +=1    
        

        # # Check for Graduation Preference
        if partner_preferences['partner_graduation_preference']:
            user_graduation = user.graduation_obj.name if user.graduation_obj else None
            partner_graduation = set(partner_preferences['partner_graduation'])
            if user_graduation and partner_graduation:
                if set(user_graduation).intersection(partner_graduation):
                    matches['partner_graduation'] = True
                    match_count += 1
                else:
                    matches['partner_graduation'] = False
                total_criteria += 1
            else:
                matches['partner_graduation']=False
                total_criteria +=1
        else:
            matches['partner_graduation']=True
            match_count +=1
            total_criteria +=1           

        # Check for Postgraduation Preference
        if partner_preferences['partner_postgraduation_preference']:
            if user.completed_post_grad:
                user_postgraduation = set(UserPostGraduation.objects.filter(
                    user=user).values_list('post_graduation__name', flat=True))
            else:
                user_postgraduation = set()    
            partner_postgraduation = set(partner_preferences['partner_postgraduation'])
            if user_postgraduation and partner_postgraduation:
                if user_postgraduation.intersection(partner_postgraduation):
                    matches['partner_postgraduation'] = True
                    match_count += 1
                else:
                    matches['partner_postgraduation'] = False
                total_criteria += 1
            else:
                matches['partner_postgraduation']= False
                total_criteria+=1
        else:
            matches['partner_postgraduation']= True
            match_count += 1
            total_criteria+=1            
        
        # Check for specialization preference
        if partner_preferences['partner_specialization_preference']:
            user_specialization = set([user.specialization.name]) if user.specialization and user.specialization.name else set()
            partner_specialization = set(partner_preferences['specialization']) if partner_preferences['specialization'] else set()

            if user_specialization and partner_specialization:
                if user_specialization.intersection(partner_specialization):
                    matches['partner_specialization'] = True
                    match_count += 1
                else:
                    matches['partner_specialization'] = False
                total_criteria += 1
            else:
                matches['partner_specialization'] = False
                total_criteria +=1
        else:
            matches['partner_specialization'] = True
            match_count += 1
            total_criteria +=1            
       
        match_percentage = (match_count / total_criteria) * \
            100 if total_criteria > 0 else 0
        print("here in the end")
        response['status_code'] = 200
        response['message'] = "Match Percentage Data"
        response.update({
            'matched_criteria': matches,
            'logged_user_preferences': partner_preferences,
            'match_percentage': match_percentage,
            "contact_hidden":contact_hidden
        })
        
        #cache.set(cache_key, response, timeout=(3600*12)) 
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


# For getting online users
def get_online_users(mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:  
        user = User.objects.filter(mlp_id=mlp_id,is_active=True, is_wrong=False, mandatory_questions_completed=True).first()
       
        if not user :
            response['status_code'] = 301
            response["message"] = "User not found"
            return response

        opposite_gender = 'm' if user.gender == 'f' else 'f'

        blocked_users = BlockedUsers.objects.filter(user=user).values_list('blocked_user__mlp_id', flat=True)
       
        keys_with_online_value = redis_client.keys("online_*")

        keys_with_online_value = [key.decode() for key in keys_with_online_value]

        mlp_ids = [key.split("_")[1] for key in keys_with_online_value]

        if user.religion:
            queryset = User.objects.filter(is_active=True,is_wrong=False,religion=user.religion, activity_status = True, gender=opposite_gender ,mandatory_questions_completed=True).exclude(mlp_id__in=blocked_users).distinct()
        else:
            response['status_code'] = 300
            response['message'] = "religion not provided by auth user"  
            return response 

        total_count = queryset.count()  
         
        if not queryset:
            response['status_code'] = 204
            response['message'] = "No content Found"
            return response    
        
        paginator = Paginator(queryset, page_size)
        paginated_queryset = paginator.get_page(page)
       
        online_data=[]
        for data in paginated_queryset:
            suggested_user_id = data.id 
            suggested_user = User.objects.get(id=suggested_user_id)

            if ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists():
                continue

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True

            res = show_name(user, suggested_user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True
                
            res = show_photographs(user,suggested_user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True        

            data1 = {
                    'mlp_id': suggested_user.mlp_id,
                    'name': suggested_user.mlp_id if name_hidden else suggested_user.name,
                    'email': suggested_user.email,
                    'religion': suggested_user.religion.name if suggested_user.religion and suggested_user.religion.name else None,
                    'mobile_number': suggested_user.mobile_number,
                    'gender': suggested_user.gender,
                    'dob': suggested_user.dob,
                    'eating_habits' : suggested_user.eating_habits,
                    'marital_status':suggested_user.marital_status.name if suggested_user.marital_status and suggested_user.marital_status.name else None,
                    'profile_pictures': json.loads(suggested_user.profile_pictures),
                    'family_photos': json.loads(suggested_user.family_photos),
                    'activity_status':suggested_user.activity_status,
                    'last_seen':suggested_user.last_seen,
                    'manglik': suggested_user.manglik,
                    'height': suggested_user.height,
                    'weight': suggested_user.weight,
                    'hobbies': json.loads(suggested_user.hobbies),
                    'other_hobbies': json.loads(suggested_user.other_hobbies),
                    'city': suggested_user.city,
                    'caste': suggested_user.caste,
                    'completed_post_grad' : suggested_user.completed_post_grad,
                    'is_bachelor': is_bachelor
                }      
            
            data1['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()
            data1['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id).exists()
            data1['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user).exists()
            data1['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data1['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data1['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user, status="Rejected").exists() 
            user_graduation = suggested_user.graduation_obj.name if suggested_user.graduation_obj else None

            if suggested_user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=suggested_user).values_list('post_graduation__name', flat=True))
            else:
                user_post_graduation = set()

            user_expertise =  suggested_user.graduation_obj.expertise_obj.name if (suggested_user.graduation_obj and suggested_user.graduation_obj.expertise_obj) else None

            data1['graduation_id'] = user_graduation
            data1['user_post_graduation'] = list(user_post_graduation)
            data1['expertise_id'] = user_expertise

            
            data1['is_bachelor'] = is_bachelor
            data1['photo_hidden']=photo_hidden
            data1['name_hidden']=name_hidden 
            online_data.append(data1)  
        response['status_code'] = 200
        response['message'] = 'Online Users Data'
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = online_data
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    

# For newly joined Users in the current week
def get_newly_joined(mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:        
        user = User.objects.filter(mlp_id=mlp_id,is_active=True, is_wrong=False,mandatory_questions_completed=True).first()

        if not user :
            response['status_code'] = 301
            response["message"] = "User not found"
            return response
         
        opposite_gender = 'm' if user.gender == 'f' else 'f'
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        blocked_users = BlockedUsers.objects.filter(user=user).values_list('blocked_user__mlp_id', flat=True) 

        queryset = User.objects.filter(
            created_date__range=(start_date, end_date),
            gender=opposite_gender,
            is_active=True,
            is_wrong=False,
            mandatory_questions_completed=True
        ).exclude(mlp_id__in=blocked_users).order_by('-created_date').distinct()

        total_count = queryset.count()
        
        paginator = Paginator(queryset, page_size)
        paginated_queryset = paginator.get_page(page)

       # serializer = UserSerializer(paginated_queryset, many=True)

        if not queryset:
            response['status_code'] = 204
            response['message'] = "No content Found"
            return response
        else:
            all_suggested_users_data = []

            for data in paginated_queryset:
                suggested_user_id = data.id 
                suggested_user = User.objects.get(id=suggested_user_id)

                if  ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists():
                    continue

                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
                if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True


                res = show_name(user, suggested_user)
                if res and res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

                    
                res = show_photographs(user,suggested_user)
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True
               
                data = {
                    'mlp_id': suggested_user.mlp_id,
                    'name': suggested_user.mlp_id if name_hidden else suggested_user.name,
                    'email': suggested_user.email,
                    'religion': suggested_user.religion.name if suggested_user.religion and suggested_user.religion.name else None,
                    'mobile_number': suggested_user.mobile_number,
                    'gender': suggested_user.gender,
                    'dob': suggested_user.dob,
                    'eating_habits' : suggested_user.eating_habits,
                    'marital_status':suggested_user.marital_status.name if suggested_user.marital_status and suggested_user.marital_status.name else None,
                    'profile_pictures': json.loads(suggested_user.profile_pictures),
                    'family_photos': json.loads(suggested_user.family_photos),
                    'activity_status':suggested_user.activity_status,
                    'last_seen':suggested_user.last_seen,
                    'manglik': suggested_user.manglik,
                    'height': suggested_user.height,
                    'weight': suggested_user.weight,
                    'hobbies': json.loads(suggested_user.hobbies),
                    'other_hobbies': json.loads(suggested_user.other_hobbies),
                    'city': suggested_user.city,
                    'caste': suggested_user.caste,
                    'completed_post_grad' : suggested_user.completed_post_grad,
                    'is_bachelor': is_bachelor
                }       

                data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()
                data['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id).exists()
                data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user).exists()
                data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists()
                data['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
                data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user, status="Rejected").exists() 
                # Include user's graduation, post-graduation, expertise
                user_graduation = suggested_user.graduation_obj.name if suggested_user.graduation_obj else None

                if suggested_user.completed_post_grad:
                    user_post_graduation = set(UserPostGraduation.objects.filter(user=suggested_user).values_list('post_graduation__name', flat=True))
                else:
                    user_post_graduation = set()

                user_expertise =  suggested_user.graduation_obj.expertise_obj.name if (suggested_user.graduation_obj and suggested_user.graduation_obj.expertise_obj) else None

                data['graduation_id'] = user_graduation
                data['user_post_graduation'] = list(user_post_graduation)
                data['expertise_id'] = user_expertise
                
                data['is_bachelor'] = is_bachelor
                data['photo_hidden']=photo_hidden
                data['name_hidden']=name_hidden
                
                all_suggested_users_data.append(data)
            
            response['status_code'] = 200
            response['message'] = "Newly Joined Users Data"
            response['total_pages'] = paginator.num_pages
            response['total_count'] = total_count
            response['data'] = all_suggested_users_data
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


# #To send email for newly joined users
# def newly_joined_users_email(mlp_id):
#     response = {
#         'status_code': 500,
#         'message': 'Internal server error'
#     }
#     try:
#         user = User.objects.filter(mlp_id=mlp_id,is_active=True, mandatory_questions_completed=True).first()

#         if not user :
#             response['status_code'] = 301
#             response["message"] = "User not found"   
#             return response
#         res=get_newly_joined(mlp_id)
#         all_suggested_users_data=res['data']
        
#         subject = "Recently Joined at medicolifepartner.com"
#         email_content = email_services.set_email_newly_joined(all_suggested_users_data)
#         ses_wrapper.send_email(receiver_email_address=user.email, subject=subject,
#                                 html_body=email_content['message'])        
        
#         response['status_code']=200
#         response['message']="Email sent successfully"
#         return response    
#     except Exception as e:
#         logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
#         return response


# To fetch users data near me in the same city
def get_users_near_me(mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        
        user = User.objects.filter(mlp_id=mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()

        if not user:
            response['status_code'] = 301
            response["message"] = "User not found"
            return response

        
        opposite_gender = 'm' if user.gender == 'f' else 'f'
       
        today = date.today()
        age = today.year - user.dob.year - ((today.month, today.day) < (user.dob.month, user.dob.day))   
        blocked_users = BlockedUsers.objects.filter(user=user).values_list('blocked_user__mlp_id', flat=True)
        if user.gender == 'm':
            min_age = age - 5
            max_age = age
        else:
            min_age = age
            max_age = age + 5

        queryset = None
        if user.city and user.state:
            all_users = User.objects.filter(
                    #dob__year=today.year - age,
                    dob__year__gte=today.year - max_age,
                    dob__year__lte=today.year - min_age,
                    gender=opposite_gender,
                    religion=user.religion,
                    is_active=True,
                    is_wrong=False,
                    mandatory_questions_completed=True
                ).exclude(
                    mlp_id__in=blocked_users
                ).distinct()  

            same_city_and_state_users = all_users.filter(city=user.city, state=user.state)
            same_state_users = all_users.exclude(city=user.city).filter(state=user.state) 
            queryset = same_city_and_state_users | same_state_users 
        else:
            response['status_code'] = 404
            response['message'] = "User not provided city details , so no content found"
            return response 
        
        # Randomize queryset
        # queryset = queryset.order_by('?')
        
        total_count = queryset.count()

        if not queryset:
            response['status_code'] = 204
            response['message'] = "No content Found"
            return response   

        paginator = Paginator(queryset, page_size)
        paginated_queryset = paginator.get_page(page)
        
        # Convert to list and shuffle
        paginated_users_list = list(paginated_queryset)
        random.shuffle(paginated_users_list)
       

        #serializer = UserSerializer(paginated_queryset, many=True) 
        near_by_users_data =[]
        for data in paginated_users_list:
            suggested_user_mlp_id = data.mlp_id
            suggested_user = User.objects.get(mlp_id=suggested_user_mlp_id)

            if  ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists():
                continue

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True

            res = show_name(user, suggested_user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True

                
            res = show_photographs(user,suggested_user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 

            data = {
                    'mlp_id': suggested_user.mlp_id,
                    'name': suggested_user.mlp_id if name_hidden else suggested_user.name,
                    'email': suggested_user.email,
                    'religion': suggested_user.religion.name if suggested_user.religion and suggested_user.religion.name else None,
                    'mobile_number': suggested_user.mobile_number,
                    'gender': suggested_user.gender,
                    'dob': suggested_user.dob,
                    'eating_habits' : suggested_user.eating_habits,
                    'marital_status':suggested_user.marital_status.name if suggested_user.marital_status and suggested_user.marital_status.name else None,
                    'profile_pictures': json.loads(suggested_user.profile_pictures),
                    'family_photos': json.loads(suggested_user.family_photos),
                    'activity_status':suggested_user.activity_status,
                    'last_seen':suggested_user.last_seen,
                    'manglik': suggested_user.manglik,
                    'height': suggested_user.height,
                    'weight': suggested_user.weight,
                    'hobbies': json.loads(suggested_user.hobbies),
                    'other_hobbies': json.loads(suggested_user.other_hobbies),
                    'city': suggested_user.city,
                    'caste': suggested_user.caste,
                    'completed_post_grad' : suggested_user.completed_post_grad,
                    'is_bachelor': is_bachelor
                }
            data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()
            data['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user, status="Rejected").exists()     
            user_graduation = suggested_user.graduation_obj.name if suggested_user.graduation_obj else None

            if suggested_user.completed_post_grad:
                user_postgraduation = set(UserPostGraduation.objects.filter(user=suggested_user).values_list(
                    'post_graduation__name', flat=True
                ))
            else:
                user_postgraduation = set() 

            user_expertise =   suggested_user.graduation_obj.expertise_obj.name if (suggested_user.graduation_obj and suggested_user.graduation_obj.expertise_obj) else None

            data['graduation_id'] = user_graduation
            data['user_post_graduation'] = list(user_postgraduation)
            data['expertise_id'] = user_expertise

            data['is_bachelor'] = is_bachelor
            data['name_hidden']=name_hidden
            data['photo_hidden']=photo_hidden

            near_by_users_data.append(data)

        response['status_code'] = 200
        response['message'] = 'Near_users_data'
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = near_by_users_data
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


#Getting profiles that viewed my profile 
def get_users_viewed_my_profile(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        
        user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()

        if not user:
            response['status_code'] = 301
            response["message"] = "User not found"
            return response

        opposite_gender = 'm' if user.gender == 'f' else 'f'

        # cache_key = f"near_users_viewed_my_profile_data_{logged_mlp_id}"
        # cached_data = cache.get(cache_key)
      
        # if cached_data is None:   
        blocked_users = BlockedUsers.objects.filter(user=user).values_list('blocked_user__mlp_id', flat=True)
        profile_views = ProfileView.objects.filter(viewed_user=user, viewer__gender=opposite_gender).exclude(viewer__mlp_id__in=blocked_users).order_by('-visited_at').distinct()
        #     cache.set(cache_key, profile_views, timeout=900)
        # else :
        #     profile_views = cached_data

        total_count = profile_views.count()

        if not profile_views:
            response['status_code']= 300
            response['message'] = "No content found"
            return response
        
        paginator = Paginator(profile_views, page_size)
        paginated_viewers = paginator.get_page(page)

        serialized_viewers = []

        for viewer_user in paginated_viewers:
            viewer = viewer_user.viewer
            if viewer.is_active and viewer.mandatory_questions_completed and viewer.is_wrong==False:
                
                if ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=viewer.mlp_id) | Q(user_two=user, user_one__mlp_id=viewer.mlp_id)).exists():
                    continue

                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
                if bachelor_of_the_day and viewer.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True

                res = show_name(user, viewer)
                if res and res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

                res = show_photographs(user,viewer)
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True 

                data = {
                    'mlp_id': viewer.mlp_id,
                    'name': viewer.mlp_id if name_hidden else viewer.name,
                    'email': viewer.email,
                    'religion': viewer.religion.name if viewer.religion and viewer.religion.name else None,
                    'mobile_number': viewer.mobile_number,
                    'gender': viewer.gender,
                    'dob': viewer.dob,
                    'eating_habits' : viewer.eating_habits,
                    'marital_status':viewer.marital_status.name if viewer.marital_status and viewer.marital_status.name else None,
                    'profile_pictures': json.loads(viewer.profile_pictures),
                    'family_photos': json.loads(viewer.family_photos),
                    'activity_status':viewer.activity_status,
                    'last_seen':viewer.last_seen,
                    'manglik': viewer.manglik,
                    'height': viewer.height,
                    'weight': viewer.weight,
                    'hobbies': json.loads(viewer.hobbies),
                    'other_hobbies': json.loads(viewer.other_hobbies),
                    'city': viewer.city,
                    'caste': viewer.caste,
                    'completed_post_grad' : viewer.completed_post_grad,
                    'is_bachelor': is_bachelor
                }

                data['interest_sent'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=viewer.mlp_id).exists()
                #data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()

                data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=viewer).exists()
                #data['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=viewer.mlp_id).exists()
                data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=viewer.mlp_id, invitation_to=user).exists()
                data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=viewer.mlp_id) | Q(user_two=user, user_one__mlp_id=viewer.mlp_id)).exists()
                data['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=viewer.mlp_id, status="Rejected").exists()
                data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=viewer.mlp_id, invitation_to=user, status="Rejected").exists() 
                user_graduation = viewer.graduation_obj.name if viewer.graduation_obj else None

                if viewer.completed_post_grad:
                    user_postgraduation = set(UserPostGraduation.objects.filter(user=viewer).values_list(
                        'post_graduation__name', flat=True
                    ))
                else:
                    user_postgraduation = set()   

                user_expertise =  viewer.graduation_obj.expertise_obj.name if (viewer.graduation_obj and viewer.graduation_obj.expertise_obj) else None

                data['graduation_id'] = user_graduation
                data['user_post_graduation'] = list(user_postgraduation)
                data['expertise_id'] = user_expertise

                data['photo_hidden']=photo_hidden
                data['name_hidden']=name_hidden

                serialized_viewers.append(data)

        response['status_code'] = 200
        response['message'] = "Query Processed Successfully"
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = serialized_viewers
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


#Getting profiles viewed by me
def get_profile_viewed_by_me(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        
        user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True,is_wrong=False, mandatory_questions_completed=True).first()

        if not user:
            response['status_code'] = 301
            response["message"] = "User not found"
            return response
        
        opposite_gender = 'm' if user.gender == 'f' else 'f'

        # profile_views = None 
        # cache_key = f"users_viewed_by_me_profile_data_{logged_mlp_id}"
        # cached_data = cache.get(cache_key)  
        # if cached_data is None:
           
        blocked_users = BlockedUsers.objects.filter(user=user).values_list('blocked_user__mlp_id', flat=True)
        profile_views = ProfileView.objects.filter(viewer=user, viewed_user__gender=opposite_gender).exclude(viewed_user__mlp_id__in=blocked_users).order_by('-visited_at').distinct()

        #    cache.set(cache_key, profile_views, timeout=900)
        # else :
        #     profile_views = cached_data

        total_count = profile_views.count()

        if not profile_views:
            response['status_code'] = 300
            response['message'] = "No content found"
            return response    

        paginator = Paginator(profile_views, page_size)
        paginated_viewers = paginator.get_page(page)


        serialized_viewers = []

        for viewer_user in paginated_viewers:
            viewer = viewer_user.viewed_user
            if viewer.is_active and viewer.mandatory_questions_completed and viewer.is_wrong==False:

                if ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=viewer.mlp_id) | Q(user_two=user, user_one__mlp_id=viewer.mlp_id)).exists():
                    continue

                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
                if bachelor_of_the_day and viewer.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True

                res = show_name(user, viewer)
                if res and res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

                res = show_photographs(user,viewer)
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True   
    
                data = {
                    'mlp_id': viewer.mlp_id,
                    'name': viewer.mlp_id if name_hidden else viewer.name,
                    'email': viewer.email,
                    'mobile_number': viewer.mobile_number,
                    'gender': viewer.gender,
                    'dob': viewer.dob,
                    'eating_habits' : viewer.eating_habits,
                    'profile_pictures': json.loads(viewer.profile_pictures),
                    'family_photos': json.loads(viewer.family_photos),
                    'activity_status':viewer.activity_status,
                    'last_seen':viewer.last_seen,
                    'marital_status':viewer.marital_status.name if viewer.marital_status and viewer.marital_status.name else None,
                    'manglik': viewer.manglik,
                    'height': viewer.height,
                    'weight': viewer.weight,
                    'hobbies': json.loads(viewer.hobbies),
                    'other_hobbies': json.loads(viewer.other_hobbies),
                    'city': viewer.city,
                    'caste': viewer.caste,
                    'completed_post_grad': viewer.completed_post_grad,
                    'is_bachelor': is_bachelor
                }

                # Additional information about shortlisted, interest sent, and interest received
               # data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=viewer).exists()
                data['interest_sent'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=viewer.mlp_id).exists()  
                data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=viewer).exists()
               # data['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=viewer.mlp_id).exists()
                data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=viewer.mlp_id, invitation_to=user).exists()
                data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=viewer.mlp_id) | Q(user_two=user, user_one__mlp_id=viewer.mlp_id)).exists()
                data['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=viewer.mlp_id, status="Rejected").exists()
                data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=viewer.mlp_id, invitation_to=user, status="Rejected").exists() 
                # Include user's graduation, post-graduation, expertise, and religion
                user_graduation = viewer.graduation_obj.name if viewer.graduation_obj else None

                if viewer.completed_post_grad:
                    user_postgraduation = set(UserPostGraduation.objects.filter(user=viewer).values_list(
                        'post_graduation__name', flat=True
                    ))
                else:
                    user_postgraduation = set()  

                user_expertise =   viewer.graduation_obj.expertise_obj.name if (viewer.graduation_obj and viewer.graduation_obj.expertise_obj) else None

                data['graduation_id'] = user_graduation
                data['user_post_graduation'] = list(user_postgraduation)
                data['expertise_id'] = user_expertise

                data['religion'] = viewer.religion.name if viewer.religion else None
                data['name_hidden']=name_hidden
                data['photo_hidden']=photo_hidden

                serialized_viewers.append(data)

        response['status_code'] = 200
        response['message'] = "Query Processed Successfully"
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = list(serialized_viewers)
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

 
    
# Get the data of users contact seen by the logged-in user
def get_contact_seen(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()
        if not user:
            response['status_code'] = 301
            response["message"] = "User not found"
            return response

        opposite_gender = 'm' if user.gender == 'f' else 'f'   
        seen_contacts = ContactViewed.objects.filter(
            user=user,
            seen_contact__is_active=True,
            seen_cotact__is_wrong=False,
            seen_contact__mandatory_questions_completed=True,
            seen_contact__gender=('f' if user.gender == 'm' else 'm'),
        ).select_related('seen_contact').order_by('-updated_date')


        total_count = seen_contacts.count()

        if not seen_contacts:
            response['status_code'] = 300
            response["message"] = "No content found"
            return response 

        seen_contact_mlp_ids = set()
        serialized_data = []

        for seen_contact in seen_contacts:
            suggested_user = seen_contact.seen_contact

            if not BlockedUsers.objects.filter(user=user, blocked_user=suggested_user).exists():
                if suggested_user.mlp_id not in seen_contact_mlp_ids:

                    if  ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists():
                            continue
                    
                    is_bachelor = False
                    bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
                    if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                        is_bachelor = True


                    res = show_name(user, suggested_user)
                    if res and res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True

                    res = show_photographs(user,suggested_user)
                    if res:
                        if res["status_code"] == 200:
                            photo_hidden = False
                        else:
                            photo_hidden = True  

                    data = {
                        'mlp_id': suggested_user.mlp_id,
                        'name': suggested_user.mlp_id if name_hidden else suggested_user.name,
                        'email': suggested_user.email,
                        'mobile_number': suggested_user.mobile_number,
                        'gender': suggested_user.gender,
                        'religion': suggested_user.religion.name if suggested_user.religion.name else None,
                        'caste': suggested_user.caste,
                        'marital_status':suggested_user.marital_status.name if suggested_user.marital_status and suggested_user.marital_status.name else None,
                        'dob': suggested_user.dob,
                        'eating_habits' :suggested_user.eating_habits,
                        'profile_pictures': json.loads(suggested_user.profile_pictures),
                        'family_photos': json.loads(suggested_user.family_photos),
                        'activity_status':suggested_user.activity_status,
                        'last_seen':suggested_user.last_seen,
                        'completed_post_grad':suggested_user.completed_post_grad,
                        'height': suggested_user.height,
                        'weight': suggested_user.weight,
                        'salary': suggested_user.salary,
                        'hobbies': json.loads(suggested_user.hobbies),
                        'other_hobbies': json.loads(suggested_user.other_hobbies),
                        'city': suggested_user.city,
                        'shortlisted': SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists(),
                        'interest_sent':  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id).exists(),
                        'is_bachelor': is_bachelor
                    }

                    user_graduation = suggested_user.graduation_obj.name if suggested_user.graduation_obj else None

                    if suggested_user.completed_post_grad:
                        user_post_graduation = set(UserPostGraduation.objects.filter(user=suggested_user).values_list('post_graduation__name', flat=True))
                    else : 
                        user_post_graduation = set()    

                    user_expertise =   suggested_user.graduation_obj.expertise_obj.name if (suggested_user.graduation_obj and suggested_user.graduation_obj.expertise_obj) else None

                    data['graduation_id'] = user_graduation
                    data['user_post_graduation'] = list(user_post_graduation)
                    data['expertise_id'] = user_expertise
                    
                   # data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()
                   # data['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id).exists()
                    data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user).exists()
                    data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists()
                    data['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
                    data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user, status="Rejected").exists() 

                    data['photo_hidden']=photo_hidden
                    data['name_hidden']=name_hidden

                    serialized_data.append(data)
                
                    seen_contact_mlp_ids.add(suggested_user.mlp_id)

        paginator = Paginator(serialized_data, page_size)
        paginated_data = paginator.get_page(page)

        response['status_code'] = 200
        response['message'] = 'Data Fetched Successfully'
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = list(paginated_data)
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


#Get the data of users whose education similar to me
def get_similar_education_users(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        logged_user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()

        if not logged_user:
            response['status_code'] = 404
            response["message"] = "User not found"
            return response
        
        opposite_gender = 'm' if logged_user.gender =='f' else 'f'

        auth_expertise=logged_user.graduation_obj.expertise_obj.name if logged_user.graduation_obj else None 
        blocked_users = BlockedUsers.objects.filter(
            user=logged_user).values_list('blocked_user__mlp_id', flat=True)

        users_with_same_expertise = User.objects.filter(  is_active=True , 
                                                          mandatory_questions_completed = True,
                                                          is_wrong=False,
                                                          gender = opposite_gender,
                                                          graduation_obj__expertise_obj__name=auth_expertise).exclude(mlp_id__in = blocked_users).prefetch_related('usersubscription__subscription')
        
    
        users_with_same_expertise = sorted(
            users_with_same_expertise,
            key=lambda user: sum(
                sub.subscription.amount if sub.subscription and sub.subscription.amount is not None else sub.subscription_ios.amount
                for sub in user.usersubscription.all()
            ),
            reverse=True
        )
        
        same_education_users = None
        similar_user = []
        if logged_user.completed_post_grad == True:
            print("inside post grad")
            for user in users_with_same_expertise:
                if user.completed_post_grad == True:
                    similar_user.append(user)
            same_education_users = similar_user        
        else:
            print("outside post grad")
            same_education_users = users_with_same_expertise  
        
        if not same_education_users:
            response['status_code'] = 300
            response['message'] = "No content found"
            return response
        
        paginator = Paginator(same_education_users, page_size)
        paginated_data = paginator.get_page(page)
        

        paginated_data_list = list(paginated_data)  # Convert to list to shuffle
        random.shuffle(paginated_data_list)
        
        # print(f"Profiles before shuffling: {[user.mlp_id for user in paginated_data]}")
        # print(f"Profiles after shuffling: {[user.mlp_id for user in paginated_data_list]}") 


        similar_users_data = []
        for user in paginated_data_list: 
                subscription_amount = sum(
                    sub.subscription.amount if sub.subscription and sub.subscription.amount is not None else sub.subscription_ios.amount
                    for sub in user.usersubscription.all()
                )
                subscription_active = any(sub.is_subscription_active for sub in user.usersubscription.all())

                if  ConnectionList.objects.filter(Q(user_one=logged_user, user_two__mlp_id=user.mlp_id) | Q(user_two=logged_user, user_one__mlp_id=user.mlp_id)).exists():
                    continue
                
                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
                if bachelor_of_the_day and user.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True

                res = show_name(logged_user, user)
                if res and res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

                res = show_photographs(logged_user,user)
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True

                data = {
                    'mlp_id': user.mlp_id,
                    'name': user.mlp_id if name_hidden else user.name,
                    'amount': subscription_amount,
                    'active': subscription_active,
                    'email': user.email,
                    'mobile_number': user.mobile_number,
                    'gender': user.gender,
                    'religion': user.religion.name if user.religion.name else None,
                    'marital_status':user.marital_status.name if user.marital_status and user.marital_status.name else None,
                    'caste': user.caste,
                    'dob': user.dob,
                    'profile_pictures': json.loads(user.profile_pictures),
                    'family_photos': json.loads(user.family_photos),
                    'activity_status':user.activity_status,
                    'last_seen':user.last_seen,
                    'height': user.height,
                    'weight': user.weight,
                    'hobbies': json.loads(user.hobbies),
                    'other_hobbies': json.loads(user.other_hobbies),
                    'city': user.city,
                    'is_bachelor':is_bachelor
                }

                user_graduation = user.graduation_obj.name if user.graduation_obj else None

                if user.completed_post_grad:
                    user_post_graduation = set(UserPostGraduation.objects.filter(user=user).values_list('post_graduation__name', flat=True))
                else : 
                    user_post_graduation = set()    

                user_expertise =   user.graduation_obj.expertise_obj.name if (user.graduation_obj and user.graduation_obj.expertise_obj) else None

                data['graduation_id'] = user_graduation
                data['user_post_graduation'] = list(user_post_graduation)
                data['expertise_id'] = user_expertise
                
                data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=logged_user).exists()
                data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=logged_user, user_two__mlp_id=user.mlp_id) | Q(user_two=logged_user, user_one__mlp_id=user.mlp_id)).exists()
                data['interest_rejected'] = Intrest.objects.filter(invitation_by=logged_user, invitation_to__mlp_id=user.mlp_id, status="Rejected").exists()
                data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=logged_user, status="Rejected").exists() 

                data['graduation_id'] = user_graduation
                data['user_post_graduation'] = list(user_post_graduation)
                data['expertise_id'] = user_expertise

                data['photo_hidden']=photo_hidden
                data['name_hidden']=name_hidden

                similar_users_data.append(data)
        
        response['status_code'] =200
        response['message'] = "Similar education user"
        response['total_pages'] = paginator.num_pages
        response['total_count'] = paginator.count
        response['data'] = sorted(similar_users_data, key=lambda x: (not x['active'], -x['amount']))
        return response

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

#To get other profiles data
def get_tier4_profiles(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:

        user_obj = User.objects.filter(mlp_id=logged_mlp_id, is_active=True,is_wrong=False, mandatory_questions_completed=True).first()
        if not user_obj:
            response['status_code'] = 301
            response['message'] = 'User not found'
            return response
      
        blocked_users = BlockedUsers.objects.filter(user=user_obj).values_list('blocked_user__mlp_id', flat=True)
        opposite_gender = 'm' if user_obj.gender == 'f' else 'f'
        today = date.today()
        age = today.year - user_obj.dob.year - ((today.month, today.day) < (user_obj.dob.month, user_obj.dob.day))

        # Determine the age range for opposite gender profiles
        if user_obj.gender == 'm':
            min_age = age - 5
            max_age = age
        else:
            min_age = age
            max_age = age + 5

        all_users = User.objects.filter(
            is_active=True, 
            is_wrong=False,
            mandatory_questions_completed=True,
            dob__year__gte=today.year - max_age,
            dob__year__lte=today.year - min_age,
            gender=opposite_gender).exclude(mlp_id__in=blocked_users).order_by('id')
        
        total_count = all_users.count()
        
        paginator = Paginator(all_users, page_size)
        paginated_users = paginator.get_page(page)


        paginated_users_list = list(paginated_users)  # Convert to list to shuffle
        random.shuffle(paginated_users_list)
        
        # print(f"Profiles before shuffling: {[user.mlp_id for user in paginated_users]}")
        # print(f"Profiles after shuffling: {[user.mlp_id for user in paginated_users_list]}")  


        serialized_users = []
        for user in paginated_users_list:

            if ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=user.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=user.mlp_id)).exists():
                continue

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user_obj.religion,opposite_gender)
            if bachelor_of_the_day and user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True

            res = show_name(user_obj, user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True

            res = show_photographs(user_obj,user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True  

            data = {
                'id': user.id,
                'mlp_id': user.mlp_id,
                'name': user.mlp_id if name_hidden else user.name,
                'email':user.email,
                'religion': user.religion.name if user.religion and user.religion.name else None,
                'mobile_number': user.mobile_number,
                'gender': user.gender,
                'dob': user.dob,
                'eating_habits' : user.eating_habits,
                'marital_status':user.marital_status.name if user.marital_status and user.marital_status.name else None,
                'profile_pictures': json.loads(user.profile_pictures),
                'family_photos': json.loads(user.family_photos),
                'activity_status':user.activity_status,
                'last_seen':user.last_seen,
                'manglik': user.manglik,
                'height': user.height,
                'weight': user.weight,
                'hobbies': json.loads(user.hobbies),
                'other_hobbies': json.loads(user.other_hobbies),
                'city': user.city,
                'caste': user.caste,
                'completed_post_grad' : user.completed_post_grad,
                'is_bachelor': is_bachelor,
                'shortlisted': SavedUser.objects.filter(user=user_obj, saved_profile=user).exists(),
                'interest_received':  Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=user.mlp_id).exists()
            }

            user_graduation = user.graduation_obj.name if user.graduation_obj else None

            if user.completed_post_grad:
               user_post_graduation = set(UserPostGraduation.objects.filter(user=user).values_list('post_graduation__name', flat=True))
            else : 
                user_post_graduation = set()

            user_expertise =   user.graduation_obj.expertise_obj.name if (user.graduation_obj and user.graduation_obj.expertise_obj) else None

            data['graduation_id'] = user_graduation
            data['user_post_graduation'] = list(user_post_graduation)
            data['expertise_id'] = user_expertise
            
            data['shortlisted'] = SavedUser.objects.filter(user=user_obj, saved_profile=user).exists()
            data['interest_sent'] = Intrest.objects.filter(Q(invitation_by=user_obj, invitation_to__mlp_id=user.mlp_id) | Q(invitation_to=user_obj, invitation_by__mlp_id=user.mlp_id)).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=user_obj).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user_obj, user_two__mlp_id=user.mlp_id) | Q(user_two=user_obj, user_one__mlp_id=user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user_obj, invitation_to__mlp_id=user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=user_obj, status="Rejected").exists()  

            data['name_hidden']=name_hidden
            data['photo_hidden']=photo_hidden

            serialized_users.append(data)

        response['status_code'] = 200
        response['message'] = 'Other User Profile'
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = serialized_users

        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
    
# add rating review model
def add_rating_review(data, logged_mlp_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id,is_active=True, is_wrong=False, mandatory_questions_completed=True).first()
        rating = data.get('rating')
        review_text = data.get('review_text')

        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
        
        if rating is None:
            response['message'] = 'Rating is required'
            response['status_code'] = 300
            return response
        

        rating_review = RatingReview.objects.filter(user=auth_user).first()
        if rating_review is not None:
            if rating != '':
                rating_review.rating = rating
                rating_review.review_text = review_text
                rating_review.save()        
        else:
            if rating != '':
                rating_review = RatingReview(
                    user=auth_user,
                    rating=rating,
                    review_text=review_text
                )
                rating_review.save()
            

        response['status_code'] = 200
        response['message'] = "Rating Review Added Successfully"
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


#get rating_review service
def get_rating_review():
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        ratings_reviews = RatingReview.objects.filter(approve=True)
        data = []

        for rr in ratings_reviews:
            # user_graduation = UserPostGraduation.objects.filter(user=rr.user).values_list('post_graduation__graduation_obj__name', flat=True).first()
            # user_post_graduation = list(set(UserPostGraduation.objects.filter(user=rr.user).values_list('post_graduation__name', flat=True)))
            # user_expertise = UserPostGraduation.objects.filter(user=rr.user).values_list('post_graduation__graduation_obj__expertise_obj__name', flat=True).first()
            user_graduation = rr.user.graduation_obj.name if rr.user.graduation_obj else None

            if rr.user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=rr.user).values_list('post_graduation__name', flat=True))
            else:
                user_post_graduation = set()

            user_expertise =  rr.user.graduation_obj.expertise_obj.name if (rr.user.graduation_obj and rr.user.graduation_obj.expertise_obj) else None

           
            data.append({
                'rating': rr.rating,
                'review_text': rr.review_text,
                'mlp_id': rr.user.mlp_id,
                'name': rr.user.name,
                'profile_pictures':json.loads(rr.user.profile_pictures),
                'user_post_graduation': list(user_post_graduation),
                'user_graduation': user_graduation,
                'user_expertise': user_expertise,
                'created_at': rr.created_date
            })

        response['data'] = data
        response['message'] = 'Rating-Review data fetched successfully'
        response['status_code'] = 200
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response



def delete_imagefunc(url):
    response={
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        if url:
            bucketname = os.getenv('S3_BUCKET_NAME')
            accesskey = os.getenv("S3_ACCESS_KEY_ID")
            secretkey = os.getenv("S3_SECRET_KEY")
            s3 = boto3.client('s3', region_name='ap-south-1', aws_access_key_id=accesskey, aws_secret_access_key=secretkey)
            parsed_url = urlparse(url)
            file_key = parsed_url.path.lstrip('/')
            image_exists = s3.head_object(Bucket=bucketname, Key=file_key)
            if image_exists:
                s3.delete_object(Bucket=bucketname,Key=file_key)
                response['message']='Image deleted successfully'
                response['status_code']=200
                return response
            else:
                response['message']='Image not found'
                response['status_code']=400
                return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response    

#Main bachelor of the day function
def calculate_bachelor_of_the_day(logged_mlp_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        
        logged_user = User.objects.get(mlp_id=logged_mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True)
        if logged_user is None:
            response['status_code'] = 300
            response['message'] = "User not Found"
            return response
        
        opposite_gender = 'm' if logged_user.gender == 'f' else 'f'

        # cache_key = f"bachelor_of_the_day_{logged_mlp_id}"
        # cached_data = cache.get(cache_key)

        # if cached_data is None:   
        bachelor=BachelorOfTheDay.get_latest_bachelor_of_the_day(logged_user.religion,opposite_gender)
        #cache.set(cache_key, bachelor , timeout= 3600)
        # else:
        #     bachelor = cached_data 

        data = None
        if bachelor:
            res = show_name(logged_user, bachelor.user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True

            res = show_photographs(logged_user,bachelor.user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True  
            data = {
                'mlp_id': bachelor.user.mlp_id,
                'name': bachelor.user.mlp_id if name_hidden else bachelor.user.name,
                'email': bachelor.user.email,
                'religion': bachelor.user.religion.name if bachelor.user.religion else None,
                'marital_status':bachelor.user.marital_status.name if bachelor.user.marital_status and bachelor.user.marital_status.name else None,
                'gender': bachelor.user.gender,
                'dob': bachelor.user.dob,
                'about': bachelor.user.about,
                'future_aspirations': bachelor.user.future_aspirations,
                'profile_pictures': json.loads(bachelor.user.profile_pictures),
                'family_photos': json.loads(bachelor.user.family_photos),
                'activity_status':bachelor.user.activity_status,
                'last_seen':bachelor.user.last_seen,
                'completed_post_grad': bachelor.user.completed_post_grad,
                'caste': bachelor.user.caste,
                'height': bachelor.user.height,
                'weight': bachelor.user.weight,
                'salary': bachelor.user.salary,
                'eating_habits': bachelor.user.eating_habits,
                'smoking_habits': bachelor.user.smoking_habits,
                'drinking_habits': bachelor.user.drinking_habits,
                'hobbies': json.loads(bachelor.user.hobbies),
                'other_hobbies': json.loads(bachelor.user.other_hobbies),
                'city': bachelor.user.city,
                'is_bachelor':True
            }
            user_graduation = bachelor.user.graduation_obj.name if bachelor.user.graduation_obj else None

            if bachelor.user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=bachelor.user).values_list('post_graduation__name', flat=True))
            else :
                user_post_graduation =set()

            user_expertise = bachelor.user.graduation_obj.expertise_obj.name if (bachelor.user.graduation_obj and bachelor.user.graduation_obj.expertise_obj) else None

            data['graduation_id'] = user_graduation
            data['user_post_graduation'] = list(user_post_graduation)
            data['expertise_id'] = user_expertise

            data['photo_hidden']=photo_hidden
            data['name_hidden']=name_hidden
            
            logged_user = User.objects.filter(mlp_id=logged_mlp_id).first()
            if logged_user:
                    data['interest_sent'] =  Intrest.objects.filter(invitation_by=logged_user, invitation_to__mlp_id=bachelor.user.mlp_id).exists()
                    #data['shortlisted'] = SavedUser.objects.filter(user=logged_user, saved_profile=bachelor.user).exists()  
                    data['shortlisted'] = SavedUser.objects.filter(user=logged_user, saved_profile=bachelor.user).exists()
                    #data['interest_sent'] =  Intrest.objects.filter(invitation_by=logged_user, invitation_to__mlp_id=bachelor.user.mlp_id).exists()
                    data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=bachelor.user.mlp_id, invitation_to=logged_user).exists()
                    data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=logged_user, user_two__mlp_id=bachelor.user.mlp_id) | Q(user_two=logged_user, user_one__mlp_id=bachelor.user.mlp_id)).exists()
                    data['interest_rejected'] = Intrest.objects.filter(invitation_by=logged_user, invitation_to__mlp_id=bachelor.user.mlp_id, status="Rejected").exists()
                    data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=bachelor.user.mlp_id, invitation_to=logged_user, status="Rejected").exists() 
            
        
        if data is not None:
            response['data'] = data
        else:
            response['data'] = None
                  
        response['status_code'] = 200
        response['message'] = "Bachelor of the day retrieved successfully" 
        return response
  
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

    
# add success stories service      
def add_success_stories(data, logged_mlp_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True,is_wrong=False).first()
        story = data.get('story')
        partner_mlp_id = data.get('partner_mlp_id')
        partner_name = data.get('partner_name')
        partner_mobile_number = data.get('partner_mobile_number')
        reason = data.get('reason')
        experience = data.get('experience')
        video = data.get('video') 
        image = data.get('image')  

        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response

        if story is None:
            response['message'] = 'Success story is required'
            response['status_code'] = 300
            return response

        if partner_mlp_id is None:
            response['message'] = 'Partner MLP id is required'
            response['status_code'] = 300
            return response

        if partner_mobile_number is None:
            response['message'] = 'Partner mobile number is required'
            response['status_code'] = 300
            return response

        if partner_name is None:
            response['message'] = 'Partner name is required'
            response['status_code'] = 300
            return response

        success_story = SuccessStory.objects.filter(user=auth_user).first()

        if success_story:
            success_story.story = story
            success_story.video = video
            success_story.image = image
            success_story.save()
        else:
            SuccessStory.objects.create(user=auth_user, story=story, partner_mobile_number=partner_mobile_number,reason=reason,experience=experience,
                                        partner_mlp_id=partner_mlp_id, partner_name=partner_name, video=video, image=image)
        

        delete_response = delete_user_profile({'mlp_id': logged_mlp_id,'reason':reason,'experience':experience})
        if delete_response['status_code'] != 200:
            return delete_response
        
        message_title = "New Success Story Added"
        message_body = f"{auth_user.mlp_id} has added a new success story. Check it out!"
        
        
        for user_obj in User.objects.exclude(mlp_id=logged_mlp_id): 
            custom_data = {
            "screen": "success_story",
            "user_id": user_obj.mlp_id
            }
            if user_obj.notification_token:
                # response = push_service.notify_single_device(
                #     registration_id=user_obj.notification_token,
                #     message_title=message_title,
                #     message_body=message_body,
                #     data_message=custom_data
                # )

                message = messaging.Message(
                token=user_obj.notification_token,  # FCM registration token
                notification=messaging.Notification(
                    title=message_title,
                    body=message_body
                ),
                data=custom_data 
                )

                messaging.send(message)



        # all_linked_users=LinkedAccount.objects.filter(primary_user=auth_user).all()
        # notificationtokens = []
        # for i in all_linked_users:
        #     if i.linked_user.notification_token:
        #         notificationtokens.append(i.linked_user.notification_token) 

        # if notificationtokens:
        #     message_body = f"{auth_user.mlp_id} has added a new success story. Check it out!"
        #     push_service.notify_multiple_devices(
        #         registration_ids=notificationtokens,
        #         message_title=message_title,
        #         message_body=message_body,
        #         data_message=custom_data
        #     )        

        response['status_code'] = 200
        response['message'] = "Success Story Added Successfully, and User Profile Deleted"
        return response

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


#get success stories service
def get_success_stories():
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        stories = SuccessStory.objects.filter(experience__in = ['Excellent','Good']).select_related('user').order_by('-id').values(
            'id',
            'story',
            'user__id',
            'user__mlp_id',
            'user__name',
            'partner_mlp_id',
            'partner_name',
            'partner_mobile_number',
            'user__email',
            'user__mobile_number',
            'user__gender',
            'user__dob',
            'user__profile_pictures',
            'user__family_photos',
            'reason',
            'experience',
            'user__city',
            'user__caste',
            'video',
            'image',
            'created_date'
        )[:5]

        profiles_seen = set()
        modified_stories = []
        for story in stories:
            if story['user__mlp_id'] not in profiles_seen:
                profiles_seen.add(story['user__mlp_id'])

                profile_pictures = json.loads(story['user__profile_pictures']) if story['user__profile_pictures'] else None
                family_photos = json.loads(story['user__family_photos']) if story['user__family_photos'] else None
                video = json.loads(story['video']) if story['video'] else None
                image = json.loads(story['image']) if story['image'] else None

                modified_story = {
                    'id': story['id'],
                    'story': story['story'],
                    'mlp_id': story['user__mlp_id'],
                    'name': story['user__name'],
                    'email': story['user__email'],
                    'partner_mlp_id': story['partner_mlp_id'],
                    'partner_name': story['partner_name'],
                    'partner_mobile_number': story['partner_mobile_number'],
                    'mobile_number': story['user__mobile_number'],
                    'gender': story['user__gender'],
                    'dob': story['user__dob'],
                    'profile_pictures': profile_pictures,
                    'family_photos': family_photos,
                    'reason':story['reason'],
                    'experience':story['experience'],
                    'city': story['user__city'],
                    'caste': story['user__caste'],
                    'video': video,
                    'image': image,
                    'created_date':story['created_date']
                }
                modified_stories.append(modified_story)

        response['message'] = "Success Stories Retrieved Successfully"
        response['status_code'] = 200
        response['data'] = modified_stories
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


#top ten profile service
def top_ten_profiles(logged_mlp_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id,is_active=True, is_wrong=False).first()

        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
        
        
        opposite_gender = 'm'  if auth_user.gender == 'f' else 'f'
      

        cache_key = f'top_ten_data_{logged_mlp_id}'
        cache_data = cache.get(cache_key)

        if cache_data is None:
            blocked_users = BlockedUsers.objects.filter(user=auth_user).values_list('blocked_user__mlp_id', flat=True)
            users = User.objects.filter(gender=opposite_gender, is_active=True, is_wrong=False, mandatory_questions_completed=True,
                                        religion=auth_user.religion).exclude(mlp_id__in=blocked_users).distinct()
            

            users_with_high_percentage = []

            for user in users:
                profile_percentage = user.calculate_profile_percentage()
                if profile_percentage >= 50:
                    users_with_high_percentage.append((user, profile_percentage))
                    if len(users_with_high_percentage) > 20:
                        break
            cache.set(cache_key, users_with_high_percentage, timeout=(3600))        
        else :
            users_with_high_percentage= cache_data

        top_ten_users = [user[0] for user in sorted(users_with_high_percentage, key=lambda x: x[1], reverse=True)[:10]]

        # for max viewed profiles
        most_viewed_profiles = (
            SeenUser.objects
            .filter(seen_profile__is_active=True, seen_profile__is_wrong=False, seen_profile__mandatory_questions_completed=True,
                    seen_profile__gender__isnull=False)
            .filter(seen_profile__mlp_id__in=[user.mlp_id for user in top_ten_users])  # Filter by top_ten_users
            .values('seen_profile__mlp_id')
            .annotate(field_count=Count('seen_profile__mlp_id'))
            .order_by('-field_count')
        )

        # Create a dictionary to map profiles to their view counts
        viewed_profiles = defaultdict(int)
        for profile in most_viewed_profiles:
            viewed_profiles[profile['seen_profile__mlp_id']] = profile['field_count']

        # Assign temp_value based on profile views
        temp_value = len(top_ten_users)
        for user in top_ten_users:
            user.temp_value = viewed_profiles.get(user.mlp_id, 0) or temp_value
            temp_value -= 1

        # for max shortlisted
        top_ten_mlp_ids = [user.mlp_id for user in top_ten_users]

        # Count occurrences of each mlp_id in SavedUser's saved_profile field
        saved_profiles_count = Counter(
            SavedUser.objects.filter(saved_profile__mlp_id__in=top_ten_mlp_ids).values_list('saved_profile__mlp_id',
                                                                                              flat=True))

        top_ten_users.sort(key=lambda user: saved_profiles_count.get(user.mlp_id, 0), reverse=True)

        # Iterate through all users in top_ten_users
        temp_value2 = len(top_ten_users)
        for user in top_ten_users:
            user.temp_value2 = temp_value2
            temp_value2 -= 1

        top_ten_mlp_ids = [user.mlp_id for user in top_ten_users]

        # Calculate average and assign to each user
        for user in top_ten_users:
            user.avg_value = ( user.temp_value + user.temp_value2 ) / 2

        # Sort users by average value in descending order
        sorted_users_by_avg = sorted(top_ten_users, key=lambda user: user.avg_value, reverse=True)
        sorted_data = [(user.mlp_id, user.avg_value) for user in sorted_users_by_avg]

        top_users=[]

        for mlp_id , avg_value in sorted_data:
            profile= User.objects.filter(mlp_id=mlp_id,is_active=True,is_wrong=False).first()

            if profile:
                is_bachelor = False
                bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(auth_user.religion, opposite_gender)
                if bachelor_of_the_day and profile.mlp_id == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True

                user_post_graduation = profile.partnerpostgraduationpreference.all()    

                res = show_name(auth_user, profile)
                if res and res["status_code"] == 200:
                    name_hidden = False
                else:
                    name_hidden = True

                res = show_photographs(auth_user,profile)
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True  

                user_info = {
                    'mlp_id': profile.mlp_id,
                    'name': profile.mlp_id if name_hidden else profile.name,
                    'email': profile.email,
                    'mobile_number': profile.mobile_number,
                    'religion':profile.religion.name if profile.religion.name else None,
                    'marital_status':profile.marital_status.name if profile.marital_status and profile.marital_status.name else None,
                    'gender':profile.gender,
                    'dob': profile.dob,
                    'profile_pictures': json.loads(profile.profile_pictures),
                    'family_photos': json.loads(profile.family_photos),
                    'activity_status':profile.activity_status,
                    'last_seen' : profile.last_seen,
                    'completed_post_grad' : profile.completed_post_grad,
                    'height': profile.height,
                    'weight': profile.weight,
                    'salary': profile.salary,
                    'hobbies': json.loads(profile.hobbies),
                    'other_hobbies':json.loads(profile.other_hobbies),
                    'city':profile.city,
                    'caste':profile.caste,
                    'is_bachelor':is_bachelor,
                    'marital_status': profile.marital_status.name if profile.marital_status else None,
                    'avg_value': avg_value
                }
                user_graduation = profile.graduation_obj.name if profile.graduation_obj else None

                # if profile.completed_post_grad:
                #     user_post_graduation = set(UserPostGraduation.objects.filter(user=profile).values_list('post_graduation__name', flat=True))
                # else : 
                #     user_post_graduation =set()

                user_expertise =profile.graduation_obj.expertise_obj.name if (profile.graduation_obj and profile.graduation_obj.expertise_obj) else None

                user_info['graduation_id'] = user_graduation
                user_info['user_post_graduation'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() and user.completed_post_grad else []
                user_info['expertise_id'] = user_expertise

                user_info['name_hidden']=name_hidden
                user_info['photo_hidden']=photo_hidden

            
                user_info['shortlisted'] = SavedUser.objects.filter(user=auth_user, saved_profile=profile).exists()
                user_info['interest_sent'] =  Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=profile.mlp_id).exists()
                # user_info['shortlisted'] = SavedUser.objects.filter(user=logged_user, saved_profile=profile).exists()
                #user_info['interest_sent'] =  Intrest.objects.filter(invitation_by=logged_user, invitation_to__mlp_id=profile.mlp_id).exists()
                user_info['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=profile.mlp_id, invitation_to=auth_user).exists()
                user_info['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=profile.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=profile.mlp_id)).exists()
                user_info['interest_rejected'] = Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=profile.mlp_id, status="Rejected").exists()
                user_info['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=profile.mlp_id, invitation_to=auth_user , status="Rejected").exists()
                top_users.append(user_info)
        
        # Shuffle the top users before returning
        random.shuffle(top_users)

        response['message'] = "Top Ten Profiles Retrieved Successfully"
        response['status_code'] = 200
        response['data'] = top_users 

        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

# To get premium profiles data
def premium_profiles(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()

        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
        opposite_gender = 'm' if auth_user.gender == 'f' else 'f'
        
        cache_key = f"user_subscription_data{logged_mlp_id}"
        premium_users = cache.get(cache_key)
 
        if premium_users is None:
            blocked_users = BlockedUsers.objects.filter(user=auth_user).values_list('blocked_user__mlp_id', flat=True)

            premium_users = UserSubscription.objects.filter(
                is_subscription_active=True,
                user__gender=opposite_gender,
                user__religion=auth_user.religion,
                user__is_active=True,
                user__is_wrong=False,
                user__mandatory_questions_completed=True
            ).exclude(user__mlp_id__in=blocked_users).distinct()
            premium_users= premium_users.order_by('-user__last_seen')
            premium_users = premium_users.order_by('-subscription__amount')
            cache.set(cache_key, premium_users, timeout=3600)

        total_count = premium_users.count()   
        paginator = Paginator(premium_users, page_size)
        paginated_users = paginator.get_page(page)

        premium_users_data = []
        for user_subscription in paginated_users:

            if ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user_subscription.user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user_subscription.user.mlp_id)).exists():
                continue

            res = show_name(auth_user, user_subscription.user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True

            res = show_photographs(auth_user,user_subscription.user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(auth_user.religion,opposite_gender)
            if bachelor_of_the_day and user_subscription.user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True         

            user_details = {
                'mlp_id': user_subscription.user.mlp_id,
                'name': user_subscription.user.mlp_id if name_hidden else user_subscription.user.name,
                'email': user_subscription.user.email,
                'gender': user_subscription.user.gender,
                'dob': user_subscription.user.dob,
                'marital_status':user_subscription.user.marital_status.name if user_subscription.user.marital_status and user_subscription.user.marital_status.name else None,
                'religion': user_subscription.user.religion.name if user_subscription.user.religion else None,
                'profile_pictures': json.loads(user_subscription.user.profile_pictures),
                'eating_habits' : user_subscription.user.eating_habits,
                'family_photos': json.loads(user_subscription.user.family_photos),
                'activity_status':user_subscription.user.activity_status,
                'last_seen':user_subscription.user.last_seen,
                'completed_post_grad':user_subscription.user.completed_post_grad,
                'height': user_subscription.user.height,
                'weight': user_subscription.user.weight,
                'salary': user_subscription.user.salary,
                'hobbies': json.loads(user_subscription.user.hobbies),
                'other_hobbies': json.loads(user_subscription.user.other_hobbies),
                'city': user_subscription.user.city,
                'caste': user_subscription.user.caste,
                'is_bachelor' : is_bachelor,
                'subscription_name': user_subscription.subscription.name if user_subscription.subscription else user_subscription.subscription_ios.name,
                'shortlisted': SavedUser.objects.filter(user=auth_user, saved_profile=user_subscription.user).exists(),
                'interest_sent':  Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user_subscription.user.mlp_id).exists()
            }

            user_graduation = user_subscription.user.graduation_obj.name if user_subscription.user.graduation_obj else None

            if user_subscription.user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=user_subscription.user).values_list('post_graduation__name', flat=True))
            else :
                user_post_graduation = set()

            user_expertise =user_subscription.user.graduation_obj.expertise_obj.name if (user_subscription.user.graduation_obj and user_subscription.user.graduation_obj.expertise_obj) else None

            user_details['graduation_id'] = user_graduation
            user_details['user_post_graduation'] = list(user_post_graduation) if  user_subscription.user.completed_post_grad else []
            user_details['expertise_id'] = user_expertise
            
           # user_details['interest_sent'] =  Intrest.objects.filter(Q(invitation_by=auth_user, invitation_to__mlp_id=user_subscription.user.mlp_id) | Q(invitation_to=auth_user, invitation_by__mlp_id=user_subscription.user.mlp_id)).exists()
            user_details['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user_subscription.user.mlp_id, invitation_to=auth_user).exists()
            user_details['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user_subscription.user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user_subscription.user.mlp_id)).exists()
            user_details['interest_rejected'] = Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user_subscription.user.mlp_id, status="Rejected").exists()
            user_details['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user_subscription.user.mlp_id, invitation_to=auth_user ,status="Rejected" ).exists()
            

            user_details['photo_hidden']=photo_hidden
            user_details['name_hidden']=name_hidden

            premium_users_data.append(user_details)

        response['status_code'] = 200
        response['message'] = 'Premium Profiles Data'
        response['total_pages'] =paginator.num_pages
        response['total_count'] = total_count
        response['data'] = premium_users_data
        
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response



def get_all_chats_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        searchname = data.get('searchname')
        page = int(data.get('page', 1))  
        page_size = int(data.get('page_size', 10))
        db = firestore.client()
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP ID is missing"
            return response
        if db:
            chats_ref = db.collection('chats').where('userIds', 'array_contains', mlp_id).stream()

            # total_documents = chats_ref.stream()  # This retrieves all documents, no pagination
            # total_documents_count = sum(1 for _ in total_documents)  # Count the total number of documents
            
            # # Calculate total pages
            # total_pages = math.ceil(total_documents_count / page_size)

            # offset = (page - 1) * page_size
            # chats_ref = chats_ref.offset(offset).limit(page_size).stream()
        
            oldchats = []

            for chat in chats_ref:
                # Fetch associated messages for the chat
                messages_ref = chat.reference.collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
                messages = [msg.to_dict() for msg in messages_ref]
                # messages = sorted(messages, key=lambda x: x.get("timestamp", ""), reverse=True)   
                lastmessageuserID= messages[0]["senderId"] if messages else None
                lastmessage = messages[0]["content"] if messages else None
                timestamp = messages[0]["timestamp"] if messages else None
                unread_count = sum(1 for msg in messages if not msg.get("isSeen", False) and msg.get("senderId")!=mlp_id) if messages else 0
                    
                chatidlist = chat.get("userIds")
                receivedchatid= chatidlist[1] if chatidlist[0]==mlp_id else chatidlist[0]
                
                user_filter = Q(mlp_id=receivedchatid)
                
                if searchname:
                    user_filter&= Q(name__istartswith=searchname) | Q(name__icontains=searchname)
                user = User.objects.filter(user_filter)
                
                if user:
                    user_obj=user.values()[0]
                    user_mm=user.first()
                    auth_user = User.objects.filter(mlp_id=mlp_id).first()
                    user_post_graduation = user_mm.partnerpostgraduationpreference.all()
                    specialization_name = user_mm.specialization.name if user_mm.specialization else None
                    data = user_obj
                    res = show_name(auth_user, user_mm)
                    
                    if res:
                        if res["status_code"] == 200:
                            name_hidden = False
                        else:
                            name_hidden = True

                    res = show_photographs(auth_user, user_mm)
        
                    if res:
                        if res["status_code"] == 200:
                            photo_hidden = False
                        else:
                            photo_hidden = True

                    opposite_gender = 'm' if auth_user.gender =='f' else 'f'

                    # auth_user = User.objects.filter(mlp_id=mlp_id).first()
                    is_bachelor = False
                    bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(auth_user.religion,opposite_gender)
                    if bachelor_of_the_day and user_mm.mlp_id == bachelor_of_the_day.user.mlp_id:
                        is_bachelor = True
                    mutually_accepted= ConnectionList.objects.filter(
                        Q(user_one__mlp_id=mlp_id, user_two=user_mm)
                        | Q(user_two__mlp_id=mlp_id, user_one=user_mm)
                    ).exists()
                    if mutually_accepted and lastmessageuserID:
                        data['name'] = data['mlp_id'] if name_hidden else data['name']
                        data['profile_pictures'] = json.loads(data['profile_pictures'])
                        data['photo_hidden'] = photo_hidden
                        data['video'] = json.loads(data['video'])
                        data['family_photos'] = json.loads(data['family_photos'])
                        data['hobbies'] = json.loads(data['hobbies'])
                        data['other_hobbies'] = json.loads(data['other_hobbies'])
                        data['profession'] = json.loads(data['profession'])
                        data['mother_tongue'] = [mt.name for mt in user_mm.mother_tongue.all()]
                        data['languages'] = [mt.name for mt in user_mm.languages.all()]
                        data['sub_caste_id'] = str(user_mm.sub_caste)
                        data['partner_cities_from'] = json.loads(data['partner_cities_from'])
                        data['partner_state_from'] = json.loads(data['partner_state_from'])
                        data['partner_country_from'] = json.loads(data['partner_country_from'])
                        data['partner_caste_from'] = json.loads(data['partner_caste_from'])
                        data['partnerExpertisePreference'] = list(user_mm.partnerexpertisepreference.values_list("expertise__name", flat=True))
                        data['partnerGraduationPreference'] = list(user_mm.partnergraduationpreference.values_list("graduation__name", flat=True))
                        data['partnerPostGraduationPreference'] = list(user_mm.partnerpgpreference.values_list("post_graduation__name", flat=True))
                        data['partnerReligionPreference'] = list(user_mm.partnerreligionpreference.values_list("religion__name", flat=True))
                        data['partnerMaritalStatusPreference'] = list(user_mm.partnermaritalstatuspreference.values_list("marital_status__name", flat=True))
                        data['partnerSpecializationPreference'] = list(user_mm.partnerspecializationpreference.values_list("specialization__name", flat=True))
                        data['siblings'] = list(user_mm.user_siblings.values())    
                        data['user_post_graduation_ids'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() else []
                        data['graduation_id'] = list(user_post_graduation.values_list("post_graduation__graduation_obj__name", flat=True))[0] if user_post_graduation.first() else None
                        data['expertise_id'] = list(user_post_graduation.values_list("post_graduation__graduation_obj__expertise_obj__name", flat=True))[0] if user_post_graduation.first() else None
                        data['partner_mothertongue_from'] = [mt.name for mt in user_mm.partner_mothertongue_from.all()]
                        data['specialization_name']=specialization_name
                        data['intrests_sent']=user_mm.invitation_to.filter(invitation_by__mlp_id=mlp_id).exists()
                        data['shortlisted_profile']=user_mm.saving_user.filter(saved_profile__mlp_id=mlp_id).exists()
                        data['interest_received']=user_mm.invitation_from.filter(invitation_to__mlp_id=mlp_id, status="Pending").exists()
                        data['interest_rejected']= user_mm.invitation_to.filter(invitation_by__mlp_id=mlp_id, status="Rejected").exists()
                        data['interest_rejected_by_me']=user_mm.invitation_from.filter(invitation_to__mlp_id=mlp_id, status="Rejected").exists()
                        data['mutually_accepted']= mutually_accepted
                        data['is_bachelor']=is_bachelor                 
                    
                    
                        oldchats.append({
                                "lastMsgUserId": lastmessageuserID,
                                "userIds": chat.get("userIds"),
                                "lastMessage": lastmessage,
                                "chatid": chat.get("id"),
                                "timestamp": timestamp,
                                # "onlineusers": chat.get("onlineusers"),
                                "onlineusers":[],
                                "unreadcount": unread_count,
                                "userdata":data
                                # "matchdata":matchdata
                            })
            if oldchats:
                oldchats = sorted(oldchats, key=lambda x: x["timestamp"], reverse=True)
            # if chatrequests:
            #     chatrequests = sorted(chatrequests, key=lambda x: x["timestamp"], reverse=True)
            response['status_code'] = 200
            response['allchats'] = oldchats
            response['message'] = "Chatlist sent successfully"
            # response['total_pages'] = total_pages  # Add the total pages to the response
            # response['current_page'] = page 
            return response
        else:
            response['status_code'] = 404
            response['message'] = "Firebase not connected"
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def get_all_chatrequests_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        searchname = data.get('searchname')
        # page = int(data.get('page', 1))  
        # page_size = int(data.get('page_size', 10))  
        db = firestore.client()
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP ID is missing"
            return response
        if db:
            chats_ref = db.collection('chats').where('userIds', 'array_contains', mlp_id).stream()
            
            
            chatrequests=[]
            for chat in chats_ref:
                messages_ref = chat.reference.collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
                messages = [msg.to_dict() for msg in messages_ref]
                # messages = sorted(messages, key=lambda x: x.get("timestamp", ""), reverse=True)
                lastmessageuserID= messages[0]["senderId"] if messages else None
                lastmessage = messages[0]["content"] if messages else None
                timestamp = messages[0]["timestamp"] if messages else None
                unread_count = sum(1 for msg in messages if not msg.get("isSeen", False) and msg.get("senderId")!=mlp_id) if messages else 0
                chatidlist = chat.get("userIds")
                receivedchatid= chatidlist[1] if chatidlist[0]==mlp_id else chatidlist[0]
                
                user_filter = Q(mlp_id=receivedchatid)
                
                if searchname:
                    user_filter&= Q(name__istartswith=searchname) | Q(name__icontains=searchname)
                user = User.objects.filter(user_filter)
                
                if user:
                    user_obj=user.values()[0]
                    user_mm=user.first()
                    auth_user = User.objects.filter(mlp_id=mlp_id).first()
                    user_post_graduation = user_mm.partnerpostgraduationpreference.all()
                    specialization_name = user_mm.specialization.name if user_mm.specialization else None
                    data=user_obj
                    res = show_name(auth_user, user_mm)
                    
                    if res:
                        if res["status_code"] == 200:
                            name_hidden = False
                        else:
                            name_hidden = True

                    res = show_photographs(auth_user, user_mm)
        
                    if res:
                        if res["status_code"] == 200:
                            photo_hidden = False
                        else:
                            photo_hidden = True

                    interest_received=user_mm.invitation_from.filter(invitation_to__mlp_id=mlp_id, status="Pending").exists()
                    mutually_accepted= ConnectionList.objects.filter(
                        Q(user_one__mlp_id=mlp_id, user_two=user_mm)
                        | Q(user_two__mlp_id=mlp_id, user_one=user_mm)
                    ).exists()
                    if interest_received and not mutually_accepted and lastmessageuserID:
                        data['name'] = data['mlp_id'] if name_hidden else data['name']
                        data['profile_pictures'] = json.loads(data['profile_pictures'])
                        data['photo_hidden'] = photo_hidden
                        data['video'] = json.loads(data['video'])
                        data['family_photos'] = json.loads(data['family_photos'])
                        data['hobbies'] = json.loads(data['hobbies'])
                        data['other_hobbies'] = json.loads(data['other_hobbies'])
                        data['profession'] = json.loads(data['profession'])
                        data['mother_tongue'] = [mt.name for mt in user_mm.mother_tongue.all()]
                        data['languages'] = [mt.name for mt in user_mm.languages.all()]
                        data['sub_caste_id'] = str(user_mm.sub_caste)
                        data['partner_cities_from'] = json.loads(data['partner_cities_from'])
                        data['partner_state_from'] = json.loads(data['partner_state_from'])
                        data['partner_country_from'] = json.loads(data['partner_country_from'])
                        data['partner_caste_from'] = json.loads(data['partner_caste_from'])
                        data['partnerExpertisePreference'] = list(user_mm.partnerexpertisepreference.values_list("expertise__name", flat=True))
                        data['partnerGraduationPreference'] = list(user_mm.partnergraduationpreference.values_list("graduation__name", flat=True))
                        data['partnerPostGraduationPreference'] = list(user_mm.partnerpgpreference.values_list("post_graduation__name", flat=True))
                        data['partnerReligionPreference'] = list(user_mm.partnerreligionpreference.values_list("religion__name", flat=True))
                        data['partnerMaritalStatusPreference'] = list(user_mm.partnermaritalstatuspreference.values_list("marital_status__name", flat=True))
                        data['partnerSpecializationPreference'] = list(user_mm.partnerspecializationpreference.values_list("specialization__name", flat=True))
                        data['siblings'] = list(user_mm.user_siblings.values())    
                        data['user_post_graduation_ids'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() else []
                        data['graduation_id'] = list(user_post_graduation.values_list("post_graduation__graduation_obj__name", flat=True))[0] if user_post_graduation.first() else None
                        data['expertise_id'] = list(user_post_graduation.values_list("post_graduation__graduation_obj__expertise_obj__name", flat=True))[0] if user_post_graduation.first() else None
                        data['partner_mothertongue_from'] = [mt.name for mt in user_mm.partner_mothertongue_from.all()]
                        data['specialization_name']=specialization_name
                        data['intrests_sent']=user_mm.invitation_to.filter(invitation_by__mlp_id=mlp_id).exists()
                        data['shortlisted_profile']=user_mm.saving_user.filter(saved_profile__mlp_id=mlp_id).exists()
                        data['interest_received']=interest_received
                        data['interest_rejected']= user_mm.invitation_to.filter(invitation_by__mlp_id=mlp_id, status="Rejected").exists()
                        data['interest_rejected_by_me']=user_mm.invitation_from.filter(invitation_to__mlp_id=mlp_id, status="Rejected").exists()
                        data['mutually_accepted']= mutually_accepted
                    
                        chatrequests.append({
                                "lastMsgUserId": lastmessageuserID,
                                "userIds": chat.get("userIds"),
                                "lastMessage": lastmessage,
                                "chatid": chat.get("id"),
                                "timestamp": timestamp,
                                "onlineusers":chat.get("onlineusers"),
                                "unreadcount":unread_count,
                                "userdata":data
                                # "matchdata":matchdata
                            })
                    
            if chatrequests:
                chatrequests = sorted(chatrequests, key=lambda x: x["timestamp"], reverse=True)
                # Paginate chatrequests
                # total_count = len(chatrequests)
                # total_pages = (total_count // page_size) + (1 if total_count % page_size > 0 else 0)
                # start_index = (page - 1) * page_size
                # end_index = start_index + page_size
                
                # Slice the chatrequests for the current page
                # paginated_chatrequests = chatrequests[start_index:end_index]

            # response['status_code'] = 200
            # response['chatrequests'] = chatrequests
            # # response['total_count'] = total_count
            # # response['total_pages'] = total_pages
            # # response['current_page'] = page
            # response['message'] = "Chatlist sent successfully"
            # return response
            # else:
            #     response['status_code'] = 404
            #     response['message'] = "No chat requests found"

            response['status_code'] = 200
            response['chatrequests'] = chatrequests
            response['message'] = "Chatlist sent successfully"
            return response
        else:
            response['status_code'] = 404
            response['message'] = "Firebase not connected"
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def get_all_mysentchats_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        searchname = data.get('searchname')
        # page = int(data.get('page', 1))  # Default page 1
        # per_page = int(data.get('per_page', 10))  # Default 10 results per page
        db = firestore.client()
        if not mlp_id:
            response["status_code"] = 301
            response["message"] = "MLP ID is missing"
            return response
        if db:
            chats_ref = db.collection('chats').where('userIds', 'array_contains', mlp_id).stream()
            chatrequests=[]
            for chat in chats_ref:
                messages_ref = chat.reference.collection('messages').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
                messages = [msg.to_dict() for msg in messages_ref]
                # messages = sorted(messages, key=lambda x: x.get("timestamp", ""), reverse=True)
                lastmessageuserID= messages[0]["senderId"] if messages else None
                lastmessage = messages[0]["content"] if messages else None
                timestamp = messages[0]["timestamp"] if messages else None
                unread_count = sum(1 for msg in messages if not msg.get("isSeen", False) and msg.get("senderId")!=mlp_id) if messages else 0
                chatidlist = chat.get("userIds")
                receivedchatid= chatidlist[1] if chatidlist[0]==mlp_id else chatidlist[0]
                
                user_filter = Q(mlp_id=receivedchatid)
                
                if searchname:
                    user_filter&= Q(name__istartswith=searchname) | Q(name__icontains=searchname)
                user = User.objects.filter(user_filter)
                
                if user:
                    user_obj=user.values()[0]
                    user_mm=user.first()
                    auth_user = User.objects.filter(mlp_id=mlp_id).first()
                    user_post_graduation = user_mm.partnerpostgraduationpreference.all()
                    specialization_name = user_mm.specialization.name if user_mm.specialization else None
                    data=user_obj
                    res = show_name(auth_user, user_mm)
                    
                    if res:
                        if res["status_code"] == 200:
                            name_hidden = False
                        else:
                            name_hidden = True
                    res = show_photographs(auth_user, user_mm)
        
                    if res:
                        if res["status_code"] == 200:
                            photo_hidden = False
                        else:
                            photo_hidden = True
                    interest_sent=user_mm.invitation_to.filter(invitation_by__mlp_id=mlp_id).exists()
                    mutually_accepted= ConnectionList.objects.filter(
                        Q(user_one__mlp_id=mlp_id, user_two=user_mm)
                        | Q(user_two__mlp_id=mlp_id, user_one=user_mm)
                    ).exists()
                    if interest_sent and not mutually_accepted and lastmessageuserID:
                        data['name'] = data['mlp_id'] if name_hidden else data['name']
                        data['profile_pictures'] = json.loads(data['profile_pictures'])
                        data['photo_hidden'] = photo_hidden
                        data['video'] = json.loads(data['video'])
                        data['family_photos'] = json.loads(data['family_photos'])
                        data['hobbies'] = json.loads(data['hobbies'])
                        data['other_hobbies'] = json.loads(data['other_hobbies'])
                        data['profession'] = json.loads(data['profession'])
                        data['mother_tongue'] = [mt.name for mt in user_mm.mother_tongue.all()]
                        data['languages'] = [mt.name for mt in user_mm.languages.all()]
                        data['sub_caste_id'] = str(user_mm.sub_caste)
                        data['partner_cities_from'] = json.loads(data['partner_cities_from'])
                        data['partner_state_from'] = json.loads(data['partner_state_from'])
                        data['partner_country_from'] = json.loads(data['partner_country_from'])
                        data['partner_caste_from'] = json.loads(data['partner_caste_from'])
                        data['partnerExpertisePreference'] = list(user_mm.partnerexpertisepreference.values_list("expertise__name", flat=True))
                        data['partnerGraduationPreference'] = list(user_mm.partnergraduationpreference.values_list("graduation__name", flat=True))
                        data['partnerPostGraduationPreference'] = list(user_mm.partnerpgpreference.values_list("post_graduation__name", flat=True))
                        data['partnerReligionPreference'] = list(user_mm.partnerreligionpreference.values_list("religion__name", flat=True))
                        data['partnerMaritalStatusPreference'] = list(user_mm.partnermaritalstatuspreference.values_list("marital_status__name", flat=True))
                        data['partnerSpecializationPreference'] = list(user_mm.partnerspecializationpreference.values_list("specialization__name", flat=True))
                        data['siblings'] = list(user_mm.user_siblings.values())    
                        data['user_post_graduation_ids'] = list(user_post_graduation.values_list("post_graduation__name", flat=True)) if user_post_graduation.first() else []
                        data['graduation_id'] = list(user_post_graduation.values_list("post_graduation__graduation_obj__name", flat=True))[0] if user_post_graduation.first() else None
                        data['expertise_id'] = list(user_post_graduation.values_list("post_graduation__graduation_obj__expertise_obj__name", flat=True))[0] if user_post_graduation.first() else None
                        data['partner_mothertongue_from'] = [mt.name for mt in user_mm.partner_mothertongue_from.all()]
                        data['specialization_name']=specialization_name
                        data['intrests_sent']=interest_sent
                        data['shortlisted_profile']=user_mm.saving_user.filter(saved_profile__mlp_id=mlp_id).exists()
                        data['interest_received']=user_mm.invitation_from.filter(invitation_to__mlp_id=mlp_id, status="Pending").exists()
                        data['interest_rejected']= user_mm.invitation_to.filter(invitation_by__mlp_id=mlp_id, status="Rejected").exists()
                        data['interest_rejected_by_me']=user_mm.invitation_from.filter(invitation_to__mlp_id=mlp_id, status="Rejected").exists()
                        data['mutually_accepted']= mutually_accepted
                        chatrequests.append({
                                "lastMsgUserId": lastmessageuserID,
                                "userIds": chat.get("userIds"),
                                "lastMessage": lastmessage,
                                "chatid": chat.get("id"),
                                "timestamp": timestamp,
                                "onlineusers":chat.get("onlineusers"),
                                "unreadcount":unread_count,
                                "userdata":data
                                # "matchdata":matchdata
                            })
                        
            # Implement pagination logic
            # start_index = (page - 1) * per_page
            # end_index = start_index + per_page
            # paginated_chatrequests = chatrequests[start_index:end_index]

            # if paginated_chatrequests:
            #     paginated_chatrequests = sorted(paginated_chatrequests, key=lambda x: x["timestamp"], reverse=True)
        
            if chatrequests:
                chatrequests = sorted(chatrequests, key=lambda x: x["timestamp"], reverse=True)
            response['status_code'] = 200
            response['mychatrequests'] = chatrequests
            response['message'] = "Chatlist sent successfully"
            # response['total_count'] = len(chatrequests) 
            # response['total_pages'] = (len(chatrequests) // per_page) + (1 if len(chatrequests) % per_page > 0 else 0)
            return response
        else:
            response['status_code'] = 404
            response['message'] = "Firebase not connected"
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response


def reportprofile_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        report_by = data.get("report_by")
        report_to = data.get("report_to")
        reason = data.get("reason")
        if report_by and report_to:
            report_by_user=User.objects.filter(mlp_id=report_by, is_active=True , is_wrong=False)
            report_to_user=User.objects.filter(mlp_id=report_to,is_active=True, is_wrong=False)
            if report_by_user and report_to_user:
                report_by_user=report_by_user.first()
                report_to_user=report_to_user.first()
                with transaction.atomic():
                   ReportUsers.objects.get_or_create(user=report_by_user,report_user=report_to_user, reason=reason)
                   if "Details seems to be incorrect" in reason or "Seems Fake Profile" in reason:
                        report_to_user.is_wrong = True
                        report_to_user.save()

                response={
                    'status_code': 200,
                    'message': 'User reported successfully'
                }
                return response
            else:
                response={
                    'status_code': 404,
                    'message': 'Users not found'
                }
                return response
        else:
            response={
                    'status_code': 404,
                    'message': 'Params not added'
                }
            return response

    except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            # traceback.print_exc()
            return response

def test_firebase():
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        db=firestore.client()
        chats_ref = db.collection('chatroom').stream()
        docs = [doc.to_dict() for doc in chats_ref]
        print(docs)
        response={
            'status_code': 200,
            'message': 'Success'
        }
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
def test_CRON_func():
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        main_cronjob()
        response={
            'status_code': 200,
            'message': 'Success'
        }
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    
#newly joined last week service
def get_newly_joined_last_week(mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        user = User.objects.filter(mlp_id=mlp_id, is_active=True, is_wrong=False,mandatory_questions_completed=True).first()

        if not user:
            response['status_code']=301
            response['message']='User not found'
            return response
        
        last_week = timezone.now() - timedelta(days=7)  
       
        opposite_gender = 'm' if user.gender == 'f' else 'f'

        # cache_key = f"get_newly_joined_last_week_{mlp_id}"
        # cached_data = cache.get(cache_key)
       # queryset = None  
        # if cached_data is None:   
        blocked_users = BlockedUsers.objects.filter(user=user).values_list('blocked_user__mlp_id', flat=True)

        queryset = User.objects.filter(
            created_date__date=last_week.date(),
            gender=opposite_gender,
            is_active=True,
            is_wrong=False,
            mandatory_questions_completed=True
        ).exclude(mlp_id__in=blocked_users).order_by('-created_date').distinct()
        #     cache.set(cache_key, queryset ,timeout=900)
        # else:
        #     queryset = cached_data  

        total_count = queryset.count()  
        
        if not queryset:
            response['status_code'] = 204
            response['message'] = "No content Found"
            return response

        paginator = Paginator(queryset, page_size)
        paginated_queryset = paginator.get_page(page)

        #serializer = UserSerializer(paginated_queryset, many=True)
        last_week_data =[]
        for data in paginated_queryset:
            suggested_user_id = data.id
            suggested_user = User.objects.get(id=suggested_user_id)
            
            if ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists():
                continue

            res = show_name(user, suggested_user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True

                

            res = show_photographs(user,suggested_user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True

            data = {
                    'mlp_id': suggested_user.mlp_id,
                    'name': suggested_user.mlp_id if name_hidden else suggested_user.name,
                    'email': suggested_user.email,
                    'religion': suggested_user.religion.name if suggested_user.religion and suggested_user.religion.name else None,
                    'mobile_number': suggested_user.mobile_number,
                    'gender': suggested_user.gender,
                    'dob': suggested_user.dob,
                    'eating_habits' : suggested_user.eating_habits,
                    'marital_status':suggested_user.marital_status.name if suggested_user.marital_status and suggested_user.marital_status.name else None,
                    'profile_pictures': json.loads(suggested_user.profile_pictures),
                    'family_photos': json.loads(suggested_user.family_photos),
                    'activity_status':suggested_user.activity_status,
                    'last_seen':suggested_user.last_seen,
                    'manglik': suggested_user.manglik,
                    'height': suggested_user.height,
                    'weight': suggested_user.weight,
                    'hobbies': json.loads(suggested_user.hobbies),
                    'other_hobbies': json.loads(suggested_user.other_hobbies),
                    'city': suggested_user.city,
                    'caste': suggested_user.caste,
                    'completed_post_grad' : suggested_user.completed_post_grad,
                    'is_bachelor': is_bachelor
                }
             
        
            data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()
            # data['interest_sent'] =  Intrest.objects.filter(Q(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id) | Q(invitation_to=user, invitation_by__mlp_id=suggested_user.mlp_id)).exists()
            # data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()
            data['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user , status="Rejected").exists()
            user_graduation = suggested_user.graduation_obj.name if suggested_user.graduation_obj else None

            if suggested_user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=suggested_user).values_list(
                    'post_graduation__name', flat=True
                ))
            else:
                user_post_graduation = set()

            user_expertise =  suggested_user.graduation_obj.expertise_obj.name if (suggested_user.graduation_obj and suggested_user.graduation_obj.expertise_obj) else None

            data['graduation_id'] = user_graduation
            data['user_post_graduation'] = list(user_post_graduation)
            data['expertise_id'] = user_expertise

            data['is_bachelor'] = is_bachelor
            data['photo_hidden']=photo_hidden
            data['name_hidden']=name_hidden

            last_week_data.append(data)

            response['message'] = "Newly Joined Users Data (Last Week)"
            response['status_code'] = 200
            response['total_pages'] = paginator.num_pages
            response['total_count'] = total_count
            response['data'] = last_week_data
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


# To get same religion users data
def same_religion_profiles(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()

        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
        opposite_gender = 'm' if auth_user.gender == 'f' else 'f'

        cache_key = f"get_same_religion_users_{logged_mlp_id}"
        cached_data = cache.get(cache_key)
        same_religion_users = None
        if cached_data is None:   
            blocked_users = BlockedUsers.objects.filter(user=auth_user).values_list('blocked_user__mlp_id', flat=True)
            if auth_user.religion:
                same_religion_users = User.objects.filter(
                    religion=auth_user.religion,
                    is_active=True,
                    is_wrong=False,
                    mandatory_questions_completed=True,
                    gender='m' if auth_user.gender == 'f' else 'f'
                ).exclude(mlp_id__in=blocked_users).distinct()
                # random.shuffle(same_religion_users)
                cache.set(cache_key , same_religion_users , timeout =900)
        else:
            same_religion_users = cached_data  


        total_count = same_religion_users.count()      
        # total_count = len(same_religion_users) 

        if not same_religion_users:
            response['status_code'] = 300
            response['message'] = "No content found"
            return response
        
        paginator = Paginator(same_religion_users, page_size)
        paginated_users = paginator.get_page(page)

        # Shuffling after pagination
        paginated_users_list = list(paginated_users)
        random.shuffle(paginated_users_list)

        # print(f"Profiles before shuffling: {[user.mlp_id for user in paginated_users]}")
        # print(f"Profiles after shuffling: {[user.mlp_id for user in paginated_users_list]}") 

        same_religion_users_data = []
        for user in paginated_users_list:

            if ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user.mlp_id)).exists():
                continue

            res = show_name(auth_user,user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True
                
            res = show_photographs(auth_user,user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(auth_user.religion,opposite_gender)
            if bachelor_of_the_day and user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True
    

            user_details = {
                'mlp_id': user.mlp_id,
                'name': user.mlp_id if name_hidden else user.name,
                'email': user.email,
                'gender': user.gender,
                'dob': user.dob,
                'religion': user.religion.name if user.religion else None,
                'marital_status' : user.marital_status.name if user.marital_status else None,
                'profile_pictures': json.loads(user.profile_pictures),
                'family_photos': json.loads(user.family_photos),
                'activity_status':user.activity_status,
                'eating_habits' : user.eating_habits,
                'last_seen':user.last_seen,
                'completed_post_grad':user.completed_post_grad,
                'height': user.height,
                'weight': user.weight,
                'salary': user.salary,
                'hobbies': json.loads(user.hobbies),
                'other_hobbies': json.loads(user.other_hobbies),
                'city': user.city,
                'caste': user.caste,
                'shortlisted': SavedUser.objects.filter(user=auth_user, saved_profile=user).exists(),
                'interest_sent':  Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user.mlp_id).exists()
            }
            
            user_details['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=auth_user).exists()
            user_details['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user.mlp_id)).exists()
            user_details['interest_rejected'] = Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user.mlp_id, status="Rejected").exists()
            user_details['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=auth_user , status="Rejected").exists()
            
            user_graduation = user.graduation_obj.name if user.graduation_obj else None

            if user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=user).values_list('post_graduation__name', flat=True))
            else :
                user_post_graduation = set()    

            user_expertise =  user.graduation_obj.expertise_obj.name if (user.graduation_obj and user.graduation_obj.expertise_obj) else None

            user_details['graduation_id'] = user_graduation
            user_details['user_post_graduation'] = list(user_post_graduation)
            user_details['expertise_id'] = user_expertise
            
            user_details['is_bachelor'] = is_bachelor
            user_details['name_hidden']=name_hidden
            user_details['photo_hidden']=photo_hidden

            same_religion_users_data.append(user_details)

        response['status_code'] = 200
        response['message'] = 'Same Religion Profiles Data'
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = same_religion_users_data
        return response

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response


# To get same caste users data
def same_caste_profiles(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:   
        auth_user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True, is_wrong=False,mandatory_questions_completed=True).first()

        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
        opposite_gender = 'm' if auth_user.gender == 'f' else 'f'
        cache_key = f"same_caste_profiles_{logged_mlp_id}"
        cached_data = cache.get(cache_key)
        same_caste_users = None 
        if cached_data is None:   
            blocked_users = BlockedUsers.objects.filter(user=auth_user).values_list('blocked_user__mlp_id', flat=True)
            if auth_user.caste:
                same_caste_users = User.objects.filter(
                    caste=auth_user.caste,
                    is_active=True,
                    is_wrong=False,
                    mandatory_questions_completed=True,
                    gender='m' if auth_user.gender == 'f' else 'f'
                ).exclude(mlp_id__in=blocked_users).distinct()
                cache.set(cache_key , same_caste_users, timeout = 900)
        else:
            same_caste_users = cached_data


        total_count = same_caste_users.count() 
        # total_count = len(same_caste_users)   
        
        if not same_caste_users:
            response['status_code'] = 300
            response['message'] = "No content found"
            return response
        
        paginator = Paginator(same_caste_users, page_size)
        paginated_users = paginator.get_page(page)

        # Shuffling after pagination
        paginated_users_list = list(paginated_users)
        random.shuffle(paginated_users_list)

        # print(f"Profiles before shuffling: {[user.mlp_id for user in paginated_users]}")
        # print(f"Profiles after shuffling: {[user.mlp_id for user in paginated_users_list]}") 

        same_caste_users_data = []
        for user in paginated_users_list:

            if  ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user.mlp_id)).exists():
                continue

            res = show_name(auth_user,user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True
                
            res = show_photographs(auth_user,user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(auth_user.religion, opposite_gender)
            if bachelor_of_the_day and user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True
            
         
            user_details = {
                'mlp_id': user.mlp_id,
                'name': user.mlp_id if name_hidden else user.name,
                'email': user.email,
                'gender': user.gender,
                'dob': user.dob,
                'religion': user.religion.name if user.religion else None,
                'marital_status' : user.marital_status.name if user.marital_status else None,
                'caste': user.caste,
                'eating_habits' : user.eating_habits,
                'profile_pictures': json.loads(user.profile_pictures),
                'family_photos': json.loads(user.family_photos),
                'activity_status':user.activity_status,
                'last_seen':user.last_seen,
                'completed_post_grad':user.completed_post_grad,
                'height': user.height,
                'weight': user.weight,
                'salary': user.salary,
                'hobbies': json.loads(user.hobbies),
                'other_hobbies': json.loads(user.other_hobbies),
                'city': user.city,
                'shortlisted': SavedUser.objects.filter(user=auth_user, saved_profile=user).exists(),
                'interest_sent':  Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user.mlp_id).exists()
            }
            
            user_details['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=auth_user).exists()
            user_details['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user.mlp_id)).exists()
            user_details['interest_rejected'] = Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user.mlp_id, status="Rejected").exists()
            user_details['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=auth_user, status="Rejected").exists()

            user_graduation =  user.graduation_obj.name if  user.graduation_obj else None

            if user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=user).values_list('post_graduation__name', flat=True))
            else:
                user_post_graduation = set()  

            user_expertise =  user.graduation_obj.expertise_obj.name if (user.graduation_obj and user.graduation_obj.expertise_obj) else None

            user_details['graduation_id'] = user_graduation
            user_details['user_post_graduation'] = list(user_post_graduation)
            user_details['expertise_id'] = user_expertise
            
            user_details['is_bachelor'] = is_bachelor
            user_details['photo_hidden']=photo_hidden
            user_details['name_hidden']=name_hidden

            same_caste_users_data.append(user_details)

        response['status_code'] = 200
        response['message'] = 'Same Caste Profiles Data'
        response['total_pages']=paginator.num_pages
        response['total_count'] = total_count
        response['data'] = same_caste_users_data
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

# To get same age and height users
def same_height_and_age_profiles(logged_mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        auth_user = User.objects.filter(mlp_id=logged_mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()

        if auth_user is None:
            response['status_code'] = 404
            response['message'] = 'User not found'
            return response
         
        blocked_users = BlockedUsers.objects.filter(user=auth_user).values_list('blocked_user__mlp_id', flat=True)

        today = date.today()
        age = today.year - auth_user.dob.year - ((today.month, today.day) < (auth_user.dob.month, auth_user.dob.day))

        same_age_and_height_users = User.objects.filter(
            height=auth_user.height,
            dob__year=today.year - age,
            is_active=True,
            is_wrong=False,
            mandatory_questions_completed=True,
            gender='m' if auth_user.gender == 'f' else 'f'
        ).exclude(mlp_id__in=blocked_users)

        same_age_users = User.objects.filter(
            dob__year=today.year - age,
            is_active=True,
            is_wrong=False,
            mandatory_questions_completed=True,
            gender='m' if auth_user.gender == 'f' else 'f'
        ).exclude(mlp_id__in=blocked_users).exclude(id__in=same_age_and_height_users)

        same_height_users = User.objects.filter(
            height=auth_user.height,
            is_active=True,
            is_wrong=False,
            mandatory_questions_completed=True,
            gender='m' if auth_user.gender == 'f' else 'f'
        ).exclude(mlp_id__in=blocked_users).exclude(id__in=same_age_and_height_users).exclude(id__in=same_age_users)

        combined_users = list(same_age_and_height_users) + list(same_age_users) + list(same_height_users)


        total_count = len(combined_users)  
        
        if not combined_users:
            response['status_code'] = 300
            response['message'] = "No content found"
            return response
         
        paginator = Paginator(combined_users, page_size)
        paginated_users = paginator.get_page(page)

        # Shuffle paginated results
        paginated_users_list = list(paginated_users)  # Convert to list to shuffle
        random.shuffle(paginated_users_list)

        combined_data = get_user_data_code(paginated_users_list, auth_user)

        response['status_code'] = 200
        response['message'] = 'Same Age and Height Profiles Data'
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data'] = combined_data

        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response

def get_user_data_code(users, auth_user):

    user_data = []
    opposite_gender = 'm' if auth_user.gender == 'f' else 'f'
    for user in users:

        if  ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user.mlp_id)).exists():
            continue

        res = show_name(auth_user,user)
        if res and res["status_code"] == 200:
            name_hidden = False
        else:
            name_hidden = True
            
        res = show_photographs(auth_user,user)
        if res:
            if res["status_code"] == 200:
                photo_hidden = False
            else:
                photo_hidden = True 
        
        is_bachelor = False
        bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(auth_user.religion,opposite_gender)
        if bachelor_of_the_day and user.mlp_id == bachelor_of_the_day.user.mlp_id:
            is_bachelor = True
        

        user_details = {
            'mlp_id': user.mlp_id,
            'name': user.mlp_id if name_hidden else user.name,
            'email': user.email,
            'gender': user.gender,
            'dob': user.dob,
            'religion': user.religion.name if user.religion else None,
            'marital_status' : user.marital_status.name if user.marital_status else None,
            'eating_habits' : user.eating_habits,
            'caste': user.caste,
            'profile_pictures': json.loads(user.profile_pictures),
            'family_photos': json.loads(user.family_photos),
            'activity_status':user.activity_status,
            'last_seen':user.last_seen,
            'completed_post_grad': user.completed_post_grad,
            'height': user.height,
            'weight': user.weight,
            'salary': user.salary,
            'hobbies': json.loads(user.hobbies),
            'other_hobbies': json.loads(user.other_hobbies),
            'city': user.city,
            'shortlisted': SavedUser.objects.filter(user=auth_user, saved_profile=user).exists(),
            'interest_sent': Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user.mlp_id).exists()
        }
        
        user_details['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=auth_user).exists()
        user_details['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=user.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=user.mlp_id)).exists()
        user_details['interest_rejected'] = Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=user.mlp_id, status="Rejected").exists()
        user_details['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=user.mlp_id, invitation_to=auth_user , status="Rejected").exists()

        user_graduation = user.graduation_obj.name if user.graduation_obj else None

        if user.completed_post_grad:
            user_post_graduation = set(UserPostGraduation.objects.filter(user=user).values_list('post_graduation__name', flat=True))
        else :
            user_post_graduation = set()

        user_expertise =  user.graduation_obj.expertise_obj.name if (user.graduation_obj and user.graduation_obj.expertise_obj) else None

        user_details['graduation_id'] = user_graduation
        user_details['user_post_graduation'] = list(user_post_graduation)
        user_details['expertise_id'] = user_expertise

        user_details['is_bachelor']= is_bachelor 
        user_details['photo_hidden']=photo_hidden
        user_details['name_hidden']=name_hidden

        user_data.append(user_details)

    return user_data


#newly joined last month service
def get_newly_joined_last_month(mlp_id,page,page_size):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        user = User.objects.filter(mlp_id=mlp_id, is_active=True, is_wrong=False, mandatory_questions_completed=True).first()

        if not user:
            response['status_code']=301
            response['message']='User not found'
            return response
        
        last_month = timezone.now() - timedelta(days=30) 
            
        opposite_gender = 'm' if user.gender == 'f' else 'f'

         
        blocked_users = BlockedUsers.objects.filter(user=user).values_list('blocked_user__mlp_id', flat=True)

        queryset = User.objects.filter(
            created_date__gte=last_month,
            gender=opposite_gender,
            is_active=True,
            is_wrong=False,
            mandatory_questions_completed=True
        ).exclude(mlp_id__in=blocked_users).order_by('-created_date').distinct()
       
        total_count = queryset.count()

        if not queryset:
            response['status_code'] = 204
            response['message'] = "No content Found"
            return response 
        
        paginator = Paginator(queryset, page_size)
        paginated_users = paginator.get_page(page)

        #serializer = UserSerializer(paginated_users, many=True)
        last_month_data =[]
        for data in paginated_users:
            suggested_user_id = data.id
            suggested_user = User.objects.get(id=suggested_user_id)

            if  ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists():
                continue

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(user.religion,opposite_gender)
            if bachelor_of_the_day and suggested_user.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True


            res = show_name(user,suggested_user)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True

          
            res = show_photographs(user,suggested_user)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 

            data = {
                    'mlp_id': suggested_user.mlp_id,
                    'name': suggested_user.mlp_id if name_hidden else suggested_user.name,
                    'email': suggested_user.email,
                    'religion': suggested_user.religion.name if suggested_user.religion and suggested_user.religion.name else None,
                    'mobile_number': suggested_user.mobile_number,
                    'gender': suggested_user.gender,
                    'dob': suggested_user.dob,
                    'eating_habits' : suggested_user.eating_habits,
                    'marital_status':suggested_user.marital_status.name if suggested_user.marital_status and suggested_user.marital_status.name else None,
                    'profile_pictures': json.loads(suggested_user.profile_pictures),
                    'family_photos': json.loads(suggested_user.family_photos),
                    'activity_status':suggested_user.activity_status,
                    'last_seen':suggested_user.last_seen,
                    'manglik': suggested_user.manglik,
                    'height': suggested_user.height,
                    'weight': suggested_user.weight,
                    'hobbies': json.loads(suggested_user.hobbies),
                    'other_hobbies': json.loads(suggested_user.other_hobbies),
                    'city': suggested_user.city,
                    'caste': suggested_user.caste,
                    'completed_post_grad' : suggested_user.completed_post_grad,
                    'is_bachelor': is_bachelor
                }        
            
            data['shortlisted'] = SavedUser.objects.filter(user=user, saved_profile=suggested_user).exists()
            data['interest_sent'] =  Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=user, user_two__mlp_id=suggested_user.mlp_id) | Q(user_two=user, user_one__mlp_id=suggested_user.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=user, invitation_to__mlp_id=suggested_user.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=suggested_user.mlp_id, invitation_to=user, status="Rejected").exists()

            user_graduation = suggested_user.graduation_obj.name if suggested_user.graduation_obj else None

            if suggested_user.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=suggested_user).values_list(
                    'post_graduation__name', flat=True
                ))
            else :
                user_post_graduation = set()

            user_expertise = suggested_user.graduation_obj.expertise_obj.name if (suggested_user.graduation_obj and suggested_user.graduation_obj.expertise_obj) else None

            data['graduation_id'] = user_graduation
            data['user_post_graduation'] = list(user_post_graduation)
            data['expertise_id'] = user_expertise

            data['is_bachelor'] = is_bachelor
            data['photo_hidden']=photo_hidden
            data['name_hidden']=name_hidden

            last_month_data.append(data)

            response['message'] = "Newly Joined Users Data (Last month)"
            response['status_code'] = 200
            response['total_pages'] = paginator.num_pages
            response['total_count'] = total_count
            response['data'] = last_month_data
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response
    

# To get matched preference profiles
def matched_preference_service(logged_mlp_id,page,page_size):
    response={
        'status_code': 500,
        'message' : 'Internal Server error'
    }

    try:
        auth_user=User.objects.filter(mlp_id=logged_mlp_id,is_active=True,is_wrong=False,mandatory_questions_completed=True).first()

        if not auth_user :
            response['status_code']=301
            response['message']='User not found'

        opposite_gender = 'm' if auth_user.gender == 'f' else 'f' 

        # cache_key = f"get_matched_preference_data_{logged_mlp_id}"
        # cached_data = cache.get(cache_key)

        # if cached_data is None:  
        today = date.today()
        age = today.year - auth_user.dob.year - ((today.month, today.day) < (auth_user.dob.month, auth_user.dob.day))   
        blocked_users = BlockedUsers.objects.filter(user=auth_user).values_list('blocked_user__mlp_id', flat=True)
        if auth_user.gender == 'm':
            min_age = age - 5
            max_age = age
        else:
            min_age = age
            max_age = age + 5 
        
        matched_data = None    
        
        if auth_user.partner_age_preference:
            partner_age_from = auth_user.partner_age_from
            partner_age_to = auth_user.partner_age_to

            matched_data = User.objects.filter(is_active=True, is_wrong=False,
                                        mandatory_questions_completed=True,
                                        religion=auth_user.religion,
                                        dob__year__gte=today.year - partner_age_to,
                                        dob__year__lte=today.year - partner_age_from,
                                        gender=opposite_gender).exclude(mlp_id__in=blocked_users).distinct()  
        else:
            matched_data = User.objects.filter(is_active=True, is_wrong=False,
                                        mandatory_questions_completed=True,
                                        religion=auth_user.religion,
                                        dob__year__gte=today.year - max_age,
                                        dob__year__lte=today.year - min_age,
                                        gender=opposite_gender).exclude(mlp_id__in=blocked_users).distinct()  
        
            # matched_data =[]
            # for user in users:
            #     res = calculate_match_percentage(auth_user.mlp_id,user.mlp_id)
            #     if res['status_code']==200 and res['match_percentage'] == 100:
            #         matched_data.append(user)
            
        #     cache.set(cache_key , matched_data , timeout = 3600)       
        # else:
        #     matched_data = cached_data

        # matched_data = matched_data.order_by('?')

        total_count = matched_data.count()

        if matched_data is None:
            response['status_code'] = 300
            response['message'] = "No content found"
            return response    

        paginator = Paginator(matched_data, page_size)
        paginated_users = paginator.get_page(page)

        # Convert paginated users to list and randomize
        paginated_users_list = list(paginated_users)
        random.shuffle(paginated_users_list) 

        # print(f"Profiles before shuffling: {[user.mlp_id for user in paginated_users]}")
        # print(f"Profiles after shuffling: {[user.mlp_id for user in paginated_users_list]}") 

        serialized_profile=[]

        for profile in paginated_users_list:

            if ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=profile.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=profile.mlp_id)).exists():
                continue

            is_bachelor = False
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(auth_user.religion,opposite_gender)
            if bachelor_of_the_day and profile.mlp_id == bachelor_of_the_day.user.mlp_id:
                is_bachelor = True


            res = show_name(auth_user,profile)
            if res and res["status_code"] == 200:
                name_hidden = False
            else:
                name_hidden = True
                
            res = show_photographs(auth_user,profile)
            if res:
                if res["status_code"] == 200:
                    photo_hidden = False
                else:
                    photo_hidden = True 
            age = today.year - profile.dob.year - ((today.month, today.day) < (profile.dob.month, profile.dob.day))   
            data = {
                'mlp_id':profile.mlp_id,
                'name': profile.mlp_id if name_hidden else profile.name,
                'email': profile.email,
                'gender': profile.gender,
                'dob': profile.dob,
                'age':age,
                'religion': profile.religion.name if profile.religion else None,
                'marital_status' : profile.marital_status.name if profile.marital_status else None,
                'profile_pictures': json.loads(profile.profile_pictures),
                'family_photos': json.loads(profile.family_photos),
                'activity_status':profile.activity_status,
                'last_seen':profile.last_seen,
                'completed_post_grad': profile.completed_post_grad,
                'height': profile.height,
                'weight': profile.weight,
                'eating_habits' : profile.eating_habits,
                'hobbies': json.loads(profile.hobbies),
                'other_hobbies': json.loads(profile.other_hobbies),
                'city': profile.city,
                'caste': profile.caste,
                'is_bachelor': is_bachelor,
                'shortlisted': SavedUser.objects.filter(user=auth_user, saved_profile=profile).exists(),
                'interest_sent': Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=profile.mlp_id).exists()
            }

           # data['shortlisted'] = SavedUser.objects.filter(user=auth_user, saved_profile=profile).exists()
           # data['interest_sent'] =  Intrest.objects.filter(Q(invitation_by=auth_user, invitation_to__mlp_id=profile.mlp_id) | Q(invitation_to=auth_user, invitation_by__mlp_id=profile.mlp_id)).exists()
            data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=profile.mlp_id, invitation_to=auth_user).exists()
            data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one=auth_user, user_two__mlp_id=profile.mlp_id) | Q(user_two=auth_user, user_one__mlp_id=profile.mlp_id)).exists()
            data['interest_rejected'] = Intrest.objects.filter(invitation_by=auth_user, invitation_to__mlp_id=profile.mlp_id, status="Rejected").exists()
            data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=profile.mlp_id, invitation_to=auth_user , status="Rejected").exists()

            user_graduation = profile.graduation_obj.name if profile.graduation_obj else None

            if profile.completed_post_grad:
                user_post_graduation = set(UserPostGraduation.objects.filter(user=profile).values_list('post_graduation__name', flat=True))
            else :
                user_post_graduation = set() 

            user_expertise =  profile.graduation_obj.expertise_obj.name if (profile.graduation_obj and profile.graduation_obj.expertise_obj) else None

            data['graduation_id'] = user_graduation
            data['user_post_graduation'] = list(user_post_graduation)
            data['expertise_id'] = user_expertise
            data['name_hidden']=name_hidden
            data['photo_hidden']=photo_hidden

            serialized_profile.append(data)
        #  # Update cache with displayed profiles
        # new_displayed_profiles = [profile.mlp_id for profile in paginated_users]
        # displayed_profiles.extend(new_displayed_profiles)
        # cache.set(cache_key, displayed_profiles, timeout=3600)  # Cache for 1 hour

        response['status_code']=200
        response['message']='Query Processed Successfully'
        response['total_pages'] = paginator.num_pages
        response['total_count'] = total_count
        response['data']=serialized_profile 
        return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        return response   


def contact_viewed_func(data):
    response = {
    'status_code': 500,
    'message': 'Internal server error'
}
    try:
        mlp_id = data.get('mlp_id', '')
        profileid = data.get('profileid','')

        if not mlp_id and not profileid:
            response["status_code"] = 301
            response["message"] = "Fields missing"
            return response
        user = User.objects.filter(mlp_id=mlp_id).first()
        profile = User.objects.filter(mlp_id=profileid).first()
        print(user, profile)
        if user and profile:
            ContactViewed.objects.get_or_create(user=user, seen_contact=profile)
            if user.mlp_id:
                message = f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile"
                Notifications.objects.get_or_create(user=profile,sender=user,message=message, type="detailview")
                custom_data={
                    "screen":"detailview",
                    "userid":user.mlp_id
                    }
                if profile.notification_token!=None:
                    message = messaging.Message(
                        token=profile.notification_token,  # FCM registration token
                        notification=messaging.Notification(
                            title="Profile Visited",
                            body=f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile"
                        ),
                        data=custom_data  
                    )

                    messaging.send(message)
                    
                    # push_service.notify_single_device(registration_id=profile.notification_token,message_title="Profile Visited",message_body=f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile",data_message=custom_data)
                all_linked_users=LinkedAccount.objects.filter(primary_user=profile).all()
                
                notificationtokens=[]
                for i in all_linked_users:
                    if i.linked_user.notification_token:
                        notificationtokens.append(i.linked_user.notification_token) 
                
                if notificationtokens:
                    message_body = f"MLP ID {user.mlp_id} visited your profile. They might be interested. Check their profile"
                    message = messaging.MulticastMessage(
                    tokens=notificationtokens,  # List of FCM registration tokens
                    notification=messaging.Notification(
                        title="Profile Visited",
                        body=message_body,
                       ),
                       data = custom_data 
                    )
                    messaging.send_multicast(message)

                      
                    # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title="Profile Visited",message_body=message_body,data_message=custom_data)
            response['status_code']=200
            response['message'] = 'Contact viewed updated successfully'
            return response
        else:
            response['status_code']=404
            response['message'] = 'User not found'
            return response
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response