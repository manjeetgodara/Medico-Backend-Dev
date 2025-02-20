import json
import logging
import os
from celery import shared_task
from django.apps import apps
from datetime import datetime, timedelta, timezone
from django.utils import timezone
from django.db.models import Q
import requests
from misc.models import ChangeLog
from notification_settings.models import NotificationSettings
from promotions.models import Promotions
from transactions.models import TransactionEntity
from users.models import BlockedUsers, Caste, ConnectionList, ContactViewed, DeleteProfile, Expertise, Graduation, Intrest, Languages, LinkedAccount, MaritalStatus, MotherTongue, Notifications, PartnerExpertisePreference, PartnerGraduationPreference, PartnerMaritalStatusPreference, PartnerPGPreference, PartnerReligionPreference, PartnerSpecializationPreference, PostGraduation, ProfileView, Religion, ReportUsers, SavedUser, Siblings, Specialization, SubCaste, Subscription, SuccessStory, User, UserPostGraduation, UserSubscription
from users.utils import connect
from django.db.models import Count
from pyfcm import FCMNotification
from firebase_admin import messaging
from rest_framework.views import APIView



logger = logging.getLogger("error_logger")
# push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))

logger = logging.getLogger("error_logger")

redis_client = connect()

#Service for change data sync
def get_change_log_data():
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:

        EXCLUDED_SUBSCRIPTIONS = [
            "Gold Old",
            "Gold Plus Web",
            "Premium Old",
            "Super Value",
            "Diamond",
            "Premium Plus Web",
            "Super Saver",
            "Classic",
            "Platinum Old",
            "Silver Old"
        ]
        thirty_minutes_ago = timezone.now() - timedelta(minutes=30)

        # # Query ChangeLog model to fetch changes from the last 30 minutes
        recent_changes = ChangeLog.objects.filter(created_at__gte=thirty_minutes_ago)
       # recent_changes = ChangeLog.objects.all()
        # Separate changes into different lists based on action type
        create_changes = []
        update_changes = []
        delete_changes = []
        seen_mlp_ids = set()

        for change in recent_changes:
            fields = change.fields
            if 'hobbies' in fields and isinstance(fields['hobbies'], str):
                fields['hobbies'] = json.loads(fields['hobbies'])
            if 'video' in fields and isinstance(fields['video'], str):
                fields['video'] = json.loads(fields['video'])
            if 'other_hobbies' in fields and isinstance(fields['other_hobbies'],str):
                fields['other_hobbies'] = json.loads(fields['other_hobbies']) 
            if 'profile_pictures' in fields and isinstance(fields['profile_pictures'],str):
                fields['profile_pictures'] = json.loads(fields['profile_pictures'])
            if 'family_photos' in fields and isinstance(fields['family_photos'],str):
                fields['family_photos'] = json.loads(fields['family_photos']) 
            if 'profession' in fields and isinstance(fields['profession'],str):
                fields['profession'] = json.loads(fields['profession'])               
            change_data = {
                'action': change.action,
                'app_name': change.app_name,
                'model_name': change.model_name,
                'fields': change.fields
            }

            # Check for excluded subscription names for UserSubscription model
            if change.model_name == 'usersubscription':
                subscription_name = fields.get('subscription_name')
                if subscription_name in EXCLUDED_SUBSCRIPTIONS:
                    continue  # Skip this change

            # Check for subscription range for TransactionEntity model
            if change.model_name == 'transactionentity':
                subscription_value = fields.get('subscription')
                if subscription_value is not None and 8 <= subscription_value <= 17:
                    continue  # Skip this change
                
            if change.action == 'create':
                mlp_id = change.fields.get('mlp_id')
                if change.model_name == 'user' and mlp_id:
                    if mlp_id not in seen_mlp_ids:
                        seen_mlp_ids.add(mlp_id)
                        create_changes.append(change_data)
                else:
                    create_changes.append(change_data)
            elif change.action == 'update':
                update_changes.append(change_data)
            elif change.action == 'delete':
                delete_changes.append(change_data)

        response['status_code'] = 200
        response['message'] = "Data For Sync Retrieved"
        response['changes'] = {
            'create': create_changes,
            'update': update_changes,
            'delete': delete_changes
        }
        return response
    except Exception as e:
        response['status_code'] = 409
        response['error'] = str(e)
        return response
    

