
from collections import defaultdict
from users.models import BachelorOfTheDay, SeenUser, User, UserSubscription
from datetime import datetime
from django.db.models import Count
from celery import shared_task

# def cronjob():
#         try: 
#             current_time = datetime.now()
#             midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
#             if current_time == midnight:
#                 find_bachelor_of_each_religion()
#         except Exception as e:
#              print(f'{e.__traceback__.tb_lineno} - {str(e)}')


@shared_task
def find_bachelor_of_each_religion():
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:
       
        all_users = UserSubscription.objects.filter(is_subscription_active=True)
        users_by_religion_and_gender = defaultdict(lambda: defaultdict(list))
        print(all_users)
        # Iterate through all users and categorize them
        for user_sub in all_users:
            # Assuming user profile has religion and gender fields
            user = user_sub.user
           # print(user)
            if user.religion and user.gender:
                religion = user.religion.name
                gender = user.gender
                profile_percent = user.calculate_profile_percentage()
                if profile_percent >= 50:
                    users_by_religion_and_gender[religion][gender].append(user)
       
        hindu_male = users_by_religion_and_gender['Hindu']['m']
        hindu_female = users_by_religion_and_gender['Hindu']['f']
        sikh_male = users_by_religion_and_gender['Sikh']['m']
        sikh_female = users_by_religion_and_gender['Sikh']['f']
        jain_male = users_by_religion_and_gender['Jain']['m']
        jain_female = users_by_religion_and_gender['Jain']['f']
        muslim_male = users_by_religion_and_gender['Muslim']['m']
        muslim_female = users_by_religion_and_gender['Muslim']['f']
        christian_male =  users_by_religion_and_gender['Christian']['m']
        christian_female =  users_by_religion_and_gender['Christian']['f']
        buddhist_male =  users_by_religion_and_gender['Buddhist']['m']
        buddhist_female =  users_by_religion_and_gender['Buddhist']['m']
        bohra_male =  users_by_religion_and_gender['Bohra']['m']
        bohra_female =  users_by_religion_and_gender['Bohra']['f']
        parsi_male =  users_by_religion_and_gender['Parsi']['m']
        parsi_female =  users_by_religion_and_gender['Parsi']['f']
        
        hindu_bachelor_male = find_bachelor_of_each_religion_service(hindu_male)
        hindu_bachelor_female = find_bachelor_of_each_religion_service(hindu_female)
        sikh_bachelor_male = find_bachelor_of_each_religion_service(sikh_male)
        sikh_bachelor_female = find_bachelor_of_each_religion_service(sikh_female)
        jain_bachelor_male = find_bachelor_of_each_religion_service(jain_male)
        jain_bachelor_female = find_bachelor_of_each_religion_service(jain_female)
        muslim_bachelor_male = find_bachelor_of_each_religion_service(muslim_male)
        muslim_bachelor_female = find_bachelor_of_each_religion_service(muslim_female)
        christian_bachelor_male = find_bachelor_of_each_religion_service(christian_male)
        christian_bachelor_female = find_bachelor_of_each_religion_service(christian_female)
        buddhist_bachelor_male = find_bachelor_of_each_religion_service(buddhist_male)
        buddhist_bachelor_female = find_bachelor_of_each_religion_service(buddhist_female)
        bohra_bachelor_male = find_bachelor_of_each_religion_service(bohra_male)
        bohra_bachelor_female = find_bachelor_of_each_religion_service(bohra_female)
        parsi_bachelor_male = find_bachelor_of_each_religion_service(parsi_male)
        parsi_bachelor_female = find_bachelor_of_each_religion_service(parsi_female)

         # For Hindu
        if hindu_bachelor_female is not None:
            BachelorOfTheDay.objects.create(user=hindu_bachelor_female,religion=hindu_bachelor_female.religion)
        if hindu_bachelor_female is None:
            print("No female bachelor for Hindu")
        if hindu_bachelor_male is None:
            print("No male bachelor for Hindu")
        if hindu_bachelor_male is not None:
            BachelorOfTheDay.objects.create(user=hindu_bachelor_male,religion=hindu_bachelor_male.religion)

        # For Sikh
        if sikh_bachelor_female is not None:
            BachelorOfTheDay.objects.create(user=sikh_bachelor_female,religion=sikh_bachelor_female.religion)
        if sikh_bachelor_female is None:
            print("No female bachelor for Sikh")
        if sikh_bachelor_male is None:
            print("No male bachelor for Sikh")
        if sikh_bachelor_male is not None:
            BachelorOfTheDay.objects.create(user=sikh_bachelor_male,religion=sikh_bachelor_male.religion)

        # For Jain
        if jain_bachelor_female is not None:
           BachelorOfTheDay.objects.create(user=jain_bachelor_female,religion=jain_bachelor_female.religion)
        if jain_bachelor_female is None:
            print("No female bachelor for Jain")
        if jain_bachelor_male is None:
            print("No male bachelor for Jain")
        if jain_bachelor_male is not None:
           BachelorOfTheDay.objects.create(user=jain_bachelor_male,religion=jain_bachelor_male.religion)

        # For Muslim
        if muslim_bachelor_female is not None:
            BachelorOfTheDay.objects.create(user=muslim_bachelor_female,religion=muslim_bachelor_female.religion)
        if muslim_bachelor_female is None:
            print("No female bachelor for Muslim")
        if muslim_bachelor_male is None:
            print("No male bachelor for Muslim")
        if muslim_bachelor_male is not None:
            BachelorOfTheDay.objects.create(user=muslim_bachelor_male,religion=muslim_bachelor_male.religion)

        # For Christian
        if christian_bachelor_female is not None:
            BachelorOfTheDay.objects.create(user=christian_bachelor_female,religion=christian_bachelor_female.religion)
        if christian_bachelor_female is None:
            print("No female bachelor for Christian")
        if christian_bachelor_male is None:
            print("No male bachelor for Christian")
        if christian_bachelor_male is not None:
            BachelorOfTheDay.objects.create(user=christian_bachelor_male,religion=christian_bachelor_male.religion)

        # For Buddhist
        if buddhist_bachelor_female is not None:
           BachelorOfTheDay.objects.create(user=buddhist_bachelor_female,religion=buddhist_bachelor_female.religion)
        if buddhist_bachelor_female is None:
            print("No female bachelor for Buddhist")
        if buddhist_bachelor_male is None:
            print("No male bachelor for Buddhist")
        if buddhist_bachelor_male is not None:
            BachelorOfTheDay.objects.create(user=buddhist_bachelor_male,religion=buddhist_bachelor_male.religion)

        # For Bohra
        if bohra_bachelor_female is not None:
            BachelorOfTheDay.objects.create(user=bohra_bachelor_female,religion=bohra_bachelor_female.religion)
        if bohra_bachelor_female is None:
            print("No female bachelor for Bohra")
        if bohra_bachelor_male is None:
            print("No male bachelor for Bohra")
        if bohra_bachelor_male is not None:
            BachelorOfTheDay.objects.create(user=bohra_bachelor_male,religion=bohra_bachelor_male.religion)

        # For Parsi
        if parsi_bachelor_female is not None:
            BachelorOfTheDay.objects.create(user=parsi_bachelor_female,religion=parsi_bachelor_female.religion)
        if parsi_bachelor_female is None:
            print("No female bachelor for Parsi")
        if parsi_bachelor_male is None:
            print("No male bachelor for Parsi")
        if parsi_bachelor_male is not None:
            BachelorOfTheDay.objects.create(user=parsi_bachelor_male,religion=parsi_bachelor_male.religion)

        
    except Exception as e:
      #  logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        response['message'] =str(e) 
        return response


def find_bachelor_of_each_religion_service(profiles):
    response = {
        'status_code': 500,
        'message': 'Internal server error'
    }
    try:  
        sorted_profiles = sorted(profiles, key=lambda user: user.calculate_profile_percentage(), reverse=True)
        
        most_viewed_profile = (
            SeenUser.objects
            .filter(seen_profile__is_active=True,seen_profile__is_wrong=False, seen_profile__mandatory_questions_completed=True, seen_profile__gender__isnull=False, seen_profile__in=profiles)
            .values('seen_profile__mlp_id')
            .annotate(field_count=Count('seen_profile__mlp_id'))
            .order_by('-field_count')
            .first()
        )
       
        bachelor = None
        if most_viewed_profile is not None:
           bachelor = User.objects.get(mlp_id=most_viewed_profile['seen_profile__mlp_id'])
        else:
            if sorted_profiles:
              bachelor = sorted_profiles[0]   
        
        return bachelor
    except Exception as e:
      #  logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        response['message'] =str(e) 
        return response            
