
import json
from rest_framework.views import APIView

from users.models import BachelorOfTheDay, BlockedUsers, ConnectionList, Intrest, ProfileView, SavedUser, User, UserSubscription
from django.contrib.postgres.aggregates import ArrayAgg
from .models import SearchResult, UserSearchHistory
from .serializers import SearchResultSerializer
from django.http import JsonResponse
import logging
from datetime import datetime, date, timedelta
from users.utils import show_data ,show_data_photo , show_name, show_name_data , show_photographs, show_photographs_data
import time
from django.db.models import Q,F, Case, When, IntegerField, ExpressionWrapper,Exists, OuterRef, Value
# from django.contrib.postgres.aggregates import ArrayAgg
from django.utils import timezone

logger = logging.getLogger("error_logger")


class UserSearchView(APIView):


    # get request can take multiple params and filter the data accordingly
    def get(self, request, *args, **kwargs):
        response = {
            "status_code": 500,
            "message": "Internal Server Error"
        }
        
        try:
            mlp_id = kwargs.get('mlp_id', None)
            if mlp_id is None:
                response['status_code'] = 400
                response['message'] = 'mlp_id parameter is missing in the URL'
                return JsonResponse(response)
            
 
            # Fetch the user with the given mlp_id
            authenticated_user = User.objects.filter(
                    mlp_id=mlp_id,
                    is_active=True,
                    is_wrong=False,
                    mandatory_questions_completed=True
                ).first()
              

            if authenticated_user is None:
                response['status_code'] = 404
                response['message'] = 'User not found'
                return JsonResponse(response)
            

            # Extract query parameters from the request
            params = self.request.query_params
            
            page = int(params.get('page', 1))
            page_size = int(params.get('page_size', 5))

            opp_gender = 'f' if authenticated_user.gender == 'm' else 'm'
            
            blocked_users_mlp_ids = BlockedUsers.objects.filter(user__mlp_id=authenticated_user.mlp_id).values_list('blocked_user__mlp_id', flat=True)

            queryset= User.objects.annotate(
                post_graduations=ArrayAgg('partnerpostgraduationpreference__post_graduation__name')   
                ).filter(
                      is_active=True, is_wrong=False, mandatory_questions_completed=True,gender=opp_gender).exclude(mlp_id__in=blocked_users_mlp_ids).distinct()
               

            # Filter based on the keyword passed in the search box
            keyword = params.get('keyword', None)

            DRINKING_MAP = {
                "non drinker": "nd",
                "social drinker": "sd",
                "occasional drinker": "od",
                "regular drinker": "rd",
            }

            SMOKING_MAP = {"non smoker": "ns",
                           "occasional smoker": "os",
                           "regular smoker": "rs",
                           "trying to quit": "tq",
                           }

            EATING_MAP = {"vegetarian": "veg",
                          "veg":"veg",
                          "vege":"veg",
                          "non vegetarian": "non_veg",
                          "non-veg":"non_veg",
                          "non_veg":"non_veg",
                          "nonveg": "non_veg",
                          "non veg":"non_veg",
                          "eggitarian":"eggitarian",
                          "veg & egg": "eggitarian",
                          "veg and egg": "eggitarian",
                          "veg+egg":"eggitarian",
                          "jain": "jain"
                          }
           
            is_premium_user= UserSubscription.objects.filter(
                user=authenticated_user, is_subscription_active=True
            ).exists() 

            queryset1= queryset

            if keyword:
                #users_found = set()
                keyword_lower =keyword 
                if keyword in EATING_MAP:
                   keyword_lower = EATING_MAP.get(keyword.lower())
                if keyword in SMOKING_MAP:   
                   keyword_lower = SMOKING_MAP.get(keyword.lower())
                if keyword in DRINKING_MAP:   
                   keyword_lower = DRINKING_MAP.get(keyword.lower())

                print(keyword_lower)

                normalized_keywords = keyword_lower.split()
                premium_filter_query = Q()  
                keyword_filter_query = Q()
                keyword_count = 0 
                
                print(normalized_keywords)
                # Construct keyword filter query
                for normalized_keyword in normalized_keywords:
                    if normalized_keyword == "lpa" or normalized_keyword == "LPA":
                       continue

                    if keyword_count >= 2:  
                        break 

                    keyword_count += 1

                    print(normalized_keyword)

                    # Add premium name filter if the user is premium
                    if is_premium_user:
                        premium_filter_query |= Q(name__icontains=normalized_keyword)
                    keyword_filter_query |= (
                        Q(city__icontains=normalized_keyword) |
                        Q(caste__icontains=normalized_keyword) |
                        Q(mlp_id__iexact=normalized_keyword) |
                        Q(religion__name__icontains=normalized_keyword) |
                        Q(marital_status__name__icontains=normalized_keyword) |
                        Q(state__icontains=normalized_keyword) |
                        Q(country__icontains=normalized_keyword) |
                        Q(sub_caste__name__icontains=normalized_keyword) |
                        Q(specialization__name__icontains=normalized_keyword) |
                        Q(about__icontains=normalized_keyword) |  
                        Q(future_aspirations__icontains=normalized_keyword) |
                        Q(graduation_obj__name__icontains=normalized_keyword) |
                        Q(partnerpostgraduationpreference__post_graduation__name__icontains=normalized_keyword) |
                        Q(graduation_obj__expertise_obj__name__icontains=normalized_keyword) |
                        Q(profession__icontains=normalized_keyword) |
                        Q(graduation_institute__icontains=normalized_keyword) |
                        Q(post_graduation_institute__icontains=normalized_keyword) |
                        Q(hobbies__icontains=normalized_keyword) |
                        Q(other_hobbies__icontains=normalized_keyword) |
                        Q(profession__icontains=normalized_keyword) |
                        Q(profession_description__icontains=normalized_keyword) |
                        Q(complexion__icontains=normalized_keyword) |
                        Q(body_build__icontains=normalized_keyword) |
                        Q(nature__icontains=normalized_keyword) |
                        Q(schooling_details__icontains=normalized_keyword) |
                        Q(physical_status__icontains=normalized_keyword) |
                        Q(drinking_habits__iexact=normalized_keyword) |
                        Q(eating_habits__iexact=normalized_keyword) |
                        Q(smoking_habits__iexact=normalized_keyword) |
                        Q(mother_name__icontains=normalized_keyword) |
                        Q(mother_occupation__icontains=normalized_keyword) |
                        Q(mother_education__icontains=normalized_keyword) |
                        Q(father_name__icontains=normalized_keyword) |
                        Q(father_occupation__icontains=normalized_keyword) |
                        Q(father_education__icontains=normalized_keyword) |
                        Q(family_financial_status__icontains=normalized_keyword) |
                        Q(family_environment__icontains=normalized_keyword) |
                        Q(family_car__icontains=normalized_keyword) |
                        Q(city_parents__icontains=normalized_keyword) |
                        Q(family_house__icontains=normalized_keyword) |
                        Q(own_car__icontains=normalized_keyword) |
                        Q(residence__icontains=normalized_keyword) |
                        Q(religious_practices__icontains=normalized_keyword) |
                        # Q(interest_party__icontains=normalized_keyword) |
                        # Q(interest_music__icontains=normalized_keyword) |
                        Q(nature__icontains=normalized_keyword) |
                        Q(eyesight__icontains=normalized_keyword) |
                        # Q(graduation_status__icontains=normalized_keyword) |
                        Q(salary__icontains=normalized_keyword) |
                        Q(disease_history__icontains=normalized_keyword) 
                    )

                # Apply filters to queryset
                matching_users = queryset1.filter(keyword_filter_query | premium_filter_query).distinct()

                # Filter the queryset based on mlp_ids and exclude the authenticated user
                queryset =  matching_users.filter(is_active=True, is_wrong=False, mandatory_questions_completed=True).exclude(mlp_id=authenticated_user.mlp_id)
               
               
            #filtering data of users by age range  
            if 'age_from' in params and 'age_to' in params:
                age_from = int(params.get('age_from'))
                age_to = int(params.get('age_to'))
                today = date.today()
                queryset = queryset.annotate(
                    user_age=ExpressionWrapper(
                        today.year - F('dob__year') -
                        Case(
                            When(
                                dob__month__gt=today.month,
                                then=1
                            ),
                            When(
                                dob__month=today.month,
                                dob__day__gt=today.day,
                                then=1
                            ),
                            default=0,
                            output_field=IntegerField()
                        ),
                        output_field=IntegerField()
                    )
                ).filter(user_age__gte=age_from, user_age__lte=age_to)
               

            #filter data of users from queryset by caste
            if 'caste' in params:
                if authenticated_user.caste:
                    caste_values = params['caste'].split(',')
                    query = Q()
                    for caste_value in caste_values:
                        query |= Q(caste__icontains=caste_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the caste field first"
                    return JsonResponse(response)
                
                
            #filter data of users from queryset by sub_caste
            if 'sub_caste' in params:
                if authenticated_user.sub_caste:
                    sub_caste_ids = params.get('sub_caste').split(',')
                    queryset = queryset.filter(sub_caste__in=sub_caste_ids)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the sub_caste field first"
                    return JsonResponse(response)
                

            #filter data of users by their religion
            if 'religion' in params:
                if authenticated_user.religion:
                    religion_values = params['religion'].split(',')
                    query = Q()
                    for religion_value in religion_values:
                        query |= Q(
                            religion__name__icontains=religion_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the religion field first"
                    return JsonResponse(response)
                

            #filter data of users by their city
            if 'city' in params:
                cities_param = params['city']
                
                if authenticated_user.city:
                    cities = cities_param.split(',')
                    query = Q()
                    for city in cities:
                        query |= Q(city__icontains=city.strip())  
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the city field first"
                    return JsonResponse(response)

                
            
            #filter data of users by their country
            if 'country' in params:
                countries_param = params['country']
                
                # Split the countries_param into a list
                countries = countries_param.split(',')
                
                # Replace country names based on the given conditions
                replacements = {
                    "USA": "United States",
                    "UK": "United Kingdom",
                    "UAE": "United Arab Emirates"
                }
                
                countries = [replacements.get(country.strip(), country.strip()) for country in countries]

                if authenticated_user.country:
                    query = Q()
                    for country in countries:
                        query |= Q(country__icontains=country)
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the country field first"
                    return JsonResponse(response)

                     
            #filter data of users from queryset by states
            if 'state' in params:
                states_param = params['state']
                
                if authenticated_user.state:
                    states = states_param.split(',')
                    query = Q()
                    for state in states:
                        query |= Q(state__icontains=state.strip())  
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the state field first"
                    return JsonResponse(response)

            
            #filter data of users from queryset by marital_status
            if 'marital_status' in params and params['marital_status']:
                if authenticated_user.marital_status:  
                    marital_status_values = params['marital_status'].split(',')
                    query = Q()
                    for marital_status_value in marital_status_values:
                        if marital_status_value.strip():
                            try:
                                query |= Q(marital_status=int(marital_status_value))
                            except ValueError:
                                response['status_code'] = 400
                                response['message'] = f"Invalid marital status value: {marital_status_value}"
                                return JsonResponse(response)
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the marital_status field first"
                    return JsonResponse(response)
            
            

            #filter data based on specialization
            if 'specialization' in params:
                # if authenticated_user.specialization:
                specialization_ids = params.get('specialization').split(',')
                queryset = queryset.filter(specialization__in=specialization_ids)
                # else:
                #     response['status_code'] = 300
                #     response['message'] = "Please provide info for the specialization field first"
                #     return JsonResponse(response)
                
                
            #filter data from queryset by profession
            if 'profession' in params:
                profession_query = params['profession'].split(',')  # Get profession value from params
                query = Q()
                if authenticated_user.profession:
                    for prof in profession_query:
                        query |= Q(profession__icontains=prof.strip())

                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the profession field first"
                    return JsonResponse(response)


             # Education related filtering
            if 'graduation' in params:
                if  authenticated_user.graduation_obj:
                    graduation_values = params['graduation'].split(',')
                    query = Q()
                    for graduation_value in graduation_values:
                        query |= Q(graduation_obj__name__icontains=graduation_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide information for the graduation field first"
                    return JsonResponse(response)


            if 'post_graduation' in params:
                    post_graduation_values = params['post_graduation'].split(',')
                    query = Q()
                    for post_graduation_value in post_graduation_values:
                        query |= Q(partnerpostgraduationpreference__post_graduation__name__icontains=post_graduation_value.strip())
                    queryset = queryset.filter(query)
                 

            if 'expertise' in params:
                if authenticated_user.graduation_obj:
                    expertise_values = params['expertise'].split(',')
                    query = Q()
                    for expertise_value in expertise_values:
                        query |= Q(graduation_obj__expertise_obj__name__icontains=expertise_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the expertise field first"
                    return JsonResponse(response)

            #get the values of filter used by authenticated user
            # new_filters = {
            #     'city': self.request.query_params.get('city'),
            #     'caste': self.request.query_params.get('caste'),
            #     'sub_caste': self.request.query_params.get('sub_caste'),
            #     'religion': self.request.query_params.get('religion'),
            #     'age_from': self.request.query_params.get('age_from'),
            #     'age_to': self.request.query_params.get('age_to') ,
            #     'marital_status': self.request.query_params.get('marital_status'),
            #     'state': self.request.query_params.get('state'),
            #     'country': self.request.query_params.get('country'),
            #     'graduation': self.request.query_params.get('graduation'),
            #     'post_graduation': self.request.query_params.get('post_graduation'),
            #     'expertise': self.request.query_params.get('expertise'),
            #     'specialization': self.request.query_params.get('specialization'),
            #     'profession': self.request.query_params.get('profession'),
            # }
            
            # if queryset is empty then return response "No content found"
            if not queryset.exists():
                response['status_code'] = 204
                response['message'] = 'No Content Found'
                return JsonResponse(response)
            
              
            #serializing the data
            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day( authenticated_user.religion, opp_gender)
            # Apply pagination
            queryset = queryset.values(
                'mlp_id','name','email', 'dob','mobile_number','gender', 'religion__name','caste','profile_pictures','family_photos','activity_status', 'eating_habits','drinking_habits','smoking_habits',
                "marital_status__name", 'last_seen','completed_post_grad','height', 'weight' , 'hobbies','other_hobbies', 'city', "post_graduations","usersubscription__subscription__name",
                "graduation_obj__name","graduation_obj__expertise_obj__name","notification_settings__name","notification_settings__photo","usersubscription__subscription__amount"
            )
            
            queryset = queryset.order_by('-last_seen')
            queryset= queryset.order_by('-usersubscription__subscription__amount')
            
            total_items = queryset.count()

            start_index = (page - 1) * page_size
            end_index = page * page_size
            paginated_queryset = queryset[start_index:end_index]
           
            serializer_data = []
            today = date.today() 
            for user in paginated_queryset:
                mlp_id = user.get("mlp_id")
                
               # user_post_graduation = user.partnerpostgraduationpreference.all()    

                is_bachelor = False
                if bachelor_of_the_day and user.get("mlp_id") == bachelor_of_the_day.user.mlp_id:
                    is_bachelor = True
                
                # res = show_data(is_premium_user, user.get("notification_settings__name"),authenticated_user.get("mlp_id"),user.get("mlp_id"))
                # if res and res["status_code"] == 200:
                #     name_hidden = False
                # else:
                #     name_hidden = True

                # res = show_data_photo(is_premium_user, user.get("notification_settings__photo"),authenticated_user.get("mlp_id"),user.get("mlp_id"))
                # if res:
                #     if res["status_code"] == 200:
                #         photo_hidden = False
                #     else:
                #         photo_hidden = True
                user1 = User.objects.filter(mlp_id = user.get("mlp_id")).first()
                res = show_name(authenticated_user,user1)
    
                if res:
                    if res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True

                res = show_photographs(authenticated_user,user1)
    
                if res:
                    if res["status_code"] == 200:
                        photo_hidden = False
                    else:
                        photo_hidden = True
                age = today.year - user.get("dob").year - ((today.month, today.day) < (user.get("dob").month, user.get("dob").day))   
                data = {
                    'mlp_id': user.get('mlp_id'),
                    'name': user.get('mlp_id') if name_hidden else user.get("name"),
                    'subscription_name' : user.get('usersubscription__subscription__name'),
                    'email': user.get("email"),
                    'mobile_number': user.get("mobile_number"),
                    'eating_habits':user.get('eating_habits'),
                    'drinking_habits':user.get('drinking_habits'),
                    'smoking_habits' : user.get('smoking_habits'),
                    'gender': user.get("gender"),
                    'religion': user.get("religion__name") if user.get("religion__name") else None,
                    'marital_status': user.get("marital_status__name") if user.get("marital_status__name") else None,
                    'caste': user.get("caste"),
                    'dob': user.get("dob"),
                    'age':age,
                    'profile_pictures': json.loads(user.get("profile_pictures")),
                    'family_photos': json.loads(user.get("family_photos")),
                    'activity_status': user.get("activity_status"),
                    'last_seen': user.get("last_seen"),
                    'completed_post_grad': user.get("completed_post_grad"),
                    'height': user.get("height"),
                    'weight': user.get("weight"),
                    'hobbies': json.loads(user.get("hobbies")),
                    'other_hobbies': json.loads(user.get("other_hobbies")),
                    'city': user.get("city"),
                }

                user_graduation = user.get("graduation_obj__name") if user.get("graduation_obj__name") else None

               
                user_expertise = user.get("graduation_obj__expertise_obj__name") 

                data['graduation_id'] = user_graduation
                data['user_post_graduation'] = user.get("post_graduations") if user.get("completed_post_grad") else []
                data['expertise_id'] = user_expertise
                data['interest_sent'] = Intrest.objects.filter(invitation_by__mlp_id=authenticated_user.mlp_id, invitation_to__mlp_id=user.get("mlp_id")).exists()
                data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user.get("mlp_id"), invitation_to__mlp_id=authenticated_user.mlp_id).exists()
                data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one__mlp_id=authenticated_user.mlp_id, user_two__mlp_id=user.get("mlp_id")) | Q(user_two__mlp_id=authenticated_user.mlp_id, user_one__mlp_id=user.get("mlp_id"))).exists()
                data['interest_rejected'] = Intrest.objects.filter(invitation_by__mlp_id=authenticated_user.mlp_id, invitation_to__mlp_id=user.get("mlp_id"), status="Rejected").exists()
                data['shortlisted']= SavedUser.objects.filter(user__mlp_id=authenticated_user.mlp_id, saved_profile__mlp_id=user.get("mlp_id")).exists()
                data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=user.get("mlp_id"), invitation_to__mlp_id=authenticated_user.mlp_id, status="Rejected").exists()

                data['is_bachelor'] = is_bachelor
                data['name_hidden'] = name_hidden
                data['photo_hidden'] = photo_hidden

                serializer_data.append(data) 
            #Saving keyword used by authenticated user in model
            if keyword:
                normalized_keyword = ' '.join(word.capitalize() for word in keyword.split())
                existing_search_record = SearchResult.objects.filter(
                    user_id=authenticated_user.id,
                    search_query=normalized_keyword
                ).first()

                if existing_search_record:
                    existing_search_record.results_count = total_items
                    existing_search_record.timestamp = timezone.now()
                    existing_search_record.save()
                else:
                    SearchResult.objects.create(
                        user_id=authenticated_user.id,
                        search_query=normalized_keyword,
                        results_count=total_items,
                        timestamp=timezone.now()
                    )
            
            #Storing filter used by authenticated user
            # if any(value is not None for value in new_filters.values()):
            #     existing_entry = UserSearchHistory.objects.filter(user_id=authenticated_user.id, filters_data__filters_used=new_filters).first()
                
            #     if existing_entry:
            #         existing_entry.filters_data['results_count'] = total_items
            #         existing_entry.save()
            #     else:
            #         filter_data = {
            #             'filters_used': new_filters,
            #             'results_count': total_items,
            #         }
            #         UserSearchHistory.objects.create(
            #             user_id=authenticated_user.id,
            #             filters_data=filter_data,
            #         )  

            response['status_code'] = 200
            response['message'] = "Data Retrieve Successfully"
            response['count'] = total_items
            response['total_pages'] = (total_items + page_size - 1) // page_size
            response['result'] = serializer_data
            return JsonResponse(response)        
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)