def fetch_update_data_migrate():
    api_url= "https://www.medicolifepartner.com/index.php/api/migrate_registration"


    # Fetch data from the API
    api_response = requests.get(api_url)
    
    data = api_response.json()
    
    for temp_data in data['changes']['create']['registration']:
        #print(item)
        item1 = temp_data['fields']
        for item in item1:
            print("mlp_id:",f"MLP00{item['id']}")
            mlp_id = f"MLP00{item['id']}"  

            user_exists = User.objects.filter(mlp_id=mlp_id,is_active = True,is_wrong=False).exists()
            if user_exists:
                # if item['country_c'] is not None:
                #     country_code = item['country_c'].replace("+", "")  
                #     mobile_number = f"{country_code}{item['mobile']}"
                # else:
                #     mobile_number = f"91{item['mobile']}" 


                # #Country name  
                # country_name = item['country_name']
                # if country_name == "USA":
                #     country_name = "United States"
                # elif country_name == "UAE":
                #     country_name = "United Arab Emirates"
                # elif country_name == "UK":
                #     country_name = "United Kingdom"        
                    
                
                # For Profession
                profession_obj = []
                temp_professions = item.get('profession', '')  
                if temp_professions: 
                    professions = temp_professions.split(',')  
                    for profession in professions:
                        values=profession.strip().capitalize()
                        profession_obj.append(values)      
                
                #For physical status
                physical_status = None
                if item['physically_challenged'] is not None:
                    if item['physically_challenged'] == "Normal" :
                        physical_status = "Normal"
                    elif item['physically_challenged'] == "Physically Challenged" :
                        physical_status = "Disabled" 
                
                #For family residence
                fath_res = None
                if item['father_owned_residence'] is not None:
                    if item['father_owned_residence'] == "owned" or item['father_owned_residence'] == "Owned":
                       fath_res = "Owned"
                    elif item['father_owned_residence'] == "rented" or item['father_owned_residence'] == "Rented":
                        fath_res = "Rented"  

                #For family car
                family_car = None
                if item['car'] is not None:
                    if item['car'] == "Nil":
                        family_car = "No"
                    elif item['car'] == "Own Car < 10 lacs" or item['car'] == "Own Car > 10 lacs":
                        family_car =item['car']    
                
                  #For family_environment
                family_environment = None
                if item['family_env'] is not None:
                    if item['family_env'] in ["Semi Orthodox","Modern" , "Orthodox"]:
                        family_environment = item['family_env']
                
                #For body clock
                body_clock = None
                if item['wakes_up_from'] is not None:
                    if item['wakes_up_from'] == "Wakes up early":
                        body_clock = "Wakes Up Early"
                    elif item['wakes_up_from'] == "Stays awake till late night":
                        body_clock = "Stays Till Midnight"    

                #for kids
                kids_choice = None
                if item['kids'] is not None:
                    if item['kids'] == "Flexible":
                        kids_choice = "Flexible"
                    if item['kids'] == "1":
                        kids_choice = "1 kid"
                    if item['kids'] == "2":
                        kids_choice = "2 kid"
                    if item['kids'] == "No Kids":
                        kids_choice = "No Kids"            


                manglik_value = 1 if item['manglik'] == "Yes" else 0 if item['manglik'] == "No" else -1 
                
                # For SubCaste
                sub_caste=None
                subcaste=SubCaste.objects.filter(name__iexact=item['sub_caste'])
                if subcaste.exists():
                    sub_caste = subcaste.first()

                # For Marital State  
                marital_status_obj = None
                if item['second_marriage'] == "Never Married":
                    marital_status_name = "Bachelor"
                    marital_status = MaritalStatus.objects.filter(name__iexact=marital_status_name)
                    if marital_status:
                        marital_status_obj = marital_status.first()
                else:
                    marital_status = MaritalStatus.objects.filter(name__iexact=item['second_marriage'])
                    if marital_status:
                        marital_status_obj = marital_status.first()       

                #For completed post grad
                completed_post_grad =False
                graduation_obj = Graduation.objects.filter(name__iexact=item["education_field"]).first()

                post_ed_names = [ele.strip() for ele in item['post_education_field'].split(',')] 
            
                for ed_name in post_ed_names:
                    if ed_name == "MCh":
                        ed_name = "Mch"
                    elif ed_name == "MD / MS Ayurveda":
                        ed_name = "MD/MS Ayurveda"

                    post_grad_objects = PostGraduation.objects.filter(name__iexact=ed_name)    

                    if post_grad_objects.exists():
                        print(post_grad_objects)
                        completed_post_grad = True
                        break    

                if not post_grad_objects:
                    completed_post_grad = False
    
                # can_upgrade_subscription = -1 
                # if item['status'] == "Active":
                #     # subscription_start_date = item['subscription_start_date']
                #     # subscription_end_date = item['subscription_end_date']
                #     subscription_start_date = datetime.strptime(item['subscription_start_date'], "%Y-%m-%d %H:%M:%S")
                #     subscription_end_date = datetime.strptime(item['subscription_end_date'], "%Y-%m-%d %H:%M:%S")


                #     # Calculate the one-month window after subscription creation
                #     upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                #     # Check if subscription is active
                #     if subscription_end_date >= datetime.now():
                #         # Check if within the upgrade window
                #         if datetime.now() <= upgrade_window_end_date:
                #             can_upgrade_subscription = 1
                #         else:
                #             can_upgrade_subscription = 0
                #     else:
                #         can_upgrade_subscription = -1

                profile_pictures = []
                if item['profile_pic'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic'].strip()}")
                if item['profile_pic2'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic2'].strip()}")
                if item['profile_pic3'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic3'].strip()}")
                if item['profile_pic4'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic4'].strip()}")
                if item['profile_pic5'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic5'].strip()}")
                if item['profile_pic6'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic6'].strip()}")
                if item['profile_pic7'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic7'].strip()}")
                if item['profile_pic8'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic8'].strip()}")
                if item['profile_pic9'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic9'].strip()}")
                if item['profile_pic10'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic10'].strip()}")
            
                # For specialization
                specialization = None
                specializations = Specialization.objects.filter(name__iexact=item['specialization'])
                if specializations.exists():
                    specialization = specializations.first()  
                    
                # For mother tongue
                spoken_languages = item['spoken_language'].split(',')
                mother_tongues = []
                for lang in spoken_languages:
                    lang = lang.strip()
                    if lang:
                        mother_tongue = MotherTongue.objects.filter(name__iexact=lang).first()
                        if mother_tongue:
                            mother_tongues.append(mother_tongue)
                
                dob = item['date_of_birth']
                if dob and dob != '0000-00-00':
                    try:
                        dob = datetime.strptime(dob, '%Y-%m-%d').date()
                    except ValueError:
                        dob = None  # Invalid date, set to None
                else:
                    dob = None 
                
                
                grad_status = None
                if item.get('education_field_status') == 'complete' or item.get('education_field_status') == 'completed':
                    grad_status = 'Completed'
                elif item.get('education_field_status') == 'ongoing' :
                    grad_status = 'Ongoing' 

                post_grad_status = None
                if item.get('post_education_field_status') == 'complete' or item.get('post_education_field_status') == 'completed':
                    post_grad_status = 'Completed'
                elif item.get('post_education_field_status') == 'ongoing' :
                    post_grad_status = 'Ongoing' 
        
                # For Hobbies
                hobbies = []
                if item['hobbies'] and ',' in item['hobbies']:
                    hobbies = [h.strip() for h in item['hobbies'].split(',') if h.strip()]


                religion_obj= Religion.objects.filter(name__iexact=item['religion']).first()
                expertise_ob = Expertise.objects.filter(name__iexact=item['medicine']).first() 
                mandatory_questions_completed = True
                if (
                    item['status'] == "Pending" or
                    item['createby'] == '' or
                    item['createby'] not in ["candidate", "family"] or
                    religion_obj is None or
                    item["candidates_name"] == "" or
                    # item.get("date_of_birth") is None or
                    dob is None or
                    item['sex'] not in ["Male", "Female"] or
                    len(profile_pictures) == 0 or
                    graduation_obj is None or
                    expertise_ob is None or
                    item['email_id'] is None or
                    item['password'] is None
                ):
                    mandatory_questions_completed = False      
                
                new_user=User.objects.filter(mlp_id=mlp_id).update(
                name=item['candidates_name'],
                email=item['email_id'],
                password=item['password'],
                # mobile_number=mobile_number,
                manglik=manglik_value,
                gender='m' if item['sex'] == "Male" else 'f',
                weight = item['weight'] if item['weight'] is not None else None,
                dob=dob,
                # body_build = item['body_build'] if item['body_build'] is not None else None,
                # complexion = item['complexion'] if item['complexion'] is not None else None,
                blood_group = item['blood_group'] if item['blood_group'] is not None else None,
                # disease_history = item['disease'] if item['disease'] is not None else None,
                schooling_details = item['schooling'] if item['schooling'] is not None else None,
                facebook_profile = item['facebook_link'] if item['facebook_link'] is not None else None,
                linkedin_profile = item['linkedin'] if item['linkedin'] is not None else None,
                birth_location=item['birth_location'],
                height=int(item['height_ft'])*12 + int(item['height_inch']),
                # salary=item['salary'],
                caste=item['caste'] if item['caste'] is not None else None, 
                sub_caste=sub_caste,
                marital_status = marital_status_obj,
                hobbies = json.dumps(["Others"]) if hobbies not in [None, '', []] else json.dumps([]),
                other_hobbies = json.dumps(hobbies),
                profile_pictures = json.dumps(profile_pictures),
                city = item['city'] if  item['city'] != "Please Select State" or item['city'] != "Select City" or item['city'] != "Select State" or item['city'] != "Please+Select+State" else None,
                # state = item['state_name'],
                # country = country_name, 
                horoscope_matching=item['horoscope_matching'] if item['horoscope_matching'] in ["Yes","No"] else None,
                future_aspirations=item['candi_future_aspiration'],
                about=item['candi_describing_myself'],
                # is_active=False if item['status'] =='Remove' or item['status']=='Wrong' or item['status'] == "Pending" else True,
                # time_birth = str(item['time_of_birth']) if item['time_of_birth'] != "00:00:00" else None,
                religion = Religion.objects.filter(name__iexact=item['religion']).first(),
                physical_status = physical_status,
                # eyesight = item['eye_sight'] if item['eye_sight'] is not None else None,
                city_parents = item['father_resided_city'] if item['father_resided_city'] is not None else None,
                # residence =  item['res_address'] if item['res_address'] is not None else None,
                family_house = fath_res,
                family_car = family_car ,
                family_environment = family_environment,
                kids_choice = kids_choice,
                body_clock = body_clock,
                profession_description = item['profession_details'] if item['profession_details'] is not None else None,
                profession = json.dumps(profession_obj),
                # is_primary_account=True,
                # sibling = None,
                # whatsapp_number = None,
                specialization = specialization,
                registration_number = item['medical_registration_number'] if item['medical_registration_number'] is not None else None,
                profile_createdby ="Parent" if item['createby'] == "family" else "Candidate",
                mother_name = item['mother_name'] if item['mother_name'] is not None else None,
                father_name = item['father_name'] if item['father_name'] is not None else None,
                father_occupation = item['father_profession'] if item['father_profession'] is not None else None,
                mother_occupation = item['mother_profession'] if item['mother_profession'] is not None else None,
                father_education = item['father_education'] if item['father_education'] is not None else None,
                mother_education = item['mother_education'] if item['mother_education'] is not None else None,
                #  nature = item['nature'] if item['nature'] is not None else None,
                # can_upgrade_subscription=can_upgrade_subscription,
                graduation_obj=graduation_obj,
                completed_post_grad=completed_post_grad,
                mandatory_questions_completed=mandatory_questions_completed,
                graduation_institute = item.get('graduation_institute'),
                post_graduation_institute = item.get('post_graduation_institute'),
                post_graduation_status = post_grad_status,
                graduation_status = grad_status,
                )
                print("new user",f"MLP00{item['id']}")
                new_user = User.objects.filter(mlp_id=f"MLP00{item['id']}").first()
                print(new_user)
                new_user.languages.set(Languages.objects.filter(name__iexact=item['language']))
                new_user.mother_tongue.set(mother_tongues)

                #For User Post Graduation
                unique_post_grad_objects = set()

                for ed_name in post_ed_names:
                    if ed_name == "MCh":
                        ed_name = "Mch"
                    elif ed_name == "MD / MS Ayurveda":
                        ed_name = "MD/MS Ayurveda"

            
                    post_grad_object = PostGraduation.objects.filter(name__iexact=ed_name).first()

                    if post_grad_object:
                        unique_post_grad_objects.add(post_grad_object)

                for pg in unique_post_grad_objects:
                    user_post_grad, created = UserPostGraduation.objects.update_or_create(
                        user=new_user,
                        post_graduation=pg
                    ) 

                # For Siblings
                # if all(item.get(key) not in [None, ''] for key in ['candi_bro_name1', 'candi_bro_education1', 'candi_bro_profession1', 'candi_bro_marital_status1']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Male', sibling_name=item['candi_bro_name1'], sibling_education=item['candi_bro_education1'], sibling_marital_status =item['candi_bro_marital_status1'] ,   sibling_profession = item['candi_bro_profession1'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_bro_name2', 'candi_bro_education2', 'candi_bro_profession2', 'candi_bro_marital_status2']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Male', sibling_name=item['candi_bro_name2'], sibling_education=item['candi_bro_education2'], sibling_marital_status =item['candi_bro_marital_status2'] ,   sibling_profession = item['candi_bro_profession2'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_bro_name3', 'candi_bro_education3', 'candi_bro_profession3', 'candi_bro_marital_status3']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Male', sibling_name=item['candi_bro_name3'], sibling_education=item['candi_bro_education3'], sibling_marital_status =item['candi_bro_marital_status3'] ,   sibling_profession = item['candi_bro_profession3'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_bro_name4', 'candi_bro_education4', 'candi_bro_profession4', 'candi_bro_marital_status4']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Male', sibling_name=item['candi_bro_name4'], sibling_education=item['candi_bro_education4'], sibling_marital_status =item['candi_bro_marital_status4'] ,   sibling_profession = item['candi_bro_profession4'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_bro_name5', 'candi_bro_education5', 'candi_bro_profession5', 'candi_bro_marital_status5']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Male', sibling_name=item['candi_bro_name5'], sibling_education=item['candi_bro_education5'], sibling_marital_status =item['candi_bro_marital_status5'] ,   sibling_profession = item['candi_bro_profession5'])


                # if all(item.get(key) not in [None, ''] for key in ['candi_sis_name1', 'candi_sis_education1', 'candi_sis_profession1', 'candi_sis_marital_status1']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Female', sibling_name=item['candi_sis_name1'], sibling_education=item['candi_sis_education1'], sibling_marital_status =item['candi_sis_marital_status1'] ,   sibling_profession = item['candi_sis_profession1'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_sis_name2', 'candi_sis_education2', 'candi_sis_profession2', 'candi_sis_marital_status2']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Female', sibling_name=item['candi_sis_name2'], sibling_education=item['candi_sis_education2'], sibling_marital_status =item['candi_sis_marital_status2'] ,   sibling_profession = item['candi_sis_profession2'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_sis_name3', 'candi_sis_education3', 'candi_sis_profession3', 'candi_sis_marital_status3']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Female', sibling_name=item['candi_sis_name3'], sibling_education=item['candi_sis_education3'], sibling_marital_status =item['candi_sis_marital_status3'] ,   sibling_profession = item['candi_sis_profession3'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_sis_name4', 'candi_sis_education4', 'candi_sis_profession4', 'candi_sis_marital_status4']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Female', sibling_name=item['candi_sis_name4'], sibling_education=item['candi_sis_education4'], sibling_marital_status =item['candi_sis_marital_status4'] ,   sibling_profession = item['candi_sis_profession4'])
                # if all(item.get(key) not in [None, ''] for key in ['candi_sis_name5', 'candi_sis_education5', 'candi_sis_profession5', 'candi_sis_marital_status5']):
                #     Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='Female', sibling_name=item['candi_sis_name5'], sibling_education=item['candi_sis_education5'], sibling_marital_status =item['candi_sis_marital_status5'] ,   sibling_profession = item['candi_sis_profession5'])
                
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name1', 'candi_bro_education1', 'candi_bro_profession1', 'candi_bro_marital_status1']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name2', 'candi_bro_education2', 'candi_bro_profession2', 'candi_bro_marital_status2']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name2'][:100], sibling_education=item['candi_bro_education2'][:100], sibling_marital_status =item['candi_bro_marital_status2'][:30] ,   sibling_profession = item['candi_bro_profession2'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name3', 'candi_bro_education3', 'candi_bro_profession3', 'candi_bro_marital_status3']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name3'][:100], sibling_education=item['candi_bro_education3'][:100], sibling_marital_status =item['candi_bro_marital_status3'][:30] ,   sibling_profession = item['candi_bro_profession3'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name4', 'candi_bro_education4', 'candi_bro_profession4', 'candi_bro_marital_status4']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name4'][:100], sibling_education=item['candi_bro_education4'][:100], sibling_marital_status =item['candi_bro_marital_status4'][:30] ,   sibling_profession = item['candi_bro_profession4'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name5', 'candi_bro_education5', 'candi_bro_profession5', 'candi_bro_marital_status5']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name5'][:100], sibling_education=item['candi_bro_education5'][:100], sibling_marital_status =item['candi_bro_marital_status5'][:30] ,   sibling_profession = item['candi_bro_profession5'][:100])


                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name1', 'candi_sis_education1', 'candi_sis_profession1', 'candi_sis_marital_status1']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name2', 'candi_sis_education2', 'candi_sis_profession2', 'candi_sis_marital_status2']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name2'][:100], sibling_education=item['candi_sis_education2'][:100], sibling_marital_status =item['candi_sis_marital_status2'][:30] ,   sibling_profession = item['candi_sis_profession2'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name3', 'candi_sis_education3', 'candi_sis_profession3', 'candi_sis_marital_status3']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name3'][:100], sibling_education=item['candi_sis_education3'][:100], sibling_marital_status =item['candi_sis_marital_status3'][:30] ,   sibling_profession = item['candi_sis_profession3'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name4', 'candi_sis_education4', 'candi_sis_profession4', 'candi_sis_marital_status4']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name4'][:100], sibling_education=item['candi_sis_education4'][:100], sibling_marital_status =item['candi_sis_marital_status4'][:30] ,   sibling_profession = item['candi_sis_profession4'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name5', 'candi_sis_education5', 'candi_sis_profession5', 'candi_sis_marital_status5']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name5'][:100], sibling_education=item['candi_sis_education5'][:100], sibling_marital_status =item['candi_sis_marital_status5'][:30] ,   sibling_profession = item['candi_sis_profession5'][:100])

                sibling = Siblings.objects.filter(user=new_user).exists()
                if sibling :
                    new_user.sibling = 1
                new_user.save()
                print("sibling data updated successfully")     
                
                # For Notification settings
                # name = None
                # phone= None
                # photo= None
                # salary = None
                # email = None
                # if new_user.email:
                #     email = new_user.email
                # if item["privacy_name"] == "interest_accepted":
                #     name = "interests"
                # if item["privacy_name"] == "to_all_subscribe":
                #     name = "paid"     
                # if item["privacy_phone"] == "interest_accepted":
                #     phone = "interests"
                # if item["privacy_phone"] == "to_all_subscribe":
                #     phone = "paid"    
                # if item["privacy_photo"] == "to_all":
                #     photo = "all" 
                # if item["privacy_photo"] == "to_all_subscribe":
                #     photo = "paid"    
                # if item["privacy_photo"] == "interest_accepted":
                #     photo= "interests"
                # if item["privacy_salary"] == "to_all_subscribe" or item["privacy_salary"] == "to_all_subscribe_registered":
                #     salary = "paid"    
                # if item["privacy_salary"] == "interest_accepted":
                #     salary= "interests"
                # NotificationSettings.objects.filter(user=new_user).update(user=new_user,email_notifications="",name=name,phone=phone,photo=photo, salary=salary, email=email)
                # print("new user notification settings added successfully")

            else:
                print("User not exists in db")

    print("after adding user") 

            
            


def fetch_and_store_data_migrate():
    api_url= "https://www.medicolifepartner.com/index.php/api/migrate_registration"


    # Fetch data from the API
    api_response = requests.get(api_url)
    
    data = api_response.json()
    
    for temp_data in data['changes']['create']['registration']:
        #print(item)
        item1 = temp_data['fields']
        for item in item1:
            print("mlp_id:",f"MLP00{item['id']}")
            
            #For Mobile Number 
            if item['country_c'] is not None:
                country_code = item['country_c'].replace("+", "")  
                mobile_number = f"{country_code}{item['mobile']}"
            else:
                mobile_number = f"91{item['mobile']}" 


            # For Profession
            profession_obj = []
            temp_professions = item.get('profession', '')  
            if temp_professions: 
                professions = temp_professions.split(',')  
                for profession in professions:
                    values=profession.strip().capitalize()
                    profession_obj.append(values)      

            # For manglik
            manglik_value = 1 if item['manglik'] == "Yes" else 0 if item['manglik'] == "No" else -1 
            
            #For physical status
            physical_status = None
            if item['physically_challenged'] is not None:
                if item['physically_challenged'] == "Normal" :
                    physical_status = "Normal"
                elif item['physically_challenged'] == "Physically Challenged" :
                    physical_status = "Disabled"

             #For family residence
            fath_res = None
            if item['father_owned_residence'] is not None:
                if item['father_owned_residence'] == "owned" or item['father_owned_residence'] == "Owned":
                    fath_res = "Owned"
                elif item['father_owned_residence'] == "rented" or item['father_owned_residence'] == "Rented":
                    fath_res = "Rented"  
                    
             #For family car
            # family_car = None
            # if item['car'] is not None:
            #     if item['car'] == "Nil":
            #         family_car = "No"
            #     elif item['car'] == "Own Car < 10 lacs" or item['car'] == "Own Car > 10 lacs":
            #         family_car =item['car']             
            
            # #For family_environment
            # family_environment = None
            # if item['family_env'] is not None:
            #     if item['family_env'] in ["Semi Orthodox","Modern" , "Orthodox"]:
            #         family_environment = item['family_env']
            
            # #For body clock
            # body_clock = None
            # if item['wakes_up_from'] is not None:
            #     if item['wakes_up_from'] == "Wakes up early":
            #         body_clock = "Wakes Up Early"
            #     elif item['wakes_up_from'] == "Stays awake till late night":
            #         body_clock = "Stays Till Midnight"    

            # #for kids
            # kids_choice = None
            # if item['kids'] is not None:
            #     if item['kids'] == "Flexible":
            #         kids_choice = "Flexible"
            #     if item['kids'] == "1":
            #         kids_choice = "1 kid"
            #     if item['kids'] == "2":
            #         kids_choice = "2 kid"
            #     if item['kids'] == "No Kids":
            #         kids_choice = "No Kids"            


            # For SubCaste
            sub_caste=None
            subcaste=SubCaste.objects.filter(name__iexact=item['sub_caste'])
            if subcaste.exists():
                sub_caste = subcaste.first()

            
            # For Marital State  
            marital_status_obj = None
            if item['second_marriage'] == "Never Married":
                marital_status_name = "Bachelor"
                marital_status = MaritalStatus.objects.filter(name__iexact=marital_status_name)
                if marital_status:
                    marital_status_obj = marital_status.first()
            else:
                marital_status = MaritalStatus.objects.filter(name__iexact=item['second_marriage'])
                if marital_status:
                    marital_status_obj = marital_status.first()       

            #For completed post grad
            completed_post_grad =False
            graduation_obj = Graduation.objects.filter(name__iexact=item["education_field"]).first()
            print("graduation",graduation_obj)
            post_ed_names = [ele.strip() for ele in item['post_education_field'].split(',')] 
            
            for ed_name in post_ed_names:
                if ed_name == "MCh":
                    ed_name = "Mch"
                elif ed_name == "MD / MS Ayurveda":
                    ed_name = "MD/MS Ayurveda"

                post_grad_objects = PostGraduation.objects.filter(name__iexact=ed_name)    
                
                if post_grad_objects.exists():
                    print(post_grad_objects)
                    completed_post_grad = True
                    break    
            print("post_grad",post_grad_objects) 
            if not post_grad_objects:
                    completed_post_grad = False

            print("before subscription")     
            can_upgrade_subscription = -1 
            if item['status'] == "Active":
                # subscription_start_date = item['subscription_start_date']
                # subscription_end_date = item['subscription_end_date']
                if item['subscription_start_date'] != "0000-00-00 00:00:00" and  item['subscription_end_date'] != "0000-00-00 00:00:00":
                    subscription_start_date = datetime.strptime(item['subscription_start_date'], "%Y-%m-%d %H:%M:%S")
                    subscription_end_date = datetime.strptime(item['subscription_end_date'], "%Y-%m-%d %H:%M:%S")
                    
                    print("subscription_start",subscription_start_date)
                    print("subscription_end",subscription_end_date)

                    # Calculate the one-month window after subscription creation
                    upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                    # Check if subscription is active
                    if subscription_end_date >= datetime.now():
                        # Check if within the upgrade window
                        if datetime.now() <= upgrade_window_end_date:
                            can_upgrade_subscription = 1
                        else:
                            can_upgrade_subscription = 0
                    else:
                        can_upgrade_subscription = -1
                else:
                    can_upgrade_subscription = -1        
            print("after subscription")

            profile_pictures = []
            if item['profile_pic'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic'].strip()}")
            if item['profile_pic2'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic2'].strip()}")
            if item['profile_pic3'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic3'].strip()}")
            if item['profile_pic4'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic4'].strip()}")
            if item['profile_pic5'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic5'].strip()}")
            if item['profile_pic6'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic6'].strip()}")
            if item['profile_pic7'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic7'].strip()}")
            if item['profile_pic8'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic8'].strip()}")
            if item['profile_pic9'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic9'].strip()}")
            if item['profile_pic10'].strip():
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic10'].strip()}")
            
            print(profile_pictures)
            # For specialization
            specialization = None
            specializations = Specialization.objects.filter(name__iexact=item['specialization'])
            if specializations.exists():
                specialization = specializations.first()  
                
            # For mother tongue
            spoken_languages = item['spoken_language'].split(',')
            mother_tongues = []
            for lang in spoken_languages:
                lang = lang.strip()
                if lang:
                    mother_tongue = MotherTongue.objects.filter(name__iexact=lang).first()
                    if mother_tongue:
                        mother_tongues.append(mother_tongue)
            
            # video = []
            # if item['video'] != "":
            #     video.append(item['video'])
            
            grad_status = None
            if item.get('education_field_status') == 'complete' or item.get('education_field_status') == 'completed':
                grad_status = 'Completed'
            elif item.get('education_field_status') == 'ongoing' :
                grad_status = 'Ongoing' 

            post_grad_status = None
            if item.get('post_education_field_status') == 'complete' or item.get('post_education_field_status') == 'completed':
                post_grad_status = 'Completed'
            elif item.get('post_education_field_status') == 'ongoing' :
                post_grad_status = 'Ongoing' 


            # For Hobbies
            hobbies = []
            if item['hobbies'] and ',' in item['hobbies']:
                hobbies = [h.strip() for h in item['hobbies'].split(',') if h.strip()]

            religion_obj= Religion.objects.filter(name__iexact=item['religion']).first()
            expertise_ob = Expertise.objects.filter(name__iexact=item['medicine']).first() 
            mandatory_questions_completed = True
            if (
                item['status'] == "Pending" or
                item['createby'] == '' or
                item['createby'] not in ["candidate", "family"] or
                religion_obj is None or
                item["candidates_name"] == "" or
                item.get("date_of_birth") is None or
                item['date_of_birth'] == "0000-00-00" or
                item['sex'] not in ["Male", "Female"] or
                len(profile_pictures) == 0 or
                graduation_obj is None or
                expertise_ob is None or
                item['email_id'] is None or
                item['password'] is None
            ):
                mandatory_questions_completed = False      

            existing_user = User.objects.filter(mlp_id=f"MLP00{item['id']}").first()
            if existing_user:
                print(f"User with mlp_id MLP00{item['id']} already exists.")
                continue


            print("before creating user")
            new_user=User.objects.create(
            mlp_id= f"MLP00{item['id']}",
            name=item['candidates_name'],
            email=item['email_id'],
            password=item['password'],
            mobile_number=mobile_number,
            manglik=manglik_value,
            gender='m' if item['sex'] == "Male" else 'f',
            weight = item['weight'] if item['weight'] is not None else 0,
            dob=item['date_of_birth'] if item['date_of_birth']!="0000-00-00" else None,
            time_birth = str(item['time_of_birth']) if item['time_of_birth'] != "00:00:00" else None,
            # body_build = item['body_build'] if item['body_build'] is not None else None,
            # complexion = item['complexion'] if item['complexion'] is not None else None,
            blood_group = item['blood_group'] if item['blood_group'] is not None else None,
            # disease_history = item['disease'] if item['disease'] is not None else None,
            schooling_details = item['schooling'] if item['schooling'] is not None else None,
            facebook_profile = item['facebook_link'] if item['facebook_link'] is not None else None,
            linkedin_profile = item['linkedin'] if item['linkedin'] is not None else None,
            birth_location=item['birth_location'],
            height=int(item['height_ft'])*12 + int(item['height_inch']),
            # salary=item['salary'],
            caste=item['caste'] if item['caste'] is not None else None, 
            sub_caste=sub_caste,
            marital_status = marital_status_obj,
            hobbies = json.dumps(["Others"]) if hobbies not in [None, '', []] else json.dumps([]),
            other_hobbies = json.dumps(hobbies),
            profile_pictures = json.dumps(profile_pictures),
            city = item['city'] if  item['city'] != "Please Select State"  or item['city'] != "Select City" or item['city'] != "Select State" or item['city'] != "Please+Select+State" else None,
            # state = item['state'],
            # country = item['country'], 
            horoscope_matching=item['horoscope_matching'] if item['horoscope_matching'] in ["Yes","No"] else None,
            future_aspirations=item['candi_future_aspiration'],
            about=item['candi_describing_myself'],
            is_active=False if item['status'] =='Remove'  else True,
            is_wrong = True if item['status']=='Wrong' else False,
            religion = Religion.objects.filter(name__iexact=item['religion']).first(),
            physical_status = physical_status,
            #  eyesight = item['eye_sight'] if item['eye_sight'] is not None else None,
            city_parents = item['father_resided_city'] if item['father_resided_city'] is not None else None,
            # residence =  item['res_address'] if item['res_address'] is not None else None,
            family_house = fath_res,
            # family_car = family_car,
            # family_environment = family_environment,
            # kids_choice = kids_choice,
            # body_clock=body_clock,
            profession_description = item['profession_details'] if item['profession_details'] is not None else None,
            profession = json.dumps(profession_obj),
            is_primary_account=True,
            # sibling = None,
            whatsapp_number = None,
            specialization = specialization,
            registration_number = item['medical_registration_number'] if item['medical_registration_number'] is not None else None,
            profile_createdby ="Parent" if item['createby'] == "family" else "Candidate",
            mother_name = item['mother_name'] if item['mother_name'] is not None else None,
            father_name = item['father_name'] if item['father_name'] is not None else None,
            father_occupation = item['father_profession'] if item['father_profession'] is not None else None,
            mother_occupation = item['mother_profession'] if item['mother_profession'] is not None else None,
            father_education = item['father_education'] if item['father_education'] is not None else None,
            mother_education = item['mother_education'] if item['mother_education'] is not None else None,
            # nature = item['nature'] if item['nature'] is not None else None,
            can_upgrade_subscription=can_upgrade_subscription,
            graduation_obj=graduation_obj,
            completed_post_grad=completed_post_grad,
            mandatory_questions_completed=mandatory_questions_completed,
            graduation_institute = item.get('graduation_institute'),
            post_graduation_institute = item.get('post_graduation_institute'),
            post_graduation_status = post_grad_status,
            graduation_status = grad_status ,
            )
            print("Here")
            new_user.languages.set(Languages.objects.filter(name__iexact=item['language']))
            new_user.mother_tongue.set(mother_tongues)

            # For User Post Graduation
            unique_post_grad_objects = set()

            for ed_name in post_ed_names:
                if ed_name == "MCh":
                    ed_name = "Mch"
                elif ed_name == "MD / MS Ayurveda":
                    ed_name = "MD/MS Ayurveda"

        
                post_grad_object = PostGraduation.objects.filter(name__iexact=ed_name).first()

                if post_grad_object:
                    unique_post_grad_objects.add(post_grad_object)

            for pg in unique_post_grad_objects:
                
                UserPostGraduation.objects.create(user=new_user, post_graduation=pg)

            print("user basic data saved successfully")

             #For siblings
            if all(item.get(key) not in [None, ''] for key in ['candi_bro_name1', 'candi_bro_education1', 'candi_bro_profession1', 'candi_bro_marital_status1']):
                Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_bro_name2', 'candi_bro_education2', 'candi_bro_profession2', 'candi_bro_marital_status2']):
                Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name2'][:100], sibling_education=item['candi_bro_education2'][:100], sibling_marital_status =item['candi_bro_marital_status2'][:30] ,   sibling_profession = item['candi_bro_profession2'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_bro_name3', 'candi_bro_education3', 'candi_bro_profession3', 'candi_bro_marital_status3']):
                Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name3'][:100], sibling_education=item['candi_bro_education3'][:100], sibling_marital_status =item['candi_bro_marital_status3'][:30] ,   sibling_profession = item['candi_bro_profession3'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_bro_name4', 'candi_bro_education4', 'candi_bro_profession4', 'candi_bro_marital_status4']):
                Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name4'][:100], sibling_education=item['candi_bro_education4'][:100], sibling_marital_status =item['candi_bro_marital_status4'][:30] ,   sibling_profession = item['candi_bro_profession4'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_bro_name5', 'candi_bro_education5', 'candi_bro_profession5', 'candi_bro_marital_status5']):
                Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name5'][:100], sibling_education=item['candi_bro_education5'][:100], sibling_marital_status =item['candi_bro_marital_status5'][:30] ,   sibling_profession = item['candi_bro_profession5'][:100])


            if all(item.get(key) not in [None, ''] for key in ['candi_sis_name1', 'candi_sis_education1', 'candi_sis_profession1', 'candi_sis_marital_status1']):
                Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_sis_name2', 'candi_sis_education2', 'candi_sis_profession2', 'candi_sis_marital_status2']):
                Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name2'][:100], sibling_education=item['candi_sis_education2'][:100], sibling_marital_status =item['candi_sis_marital_status2'][:30] ,   sibling_profession = item['candi_sis_profession2'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_sis_name3', 'candi_sis_education3', 'candi_sis_profession3', 'candi_sis_marital_status3']):
                Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name3'][:100], sibling_education=item['candi_sis_education3'][:100], sibling_marital_status =item['candi_sis_marital_status3'][:30] ,   sibling_profession = item['candi_sis_profession3'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_sis_name4', 'candi_sis_education4', 'candi_sis_profession4', 'candi_sis_marital_status4']):
                Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name4'][:100], sibling_education=item['candi_sis_education4'][:100], sibling_marital_status =item['candi_sis_marital_status4'][:30] ,   sibling_profession = item['candi_sis_profession4'][:100])
            if all(item.get(key) not in [None, ''] for key in ['candi_sis_name5', 'candi_sis_education5', 'candi_sis_profession5', 'candi_sis_marital_status5']):
                Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name5'][:100], sibling_education=item['candi_sis_education5'][:100], sibling_marital_status =item['candi_sis_marital_status5'][:30] ,   sibling_profession = item['candi_sis_profession5'][:100])
            
            sibling = Siblings.objects.filter(user=new_user).exists()
            if sibling :
                new_user.sibling = 1
            new_user.save()     
            print("sibling data added successfully")

            name = None
            phone= None
            photo= None
            salary = None
            email = None
            if new_user.email:
                email = new_user.email
            if item["privacy_name"] == "interest_accepted":
                name = "interests"
            if item["privacy_name"] == "to_all_subscribe":
                name = "paid"     
            if item["privacy_phone"] == "interest_accepted":
                phone = "interests"
            if item["privacy_phone"] == "to_all_subscribe":
                phone = "paid"    
            if item["privacy_photo"] == "to_all":
                photo = "all" 
            if item["privacy_photo"] == "to_all_subscribe":
                photo = "paid"    
            if item["privacy_photo"] == "interest_accepted":
                photo= "interests"
            if item["privacy_salary"] == "to_all_subscribe" or item["privacy_salary"] == "to_all_subscribe_registered":
                salary = "paid"    
            if item["privacy_salary"] == "interest_accepted":
                salary= "interests"
            NotificationSettings.objects.create(user=new_user,email_notifications="",name=name,phone=phone,photo=photo, salary=salary, email=email)
            print("new user notification settings added successfully")
        
    for temp_data in data['changes']['create']['partner_preference']:
        item1 = temp_data['fields']
        
        for item in item1:
            print(f"MLP00{item['user_id']}") 
            existing_user = User.objects.filter(mlp_id=f"MLP00{item['user_id']}").first()
            if existing_user:
                # For partner age preference
                existing_user.partner_age_from = None
                existing_user.partner_age_to = None
                existing_user.partner_age_preference = False
                
                existing_user.partner_age_from = int(item['plus_years']) if item['plus_years'] and item['plus_years'] != '' else None
                existing_user.partner_age_to = int(item['minus_years']) if item['minus_years'] and item['minus_years'] != '' else None
                existing_user.partner_age_preference = True if item['minus_years'] and item['minus_years'] != '' else False
                
                existing_user.save()

                print(f"Partner age preference updated for user {existing_user.mlp_id}")
                


                # For Partner Height Preference
                existing_user.partner_height_preference = False
                existing_user.partner_height_from = None
                existing_user.partner_height_to = None

                height_preference = False
                height_from = None
                height_to = None
                if item['height_ft_from'] and item['height_ft_to'] and item['height_inch_to'] and item['height_inch_from']:
                    height_from = (int(item['height_ft_from']) * 12 + int(item['height_inch_from'])) if item['height_inch_from'] and item['height_ft_from'] else None
                    height_to = (int(item['height_ft_to']) * 12 + int(item['height_inch_to'])) if item['height_inch_to'] and item['height_ft_to'] else None
                    if height_from is not None and height_to is not None:
                        height_preference = True
                
                existing_user.partner_height_preference = height_preference
                existing_user.partner_height_from = height_from
                existing_user.partner_height_to = height_to
                existing_user.save()

                print(f"height preference updated for user {existing_user.mlp_id}")


                # For Partner Expertise Preference    
                PartnerExpertisePreference.objects.filter(user=existing_user).delete()
                partner_expertise_preference = False
                medicine_names = []
                if item['medicine_search'] and item['medicine_search'] not in ["Does not matter", "No Matter"]:
                    partner_expertise_preference = True
                    medicine_names = [medicine.strip() for medicine in item['medicine_search'].split(',')]
                if not medicine_names:
                    partner_expertise_preference = False
                else:
                    partner_expertise_preference = True    
                existing_user.partner_expertise_preference = partner_expertise_preference
                existing_user.save()

                # For Expertise of Partner
                if medicine_names:
                    for medicine_name in medicine_names:
                        expertise_objects = Expertise.objects.filter(name__iexact=medicine_name)
                        if expertise_objects.exists():
                            for expertise in expertise_objects:
                                PartnerExpertisePreference.objects.create(user=existing_user, expertise=expertise)

                print(f"Partner expertise preference updated for user {existing_user.mlp_id}")


                # Partner Post Graduation Preference
                PartnerPGPreference.objects.filter(user=existing_user).delete()
                partner_post_education_preference = False
                post_education_field_names = []
                if item['post_education_field_search'] and item['post_education_field_search'] not in ["Does not matter", "No Matter"]:
                    partner_post_education_preference = True
                    post_education_field_names = [field.strip() for field in item['post_education_field_search'].split(',')] 
                if not post_education_field_names:
                   partner_post_education_preference = False
                else:
                    partner_post_education_preference = True  
                existing_user.partner_postgraduation_preference = partner_post_education_preference
                unique_pref = set()
                
                for field_name in post_education_field_names:
                    if field_name == "MCh":
                        field_name = "Mch"
                    elif field_name == "MD / MS Ayurveda":
                        field_name = "MD/MS Ayurveda"    

                    matching_object = PostGraduation.objects.filter(name__iexact=field_name).first()
                    if matching_object:
                        unique_pref.add(matching_object)
                        
                for post_education_object in unique_pref:
                    PartnerPGPreference.objects.create(user=existing_user, post_graduation=post_education_object)
                
                existing_user.save()
            
                print(f"Partner post graduation preference updated for user {existing_user.mlp_id}")

                    

                # Partner Graduation Preference
                PartnerGraduationPreference.objects.filter(user=existing_user).delete()
                partner_education_preference = False
                education_field_names = []
                if item['education_field_search'] and item['education_field_search'] not in ["Does not matter", "No Matter"]:
                    partner_education_preference = True
                    education_field_names = [field.strip() for field in item['education_field_search'].split(',')] 
                if not education_field_names:
                    partner_education_preference = False
                else:
                    partner_education_preference = True    
                existing_user.partner_graduation_preference = partner_education_preference 
                existing_user.save()
                
                for field_name in education_field_names:
                    education_objects = Graduation.objects.filter(name__iexact=field_name)
                    if education_objects.exists():
                        for education in education_objects:
                            PartnerGraduationPreference.objects.create(user=existing_user, graduation=education)

                print(f"Partner graduation preference updated for user {existing_user.mlp_id}")
                


                # Partner Specialization Preference
                # Clear existing specialization preferences
                PartnerSpecializationPreference.objects.filter(user=existing_user).delete()

                specialization_names = []
                partner_specialization_preference = False
                if item['specialization_search'] and item['specialization_search'] not in ["Does not matter", "No Matter"]:
                    partner_specialization_preference = True
                    specialization_names = [specialization.strip() for specialization in item['specialization_search'].split(',')]
                
                if not specialization_names:
                    partner_specialization_preference = False
                else:
                    partner_specialization_preference = True                        

                existing_user.partner_specialization_preference = partner_specialization_preference
                existing_user.save()
                
                for specialization_name in specialization_names:
                    specialization_objects = Specialization.objects.filter(name__iexact=specialization_name)
                    if specialization_objects.exists():
                        for specialization in specialization_objects:
                            PartnerSpecializationPreference.objects.create(user=existing_user, specialization=specialization)

                print(f"Partner specialization preference updated for user {existing_user.mlp_id}")
                    
                

                # For partner religion Preference
                PartnerReligionPreference.objects.filter(user=existing_user).delete()

                religion_names = []
                partner_religion_preference = False
                if item['religion_search'] and item['religion_search'] not in ["Does not matter", "No Matter"]:
                    partner_religion_preference = True
                    religion_names = [religion.strip() for religion in item['religion_search'].split(',')]
                if not religion_names:
                   partner_religion_preference = False
                else:
                    partner_religion_preference = True   
                existing_user.partner_religion_preference = partner_religion_preference
                for religion_name in religion_names:
                    religion_objects = Religion.objects.filter(name__iexact=religion_name)
                    if religion_objects.exists():
                        for religion in religion_objects:
                            PartnerReligionPreference.objects.create(user=existing_user, religion=religion)
                existing_user.save()
                print(f"Partner religion preference updated for user {existing_user.mlp_id}")
                


                # For Partner Marital State Preference
                PartnerMaritalStatusPreference.objects.filter(user=existing_user).delete()
                partner_marital_pref = False
                marital_preference_data = None
                if item['second_marriage'] and item['second_marriage'] not in ["Does not matter", "No Matter"]:
                    partner_marital_pref = True
                    marital_pref_name = item['second_marriage'].strip()  
                    if marital_pref_name == "Never Married":
                        marital_pref_name = "Bachelor"
                    marital_preference_data = MaritalStatus.objects.filter(name__iexact=marital_pref_name).first()  # Get the single instance

                existing_user.partner_marital_status_preference = partner_marital_pref   
                if marital_preference_data:
                    PartnerMaritalStatusPreference.objects.create(user=existing_user, marital_status=marital_preference_data)
                existing_user.save()
            
                print(f"marital status preference updated to the user {existing_user.mlp_id}") 



                # For Partner Mother Tongue Preference
                existing_user.partner_mothertongue_from.clear()

                mother_tongue_objs = []
                partner_mother_tongue_preference = False
                if item['mother_tongue'] and item['mother_tongue'] not in ["Does not matter", "No Matter"]:
                    partner_mother_tongue = item['mother_tongue'].split(',')
                    if partner_mother_tongue:
                        partner_mother_tongue_preference = True
                        for lang in partner_mother_tongue:
                            lang = lang.strip()
                            if lang:
                                mother_tongue_object = MotherTongue.objects.filter(name__iexact=lang).first()
                                if mother_tongue_object:
                                    mother_tongue_objs.append(mother_tongue_object)
                    else:
                        partner_mother_tongue_preference = False
                if not mother_tongue_objs:
                   partner_mother_tongue_preference = False
                else:
                    partner_mother_tongue_preference = True    
                existing_user.partner_mothertongue_preference = partner_mother_tongue_preference
                existing_user.partner_mothertongue_from.set(mother_tongue_objs) 
                existing_user.save()
                print(f"Partner mother tongue preference updated for user {existing_user.mlp_id}")
                


                # For Partner Caste Preference
                existing_user.partner_caste_from = json.dumps([])  # Reset the field to empty list

                caste_objs = []
                partner_caste_preference = False
                if item['caste_search'] and item['caste_search'] not in ["Does not matter", "No Matter"]:
                    partner_caste_search = item['caste_search'].split(',')
                    if partner_caste_search:
                        partner_caste_preference = True
                        for caste in partner_caste_search:
                            caste = caste.strip()
                            if caste:
                                caste_object = Caste.objects.filter(name__iexact=caste).first()
                                if caste_object:
                                    caste_objs.append(caste_object)
                    else:
                        partner_caste_preference = False
                caste_names = [caste.name for caste in caste_objs]
                # Check if caste_names is empty or None
                if not caste_names:
                    partner_caste_preference = False
                else:
                    partner_caste_preference = True

                existing_user.partner_caste_preference = partner_caste_preference
                existing_user.partner_caste_from = json.dumps(caste_names)
                existing_user.save()

                print(f"Partner caste preference updated for user {existing_user.mlp_id}")
                

                # For Partner city Preference
                # Clear existing city preferences
                existing_user.partner_cities_from = json.dumps([])  
                partner_city_preference = False
                item['city_search'] = [] if not item['city_search'] else [ele.strip() for ele in item['city_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"]]
                if item['city_search']:
                    partner_city_preference = True
                existing_user.partner_cities_preference = partner_city_preference 
                existing_user.partner_cities_from = json.dumps(item['city_search'])
                existing_user.save()

                print(f"Partner cities preference updated for user {existing_user.mlp_id}")
                    
                
                # For Partner State Preference
                # Clear existing state preferences
                existing_user.partner_state_from = json.dumps([])  

                partner_state_preference = False
                item['state_field_search'] = [] if not item['state_field_search'] else [ele.strip() for ele in item['state_field_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"]]
                if item['state_field_search']:
                    partner_state_preference = True
                existing_user.partner_state_preference = partner_state_preference   
                existing_user.partner_state_from = json.dumps(item['state_field_search'])
                existing_user.save()

                print(f"Partner state preference updated for user {existing_user.mlp_id}")

                
                # For Partner Country Preference
                # Clear existing country preferences
                existing_user.partner_country_from = json.dumps([]) 
                
                partner_country_preference = False
                item['country_field_search'] = [] if not item['country_field_search'] else [ele.strip() for ele in item['country_field_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"]]
                if item['country_field_search']:
                    partner_country_preference = True
                existing_user.partner_country_preference = partner_country_preference    
                existing_user.partner_country_from = json.dumps(item['country_field_search'])
                existing_user.save()

                print(f"Partner country preference updated for user {existing_user.mlp_id}")
                

                #     # For User Post Graduation
                #     unique_post_grad_objects = set()

                #     for ed_name in post_ed_names:
                #         if ed_name == "MCh":
                #             ed_name = "Mch"
                #         elif ed_name == "MD / MS Ayurveda":
                #             ed_name = "MD/MS Ayurveda"

                #         post_grad_object = PostGraduation.objects.filter(name__iexact=ed_name).first()

                #         if post_grad_object:
                #             unique_post_grad_objects.add(post_grad_object)
                #     print(unique_post_grad_objects) 
                #     for pg in unique_post_grad_objects:
                #         user_post_grad_exists = UserPostGraduation.objects.filter(user=existing_user, post_graduation=pg).exists()
                #         if user_post_grad_exists:
                #             print(f"UserPostGraduation already present for user {existing_user.mlp_id} and post_graduation {pg.name}")
                #         else:
                #             UserPostGraduation.objects.create(user=existing_user, post_graduation=pg)
                #             print(f"UserPostGraduation created for user {existing_user.mlp_id} and post_graduation {pg.name}")
                # else:
                #     print(f"User with mlp_id not exists MLP00{item['user_id']}") 
            else:
                print("existing user not found")
        print("user partner preference data saved")
    

    print("`````Data sync successfully~~~")
    



@shared_task()
def sync_data():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url = "https://www.medicolifepartner.com/index.php/api/apisync"
    
    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()
       
        print("before fetching data")
        viewed_data = data['changes']['create']['viewed']['fields']
        interested_data = data['changes']['create']['interested']['fields']
        selected_data = data['changes']['create']['selected']['fields']
        blocked_data = data['changes']['create']['donotshow']['fields']
        accept_interest_data = data['changes']['update']['accept']
        reject_interest_data = data['changes']['update']['decline']
        delete_profile_data = data['changes']['delete']
        user_updated_data = data['changes']['update']['edit']
        unselected_data = data['changes']['update']['unselected']
        unblock_data = data['changes']['update']['unblock']
        # report_users_data = data.get('changes', {}).get('create', {}).get('report', {}).get('fields', [])
        # payment_data = data.get('changes', {}).get('create', {}).get('payment', {}).get('fields', [])
        # partpref_data = data.get('changes', {}).get('create', {}).get('partpref', {}).get('fields', [])
      
        
        for fields in user_updated_data:
            items = fields['fields']
            for item in items:
                mlp_id = f"MLP00{item['id']}"

                user_exists = User.objects.filter(mlp_id=mlp_id,is_active = True,is_wrong=False).exists()
                if user_exists:
                    if item['country_c'] is not None:
                        country_code = item['country_c'].replace("+", "")  
                        mobile_number = f"{country_code}{item['mobile']}"
                    else:
                        mobile_number = f"91{item['mobile']}" 


                    #Country name  
                    country_name = item['country_name']
                    if country_name == "USA":
                        country_name = "United States"
                    elif country_name == "UAE":
                        country_name = "United Arab Emirates"
                    elif country_name == "UK":
                        country_name = "United Kingdom" 

                    physical_status = None
                    if item['physically_challenged'] is not None:
                        if item['physically_challenged'] == "Normal" :
                            physical_status = "Normal"
                        elif item['physically_challenged'] == "Physically Challenged" :
                            physical_status = "Disabled"   
                                  
                       
                    
                    # For Profession
                    profession_obj = []
                    temp_professions = item.get('profession', '')  
                    if temp_professions: 
                        professions = temp_professions.split(',')  
                        for profession in professions:
                            values=profession.strip().capitalize()
                            profession_obj.append(values)      


                    manglik_value = 1 if item['manglik'] == "Yes" else 0 if item['manglik'] == "No" else -1 
                    
                    # For SubCaste
                    sub_caste=None
                    subcaste=SubCaste.objects.filter(name__iexact=item['sub_caste'])
                    if subcaste.exists():
                        sub_caste = subcaste.first()


                    
                    #For family residence
                    fath_res = None
                    if item['father_owned_residence'] is not None:
                        if item['father_owned_residence'] == "owned" or item['father_owned_residence'] == "Owned":
                            fath_res = "Owned"
                        elif item['father_owned_residence'] == "rented" or item['father_owned_residence'] == "Rented":
                            fath_res = "Rented"  
                            
                    #For family car
                    family_car = None
                    if item['car'] is not None:
                        if item['car'] == "Nil":
                            family_car = "No"
                        elif item['car'] == "Own Car < 10 lacs" or item['car'] == "Own Car > 10 lacs":
                            family_car =item['car']             
                    
                    #For family_environment
                    family_environment = None
                    if item['family_env'] is not None:
                        if item['family_env'] in ["Semi Orthodox","Modern" , "Orthodox"]:
                            family_environment = item['family_env']
                    
                    #For body clock
                    body_clock = None
                    if item['wakes_up_from'] is not None:
                        if item['wakes_up_from'] == "Wakes up early":
                            body_clock = "Wakes Up Early"
                        elif item['wakes_up_from'] == "Stays awake till late night":
                            body_clock = "Stays Till Midnight"    

                    #for kids
                    kids_choice = None
                    if item['kids'] is not None:
                        if item['kids'] == "Flexible":
                            kids_choice = "Flexible"
                        if item['kids'] == "1":
                            kids_choice = "1 kid"
                        if item['kids'] == "2":
                            kids_choice = "2 kid"
                        if item['kids'] == "No Kids":
                            kids_choice = "No Kids"            


                    # For Marital State  
                    marital_status_obj = None
                    if item['second_marriage'] == "Never Married":
                        marital_status_name = "Bachelor"
                        marital_status = MaritalStatus.objects.filter(name__iexact=marital_status_name)
                        if marital_status:
                            marital_status_obj = marital_status.first()
                    else:
                        marital_status = MaritalStatus.objects.filter(name__iexact=item['second_marriage'])
                        if marital_status:
                            marital_status_obj = marital_status.first()       

                    #For completed post grad
                    completed_post_grad =False
                    graduation_obj = Graduation.objects.filter(name__iexact=item["education_field"]).first()

                    post_ed_names = [ele.strip() for ele in item['post_education_field'].split(',')] 
                
                    for ed_name in post_ed_names:
                        if ed_name == "MCh":
                            ed_name = "Mch"
                        elif ed_name == "MD / MS Ayurveda":
                            ed_name = "MD/MS Ayurveda"

                        post_grad_objects = PostGraduation.objects.filter(name__iexact=ed_name)    

                        if post_grad_objects.exists():
                            print(post_grad_objects)
                            completed_post_grad = True
                            break    

                    if not post_grad_objects:
                        completed_post_grad = False
        
                    can_upgrade_subscription = -1 
                    if item['status'] == "Active":
                        # subscription_start_date = item['subscription_start_date']
                        # subscription_end_date = item['subscription_end_date']
                        if item['subscription_start_date'] != "0000-00-00 00:00:00" and  item['subscription_end_date'] != "0000-00-00 00:00:00":
                            subscription_start_date = datetime.strptime(item['subscription_start_date'], "%Y-%m-%d %H:%M:%S")
                            subscription_end_date = datetime.strptime(item['subscription_end_date'], "%Y-%m-%d %H:%M:%S")


                            # Calculate the one-month window after subscription creation
                            upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                            # Check if subscription is active
                            if subscription_end_date >= datetime.now():
                                # Check if within the upgrade window
                                if datetime.now() <= upgrade_window_end_date:
                                    can_upgrade_subscription = 1
                                else:
                                    can_upgrade_subscription = 0
                            else:
                                can_upgrade_subscription = -1
                        else:
                            can_upgrade_subscription = -1        

                    profile_pictures = []
                    if item['profile_pic'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic'].strip()}")
                    if item['profile_pic2'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic2'].strip()}")
                    if item['profile_pic3'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic3'].strip()}")
                    if item['profile_pic4'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic4'].strip()}")
                    if item['profile_pic5'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic5'].strip()}")
                    if item['profile_pic6'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic6'].strip()}")
                    if item['profile_pic7'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic7'].strip()}")
                    if item['profile_pic8'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic8'].strip()}")
                    if item['profile_pic9'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic9'].strip()}")
                    if item['profile_pic10'].strip():
                        profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic10'].strip()}")
                
                    # For specialization
                    specialization = None
                    specializations = Specialization.objects.filter(name__iexact=item['specialization'])
                    if specializations.exists():
                        specialization = specializations.first()  
                        
                    # For mother tongue
                    spoken_languages = item['spoken_language'].split(',')
                    mother_tongues = []
                    for lang in spoken_languages:
                        lang = lang.strip()
                        if lang:
                            mother_tongue = MotherTongue.objects.filter(name__iexact=lang).first()
                            if mother_tongue:
                                mother_tongues.append(mother_tongue)

                   
                    
                    grad_status = None
                    if item.get('education_field_status') == 'complete' or item.get('education_field_status') == 'completed':
                        grad_status = 'Completed'
                    elif item.get('education_field_status') == 'ongoing' :
                        grad_status = 'Ongoing' 

                    post_grad_status = None
                    if item.get('post_education_field_status') == 'complete' or item.get('post_education_field_status') == 'completed':
                        post_grad_status = 'Completed'
                    elif item.get('post_education_field_status') == 'ongoing' :
                        post_grad_status = 'Ongoing' 
            
                    # For Hobbies
                    hobbies = []
                    if item['hobbies'] and ',' in item['hobbies']:
                        hobbies = [h.strip() for h in item['hobbies'].split(',') if h.strip()]

                    religion_obj= Religion.objects.filter(name__iexact=item['religion']).first()
                    expertise_ob = Expertise.objects.filter(name__iexact=item['medicine']).first() 
                    mandatory_questions_completed = True
                    if (
                        item['status'] == "Pending" or
                        item['createby'] == '' or
                        item['createby'] not in ["candidate", "family"] or
                        religion_obj is None or
                        item["candidates_name"] == "" or
                        item.get("date_of_birth") is None or
                        item['date_of_birth'] == "0000-00-00" or
                        item['sex'] not in ["Male", "Female"] or
                        len(profile_pictures) == 0 or
                        graduation_obj is None or
                        expertise_ob is None or
                        item['email_id'] is None or
                        item['password'] is None
                    ):
                      mandatory_questions_completed = False      
                    
                    new_user=User.objects.filter(mlp_id=mlp_id).update(
                    name=item['candidates_name'],
                    email=item['email_id'],
                    password=item['password'],
                    mobile_number=mobile_number,
                    manglik=manglik_value,
                    gender='m' if item['sex'] == "Male" else 'f',
                    weight = item['weight'] if item['weight'] is not None else None,
                    dob=item['date_of_birth'] if item['date_of_birth']!="0000-00-00" else None,
                   # body_build = item['body_build'] if item['body_build'] is not None else None,
                   # complexion = item['complexion'] if item['complexion'] is not None else None,
                    blood_group = item['blood_group'] if item['blood_group'] is not None else None,
                   # disease_history = item['disease'] if item['disease'] is not None else None,
                    schooling_details = item['schooling'] if item['schooling'] is not None else None,
                    facebook_profile = item['facebook_link'] if item['facebook_link'] is not None else None,
                    linkedin_profile = item['linkedin'] if item['linkedin'] is not None else None,
                    birth_location=item['birth_location'],
                    height=int(item['height_ft'])*12 + int(item['height_inch']),
                   # salary=item['salary'],
                    caste=item['caste'] if item['caste'] is not None else None, 
                    sub_caste=sub_caste,
                    marital_status = marital_status_obj,
                    hobbies = json.dumps(["Others"]) if hobbies not in [None, '', []] else "[]",
                    other_hobbies = json.dumps(hobbies),
                    profile_pictures = json.dumps(profile_pictures),
                    city = item['city'] if  item['city'] != "Please Select State" or item['city'] != "Select City" or item['city'] != "Select State" or item['city'] != "Please+Select+State" else None,
                    state = item['state_name'],
                    country = country_name, 
                    horoscope_matching = item['horoscope_matching'] if item['horoscope_matching'] in ["Yes", "No"] else None,
                    future_aspirations=item['candi_future_aspiration'],
                    about=item['candi_describing_myself'],
                    is_active=False if item['status'] =='Remove' or item['status'] == "Pending" else True,
                    is_wrong = True if  item['status']=='Wrong' else False,
                    time_birth = str(item['time_of_birth']) if item['time_of_birth'] != "00:00:00" else None,
                    religion = Religion.objects.filter(name__iexact=item['religion']).first(),
                    physical_status = physical_status,
                   # eyesight = item['eye_sight'] if item['eye_sight'] is not None else None,
                    city_parents = item['father_resided_city'] if item['father_resided_city'] is not None else None,
                   # residence =  item['res_address'] if item['res_address'] is not None else None,
                    family_house = fath_res,
                    family_car = family_car,
                    profession_description = item['profession_details'] if item['profession_details'] is not None else None,
                    family_financial_status = item['fam_fin_range'] if item['fam_fin_range'] is not None else None,
                    family_environment = family_environment,
                    body_clock = body_clock,
                    kids_choice=kids_choice,
                    profession = json.dumps(profession_obj),
                    # is_primary_account=True,
                    # sibling = None,
                    # whatsapp_number = None,
                    specialization = specialization,
                    registration_number = item['medical_registration_number'] if item['medical_registration_number'] is not None else None,
                    profile_createdby ="Parent" if item['createby'] == "family" else "Candidate",
                    mother_name = item['mother_name'] if item['mother_name'] is not None else None,
                    father_name = item['father_name'] if item['father_name'] is not None else None,
                    father_occupation = item['father_profession'] if item['father_profession'] is not None else None,
                    mother_occupation = item['mother_profession'] if item['mother_profession'] is not None else None,
                    father_education = item['father_education'] if item['father_education'] is not None else None,
                    mother_education = item['mother_education'] if item['mother_education'] is not None else None,
                  #  nature = item['nature'] if item['nature'] is not None else None,
                    can_upgrade_subscription=can_upgrade_subscription,
                    graduation_obj=graduation_obj,
                    completed_post_grad=completed_post_grad,
                    mandatory_questions_completed=mandatory_questions_completed,
                    graduation_institute = item.get('graduation_institute'),
                    post_graduation_institute = item.get('post_graduation_institute'),
                    post_graduation_status = post_grad_status,
                    graduation_status = grad_status,
                    )
                    print("new user",f"MLP00{item['id']}")
                    new_user = User.objects.filter(mlp_id=f"MLP00{item['id']}").first()
                    print(new_user)
                    new_user.languages.set(Languages.objects.filter(name__iexact=item['language']))
                    new_user.mother_tongue.set(mother_tongues)

                    #For User Post Graduation
                    unique_post_grad_objects = set()

                    for ed_name in post_ed_names:
                        if ed_name == "MCh":
                            ed_name = "Mch"
                        elif ed_name == "MD / MS Ayurveda":
                            ed_name = "MD/MS Ayurveda"

                
                        post_grad_object = PostGraduation.objects.filter(name__iexact=ed_name).first()

                        if post_grad_object:
                            unique_post_grad_objects.add(post_grad_object)

                    for pg in unique_post_grad_objects:
                        user_post_grad, created = UserPostGraduation.objects.update_or_create(
                            user=new_user,
                            post_graduation=pg
                        ) 


                    #For siblings
                    if all(item.get(key) not in [None, ''] for key in ['candi_bro_name1', 'candi_bro_education1', 'candi_bro_profession1', 'candi_bro_marital_status1']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_bro_name2', 'candi_bro_education2', 'candi_bro_profession2', 'candi_bro_marital_status2']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_bro_name3', 'candi_bro_education3', 'candi_bro_profession3', 'candi_bro_marital_status3']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_bro_name4', 'candi_bro_education4', 'candi_bro_profession4', 'candi_bro_marital_status4']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_bro_name5', 'candi_bro_education5', 'candi_bro_profession5', 'candi_bro_marital_status5']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])


                    if all(item.get(key) not in [None, ''] for key in ['candi_sis_name1', 'candi_sis_education1', 'candi_sis_profession1', 'candi_sis_marital_status1']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_sis_name2', 'candi_sis_education2', 'candi_sis_profession2', 'candi_sis_marital_status2']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_sis_name3', 'candi_sis_education3', 'candi_sis_profession3', 'candi_sis_marital_status3']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_sis_name4', 'candi_sis_education4', 'candi_sis_profession4', 'candi_sis_marital_status4']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])
                    if all(item.get(key) not in [None, ''] for key in ['candi_sis_name5', 'candi_sis_education5', 'candi_sis_profession5', 'candi_sis_marital_status5']):
                        Siblings.objects.filter(user=new_user).update(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])


                    sibling = Siblings.objects.filter(user=new_user).exists()
                    if sibling :
                        new_user.sibling = 1
                    new_user.save()     
                    print("sibling data updated successfully") 
                    
                    # For Notification settings
                    name = None
                    phone= None
                    photo= None
                    salary = None
                    email = None
                    if new_user.email:
                        email = new_user.email
                    if item["privacy_name"] == "interest_accepted":
                        name = "interests"
                    if item["privacy_name"] == "to_all_subscribe":
                        name = "paid"     
                    if item["privacy_phone"] == "interest_accepted":
                        phone = "interests"
                    if item["privacy_phone"] == "to_all_subscribe":
                        phone = "paid"    
                    if item["privacy_photo"] == "to_all":
                        photo = "all" 
                    if item["privacy_photo"] == "to_all_subscribe":
                        photo = "paid"    
                    if item["privacy_photo"] == "interest_accepted":
                        photo= "interests"
                    if item["privacy_salary"] == "to_all_subscribe" or item["privacy_salary"] == "to_all_subscribe_registered":
                        salary = "paid"    
                    if item["privacy_salary"] == "interest_accepted":
                        salary= "interests"
                    NotificationSettings.objects.filter(user=new_user).update(user=new_user,email_notifications="",name=name,phone=phone,photo=photo, salary=salary, email=email)
                    print("new user notification settings added successfully")

                else:
                    print("User not exists in db")

        print("after adding user") 
        
      
       

        for item in viewed_data:
            user_id = f"MLP00{item['who_seen']}"
            seen_user_id = f"MLP00{item['whom_seen']}"
            contact_seen = item['contact_seen']

            user= User.objects.filter(mlp_id__iexact=user_id, is_active=True, is_wrong=False).first()
            seen_user = User.objects.filter(mlp_id__iexact=seen_user_id, is_active=True, is_wrong=False).first()
            profile_view_already = ProfileView.objects.filter( viewer__mlp_id__iexact=user_id, viewed_user__mlp_id__iexact=seen_user_id).exists()
            contact_already_exists = ContactViewed.objects.filter(user__mlp_id__iexact=user_id, seen_contact__mlp_id__iexact=seen_user_id).exists()


            if user and seen_user :
               # user = User.objects.get(mlp_id__iexact=user_id)
               # seen_user = User.objects.get(mlp_id__iexact=seen_user_id)

                if not profile_view_already:
                    profile_viewing = ProfileView(viewer =user, viewed_user=seen_user)
                    profile_viewing.save()
                    print("profile view data saved")
                else:
                    print("profile view already added")    
                if not contact_already_exists and contact_seen == "Yes":
                    contact_instance = ContactViewed(user=user, seen_contact=seen_user)
                    contact_instance.save() 
                    print("contact view data saved") 
                else: 
                    print("contact viewed already exists")      
            else:
                print("user/seen user don't exists")        
                  
        for item in interested_data:
            invitation_by = User.objects.filter(mlp_id__iexact=f"MLP00{item['id']}", is_active=True,is_wrong=False).first()
            invitation_to = User.objects.filter(mlp_id__iexact=f"MLP00{item['interested_id']}", is_active=True, is_wrong=False).first()
            # if  item['accept_status'] == '1':
            #     status = "Accepted"
            # elif item['accept_status'] == '0':
            #     status = "Pending"
            # else:
            #     status = "Rejected"
            connection_exist = ConnectionList.objects.filter(Q(user_one=invitation_by, user_two=invitation_to) | Q(user_two=invitation_by, user_one=invitation_to)).exists()
            interest_exists = Intrest.objects.filter(invitation_by=invitation_by, invitation_to=invitation_to).exists()
            if invitation_by and invitation_to:
                if not interest_exists:
                    # status = 'Accepted' if accepted_status == '1' else 'Pending'
                    status = "Pending"
                    interest = Intrest(invitation_by=invitation_by, invitation_to=invitation_to, status=status)
                    interest.save()
                    print("intrest data saved")
                else:
                    print("interest already sent")    

                # if status == 'Accepted' and not connection_exist:
                #     connection_list_instance=ConnectionList(user_one=invitation_by, user_two=invitation_to)
                #     connection_list_instance.save()
                #     print("mutually data saved")   
                # else:
                #     print(" status is not accepted/mutually accepted already exist data")      
            else:
                print("One or more users not found for interest data")

        for item in selected_data:
            who_seen_id = f"MLP00{item['id']}"
            whom_seen_id = f"MLP00{item['selected_id']}"
            who_seen = User.objects.filter(mlp_id__iexact = who_seen_id, is_active=True, is_wrong=False).first()
            whom_seen = User.objects.filter(mlp_id__iexact = whom_seen_id , is_active=True, is_wrong=False).first()
            shortlisted_already = SavedUser.objects.filter(user=who_seen, saved_profile=whom_seen).exists()
            if who_seen and whom_seen:
                    if not shortlisted_already:
                        shortlist_instance = SavedUser(user=who_seen, saved_profile=whom_seen)
                        shortlist_instance.save()
                        print("Saved User added")
                    else:
                        print("shortlisted data already present")    
            else:
                print("Saved users not exist")  


        print("Blocked data start") 
        for item in blocked_data:
            print("Inside blocked")
            who_blocked_id = f"MLP00{item['member_id']}"
            whom_blocked_id = f"MLP00{item['donot_show_profile_id']}"
            who_blocked = User.objects.filter(mlp_id__iexact = who_blocked_id, is_active=True, is_wrong=False).first()
            whom_blocked = User.objects.filter(mlp_id__iexact = whom_blocked_id , is_active=True, is_wrong=False).first()
            blocked_already = BlockedUsers.objects.filter(user=who_blocked, blocked_user=whom_blocked).exists()
            if who_blocked and whom_blocked:
                    if not blocked_already:
                        blocked_instance = BlockedUsers(user=who_blocked, blocked_user=whom_blocked)
                        blocked_instance.save()
                        print("Blocked User added")
                    else:
                        print("Blocked users data already present")    
            else:
                print("Blocked users not exist in db") 
        

        for fields in accept_interest_data:
            print("Inside accept")
            items = fields['fields']
            # Now you can access the fields for each item
            for item in items:
                invitation_by = User.objects.filter(mlp_id__iexact=f"MLP00{item['id']}", is_active=True, is_wrong=False).first()
                invitation_to = User.objects.filter(mlp_id__iexact=f"MLP00{item['interested_id']}", is_active=True , is_wrong=False).first()
                # if  item['accept_status'] == '1':
                #     status = "Accepted"
                # elif item['accept_status'] == '0':
                #     status = "Pending"
                # else:
                #     status = "Rejected"
                connection_exist = ConnectionList.objects.filter(Q(user_one=invitation_by, user_two=invitation_to) | Q(user_two=invitation_by, user_one=invitation_to)).exists()
                interest_exists = Intrest.objects.filter(invitation_by=invitation_by, invitation_to=invitation_to).first()
                if invitation_by and invitation_to:
                    if  interest_exists:
                        #status = 'Accepted' if accepted_status == '1' else 'Pending'
                        #interest_exists.status = status
                        interest_exists.status = "Accepted"
                        interest_exists.save()
                        print("intrest data updated successfully")
                    else:
                        print("interest not found")    

                    if item['accept_status'] == '1' and not connection_exist:
                        connection_list_instance=ConnectionList(user_one=invitation_by, user_two=invitation_to)
                        connection_list_instance.save()
                        print("mutually data saved")   
                    else:
                        print("status not accepted/mutually accepted already exist data")      
                else:
                    print("One or more users not found.")

        for fields in reject_interest_data:
            items = fields['fields']
            for item in items:
                invitation_by = User.objects.filter(mlp_id__iexact=f"MLP00{item['id']}", is_active=True, is_wrong=False).first()
                invitation_to = User.objects.filter(mlp_id__iexact=f"MLP00{item['interested_id']}", is_active=True, is_wrong=False).first()
                # if  item['accept_status'] == '1':
                #     status = "Accepted"
                # elif item['accept_status'] == '0':
                #     status = "Pending"
                # else:
                #     status = "Rejected"
                connection_exist = ConnectionList.objects.filter(Q(user_one=invitation_by, user_two=invitation_to) | Q(user_two=invitation_by, user_one=invitation_to)).exists()
                interest_exists = Intrest.objects.filter(invitation_by=invitation_by, invitation_to=invitation_to).first()
                if invitation_by and invitation_to:
                    if  interest_exists:
                       # interest_exists.status = status
                        interest_exists.status = "Rejected"
                        interest_exists.save()
                        print("intrest data updated successfully")
                    else:
                        print("interest not found rejected case")    

                    # if status == 'Accepted' and not connection_exist:
                    #     connection_list_instance=ConnectionList(user_one=invitation_by, user_two=invitation_to)
                    #     connection_list_instance.save()
                    #     print("mutually data saved")   
                    # else:
                    #     print("mutually accepted already exist data")      
                else:
                    print("One or more users not found.")   
        
       
        for fields in delete_profile_data:
            items = fields['fields']
            for item in items:
                mlp_id = f"MLP00{item['user_id']}"
                reason = item['deleteprofile_reasion']
                experience = item['member_feedback'] 
                delete_date_str = item['delete_date']
                delete_date = None  # Handle the error as needed
                try:
                    delete_date = datetime.strptime(delete_date_str, "%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    print(f"Date conversion error for mlp_id {mlp_id}: {e}")

               
                user_exists = User.objects.filter(mlp_id=mlp_id,is_active =True, is_wrong=False).exists()
                if user_exists :
                    user = User.objects.filter(mlp_id=mlp_id).first()
                    delete_profile_exists = DeleteProfile.objects.filter(mlp_id=mlp_id).exists()

                    if delete_profile_exists:
                        print(f"Data already present for mlp_id: {mlp_id}")
                    else:
                        DeleteProfile.objects.create(mlp_id = mlp_id , reason = reason , experience=experience,deleted_at = delete_date)
                        user.is_active = False
                        user.save()
                        print("User deleted and Saved data in Delete Profile model")
                else:
                    print("User not present with mlp_id in : ",{mlp_id})   



        for items in unselected_data:
           # print(items['fields'])
            for item in items['fields']:
                who_seen_id = f"MLP00{item['id']}"
                whom_seen_id = f"MLP00{item['selected_id']}"
                select_status = item['status']
                who_seen = User.objects.filter(mlp_id__iexact = who_seen_id, is_active=True, is_wrong=False).first()
                whom_seen = User.objects.filter(mlp_id__iexact = whom_seen_id , is_active=True, is_wrong=False).first()
                shortlisted_already = SavedUser.objects.filter(user=who_seen, saved_profile=whom_seen).exists()
                if who_seen and whom_seen:
                        if  shortlisted_already and select_status == "Deactive":
                            shortlist_instance = SavedUser.objects.filter(user=who_seen, saved_profile=whom_seen).first()
                            if shortlist_instance:
                                shortlist_instance.delete()
                                print("UnShortlisted successfully")
                        else:
                            print("shortlisted data not present in db")    
                else:
                    print("Saved users not exist")  

        for items in unblock_data:
            print(items)
            for item in items['fields']:
                who_blocked_id = f"MLP00{item['member_id']}"
                whom_blocked_id = f"MLP00{item['unblock_id']}"
                who_blocked = User.objects.filter(mlp_id__iexact = who_blocked_id, is_active=True, is_wrong=False).first()
                whom_blocked = User.objects.filter(mlp_id__iexact = whom_blocked_id , is_active=True, is_wrong=False).first()
                blocked_already = BlockedUsers.objects.filter(user=who_blocked, blocked_user=whom_blocked).exists()
                if who_blocked and whom_blocked:
                        if  blocked_already:
                            blocked_instance = BlockedUsers.objects.filter(user=who_blocked, blocked_user=whom_blocked).first()
                            if blocked_instance:
                                blocked_instance.delete()
                                print("UnBlocked User successfully")
                        else:
                            print("Blocked users data not present in db")    
                else:
                    print("Blocked users not exist in db") 


        response['message'] = "Data sync successfully"
        response['status_code'] = 200
        return response
    except Exception as e:
        response["error"] = str(e)
        return response  




def sync_payment_data():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url = "https://www.medicolifepartner.com/index.php/api/apisync"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()
       
        print("before fetching data")
      
        report_users_data = data.get('changes', {}).get('create', {}).get('report', {}).get('fields', [])
        payment_data = data.get('changes', {}).get('create', {}).get('payment', {}).get('fields', [])
        partpref_data = data.get('changes', {}).get('create', {}).get('partpref', {}).get('fields', []) 
        
        print("Payment data started")
        for fields in payment_data:
            print("Inside payment")
            user_id = f"MLP00{fields['user_id']}"
            price = fields["price"]
            plan_name = fields["plan_name"]
            create_date = fields['subscription_start_date']
            mihpayid = fields['mihpayid'] if fields['mihpayid'] and fields['mihpayid'] != "" else user_id
            status = fields['payment_status']
            coupon_code = None
            payload = {}

            print("Processing user with ID:", user_id)
            print("Plan name retrieved:", plan_name)

            # # Your existing plan name transformations
            # if plan_name == "Gold":
            #     plan_name = "Gold Old"
            # if plan_name == "Premium":
            #     plan_name = "Premium Old"
            # if plan_name == "Silver":
            #     plan_name = "Silver Old"
            # if plan_name == "Platinum":
            #     plan_name = "Platinum Old"
            # if plan_name == "Gold Plus":
            #     plan_name = "Gold Plus Web"
            # if plan_name == "Premium Plus":
            #     plan_name = "Premium Plus Web"   

            print("Transformed plan name:", plan_name)
            print("status",status)

            user = User.objects.filter(mlp_id__iexact=user_id, is_active=True, is_wrong=False).first()
            subscription = Subscription.objects.filter(name__iexact=plan_name).first()

            if user and subscription and status == "complete":
                # Check if UserSubscription already exists
                subscription_exists = UserSubscription.objects.filter(user=user, subscription=subscription).exists()
                if not subscription_exists:
                    sub_instance = UserSubscription(user=user, subscription=subscription, subscription_ios=None, created_date=create_date)
                    sub_instance.save()
                    print("Subscribed user saved successfully")
                    
                    print("Can upgrade subscription value")
                    can_upgrade_subscription = -1 
                    if status == "complete":
                        # subscription_start_date = item['subscription_start_date']
                        # subscription_end_date = item['subscription_end_date']
                        subscription_start_date = datetime.strptime(fields['subscription_start_date'], "%Y-%m-%d %H:%M:%S")
                        subscription_end_date = datetime.strptime(fields['subscription_end_date'], "%Y-%m-%d %H:%M:%S")


                        # Calculate the one-month window after subscription creation
                        upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                        # Check if subscription is active
                        if subscription_end_date >= datetime.now():
                            # Check if within the upgrade window
                            if datetime.now() <= upgrade_window_end_date:
                                can_upgrade_subscription = 1
                            else:
                                can_upgrade_subscription = 0
                        else:
                            can_upgrade_subscription = -1

                    user.can_upgrade_subscription = can_upgrade_subscription
                    user.save() 
                    print("Can upgrade subscription value updated successfully")       

                else:
                    print("User subscription already exists")

                # Check if TransactionEntity already exists
                transaction_exists = TransactionEntity.objects.filter(mihpayid=mihpayid, user=user).exists()
                if not transaction_exists:
                    TransactionEntity.objects.create(
                        mihpayid=mihpayid,
                        status="success",
                        amount=price,
                        user=user,
                        coupon_code=coupon_code,
                        subscription=subscription,
                        payload=payload
                    )
                    print("Transaction data saved successfully")
                else:
                    print("Transaction already exists")
            else:
                print("User and/or subscription not found")
        print("payment data added successfully")
        

        print("report data started")
        for item in report_users_data:
            who_report_id = f"MLP00{item['report_from']}"
            whom_report_id = f"MLP00{item['report_for']}"
            
            who_report = User.objects.filter(mlp_id__iexact = who_report_id, is_active=True, is_wrong=False).first()
            whom_report = User.objects.filter(mlp_id__iexact = whom_report_id , is_active=True, is_wrong=False).first()
            report_already = ReportUsers.objects.filter(user=who_report, report_user=whom_report).exists()
            if who_report and whom_report:
                    if not report_already:
                        reason = item.get('report_reasion', '')
                        formatted_reason = json.dumps([reason]) if reason else '[]'
                        report_instance = ReportUsers(user=who_report, report_user=whom_report, reason=formatted_reason)
                        report_instance.save()
                        if "Details seems to be incorrect" in reason or "Seems Fake Profile" in reason:
                        # report_to_user.is_wrong = True
                        # report_to_user.save()
                            whom_report.is_wrong = True
                            whom_report.save()
                        print("Report User data added")
                    else:
                        print("Report users data already present")    
            else:
                print("Report users not exist in db") 

        print("report data added successfully") 

        # success_stories_data = data.get('changes', {}).get('create', {}).get('success_story', {}).get('fields', [])
        
        # print("Processing success stories data")
        # for fields in success_stories_data:
        #     user_id = f"MLP00{fields['user_id']}"
        #     story = fields.get('story')
        #     partner_mlp_id = fields.get('partner_mlp_id')
        #     partner_name = fields.get('partner_name')
        #     partner_mobile_number = fields.get('partner_mobile_number')
        #     reason = fields.get('reason')
        #     experience = fields.get('experience')
        #     video = fields.get('video') 
        #     image = fields.get('image')  

        #     user = User.objects.filter(mlp_id__iexact=user_id, is_active=True).first()
        #     if user and story:
        #         # Create or update the success story for the user
        #         success_story, created = SuccessStory.objects.update_or_create(
        #             user=user,
        #             defaults={
        #                 'story': story,
        #                 'partner_mlp_id': partner_mlp_id,
        #                 'partner_name': partner_name,
        #                 'partner_mobile_number': partner_mobile_number,
        #                 'reason': reason,
        #                 'experience': experience,
        #                 'video': video,
        #                 'image': image,
        #             }
        #         )
        #         if created:
        #             print("New success story added for user:", user_id)
        #         else:
        #             print("Success story updated for user:", user_id)
        #     else:
        #         print("User not found or story is empty for user ID:", user_id)
        
        print("partner data adding")
        for item in partpref_data:
            print(f"MLP00{item['user_id']}") 
            existing_user = User.objects.filter(mlp_id=f"MLP00{item['user_id']}",is_active = True, is_wrong=False).first()
            if existing_user:
                if existing_user:
                    # For partner age preference
                    existing_user.partner_age_from = None
                    existing_user.partner_age_to = None
                    existing_user.partner_age_preference = False
                    
                    existing_user.partner_age_from = int(item['plus_years']) if item['plus_years'] and item['plus_years'] != '' else None
                    existing_user.partner_age_to = int(item['minus_years']) if item['minus_years'] and item['minus_years'] != '' else None
                    existing_user.partner_age_preference = True if item['minus_years'] and item['minus_years'] != '' else False
                    
                    existing_user.save()

                    print(f"Partner age preference updated for user {existing_user.mlp_id}")
                    
                    #For Partner Physical_status
                    physical_status = None
                    if item["physically_challenged"] is not None:
                        if item["physically_challenged"] == "Normal":
                            physical_status = "Normal"
                        elif item["physically_challenged"] == "Physically Challenged":
                            physical_status = "Disabled"  
                        elif item["physically_challenged"] == "Does not matter":
                            physical_status = "Doesn't Matter"      
                    existing_user.partner_physicalstatus = physical_status
                    existing_user.save()

                    print(f"Partner physical status preference updated for user {existing_user.mlp_id}") 


                    # For Partner Height Preference
                    existing_user.partner_height_preference = False
                    existing_user.partner_height_from = None
                    existing_user.partner_height_to = None

                    height_preference = False
                    height_from = None
                    height_to = None
                    if item['height_ft_from'] and item['height_ft_to'] and item['height_inch_to'] and item['height_inch_from']:
                        height_from = (int(item['height_ft_from']) * 12 + int(item['height_inch_from'])) if item['height_inch_from'] and item['height_ft_from'] else None
                        height_to = (int(item['height_ft_to']) * 12 + int(item['height_inch_to'])) if item['height_inch_to'] and item['height_ft_to'] else None
                        if height_from is not None and height_to is not None:
                            height_preference = True
                    
                    existing_user.partner_height_preference = height_preference
                    existing_user.partner_height_from = height_from
                    existing_user.partner_height_to = height_to
                    existing_user.save()

                    print(f"height preference updated for user {existing_user.mlp_id}")


                    # For Partner Expertise Preference    
                    PartnerExpertisePreference.objects.filter(user=existing_user).delete()
                    partner_expertise_preference = False
                    medicine_names = []
                    if item['medicine_search'] and item['medicine_search'] not in ["Does not matter", "No Matter"]:
                        partner_expertise_preference = True
                        medicine_names = [medicine.strip() for medicine in item['medicine_search'].split(',')]
                    if not medicine_names:
                        partner_expertise_preference = False
                    else:
                        partner_expertise_preference = True    
                    existing_user.partner_expertise_preference = partner_expertise_preference
                    existing_user.save()

                    # For Expertise of Partner
                    if medicine_names:
                        for medicine_name in medicine_names:
                            expertise_objects = Expertise.objects.filter(name__iexact=medicine_name)
                            if expertise_objects.exists():
                                for expertise in expertise_objects:
                                    PartnerExpertisePreference.objects.create(user=existing_user, expertise=expertise)

                    print(f"Partner expertise preference updated for user {existing_user.mlp_id}")


                    # Partner Post Graduation Preference
                    PartnerPGPreference.objects.filter(user=existing_user).delete()
                    partner_post_education_preference = False
                    post_education_field_names = []
                    if item['post_education_field_search'] and item['post_education_field_search'] not in ["Does not matter", "No Matter"]:
                        partner_post_education_preference = True
                        post_education_field_names = [field.strip() for field in item['post_education_field_search'].split(',')] 
                    if not post_education_field_names:
                        partner_post_education_preference = False
                    else:
                        partner_post_education_preference = True  
                    existing_user.partner_postgraduation_preference = partner_post_education_preference
                    unique_pref = set()
                    
                    for field_name in post_education_field_names:
                        if field_name == "MCh":
                            field_name = "Mch"
                        elif field_name == "MD / MS Ayurveda":
                            field_name = "MD/MS Ayurveda"    

                        matching_object = PostGraduation.objects.filter(name__iexact=field_name).first()
                        if matching_object:
                            unique_pref.add(matching_object)
                            
                    for post_education_object in unique_pref:
                        PartnerPGPreference.objects.create(user=existing_user, post_graduation=post_education_object)
                    
                    existing_user.save()
                
                    print(f"Partner post graduation preference updated for user {existing_user.mlp_id}")

                        

                    # Partner Graduation Preference
                    PartnerGraduationPreference.objects.filter(user=existing_user).delete()
                    partner_education_preference = False
                    education_field_names = []
                    if item['education_field_search'] and item['education_field_search'] not in ["Does not matter", "No Matter"]:
                        partner_education_preference = True
                        education_field_names = [field.strip() for field in item['education_field_search'].split(',')] 
                    if not education_field_names:
                        partner_education_preference = False
                    else:
                        partner_education_preference = True    
                    existing_user.partner_graduation_preference = partner_education_preference 
                    existing_user.save()
                    
                    for field_name in education_field_names:
                        education_objects = Graduation.objects.filter(name__iexact=field_name)
                        if education_objects.exists():
                            for education in education_objects:
                                PartnerGraduationPreference.objects.create(user=existing_user, graduation=education)

                    print(f"Partner graduation preference updated for user {existing_user.mlp_id}")
                    


                    # Partner Specialization Preference
                    # Clear existing specialization preferences
                    PartnerSpecializationPreference.objects.filter(user=existing_user).delete()

                    specialization_names = []
                    partner_specialization_preference = False
                    if item['specialization_search'] and item['specialization_search'] not in ["Does not matter", "No Matter"]:
                        partner_specialization_preference = True
                        specialization_names = [specialization.strip() for specialization in item['specialization_search'].split(',')]
                    
                    if not specialization_names:
                        partner_specialization_preference = False
                    else:
                        partner_specialization_preference = True                        

                    existing_user.partner_specialization_preference = partner_specialization_preference
                    existing_user.save()
                    
                    for specialization_name in specialization_names:
                        specialization_objects = Specialization.objects.filter(name__iexact=specialization_name)
                        if specialization_objects.exists():
                            for specialization in specialization_objects:
                                PartnerSpecializationPreference.objects.create(user=existing_user, specialization=specialization)

                    print(f"Partner specialization preference updated for user {existing_user.mlp_id}")
                        
                    

                    # For partner religion Preference
                    PartnerReligionPreference.objects.filter(user=existing_user).delete()

                    religion_names = []
                    partner_religion_preference = False
                    if item['religion_search'] and item['religion_search'] not in ["Does not matter", "No Matter"]:
                        partner_religion_preference = True
                        religion_names = [religion.strip() for religion in item['religion_search'].split(',')]
                    if not religion_names:
                        partner_religion_preference = False
                    else:
                        partner_religion_preference = True   
                    existing_user.partner_religion_preference = partner_religion_preference
                    for religion_name in religion_names:
                        religion_objects = Religion.objects.filter(name__iexact=religion_name)
                        if religion_objects.exists():
                            for religion in religion_objects:
                                PartnerReligionPreference.objects.create(user=existing_user, religion=religion)
                    existing_user.save()
                    print(f"Partner religion preference updated for user {existing_user.mlp_id}")
                    


                    # For Partner Marital State Preference
                    PartnerMaritalStatusPreference.objects.filter(user=existing_user).delete()
                    partner_marital_pref = False
                    marital_preference_data = None
                    if item['second_marriage'] and item['second_marriage'] not in ["Does not matter", "No Matter"]:
                        partner_marital_pref = True
                        marital_pref_name = item['second_marriage'].strip()  
                        if marital_pref_name == "Never Married":
                            marital_pref_name = "Bachelor"
                        marital_preference_data = MaritalStatus.objects.filter(name__iexact=marital_pref_name).first()  # Get the single instance

                    existing_user.partner_marital_status_preference = partner_marital_pref   
                    if marital_preference_data:
                        PartnerMaritalStatusPreference.objects.create(user=existing_user, marital_status=marital_preference_data)
                    existing_user.save()
                
                    print(f"marital status preference updated to the user {existing_user.mlp_id}") 



                    # For Partner Mother Tongue Preference
                    existing_user.partner_mothertongue_from.clear()

                    mother_tongue_objs = []
                    partner_mother_tongue_preference = False
                    if item['mother_tongue'] and item['mother_tongue'] not in ["Does not matter", "No Matter"]:
                        partner_mother_tongue = item['mother_tongue'].split(',')
                        if partner_mother_tongue:
                            partner_mother_tongue_preference = True
                            for lang in partner_mother_tongue:
                                lang = lang.strip()
                                if lang:
                                    mother_tongue_object = MotherTongue.objects.filter(name__iexact=lang).first()
                                    if mother_tongue_object:
                                        mother_tongue_objs.append(mother_tongue_object)
                        else:
                            partner_mother_tongue_preference = False
                    if not mother_tongue_objs:
                        partner_mother_tongue_preference = False
                    else:
                        partner_mother_tongue_preference = True    
                    existing_user.partner_mothertongue_preference = partner_mother_tongue_preference
                    existing_user.partner_mothertongue_from.set(mother_tongue_objs) 
                    existing_user.save()
                    print(f"Partner mother tongue preference updated for user {existing_user.mlp_id}")
                    


                    # For Partner Caste Preference
                    existing_user.partner_caste_from = json.dumps([])  # Reset the field to empty list

                    caste_objs = []
                    partner_caste_preference = False
                    if item['caste_search'] and item['caste_search'] not in ["Does not matter", "No Matter"]:
                        partner_caste_search = item['caste_search'].split(',')
                        if partner_caste_search:
                            partner_caste_preference = True
                            for caste in partner_caste_search:
                                caste = caste.strip()
                                if caste:
                                    caste_object = Caste.objects.filter(name__iexact=caste).first()
                                    if caste_object:
                                        caste_objs.append(caste_object)
                        else:
                            partner_caste_preference = False
                    caste_names = [caste.name for caste in caste_objs]
                    # Check if caste_names is empty or None
                    if not caste_names:
                        partner_caste_preference = False
                    else:
                        partner_caste_preference = True

                    existing_user.partner_caste_preference = partner_caste_preference
                    existing_user.partner_caste_from = json.dumps(caste_names)
                    existing_user.save()

                    print(f"Partner caste preference updated for user {existing_user.mlp_id}")
                    

                    # For Partner city Preference
                    # Clear existing city preferences
                    existing_user.partner_cities_from = json.dumps([])  
                    partner_city_preference = False
                    item['city_search'] = [] if not item['city_search'] else [ele.strip() for ele in item['city_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"]]
                    if item['city_search']:
                        partner_city_preference = True
                    existing_user.partner_cities_preference = partner_city_preference 
                    existing_user.partner_cities_from = json.dumps(item['city_search'])
                    existing_user.save()

                    print(f"Partner cities preference updated for user {existing_user.mlp_id}")
                        
                    
                    # For Partner State Preference
                    # Clear existing state preferences
                    existing_user.partner_state_from = json.dumps([])  

                    partner_state_preference = False
                    item['state_field_search'] = [] if not item['state_field_search'] else [ele.strip() for ele in item['state_field_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"]]
                    if item['state_field_search']:
                        partner_state_preference = True
                    existing_user.partner_state_preference = partner_state_preference   
                    existing_user.partner_state_from = json.dumps(item['state_field_search'])
                    existing_user.save()

                    print(f"Partner state preference updated for user {existing_user.mlp_id}")

                    
                    # For Partner Country Preference
                    # Clear existing country preferences
                    existing_user.partner_country_from = json.dumps([]) 
                    
                    partner_country_preference = False
                    item['country_field_search'] = [] if not item['country_field_search'] else [ele.strip() for ele in item['country_field_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"]]
                    if item['country_field_search']:
                        partner_country_preference = True
                    existing_user.partner_country_preference = partner_country_preference    
                    existing_user.partner_country_from = json.dumps(item['country_field_search'])
                    existing_user.save()

                    print(f"Partner country preference updated for user {existing_user.mlp_id}")
                    
            else:
                print(f"User with mlp_id not exists MLP00{item['user_id']}") 

        print("user partner preference data saved")
               


    except Exception as e:
        response["error"] = str(e)
        return response  


class CreateUserView(APIView):
    def post(self, request):

        # Parse data from the request body
        data = request.data

        
        try:
            # Extract user details
            id = data.get('id')
            candidates_name = data.get('candidates_name')
            email_id = data.get('email_id')
            password = data.get('password')
            country_c = data.get('country_c',None)
            mobile = data.get('mobile',None)
            sex = data.get('sex')
            date_of_birth = data.get('date_of_birth',None)
            subscription_end_date = data.get('subscription_end_date')
            subscription_start_date = data.get('subscription_start_date')
            status = data.get('status')
            religion = data.get('religion')
            mandatory_questions_completed = data.get('mandatory_questions_completed', False)
            second_marriage = data.get('second_marriage')
            education_field = data.get('education_field','')
            post_education_field = data.get('post_education_field','')
            profile_pic = data.get('profile_pic')
            profile_pic2 = data.get('profile_pic2')
            profile_pic3 = data.get('profile_pic3')
            profile_pic4 = data.get('profile_pic4')
            profile_pic5 = data.get('profile_pic5')
            profile_pic6 = data.get('profile_pic6')
            profile_pic7 = data.get('profile_pic7')
            profile_pic8 = data.get('profile_pic8')
            profile_pic9 = data.get('profile_pic9')
            profile_pic10 = data.get('profile_pic10')
            education_field_status = data.get('education_field_status')
            post_education_field_status = data.get('post_education_field_status')
            createby = data.get('createby','')
            medicine = data.get('medicine')
            medical_registration_number = data.get('medical_registration_number')
           
            #For Mobile Number 
            if  country_c is not None:
                country_code = country_c.replace("+", "")  
                mobile_number = f"{country_code}{mobile}"
            else:
                mobile_number = f"91{mobile}" 
                
                # # For Profession
                # profession_obj = []
                # temp_professions = profession  
                # if temp_professions: 
                #     professions = temp_professions.split(',')  
                #     for profession in professions:
                #         values=profession.strip().capitalize()
                #         profession_obj.append(values)      

            # For manglik
            # manglik_value = 1 if manglik == "Yes" else 0 if manglik == "No" else -1 

            
            # For Marital State  
            marital_status_obj = None
            if second_marriage == "Never Married":
                marital_status_name = "Bachelor"
                marital_status = MaritalStatus.objects.filter(name__iexact=marital_status_name)
                if marital_status:
                    marital_status_obj = marital_status.first()
            else:
                marital_status = MaritalStatus.objects.filter(name__iexact=second_marriage)
                if marital_status:
                    marital_status_obj = marital_status.first()       

            #For completed post grad
            completed_post_grad =False
            graduation_obj = Graduation.objects.filter(name__iexact=education_field).first()
            print("graduation",graduation_obj)
            post_ed_names = [ele.strip() for ele in post_education_field.split(',')] 
            
            for ed_name in post_ed_names:
                if ed_name == "MCh":
                    ed_name = "Mch"
                elif ed_name == "MD / MS Ayurveda":
                    ed_name = "MD/MS Ayurveda"

                post_grad_objects = PostGraduation.objects.filter(name__iexact=ed_name)    
                
                if post_grad_objects.exists():
                    print(post_grad_objects)
                    completed_post_grad = True
                    break    
            print("post_grad",post_grad_objects) 
            if not post_grad_objects:
                    completed_post_grad = False

            print("before subscription")  
            can_upgrade_subscription = -1   
            if status == "Active":
                if subscription_start_date != "0000-00-00 00:00:00" and  subscription_end_date != "0000-00-00 00:00:00":
                    subscription_start_date = datetime.strptime(subscription_start_date, "%Y-%m-%d %H:%M:%S")
                    subscription_end_date = datetime.strptime(subscription_end_date, "%Y-%m-%d %H:%M:%S")


                    # Calculate the one-month window after subscription creation
                    upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                    # Check if subscription is active
                    if subscription_end_date >= datetime.now():
                        # Check if within the upgrade window
                        if datetime.now() <= upgrade_window_end_date:
                            can_upgrade_subscription = 1
                        else:
                            can_upgrade_subscription = 0
                    else:
                        can_upgrade_subscription = -1
                else:
                    can_upgrade_subscription = -1        

            profile_pictures = []
            if profile_pic:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic.strip()}")
            if profile_pic2:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic2.strip()}")
            if profile_pic3:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic3.strip()}")
            if profile_pic4:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic4.strip()}")
            if profile_pic5:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic5.strip()}")
            if profile_pic6:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic6.strip()}")
            if profile_pic7:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic7.strip()}")
            if profile_pic8:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic8.strip()}")
            if profile_pic9:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic9.strip()}")
            if profile_pic10:
                profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{id}/{profile_pic10.strip()}")
            
            print(profile_pictures)
            
            
            grad_status = None
            if education_field_status == 'complete' or education_field_status == 'completed':
                grad_status = 'Completed'
            elif education_field_status == 'ongoing' :
                grad_status = 'Ongoing' 

            post_grad_status = None
            if post_education_field_status == 'complete' or post_education_field_status == 'completed':
                post_grad_status = 'Completed'
            elif post_education_field_status == 'ongoing' :
                post_grad_status = 'Ongoing' 
            

            religion_obj= Religion.objects.filter(name__iexact=religion).first()
            expertise_ob = Expertise.objects.filter(name__iexact=medicine).first() 
            mandatory_questions_completed = True
            if (
                status == "Pending" or
                createby == '' or
                createby not in ["candidate", "family"] or
                religion_obj is None or
                candidates_name == "" or
                date_of_birth is None or
                date_of_birth == "0000-00-00" or
                sex not in ["Male", "Female"] or
                len(profile_pictures) == 0 or
                graduation_obj is None or
                expertise_ob is None or
                email_id is None or
                password is None
            ):
                mandatory_questions_completed = False      

            existing_user = User.objects.filter(mlp_id=f"MLP00{id}").first()
            if existing_user:
                print(f"User with mlp_id MLP00{id} already exists.")
                return Response({"status_code": 200, "message": "User already present"})


            print("before creating user")
            new_user=User.objects.create(
            mlp_id= f"MLP00{id}",
            name=candidates_name,
            email=email_id,
            password=password,
            mobile_number=mobile_number,
            # manglik=manglik_value,
            gender='m' if sex == "Male" else 'f',
            dob=date_of_birth if date_of_birth !="0000-00-00" else None,
            marital_status = marital_status_obj,
            profile_pictures = json.dumps(profile_pictures),
            # horoscope_matching=horoscope_matching if horoscope_matching in ["Yes", "No"] else None,
            is_active=False if status =='Remove' else True,
            is_wrong =True if  status == 'Wrong' else False,
            religion = religion_obj,
            # profession = json.dumps(profession_obj),
            is_primary_account=True,
            whatsapp_number = None,
            # specialization = specialization,
            registration_number = medical_registration_number if medical_registration_number is not None else None,
            profile_createdby ="Parent" if createby == "family" else "Candidate",
            can_upgrade_subscription=can_upgrade_subscription,
            graduation_obj=graduation_obj,
            completed_post_grad=completed_post_grad,
            mandatory_questions_completed=mandatory_questions_completed,
            # graduation_institute = item.get('graduation_institute'),
            # post_graduation_institute = item.get('post_graduation_institute'),
            post_graduation_status = post_grad_status,
            graduation_status = grad_status ,
            )

            # For User Post Graduation
            unique_post_grad_objects = set()

            for ed_name in post_ed_names:
                if ed_name == "MCh":
                    ed_name = "Mch"
                elif ed_name == "MD / MS Ayurveda":
                    ed_name = "MD/MS Ayurveda"

        
                post_grad_object = PostGraduation.objects.filter(name__iexact=ed_name).first()

                if post_grad_object:
                    unique_post_grad_objects.add(post_grad_object)

            for pg in unique_post_grad_objects:
                
                UserPostGraduation.objects.create(user=new_user, post_graduation=pg)

            print("user basic data saved successfully")

           
            return Response({"status_code": 200, "message": "User created successfully"})
        
        except Exception as e:
            logger.error("Error in CreateUserView: %s", str(e))
            return Response({"status_code": 500, "message": "Internal server error"})        




def fetch_and_store_data():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url = "https://www.medicolifepartner.com/index.php/api/sync_registration"
   # api_url= "https://www.medicolifepartner.com/index.php/api/migrate_registration"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
       
        data = api_response.json()
       # print(data)
        
        for temp_data in data['changes']['create']:
            #print(item)
            item1 = temp_data['fields']
            for item in item1:
                print("mlp_id:",f"MLP00{item['id']}")
                
                #For Mobile Number 
                if item['country_c'] is not None:
                    country_code = item['country_c'].replace("+", "")  
                    mobile_number = f"{country_code}{item['mobile']}"
                else:
                    mobile_number = f"91{item['mobile']}" 
                
                # For Profession
                profession_obj = []
                temp_professions = item.get('profession', '')  
                if temp_professions: 
                    professions = temp_professions.split(',')  
                    for profession in professions:
                        values=profession.strip().capitalize()
                        profession_obj.append(values)      

                # For manglik
                manglik_value = 1 if item['manglik'] == "Yes" else 0 if item['manglik'] == "No" else -1 

                #For physical status 
                physical_status = None
                if item['physically_challenged'] is not None:
                    if item['physically_challenged'] == "Normal" :
                        physical_status = "Normal"
                    elif item['physically_challenged'] == "Physically Challenged" :
                        physical_status = "Disabled"   

                # For SubCaste
                sub_caste=None
                subcaste=SubCaste.objects.filter(name__iexact=item['sub_caste'])
                if subcaste.exists():
                    sub_caste = subcaste.first()


                
                #For family residence
                fath_res = None
                if item['father_owned_residence'] is not None:
                    if item['father_owned_residence'] == "owned" or item['father_owned_residence'] == "Owned":
                        fath_res = "Owned"
                    elif item['father_owned_residence'] == "rented" or item['father_owned_residence'] == "Rented":
                        fath_res = "Rented"  
                        
                #For family car
                family_car = None
                if item['car'] is not None:
                    if item['car'] == "Nil":
                        family_car = "No"
                    elif item['car'] == "Own Car < 10 lacs" or item['car'] == "Own Car > 10 lacs":
                        family_car =item['car']             
                
                #For family_environment
                family_environment = None
                if item['family_env'] is not None:
                    if item['family_env'] in ["Semi Orthodox","Modern" , "Orthodox"]:
                        family_environment = item['family_env']
                
                #For body clock
                body_clock = None
                if item['wakes_up_from'] is not None:
                    if item['wakes_up_from'] == "Wakes up early":
                        body_clock = "Wakes Up Early"
                    elif item['wakes_up_from'] == "Stays awake till late night":
                        body_clock = "Stays Till Midnight"    

                #for kids
                kids_choice = None
                if item['kids'] is not None:
                    if item['kids'] == "Flexible":
                        kids_choice = "Flexible"
                    if item['kids'] == "1":
                        kids_choice = "1 kid"
                    if item['kids'] == "2":
                        kids_choice = "2 kid"
                    if item['kids'] == "No Kids":
                        kids_choice = "No Kids"            


               
                # For Marital State  
                marital_status_obj = None
                if item['second_marriage'] == "Never Married":
                    marital_status_name = "Bachelor"
                    marital_status = MaritalStatus.objects.filter(name__iexact=marital_status_name)
                    if marital_status:
                        marital_status_obj = marital_status.first()
                else:
                    marital_status = MaritalStatus.objects.filter(name__iexact=item['second_marriage'])
                    if marital_status:
                        marital_status_obj = marital_status.first()       

                #For completed post grad
                completed_post_grad =False
                graduation_obj = Graduation.objects.filter(name__iexact=item["education_field"]).first()
                print("graduation",graduation_obj)
                post_ed_names = [ele.strip() for ele in item['post_education_field'].split(',')] 
                
                for ed_name in post_ed_names:
                    if ed_name == "MCh":
                        ed_name = "Mch"
                    elif ed_name == "MD / MS Ayurveda":
                        ed_name = "MD/MS Ayurveda"

                    post_grad_objects = PostGraduation.objects.filter(name__iexact=ed_name)    
                   
                    if post_grad_objects.exists():
                        print(post_grad_objects)
                        completed_post_grad = True
                        break    
                print("post_grad",post_grad_objects) 
                if not post_grad_objects:
                     completed_post_grad = False

                print("before subscription")     
                can_upgrade_subscription = -1 
                if item['status'] == "Active":
                    # subscription_start_date = item['subscription_start_date']
                    # subscription_end_date = item['subscription_end_date']
                    subscription_start_date = datetime.strptime(item['subscription_start_date'], "%Y-%m-%d %H:%M:%S")
                    subscription_end_date = datetime.strptime(item['subscription_end_date'], "%Y-%m-%d %H:%M:%S")
                    
                    print("subscription_start",subscription_start_date)
                    print("subscription_end",subscription_end_date)

                    # Calculate the one-month window after subscription creation
                    upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                    # Check if subscription is active
                    if subscription_end_date >= datetime.now():
                        # Check if within the upgrade window
                        if datetime.now() <= upgrade_window_end_date:
                            can_upgrade_subscription = 1
                        else:
                            can_upgrade_subscription = 0
                    else:
                        can_upgrade_subscription = -1
                print("after subscription")

                profile_pictures = []
                if item['profile_pic'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic'].strip()}")
                if item['profile_pic2'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic2'].strip()}")
                if item['profile_pic3'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic3'].strip()}")
                if item['profile_pic4'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic4'].strip()}")
                if item['profile_pic5'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic5'].strip()}")
                if item['profile_pic6'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic6'].strip()}")
                if item['profile_pic7'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic7'].strip()}")
                if item['profile_pic8'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic8'].strip()}")
                if item['profile_pic9'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic9'].strip()}")
                if item['profile_pic10'].strip():
                    profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{item['id']}/{item['profile_pic10'].strip()}")
                
                print(profile_pictures)
                # For specialization
                specialization = None
                specializations = Specialization.objects.filter(name__iexact=item['specialization'])
                if specializations.exists():
                    specialization = specializations.first()  
                    
                # For mother tongue
                spoken_languages = item['spoken_language'].split(',')
                mother_tongues = []
                for lang in spoken_languages:
                    lang = lang.strip()
                    if lang:
                        mother_tongue = MotherTongue.objects.filter(name__iexact=lang).first()
                        if mother_tongue:
                            mother_tongues.append(mother_tongue)
                
                # video = []
                # if item['video'] != "":
                #     video.append(item['video'])
                
                grad_status = None
                if item.get('education_field_status') == 'complete' or item.get('education_field_status') == 'completed':
                    grad_status = 'Completed'
                elif item.get('education_field_status') == 'ongoing' :
                    grad_status = 'Ongoing' 

                post_grad_status = None
                if item.get('post_education_field_status') == 'complete' or item.get('post_education_field_status') == 'completed':
                    post_grad_status = 'Completed'
                elif item.get('post_education_field_status') == 'ongoing' :
                    post_grad_status = 'Ongoing' 

               
                # For Hobbies
                hobbies = []
                if item['hobbies'] and ',' in item['hobbies']:
                    hobbies = [h.strip() for h in item['hobbies'].split(',') if h.strip()]

                religion_obj= Religion.objects.filter(name__iexact=item['religion']).first()
                expertise_ob = Expertise.objects.filter(name__iexact=item['medicine']).first() 
                mandatory_questions_completed = True
                if (
                    item['status'] == "Pending" or
                    item['createby'] == '' or
                    item['createby'] not in ["candidate", "family"] or
                    religion_obj is None or
                    item["candidates_name"] == "" or
                    item.get("date_of_birth") is None or
                    item['sex'] not in ["Male", "Female"] or
                    len(profile_pictures) == 0 or
                    graduation_obj is None or
                    expertise_ob is None or
                    item['email_id'] is None or
                    item['password'] is None
                ):
                  mandatory_questions_completed = False      

                existing_user = User.objects.filter(mlp_id=f"MLP00{item['id']}").first()
                if existing_user:
                    print(f"User with mlp_id MLP00{item['id']} already exists.")
                    continue


                print("before creating user")
                new_user=User.objects.create(
                mlp_id= f"MLP00{item['id']}",
                name=item['candidates_name'],
                email=item['email_id'],
                password=item['password'],
                mobile_number=mobile_number,
                manglik=manglik_value,
                gender='m' if item['sex'] == "Male" else 'f',
                weight = item['weight'] if item['weight'] is not None else 0,
                dob=item['date_of_birth'],
                time_birth = str(item['time_of_birth']) if item['time_of_birth'] != "00:00:00" else None,
               # body_build = item['body_build'] if item['body_build'] is not None else None,
               # complexion = item['complexion'] if item['complexion'] is not None else None,
                blood_group = item['blood_group'] if item['blood_group'] is not None else None,
               # disease_history = item['disease'] if item['disease'] is not None else None,
                schooling_details = item['schooling'] if item['schooling'] is not None else None,
                facebook_profile = item['facebook_link'] if item['facebook_link'] is not None else None,
                linkedin_profile = item['linkedin'] if item['linkedin'] is not None else None,
                birth_location=item['birth_location'],
                height=int(item['height_ft'])*12 + int(item['height_inch']),
               # salary=item['salary'],
                caste=item['caste'] if item['caste'] is not None else None, 
                sub_caste=sub_caste,
                marital_status = marital_status_obj,
                hobbies = json.dumps(["Others"]) if hobbies not in [None, '', []] else json.dumps([]),
                other_hobbies = json.dumps(hobbies),
                profile_pictures = json.dumps(profile_pictures),
                city = item['city'] if  item['city'] != "Please Select State"  or item['city'] != "Select City" or item['city'] != "Select State" or item['city'] != "Please+Select+State" else None,
               # state = item['state'],
               # country = item['country'], 
                horoscope_matching=item['horoscope_matching'] if item['horoscope_matching'] in ["Yes", "No"] else None,
                future_aspirations=item['candi_future_aspiration'],
                about=item['candi_describing_myself'],
                is_active=False if item['status'] =='Remove' or item['status'] == "Pending" else True,
                is_wrong =True if  item['status']=='Wrong' else False,
                religion = Religion.objects.filter(name__iexact=item['religion']).first() if item['religion'] else None,
                physical_status = physical_status,
              #  eyesight = item['eye_sight'] if item['eye_sight'] is not None else None,
                city_parents = item['father_resided_city'] if item['father_resided_city'] is not None else None,
               # residence =  item['res_address'] if item['res_address'] is not None else None,
                family_house = fath_res,
                family_car = family_car,
                family_environment = family_environment,
                body_clock = body_clock,
                kids_choice = kids_choice,
                profession_description = item['profession_details'] if item['profession_details'] is not None else None,
                profession = json.dumps(profession_obj),
                is_primary_account=True,
                whatsapp_number = None,
                specialization = specialization,
                registration_number = item['medical_registration_number'] if item['medical_registration_number'] is not None else None,
                profile_createdby ="Parent" if item['createby'] == "family" else "Candidate",
                mother_name = item['mother_name'] if item['mother_name'] is not None else None,
                father_name = item['father_name'] if item['father_name'] is not None else None,
                father_occupation = item['father_profession'] if item['father_profession'] is not None else None,
                mother_occupation = item['mother_profession'] if item['mother_profession'] is not None else None,
                father_education = item['father_education'] if item['father_education'] is not None else None,
                mother_education = item['mother_education'] if item['mother_education'] is not None else None,
               # nature = item['nature'] if item['nature'] is not None else None,
                can_upgrade_subscription=can_upgrade_subscription,
                graduation_obj=graduation_obj,
                completed_post_grad=completed_post_grad,
                mandatory_questions_completed=mandatory_questions_completed,
                graduation_institute = item.get('graduation_institute'),
                post_graduation_institute = item.get('post_graduation_institute'),
                post_graduation_status = post_grad_status,
                graduation_status = grad_status ,
                )
                print("Here")
                new_user.languages.set(Languages.objects.filter(name__iexact=item['language']))
                new_user.mother_tongue.set(mother_tongues)

                # For User Post Graduation
                unique_post_grad_objects = set()

                for ed_name in post_ed_names:
                    if ed_name == "MCh":
                        ed_name = "Mch"
                    elif ed_name == "MD / MS Ayurveda":
                        ed_name = "MD/MS Ayurveda"

            
                    post_grad_object = PostGraduation.objects.filter(name__iexact=ed_name).first()

                    if post_grad_object:
                        unique_post_grad_objects.add(post_grad_object)

                for pg in unique_post_grad_objects:
                    
                    UserPostGraduation.objects.create(user=new_user, post_graduation=pg)

                print("user basic data saved successfully")


                 #For siblings
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name1', 'candi_bro_education1', 'candi_bro_profession1', 'candi_bro_marital_status1']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name1'][:100], sibling_education=item['candi_bro_education1'][:100], sibling_marital_status =item['candi_bro_marital_status1'][:30] ,   sibling_profession = item['candi_bro_profession1'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name2', 'candi_bro_education2', 'candi_bro_profession2', 'candi_bro_marital_status2']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name2'][:100], sibling_education=item['candi_bro_education2'][:100], sibling_marital_status =item['candi_bro_marital_status2'][:30] ,   sibling_profession = item['candi_bro_profession2'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name3', 'candi_bro_education3', 'candi_bro_profession3', 'candi_bro_marital_status3']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name3'][:100], sibling_education=item['candi_bro_education3'][:100], sibling_marital_status =item['candi_bro_marital_status3'][:30] ,   sibling_profession = item['candi_bro_profession3'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name4', 'candi_bro_education4', 'candi_bro_profession4', 'candi_bro_marital_status4']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name4'][:100], sibling_education=item['candi_bro_education4'][:100], sibling_marital_status =item['candi_bro_marital_status4'][:30] ,   sibling_profession = item['candi_bro_profession4'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_bro_name5', 'candi_bro_education5', 'candi_bro_profession5', 'candi_bro_marital_status5']):
                    Siblings.objects.create(user=new_user, sibling_gender='m', sibling_name=item['candi_bro_name5'][:100], sibling_education=item['candi_bro_education5'][:100], sibling_marital_status =item['candi_bro_marital_status5'][:30] ,   sibling_profession = item['candi_bro_profession5'][:100])


                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name1', 'candi_sis_education1', 'candi_sis_profession1', 'candi_sis_marital_status1']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name1'][:100], sibling_education=item['candi_sis_education1'][:100], sibling_marital_status =item['candi_sis_marital_status1'][:30] ,   sibling_profession = item['candi_sis_profession1'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name2', 'candi_sis_education2', 'candi_sis_profession2', 'candi_sis_marital_status2']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name2'][:100], sibling_education=item['candi_sis_education2'][:100], sibling_marital_status =item['candi_sis_marital_status2'][:30] ,   sibling_profession = item['candi_sis_profession2'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name3', 'candi_sis_education3', 'candi_sis_profession3', 'candi_sis_marital_status3']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name3'][:100], sibling_education=item['candi_sis_education3'][:100], sibling_marital_status =item['candi_sis_marital_status3'][:30] ,   sibling_profession = item['candi_sis_profession3'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name4', 'candi_sis_education4', 'candi_sis_profession4', 'candi_sis_marital_status4']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name4'][:100], sibling_education=item['candi_sis_education4'][:100], sibling_marital_status =item['candi_sis_marital_status4'][:30] ,   sibling_profession = item['candi_sis_profession4'][:100])
                if all(item.get(key) not in [None, ''] for key in ['candi_sis_name5', 'candi_sis_education5', 'candi_sis_profession5', 'candi_sis_marital_status5']):
                    Siblings.objects.create(user=new_user, sibling_gender='f', sibling_name=item['candi_sis_name5'][:100], sibling_education=item['candi_sis_education5'][:100], sibling_marital_status =item['candi_sis_marital_status5'][:30] ,   sibling_profession = item['candi_sis_profession5'][:100])
            
                
                sibling = Siblings.objects.filter(user=new_user).exists()
                if sibling :
                    new_user.sibling = 1
                new_user.save()     
                print("sibling data added successfully")

                name = None
                phone= None
                photo= None
                salary = None
                email = None
                if new_user.email:
                    email = new_user.email
                if item["privacy_name"] == "interest_accepted":
                    name = "interests"
                if item["privacy_name"] == "to_all_subscribe":
                    name = "paid"     
                if item["privacy_phone"] == "interest_accepted":
                    phone = "interests"
                if item["privacy_phone"] == "to_all_subscribe":
                    phone = "paid"    
                if item["privacy_photo"] == "to_all":
                    photo = "all" 
                if item["privacy_photo"] == "to_all_subscribe":
                    photo = "paid"    
                if item["privacy_photo"] == "interest_accepted":
                    photo= "interests"
                if item["privacy_salary"] == "to_all_subscribe" or item["privacy_salary"] == "to_all_subscribe_registered":
                    salary = "paid"    
                if item["privacy_salary"] == "interest_accepted":
                    salary= "interests"
                NotificationSettings.objects.create(user=new_user,email_notifications="",name=name,phone=phone,photo=photo, salary=salary, email=email)
                print("new user notification settings added successfully")
        response['status_code'] = 200
        response['message'] = "User data sync successfully"
        return response    
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

def delete_duplicate_pg():
    # Step 1: Identify duplicates and determine which to keep
    duplicates = (
        UserPostGraduation.objects.values('user', 'post_graduation')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )

    
    for entry in duplicates:
        user = entry['user']
        post_graduation = entry['post_graduation']

        # Get all duplicate records for this combination
        duplicate_records = (
            UserPostGraduation.objects
            .filter(user=user, post_graduation=post_graduation)
            .order_by('id')  # Ensure that the record you want to keep is the first
        )
        
       # Keep the first record and delete the rest
        records_to_delete_ids = duplicate_records.values_list('id', flat=True)[1:]

        # Delete the extra duplicates using the IDs
        UserPostGraduation.objects.filter(id__in=records_to_delete_ids).delete()

    print("Duplicates removed successfully.") 




@shared_task
def send_notifications_promotion(promotion_id):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
        promotion = Promotions.objects.get(id=promotion_id)
        print("promotion",promotion)
        #if sent == True then function return
        if promotion.sent:
            return
        
        if promotion.users=="all":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                Notifications.objects.create(
                    user=user,
                    message=promotion.message_body,
                    type="promotion"
                )
                custom_data={
                    "screen":"promotions",
                    "userid":user.mlp_id
                    }
                if user.notification_token!=None:
                    message = messaging.Message(
                        token=user.notification_token,  # FCM registration token
                        notification=messaging.Notification(
                            title=promotion.message_title,
                            body=promotion.message_body
                        ),
                        data=custom_data  # Custom data payload
                    )

                    messaging.send(message)
                    
                    # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                
                notificationtokens=[]
                for i in all_linked_users:
                    if i.linked_user.notification_token:
                        notificationtokens.append(i.linked_user.notification_token) 
                
                if notificationtokens:
                    message = messaging.MulticastMessage(
                    tokens=notificationtokens,  # List of FCM registration tokens
                    notification=messaging.Notification(
                        title=promotion.message_title,
                        body=promotion.message_body,
                    ),
                    data=custom_data
                    )
                    res= messaging.send_multicast(message)
                    # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="silverregular":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if existing_subscription and existing_subscription.subscription.name=="Silver" and existing_subscription.subscription.regular_plan==True:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                    if user.notification_token!=None:
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body,
                            ),
                            data = custom_data
                        )
                        res= messaging.send_multicast(message)
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="goldregular":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if existing_subscription and existing_subscription.subscription.name=="Gold" and existing_subscription.subscription.regular_plan==True:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                    if user.notification_token!=None:
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                        tokens=notificationtokens,  # List of FCM registration tokens
                        notification=messaging.Notification(
                            title=promotion.message_title,
                            body=promotion.message_body,
                        ),
                        data=custom_data
                        )
                        res= messaging.send_multicast(message)
                        
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="platinumregular":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if existing_subscription and existing_subscription.subscription.name=="Platinum" and existing_subscription.subscription.regular_plan==True:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    if user.notification_token!=None:
                        custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body,
                            ),
                            data=custom_data
                            )
                        res= messaging.send_multicast(message)
                        
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="silver":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if existing_subscription and existing_subscription.subscription.name=="Silver" and existing_subscription.subscription.regular_plan==False:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                    if user.notification_token!=None:
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body,
                            ),
                            data=custom_data
                        )
                        res= messaging.send_multicast(message)
                        
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="gold":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if existing_subscription and existing_subscription.subscription.name=="Gold" and existing_subscription.subscription.regular_plan==False:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                    if user.notification_token!=None:
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body,
                            ),
                            data=custom_data
                        )
                        res= messaging.send_multicast(message)
                        
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="platinum":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if existing_subscription and existing_subscription.subscription.name=="Platinum" and existing_subscription.subscription.regular_plan==False:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                    if user.notification_token!=None:
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body,
                            ),
                            data=custom_data
                            )
                        res= messaging.send_multicast(message)
                        
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="premium":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if existing_subscription and existing_subscription.subscription.name=="Premium" and existing_subscription.subscription.regular_plan==False:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                    if user.notification_token!=None:
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body,
                            ),
                        data=custom_data
                        )
                        res= messaging.send_multicast(message)
                        
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()
        elif promotion.users=="Noplans":
            all_users = User.objects.filter(is_active=True, is_wrong=False)
            for user in all_users:
                existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
                if not existing_subscription:
                    
                    Notifications.objects.create(
                        user=user,
                        message=promotion.message_body,
                        type="promotion"
                    )
                    
                    custom_data={
                        "screen":"promotions",
                        "userid":user.mlp_id
                        }
                    if user.notification_token!=None:
                        message = messaging.Message(
                            token=user.notification_token,  # FCM registration token
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body
                            ),
                            data=custom_data  # Custom data payload
                        )
                        messaging.send(message)
                        
                        # push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
                    all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
                    notificationtokens=[]
                    for i in all_linked_users:
                        if i.linked_user.notification_token:
                            notificationtokens.append(i.linked_user.notification_token) 
                    
                    if notificationtokens:
                        message = messaging.MulticastMessage(
                            tokens=notificationtokens,  # List of FCM registration tokens
                            notification=messaging.Notification(
                                title=promotion.message_title,
                                body=promotion.message_body,
                            ),
                            data=custom_data
                        )
                        res= messaging.send_multicast(message)
                        
                        # push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
            promotion.sent=True
            promotion.save()

    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        # traceback.print_exc()
        return response

from rest_framework.views import APIView
from rest_framework.response import Response
class UsersWithSubscriptionAPIView(APIView):
    def get(self, request):
        try:
            # Fetch subscriptions
            subs = UserSubscription.objects.all()
            data = []

            # Iterate and collect data
            for sub in subs:
                if sub.user.can_upgrade_subscription !=-1:
                    res = {
                        'mlp_id': sub.user.mlp_id,
                        'name': sub.user.name,
                        'phone_number': sub.user.mobile_number[-10:],
                        'religion' : sub.user.religion.name if sub.user.religion else None,
                        'can_upgrade_subscription' : sub.user.can_upgrade_subscription,
                        'marital_status' : sub.user.marital_status.name if sub.user.marital_status else None,
                        'is_active' : sub.user.is_active,
                        'is_wrong' : sub.user.is_wrong
                    }
                    data.append(res)

            return Response({
                'status_code': 200,
                'message': "User with subscription data",
                'data': data,
            })

        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return Response({
                'status_code': 500,
                'message': "Internal Server Error",
            })

from django.utils.timezone import make_aware
class UsersWithProvisionalAPIView(APIView):
    def get(self, request):
        try:
            # Fetch users
            cutoff_date = make_aware(datetime.strptime("2024-12-06", "%Y-%m-%d"))

            users = User.objects.filter(mandatory_questions_completed=True,is_active=True,is_wrong=False, created_date__gte=cutoff_date)
            data = []
          
            # Iterate and collect data
            for sub in users:
                if sub.can_upgrade_subscription == -1:
                    res = {
                        'mlp_id': sub.mlp_id,
                        'name': sub.name,
                        'phone_number': sub.mobile_number[-10:],
                        'can_upgrade_subscription' : sub.can_upgrade_subscription,
                        'mandatory_questions_completed' : sub.mandatory_questions_completed,
                        'is_active' : sub.is_active,
                        'is_wrong' : sub.is_wrong,
                        'created_at': sub.created_date,
                        'updated_at':sub.updated_date
                    }
                    data.append(res)

            return Response({
                'status_code': 200,
                'message': "User with provisonal status data",
                'data': data,
            })

        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return Response({
                'status_code': 500,
                'message': "Internal Server Error",
            })