UserSearch = UserSearchView.as_view()


#filter saving
class UserSearchViewfilter(APIView):

    # get request can take multiple params and filter the data accordingly
    def get(self, request, *args, **kwargs):
        response = {
            "status_code": 500,
            "message": "Internal Server Error"
        }
        
        try:
            mlp_id = kwargs.get('mlp_id', None)
            if mlp_id is None:
                response['status_code'] = 400
                response['message'] = 'mlp_id parameter is missing in the URL'
                return JsonResponse(response)
            
 
            # Fetch the user with the given mlp_id
            authenticated_user = User.objects.filter(
                    mlp_id=mlp_id,
                    is_active=True,
                    is_wrong=False,
                    mandatory_questions_completed=True
                ).first()
              

            if authenticated_user is None:
                response['status_code'] = 404
                response['message'] = 'User not found'
                return JsonResponse(response)
            

            # Extract query parameters from the request
            params = self.request.query_params
            

            opp_gender = 'f' if authenticated_user.gender == 'm' else 'm'
            
            blocked_users_mlp_ids = BlockedUsers.objects.filter(user__mlp_id=authenticated_user.mlp_id).values_list('blocked_user__mlp_id', flat=True)

            queryset= User.objects.filter(
                      is_active=True, is_wrong=False, mandatory_questions_completed=True,gender=opp_gender).exclude(mlp_id__in=blocked_users_mlp_ids).distinct()
               
               
            #filtering data of users by age range  
            if 'age_from' in params and 'age_to' in params:
                age_from = int(params.get('age_from'))
                age_to = int(params.get('age_to'))
                today = date.today()
                queryset = queryset.annotate(
                    user_age=ExpressionWrapper(
                        today.year - F('dob__year') -
                        Case(
                            When(
                                dob__month__gt=today.month,
                                then=1
                            ),
                            When(
                                dob__month=today.month,
                                dob__day__gt=today.day,
                                then=1
                            ),
                            default=0,
                            output_field=IntegerField()
                        ),
                        output_field=IntegerField()
                    )
                ).filter(user_age__gte=age_from, user_age__lte=age_to)
               

            #filter data of users from queryset by caste
            if 'caste' in params:
                if authenticated_user.caste:
                    caste_values = params['caste'].split(',')
                    query = Q()
                    for caste_value in caste_values:
                        query |= Q(caste__icontains=caste_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the caste field first"
                    return JsonResponse(response)
                
                
            #filter data of users from queryset by sub_caste
            if 'sub_caste' in params:
                if authenticated_user.sub_caste:
                    sub_caste_ids = params.get('sub_caste').split(',')
                    queryset = queryset.filter(sub_caste__in=sub_caste_ids)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the sub_caste field first"
                    return JsonResponse(response)
                

            #filter data of users by their religion
            if 'religion' in params:
                if authenticated_user.religion:
                    religion_values = params['religion'].split(',')
                    query = Q()
                    for religion_value in religion_values:
                        query |= Q(
                            religion__name__icontains=religion_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the religion field first"
                    return JsonResponse(response)
                

            #filter data of users by their city
            if 'city' in params:
                cities_param = params['city']
                
                if authenticated_user.city:
                    cities = cities_param.split(',')
                    query = Q()
                    for city in cities:
                        query |= Q(city__icontains=city.strip())  
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the city field first"
                    return JsonResponse(response)

                
            
            #filter data of users by their country
            if 'country' in params:
                countries_param = params['country']
                
                if authenticated_user.country:
                    countries = countries_param.split(',')
                    query = Q()
                    for country in countries:
                        query |= Q(country__icontains=country.strip())  
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the country field first"
                    return JsonResponse(response)

                     
            #filter data of users from queryset by states
            if 'state' in params:
                states_param = params['state']
                
                if authenticated_user.state:
                    states = states_param.split(',')
                    query = Q()
                    for state in states:
                        query |= Q(state__icontains=state.strip())  
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the state field first"
                    return JsonResponse(response)

            
            #filter data of users from queryset by marital_status
            if 'marital_status' in params and params['marital_status']:
                if authenticated_user.marital_status:  
                    marital_status_values = params['marital_status'].split(',')
                    query = Q()
                    for marital_status_value in marital_status_values:
                        if marital_status_value.strip():
                            try:
                                query |= Q(marital_status=int(marital_status_value))
                            except ValueError:
                                response['status_code'] = 400
                                response['message'] = f"Invalid marital status value: {marital_status_value}"
                                return JsonResponse(response)
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the marital_status field first"
                    return JsonResponse(response)
            
            

            #filter data based on specialization
            if 'specialization' in params:
                if authenticated_user.specialization:
                    specialization_ids = params.get('specialization').split(',')
                    queryset = queryset.filter(specialization__in=specialization_ids)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the specialization field first"
                    return JsonResponse(response)
                
                
            #filter data from queryset by profession
            if 'profession' in params:
                profession_query = params['profession'].split(',')  # Get profession value from params
                query = Q()
                if authenticated_user.profession:
                    for prof in profession_query:
                        query |= Q(profession__icontains=prof.strip())

                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the profession field first"
                    return JsonResponse(response)


             # Education related filtering
            if 'graduation' in params:
                if  authenticated_user.graduation_obj:
                    graduation_values = params['graduation'].split(',')
                    query = Q()
                    for graduation_value in graduation_values:
                        query |= Q(graduation_obj__name__icontains=graduation_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide information for the graduation field first"
                    return JsonResponse(response)


            if 'post_graduation' in params:
                    post_graduation_values = params['post_graduation'].split(',')
                    query = Q()
                    for post_graduation_value in post_graduation_values:
                        query |= Q(partnerpostgraduationpreference__post_graduation__name__icontains=post_graduation_value.strip())
                    queryset = queryset.filter(query)
                 

            if 'expertise' in params:
                if authenticated_user.graduation_obj:
                    expertise_values = params['expertise'].split(',')
                    query = Q()
                    for expertise_value in expertise_values:
                        query |= Q(graduation_obj__expertise_obj__name__icontains=expertise_value.strip())
                    queryset = queryset.filter(query)
                else:
                    response['status_code'] = 300
                    response['message'] = "Please provide info for the expertise field first"
                    return JsonResponse(response)

            # get the values of filter used by authenticated user
            new_filters = {
                'city': self.request.query_params.get('city'),
                'caste': self.request.query_params.get('caste'),
                'sub_caste': self.request.query_params.get('sub_caste'),
                'religion': self.request.query_params.get('religion'),
                'age_from': self.request.query_params.get('age_from'),
                'age_to': self.request.query_params.get('age_to') ,
                'marital_status': self.request.query_params.get('marital_status'),
                'state': self.request.query_params.get('state'),
                'country': self.request.query_params.get('country'),
                'graduation': self.request.query_params.get('graduation'),
                'post_graduation': self.request.query_params.get('post_graduation'),
                'expertise': self.request.query_params.get('expertise'),
                'specialization': self.request.query_params.get('specialization'),
                'profession': self.request.query_params.get('profession'),
            }
            
            # if queryset is empty then return response "No content found"
            if not queryset.exists():
                response['status_code'] = 204
                response['message'] = 'No Content Found'
                return JsonResponse(response)
            
            total_items = queryset.count()

            # Storing filter used by authenticated user
            if any(value is not None for value in new_filters.values()):
                existing_entry = UserSearchHistory.objects.filter(user_id=authenticated_user.id, filters_data__filters_used=new_filters).first()
                
                if existing_entry:
                    existing_entry.filters_data['results_count'] = total_items
                    existing_entry.save()
                else:
                    filter_data = {
                        'filters_used': new_filters,
                        'results_count': total_items,
                    }
                    UserSearchHistory.objects.create(
                        user_id=authenticated_user.id,
                        filters_data=filter_data,
                    )  

            response['status_code'] = 200
            response['message'] = "Filter saved successfully"
            return JsonResponse(response)        
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)

UserSearchfilter = UserSearchViewfilter.as_view()
 # filter save and response nothing
    
class RetrieveSearchResultsView(APIView):

    def get(self, request, *args, **kwargs):
        response = {
            "status_code": 500,
            "message": "Internal Server Error"
        }
        try:
            logged_mlp_id = kwargs.get('mlp_id', None)
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

            if logged_mlp_id is None:
                response['status_code'] = 400
                response['message'] = 'mlp_id parameter is missing in the URL'
                return JsonResponse(response)

            authenticated_user = User.objects.filter(
                mlp_id=logged_mlp_id,is_active=True, is_wrong=False,
                mandatory_questions_completed=True).first()
            
            if authenticated_user is None:
                response['status_code'] = 404
                response['message'] = 'User not found'
                return JsonResponse(response)
            
            blocked_users_mlp_ids = BlockedUsers.objects.filter(user__mlp_id=authenticated_user.mlp_id).values_list('blocked_user__mlp_id', flat=True)
           # is_premium_user = authenticated_user.get('usersubscription__is_subscription_active')


            opposite_gender = 'm' if authenticated_user.gender == 'f' else 'f' 
            search_results = SearchResult.objects.filter(user__mlp_id=authenticated_user.mlp_id)
                
            serializer = SearchResultSerializer(search_results, many=True)

            bachelor_of_the_day = BachelorOfTheDay.get_latest_bachelor_of_the_day(authenticated_user.religion,opposite_gender)


            # Retrieve profiles viewed by the logged user within the last 24 hours
            viewed_user_mlp_ids = ProfileView.objects.filter(viewer__mlp_id=authenticated_user.mlp_id, visited_at__gte=twenty_four_hours_ago).values_list('viewed_user__mlp_id', flat=True)

            #blocked_user_mlp_ids = BlockedUsers.objects.filter(user=authenticated_user).values_list('blocked_user__mlp_id', flat=True) 
            user_data = User.objects.annotate(
                        post_graduations=ArrayAgg('partnerpostgraduationpreference__post_graduation__name')   
                        ).values(
                        "id","mlp_id", "name", "email", "mobile_number","gender", "dob",
                        "about", "future_aspirations",
                        "mother_tongue", "languages",
                        "religion__name", "profile_pictures",
                        "video", "family_photos",
                        "height", "weight", "physical_status",
                        "salary", "marital_status__name", "post_graduations",
                        "hobbies", "other_hobbies", "activity_status", "last_seen", "completed_post_grad",
                        "city", "state", "country", "caste","notification_settings__name","notification_settings__photo",
                        "sub_caste","graduation_obj__name","graduation_obj__expertise_obj__name"
                    ).filter(mlp_id__in = viewed_user_mlp_ids, is_active=True, is_wrong=False, mandatory_questions_completed=True).exclude(mlp_id__in =blocked_users_mlp_ids)
            

            seen_user_ids = set()
            most_recent_viewed = []

            for user in user_data: 
                if user['mlp_id'] not in seen_user_ids:
                    seen_user_ids.add(user['mlp_id'])   
                    is_bachelor = False
                    if bachelor_of_the_day and user["mlp_id"] == bachelor_of_the_day.user.mlp_id:
                        is_bachelor = True
                    user1 = User.objects.filter(mlp_id = user.get("mlp_id")).first()
                    res = show_name(authenticated_user,user1)
                    if res and res["status_code"] == 200:
                        name_hidden = False
                    else:
                        name_hidden = True

                    res = show_photographs(authenticated_user,user1)
                    if res:
                        if res["status_code"] == 200:
                            photo_hidden = False
                        else:
                            photo_hidden = True

                    data = {
                        'mlp_id':  user['mlp_id'],
                        'name': user['mlp_id'] if name_hidden else user["name"] ,
                        'email': user['email'],
                        'mobile_number': user['mobile_number'],
                        'gender': user['gender'],
                        'religion': user['religion__name'] if user['religion__name'] else None,
                        'marital_status': user['marital_status__name'] if user['marital_status__name'] else None,
                        'caste': user['caste'],
                        'dob': user['dob'],
                        'profile_pictures': json.loads(user['profile_pictures']),
                        'family_photos': json.loads(user['family_photos']),
                        'activity_status': user['activity_status'],
                        'last_seen': user['last_seen'],
                        'completed_post_grad': user['completed_post_grad'],
                        'height': user['height'],
                        'weight': user['weight'],
                        'hobbies': json.loads(user['hobbies']),
                        'other_hobbies': json.loads(user['other_hobbies']),
                        'city': user['city'],
                    }
                    
                    data['interest_sent'] = Intrest.objects.filter(invitation_by__mlp_id=authenticated_user.mlp_id, invitation_to__mlp_id=user.get("mlp_id")).exists()
                    data['interest_received'] = Intrest.objects.filter(invitation_by__mlp_id=user.get("mlp_id"), invitation_to__mlp_id=authenticated_user.mlp_id).exists()
                    data['mutually_accepted'] = ConnectionList.objects.filter(Q(user_one__mlp_id=authenticated_user.mlp_id, user_two__mlp_id=user.get("mlp_id")) | Q(user_two__mlp_id=authenticated_user.mlp_id, user_one__mlp_id=user.get("mlp_id"))).exists()
                    data['interest_rejected'] = Intrest.objects.filter(invitation_by__mlp_id=authenticated_user.mlp_id, invitation_to__mlp_id=user.get("mlp_id"), status="Rejected").exists()
                    data['shortlisted']= SavedUser.objects.filter(user__mlp_id=authenticated_user.mlp_id, saved_profile__mlp_id=user.get("mlp_id")).exists()
                    data['interest_rejected_by_me'] = Intrest.objects.filter(invitation_by__mlp_id=user.get("mlp_id"), invitation_to__mlp_id=authenticated_user.mlp_id, status="Rejected").exists()
                    
                    data['profile_pictures'] = json.loads(user['profile_pictures'])
                    data['video'] = json.loads(user['video'])
                    data['family_photos'] = json.loads(user['family_photos'])
                    data['hobbies'] = json.loads(user['hobbies'])
                    data['other_hobbies'] = json.loads(user['other_hobbies'])

                    data['name_hidden'] = name_hidden
                    data['photo_hidden'] = photo_hidden
                    data['is_bachelor'] = is_bachelor

        
                    user_graduation = user["graduation_obj__name"] 
                    
                    user_expertise = user['graduation_obj__expertise_obj__name'] 

                    data['graduation_id'] = user_graduation
                    data['user_post_graduation'] = user.get("post_graduations") if user.get("completed_post_grad") else []
                    data['expertise_id'] = user_expertise

                    # Add visited_at timestamp to user_data
                    profile_view = ProfileView.objects.filter(viewer__mlp_id=authenticated_user.mlp_id, visited_at__gte=twenty_four_hours_ago, viewed_user__mlp_id=user["mlp_id"]).first()
                    if profile_view:
                        data['visited_at'] = profile_view.visited_at

                    most_recent_viewed.append(data)


            search_history = UserSearchHistory.objects.filter(user__mlp_id=authenticated_user.mlp_id).order_by('-timestamp')
            
            search_history_data = []
            for history in search_history:
                search_history_data.append({
                    'id': history.id,
                    'filters_used': history.filters_data['filters_used'],
                    'result_count':history.filters_data['results_count'],
                    'timestamp': history.timestamp
                }) 

            response['status_code'] = 200
            response['message'] = "Retrieved Search Results Successfully"
            #response['final_data'] = serializer.data + search_history_data
            response['data'] = serializer.data
            response['Recent_Viewed_count'] = len(most_recent_viewed)
            response['Recent_Viewed'] = most_recent_viewed
            response['filtered_data'] = search_history_data
            return JsonResponse(response, safe=False)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)


RetrieveSearchResults = RetrieveSearchResultsView.as_view()

# To delete saved search result view
class DeleteSearchResultAPIView(APIView):
    def delete(self, request, result_id):
        response = {
            "status_code": 500,
            "message": "Internal Server Error"
        }
        try:
            search_result = SearchResult.objects.filter(id=result_id)
            if search_result.exists():
                search_result.delete()
                response['message']="Search result deleted successfully"
                response['status_code']=200
                return JsonResponse(response,safe=False)
            else:
                response['message']="Search result not exist with given id"
                response['status_code']=300
                return JsonResponse(response , safe=False)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)
        
DeleteSearchResult = DeleteSearchResultAPIView.as_view()        

# To Delete User Search History
class DeleteUserSearchHistoryAPIView(APIView):
    def delete(self, request, search_history_id, *args, **kwargs):
        response = {
            "status_code": 500,
            "message": "Internal Server Error"
        }
        try:
            search_history = UserSearchHistory.objects.filter(id=search_history_id)
            if not search_history.exists():
                response['status_code'] = 300
                response['message'] = "User search history of filter not found with given id"
                return JsonResponse(response, safe=False)

            search_history.delete()
            response['status_code'] = 200
            response['message'] = "User search history of filter deleted successfully"
            return JsonResponse(response, safe=False)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
            return JsonResponse(response)

DeleteUserSearchHistory = DeleteUserSearchHistoryAPIView.as_view()        