from collections import defaultdict
from datetime import datetime, timedelta
import mysql.connector
from notification_settings.models import NotificationSettings
from transactions.models import *
import json
from django.db.models import Count

def import_core_data():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT religion, caste, sub_caste, specialization, language, spoken_language FROM medico_members group by religion, caste, sub_caste, specialization, language, spoken_language")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()

    for obj in data:
        if str(obj['caste']).strip() and not Caste.objects.filter(name__iexact=str(obj['caste']).strip()).exists():
            Caste.objects.create(name=str(obj['caste']).strip())
        if str(obj['sub_caste']).strip() and not SubCaste.objects.filter(name__iexact=str(obj['sub_caste']).strip()).exists():
            SubCaste.objects.create(name=str(obj['sub_caste']).strip())
    print("data added of caste and subcaste successfully")   

def import_data():
        # Connect to MySQL
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    #mycursor.execute("SELECT *,medico_members.id as Mlp_id,country.country_c as Country_Code, medico_partner_preference.second_marriage AS Marital_Pref, medico_partner_preference.physically_challenged AS Preference,country.country_name AS Country_Name,state.state_name AS State_Name FROM medico_members LEFT JOIN medico_partner_preference ON medico_members.id = medico_partner_preference.user_id LEFT JOIN country ON medico_members.country = country.country_id LEFT JOIN state ON medico_members.state= state.state_id WHERE  email_id = 'sandipbhosale0019@gmail.com'")
    mycursor.execute("SELECT *,medico_members.id as Mlp_id,country.country_c as Country_Code, medico_partner_preference.second_marriage AS Marital_Pref, medico_partner_preference.physically_challenged AS Preference,country.country_name AS Country_Name,state.state_name AS State_Name FROM medico_members LEFT JOIN medico_partner_preference ON medico_members.id = medico_partner_preference.user_id LEFT JOIN country ON medico_members.country = country.country_id LEFT JOIN state ON medico_members.state= state.state_id WHERE medico_members.status != 'Deactive' AND medico_members.status != 'Repeat' AND LENGTH(candidates_name) >=30")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()
    # print(data[0]["id"])
    
    for i in range(len(data)):
        temp_obj = data[i]
        print(i)
        print( f"Preference of user: MLP00{temp_obj['Mlp_id']}")

        #For Partner Age Preference 
        temp_obj['plus_years'] = int(temp_obj['plus_years']) if temp_obj['plus_years'] and temp_obj['plus_years'] != '' else None
        temp_obj['minus_years'] = int(temp_obj['minus_years']) if temp_obj['minus_years'] and temp_obj['minus_years'] != '' else None
        age_preference = True if temp_obj['minus_years'] and temp_obj['minus_years'] != '' else False
        

        #For Partner Height Preference
        height_preference = False
        if temp_obj['height_ft_from'] is not None and temp_obj['height_ft_to'] is not None and temp_obj['height_inch_to'] is not None and temp_obj['height_inch_from'] is not None:
            temp_obj['height_inch_from'] = (int(temp_obj['height_ft_from']) * 12 + int(temp_obj['height_inch_from'])) if temp_obj['height_inch_from'] and temp_obj['height_ft_from'] and int(temp_obj['height_ft_from']) >= 0 else None
            temp_obj['height_inch_to'] = (int(temp_obj['height_ft_to']) * 12 + int(temp_obj['height_inch_to'])) if temp_obj['height_inch_to'] and temp_obj['height_ft_to'] and int(temp_obj['height_ft_to']) >= 0 else None
            if temp_obj['height_inch_to'] is not None and temp_obj['height_inch_from'] is not None:
                height_preference = True if int(temp_obj['height_inch_to']) > 0 else False

       
       #For Partner Expertise Preference
        partner_expertise_preference = False
        medicine_names=[]
        if temp_obj['medicine_search'] and temp_obj['medicine_search'] != "Does not matter" and temp_obj['medicine_search'] != "No Matter":
            partner_expertise_preference = True
            medicine_names = [medicine.strip() for medicine in temp_obj['medicine_search'].split(',')] 
         
        
        # For completed post grad
        completed_post_grad =False
        graduation_obj = Graduation.objects.filter(name__iexact=temp_obj["education_field"]).first()

        post_ed_names = [ele.strip() for ele in temp_obj['post_education_field'].split(',')] 
       
        for ed_name in post_ed_names:
            if ed_name == "MCh":
                ed_name = "Mch"
            elif ed_name == "MD / MS Ayurveda":
                ed_name = "MD/MS Ayurveda"

            post_grad_objects = PostGraduation.objects.filter(name__iexact=ed_name)    

            if post_grad_objects.exists():
                completed_post_grad = True
                break 

        if not post_grad_objects:
            completed_post_grad = False 
            
        religion_names = []
        partner_religion_preference = False
        if temp_obj['religion_search'] and temp_obj['religion_search'] != "Does not matter" and temp_obj['religion_search'] != "No Matter":
            partner_religion_preference = True
            religion_names = [religion.strip() for religion in temp_obj['religion_search'].split(',')] 
        
        # For Partner city Preference
        partner_city_preference = False
        temp_obj['city_search'] = [] if not temp_obj['city_search'] else [ele.strip() for ele in temp_obj['city_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"] ]
        if temp_obj['city_search'] and "Does not matter" not in temp_obj['city_search'] and "No Matter" not in temp_obj['city_search']:
            partner_city_preference = True
        
        # For Partner State Preference
        partner_state_preference = False
        temp_obj['state_field_search'] = [] if not temp_obj['state_field_search'] else [ele.strip() for ele in temp_obj['state_field_search'].split(',') if ele.strip() not in ["Does not matter", "No Matter"]]
        if temp_obj['state_field_search'] and "Does not matter" not in temp_obj['state_field_search'] and "No Matter" not in temp_obj['state_field_search']:
            partner_state_preference = True

        # For Partner Country Preference
        partner_country_preference = False
        temp_obj['country_field_search'] = [] if not temp_obj['country_field_search'] else [ele.strip() for ele in temp_obj['country_field_search'].split(',') if ele.strip()  not in ["Does not matter", "No Matter"]]
        if temp_obj['country_field_search'] and "Does not matter" not in temp_obj['country_field_search']  and "No Matter" not in temp_obj['country_field_search']:
            partner_country_preference = True
        
        # For Marital State  
        marital_status_obj = None
        if temp_obj['second_marriage'] == "Never Married":
            marital_status_name = "Bachelor"
            marital_status = MaritalStatus.objects.filter(name__iexact=marital_status_name)
            if marital_status:
                marital_status_obj = marital_status.first()
        else:
            marital_status = MaritalStatus.objects.filter(name__iexact=temp_obj['second_marriage'])
            if marital_status:
                marital_status_obj = marital_status.first()   

        # For Partner Marital State Preference
        partner_marital_pref = False
        marital_preference_data = None
        if temp_obj['Marital_Pref'] and temp_obj['Marital_Pref'] != "Does not matter" and temp_obj['Marital_Pref'] != "No Matter":
            partner_marital_pref = True
            marital_pref_name = temp_obj['Marital_Pref'].strip()  
            if marital_pref_name == "Never Married":
                marital_pref_name = "Bachelor"
            marital_preference_data = MaritalStatus.objects.filter(name__iexact=marital_pref_name).first()  # Get the single instance

            
        # For Profile Pictures
        profile_pictures = []
        if temp_obj['profile_pic'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic'].strip()}")
        if temp_obj['profile_pic2'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic2'].strip()}")
        if temp_obj['profile_pic3'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic3'].strip()}")
        if temp_obj['profile_pic4'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic4'].strip()}")
        if temp_obj['profile_pic5'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic5'].strip()}")
        if temp_obj['profile_pic6'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic6'].strip()}")
        if temp_obj['profile_pic7'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic7'].strip()}")
        if temp_obj['profile_pic8'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic8'].strip()}")
        if temp_obj['profile_pic9'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic9'].strip()}")
        if temp_obj['profile_pic10'].strip():
            profile_pictures.append(f"https://www.medicolifepartner.com/images/profile/{temp_obj['Mlp_id']}/{temp_obj['profile_pic10'].strip()}")
        
       
        # For manglik    
        manglik_value = 1 if temp_obj['manglik'] == "Yes" else 0 if temp_obj['manglik'] == "No" else -1
        
        # For specialization
        specialization = None
        specializations = Specialization.objects.filter(name__iexact=temp_obj['specialization'])
        if specializations.exists():
            specialization = specializations.first()  
            
        # For mother tongue
        spoken_languages = temp_obj['spoken_language'].split(',')
        mother_tongues = []
        for lang in spoken_languages:
            lang = lang.strip()
            if lang:
                mother_tongue = MotherTongue.objects.filter(name__iexact=lang).first()
                if mother_tongue:
                    mother_tongues.append(mother_tongue)

        # For Partner Mother Tongue Preference
        mother_tongue_objs = []
        partner_mother_tongue_preference= False
        if temp_obj['mother_tongue'] and temp_obj['mother_tongue'] != "Does not matter" and temp_obj['mother_tongue'] != "No Matter":
            partner_mother_tongue = temp_obj['mother_tongue'].split(',')
            if partner_mother_tongue:
                partner_mother_tongue_preference= True
                for lang in partner_mother_tongue:
                    lang=lang.strip()
                    if lang:
                        mother_tongue_object = MotherTongue.objects.filter(name__iexact=lang).first()
                        if mother_tongue_object:
                            mother_tongue_objs.append(mother_tongue_object)
            else :
                partner_mother_tongue_preference = False
        
        # For Partner Caste Preference
        caste_objs = []
        partner_caste_preference = False
        if temp_obj['caste_search'] and temp_obj['caste_search'] != "Does not matter" and temp_obj['caste_search'] != "No Matter":
            partner_caste_search = temp_obj['caste_search'].split(',')
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
        
        # Partner Post Graduation Preference
        partner_post_education_preference = False
        post_education_field_names=[]
        if temp_obj['post_education_field_search'] and temp_obj['post_education_field_search'] != "Does not matter" and temp_obj['post_education_field_search'] != "No Matter":
            partner_post_education_preference = True
            post_education_field_names = [field.strip() for field in temp_obj['post_education_field_search'].split(',')] 
            
        # Partner Graduation Preference
        partner_education_preference = False
        education_field_names=[]
        if temp_obj['education_field_search'] and temp_obj['education_field_search'] != "Does not matter" and temp_obj['education_field_search'] != "No Matter":
            partner_education_preference = True
            education_field_names = [field.strip() for field in temp_obj['education_field_search'].split(',')] 
        
        # Partner Specialization Preference
        specialization_names =[]
        partner_specialization_preference = False
        if temp_obj['specialization_search'] and temp_obj['specialization_search'] != "Does not matter" and temp_obj['specialization_search'] != "No Matter":
            partner_specialization_preference = True
            specialization_names = [specialization.strip() for specialization in temp_obj['specialization_search'].split(',')] 

        # For SubCaste
        sub_caste=None
        subcaste=SubCaste.objects.filter(name__iexact=temp_obj['sub_caste'])
        if subcaste.exists():
            sub_caste = subcaste.first()

        # For Hobbies
        hobbies = []
        if temp_obj['hobbies'] and ',' in temp_obj['hobbies']:
            hobbies = [h.strip() for h in temp_obj['hobbies'].split(',') if h.strip()]
        
        # For Profession
        profession_obj = []
        temp_professions = temp_obj.get('profession', '')  
        if temp_professions: 
            professions = temp_professions.split(',')  
            for profession in professions:
                values=profession.strip().capitalize()
                profession_obj.append(values) 
        

        can_upgrade_subscription = -1 
        if temp_obj['status'] == "Active":
            subscription_start_date = temp_obj['subscription_start_date']
            subscription_end_date = temp_obj['subscription_end_date']

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

        # video = []
        # if temp_obj['video'] != "":
        #     video.append(temp_obj['video'])
        
        grad_status = None
        if temp_obj.get('education_field_status') == 'complete' or temp_obj.get('education_field_status') == 'completed':
            grad_status = 'Completed'
        elif temp_obj.get('education_field_status') == 'ongoing' :
            grad_status = 'Ongoing' 

        post_grad_status = None
        if temp_obj.get('post_education_field_status') == 'complete' or temp_obj.get('post_education_field_status') == 'completed':
            post_grad_status = 'Completed'
        elif temp_obj.get('post_education_field_status') == 'ongoing' :
            post_grad_status = 'Ongoing'         
       
        # For mobile number 
        if  temp_obj['Country_Code'] is not None:
                country_code = temp_obj['Country_Code'].replace("+", "")  
                mobile_number = f"{country_code}{temp_obj['mobile']}"
        else:
                mobile_number = f"91{temp_obj['mobile']}" 

             
        religion_obj= Religion.objects.filter(name__iexact=temp_obj['religion']).first()
        expertise_ob = Expertise.objects.filter(name__iexact=temp_obj['medicine']).first() 
        mandatory_questions_completed = True
        if (
            temp_obj['status'] == "Pending" or
            temp_obj['createby'] == '' or
            temp_obj['createby'] not in ["candidate", "family"] or
            religion_obj is None or
            temp_obj["candidates_name"] == "" or
            temp_obj.get("date_of_birth") is None or
            temp_obj['sex'] not in ["Male", "Female"] or
            len(profile_pictures) == 0 or
            graduation_obj is None or
            expertise_ob is None or
            temp_obj['email_id'] == '' or
            temp_obj['password'] == ''
        ) :
          mandatory_questions_completed = False          

        existing_user = User.objects.filter(mlp_id=f"MLP00{temp_obj['Mlp_id']}").first()
        if existing_user:
            print(f"User with mlp_id MLP00{temp_obj['Mlp_id']} already exists.")
            continue
   

        new_user=User.objects.create(
            mlp_id= f"MLP00{temp_obj['Mlp_id']}",
            mobile_number=mobile_number,
            name=temp_obj['candidates_name'],
            email=temp_obj['email_id'],
            password=temp_obj['password'],
            gender='m' if temp_obj['sex'] == "Male" else 'f',
            weight = temp_obj['weight'] if temp_obj['weight'] is not None else None,
            profile_pictures = json.dumps(profile_pictures),
            partner_caste_from = json.dumps(caste_names),
            dob=temp_obj['date_of_birth'],
            marital_status = marital_status_obj,
            partner_age_preference=age_preference,
            partner_age_from=temp_obj['plus_years'],
            partner_age_to=temp_obj['minus_years'],
            partner_expertise_preference=partner_expertise_preference,
            partner_cities_preference= partner_city_preference,
            partner_cities_from = json.dumps(temp_obj['city_search']),
            partner_country_preference=partner_country_preference,
            partner_country_from = json.dumps(temp_obj['country_field_search']),
            partner_state_preference=partner_state_preference,
            partner_state_from = json.dumps(temp_obj['state_field_search']) ,
            partner_height_preference= height_preference,
            partner_height_from = temp_obj['height_inch_from'],
            partner_height_to= temp_obj['height_inch_to'],
            partner_postgraduation_preference= partner_post_education_preference,
            partner_graduation_preference = partner_education_preference,
            partner_specialization_preference = partner_specialization_preference,
            graduation_obj=graduation_obj,
            completed_post_grad=completed_post_grad,
           # body_build = temp_obj['body_build'] if temp_obj['body_build'] is not None else None,
           # complexion = temp_obj['complexion'] if temp_obj['complexion'] is not None else None,
            other_hobbies = json.dumps(hobbies),
            blood_group = temp_obj['blood_group'] if temp_obj['blood_group'] is not None else None,
           # disease_history = temp_obj['disease'] if temp_obj['disease'] is not None else None,
            schooling_details = temp_obj['schooling'] if temp_obj['schooling'] is not None else None,
            facebook_profile = temp_obj['facebook_link'] if temp_obj['facebook_link'] is not None else None,
            linkedin_profile = temp_obj['linkedin'] if temp_obj['linkedin'] is not None else None,
            partner_religion_preference=partner_religion_preference,
            partner_mothertongue_preference= partner_mother_tongue_preference,
            partner_physicalstatus = temp_obj['Preference']  if temp_obj["Preference"] is not None and temp_obj["Preference"] != "No Matter" and temp_obj['Preference'] != "Does not matter" else None,
            partner_marital_status_preference = partner_marital_pref,
            mandatory_questions_completed = mandatory_questions_completed,
            manglik = manglik_value,
            birth_location=temp_obj['birth_location'],
            height=temp_obj['height_ft']*12 + temp_obj['height_inch'],
           # salary=temp_obj['salary'],
            caste=temp_obj['caste'], 
            specialization = specialization,
            sub_caste=sub_caste,
            city = temp_obj['city'] if  temp_obj['city'] != "Please Select State" or temp_obj['city'] != "Select State" or temp_obj['city'] != "Please+Select+State" else None,
            state = temp_obj['State_Name'],
            country = temp_obj['Country_Name'], 
           # horoscope_matching=temp_obj['horoscope_matching'],
            future_aspirations=temp_obj['candi_future_aspiration'],
            about=temp_obj['candi_describing_myself'],
            is_active=False if temp_obj['status'] =='Remove' or temp_obj['status']=='Wrong' else True,
            time_birth=str(temp_obj['time_of_birth']) if temp_obj['time_of_birth'] != "00:00:00" else None,
            religion = Religion.objects.filter(name__iexact=temp_obj['religion']).first(),
            graduation_institute = temp_obj.get('graduation_institute'),
            post_graduation_institute = temp_obj.get('post_graduation_institute'),
            post_graduation_status = post_grad_status,
            graduation_status = grad_status,
            partner_caste_preference= partner_caste_preference,
            mother_name = temp_obj['mother_name'] if temp_obj['mother_name'] is not None else None,
            father_name = temp_obj['father_name'] if temp_obj['father_name'] is not None else None,
            father_occupation = temp_obj['father_profession'] if temp_obj['father_profession'] is not None else None,
            mother_occupation = temp_obj['mother_profession'] if temp_obj['mother_profession'] is not None else None,
            father_education = temp_obj['father_education'] if temp_obj['father_education'] is not None else None,
            mother_education = temp_obj['mother_education'] if temp_obj['mother_education'] is not None else None,
           # nature = temp_obj['nature'] if temp_obj['nature'] is not None else None,
           # physical_status = temp_obj['physically_challenged'] if temp_obj["physically_challenged"] is not None and temp_obj["physically_challenged"] != "No Matter" and temp_obj['physically_challenged'] != "Does not matter" else None,
           # eyesight = temp_obj['eye_sight'] if temp_obj['eye_sight'] is not None else None,
            city_parents = temp_obj['father_resided_city'] if temp_obj['father_resided_city'] is not None else None,
           # residence =  temp_obj['res_address'] if temp_obj['res_address'] is not None else None,
            family_house = temp_obj['father_owned_residence'] if temp_obj['father_owned_residence'] is not None else None,
            profession_description = temp_obj['profession_details'] if temp_obj['profession_details'] is not None else None,
            profession = json.dumps(profession_obj),
            is_primary_account=True,
            sibling = None,
            whatsapp_number = None,
            registration_number = temp_obj['medical_registration_number'] if temp_obj['medical_registration_number'] is not None else None,
            profile_createdby ="Parent" if temp_obj['createby'] == "family" else "Candidate",
            can_upgrade_subscription = can_upgrade_subscription
            
        )

        # For Language , mother_tongue, partner_mother_tongue
        new_user.languages.set(Languages.objects.filter(name__iexact=temp_obj['language']))
        new_user.mother_tongue.set(mother_tongues)
        new_user.partner_mothertongue_from.set(mother_tongue_objs)
        
        name = None
        phone= None
        photo= None
        salary = None
        email = None
        if new_user.email:
            email = new_user.email
        if temp_obj["privacy_name"] == "interest_accepted":
            name = "interests"
        if temp_obj["privacy_name"] == "to_all_subscribe":
            name = "paid"     
        if temp_obj["privacy_phone"] == "interest_accepted":
            phone = "interests"
        if temp_obj["privacy_phone"] == "to_all_subscribe":
            phone = "paid"    
        if temp_obj["privacy_photo"] == "to_all":
            photo = "all" 
        if temp_obj["privacy_photo"] == "to_all_subscribe":
            photo = "paid"    
        if temp_obj["privacy_photo"] == "interest_accepted":
            photo= "interests"
        if temp_obj["privacy_salary"] == "to_all_subscribe" or temp_obj["privacy_salary"] == "to_all_subscribe_registered":
            salary = "paid"    
        if temp_obj["privacy_salary"] == "interest_accepted":
            salary= "interests"
        NotificationSettings.objects.create(user=new_user,email_notifications="",name=name,phone=phone,photo=photo, salary=salary, email=email)
        print("new user notification settings added successfully")


        # For Partner Marital Status Preference
        if marital_preference_data and new_user:
           PartnerMaritalStatusPreference.objects.create(user=new_user, marital_status=marital_preference_data)
        

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

        # For Partner Religion Preference
        for religion_name in religion_names:
            religion_objects = Religion.objects.filter(name__iexact=religion_name)
            if religion_objects.exists():
                for religion in religion_objects:
                    PartnerReligionPreference.objects.create(user=new_user, religion=religion)
        
        # For Specialization Preference
        for specialization_name in specialization_names:
            specialization_objects = Specialization.objects.filter(name__iexact=specialization_name)
            if specialization_objects.exists():
                for specialization in specialization_objects:
                    PartnerSpecializationPreference.objects.create(user=new_user, specialization=specialization)
        
        # For Expertise of Partner
        if medicine_names:            
            for medicine_name in medicine_names:
                expertise_objects = Expertise.objects.filter(name__iexact=medicine_name)
                if expertise_objects.exists():
                    for expertise in expertise_objects:
                        PartnerExpertisePreference.objects.create(user=new_user, expertise=expertise)
            
        # For Partner Graduation Preference
        for field_name in education_field_names:
            education_objects = Graduation.objects.filter(name__iexact=field_name)
            if education_objects.exists():
                for education in education_objects:
                    PartnerGraduationPreference.objects.create(user=new_user, graduation=education)

         # For Partner Post-Graduation Preference
        unique_pref= set()
    
        for field_name in post_education_field_names:
            if field_name == "MCh":
                field_name = "Mch"
            elif field_name == "MD / MS Ayurveda":
                field_name = "MD/MS Ayurveda"    

            # Retrieve matching PostGraduation objects
            matching_objects = PostGraduation.objects.filter(name__iexact=field_name).first()
            if matching_objects:
                unique_pref.add(matching_objects)
        for post_education_object in unique_pref:
                PartnerPGPreference.objects.create(user=new_user, post_graduation=post_education_object)

def update_partner():
    all_users = User.objects.all() 
    for user in all_users:
        if user.partner_income_from is not None and user.partner_income_from != "":
            user.partner_income_preference = True
        else:
            user.partner_income_preference = False
        user.save() 


def update_mobile_numbers():
    users_with_plus = User.objects.filter(mobile_number__contains='+')
    users_with_count = users_with_plus.count()
    print(users_with_count)
    for user in users_with_plus:
        mobile_number = user.mobile_number
        
        mobile_number = mobile_number.replace('+', '')

        user.mobile_number = mobile_number

        user.save()

        print(f"Updated mobile number for user {user.name}: {user.mobile_number}")

    print("Mobile numbers updated successfully!")



def update_data_migrate():
    all_user = User.objects.all()

    for user in all_user:
        user.disease_history = ''
        user.residence=''

        if user.post_graduation_status=='complete':
            user.post_graduation_status='Completed'
        elif user.post_graduation_status == 'ongoing' :
            user.post_graduation_status='Ongoing'
        else:
            user.post_graduation_status=''   
        
        if user.graduation_status=='complete':
            user.graduation_status='Completed'
        elif user.graduation_status == 'ongoing' :
            user.graduation_status='Ongoing'
        else:
            user.post_graduation_status='' 

        user.salary=''
        user.horoscope_matching=''
        user.complexion=''
        user.nature=''
        user.body_build=''
        user.physical_status='' 
        user.city_parents=''
        user.family_house=''        

        user.save()

    print("user data updated successfully")    


def mobile_added():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT medico_members.id as Mlp_id,country.country_c as Country_Code, mobile FROM medico_members LEFT JOIN medico_partner_preference ON medico_members.id = medico_partner_preference.user_id LEFT JOIN country ON medico_members.country = country.country_id LEFT JOIN state ON medico_members.state= state.state_id WHERE medico_members.status != 'Deactive' AND medico_members.status != 'Repeat' AND LENGTH(medico_members.mobile) = 10")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()

    for i in range(len(data)):
        temp_data=data[i]
        print(i)
        Mlp_id = temp_data['Mlp_id']
        if temp_data['Country_Code'] is not None:
                mobile_number = f"{temp_data['Country_Code']}{temp_data['mobile']}"
        else:
                mobile_number = f"91{temp_data['mobile']}"
        

        user = User.objects.filter(mlp_id__iexact=Mlp_id, is_active =True).first()

        if user:
            user.mobile_number= mobile_number
            user.save()
            print("User mobile number added")
        else:
            print("User won't exist with mlp_id")        

from django.db.models import Q
def connection_list_data():
        accepted_invitations = Intrest.objects.filter(status="Accepted")
        count =0
        for invitation in accepted_invitations:
            print(count)
            who_seen = User.objects.filter(mlp_id__iexact =  invitation.invitation_by.mlp_id, is_active=True).first()
            whom_seen = User.objects.filter(mlp_id__iexact = invitation.invitation_to.mlp_id , is_active=True).first()
            connection_exists = ConnectionList.objects.filter(Q(user_one=who_seen, user_two=whom_seen) | Q(user_one=whom_seen, user_two=who_seen)).exists()
            if who_seen  and whom_seen:
                if not connection_exists and who_seen !=whom_seen:
                    connection_list_instance=ConnectionList(user_one=who_seen, user_two=whom_seen)
                    connection_list_instance.save()
                    print("user saved")
                else:
                    print("data already present")     
            else:
                print("users not found")
            count+=1               

        print("data added successfully")        

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
            religion = user.religion.name
            gender = user.gender
            profile_percent = user.calculate_profile_percentage()
            if profile_percent > 60:
                users_by_religion_and_gender[religion][gender].append(user)

        print(users_by_religion_and_gender)        
       
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
            .filter(seen_profile__is_active=True, seen_profile__mandatory_questions_completed=True, seen_profile__gender__isnull=False, seen_profile__in=profiles)
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


def post_grad_update():
    all_users = User.objects.filter(is_active=True).all()

    for user in all_users:
        all_post =  UserPostGraduation.objects.filter(user=user)
        print(f"User with ID {user.mlp_id} : userpostgraduation {all_post}")
        has_post_graduation = UserPostGraduation.objects.filter(user=user).exists()
        if has_post_graduation:
            user.completed_post_grad = True
        else:
            user.completed_post_grad = False
        print(f"User with ID {user.mlp_id} has completed post-graduation: {user.completed_post_grad}")
        user.save()


def selected_profile_data():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * from medico_selected_profile where medico_selected_profile.id IN ( 71966, 143781)")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()
    
    for i in range(len(data)):
        temp_data = data[i]
        print(i)  
        who_seen_id = f"MLP00{temp_data['id']}"
        whom_seen_id = f"MLP00{temp_data['selected_id']}"
        

        who_seen = User.objects.filter(mlp_id__iexact = who_seen_id, is_active=True).first()
        whom_seen = User.objects.filter(mlp_id__iexact = whom_seen_id , is_active=True).first()
        saved_user_exists = SavedUser.objects.filter(user=who_seen, saved_profile=whom_seen).exists()
        if who_seen and whom_seen:
                if not saved_user_exists:
                    profile_view_instance = SavedUser(user=who_seen, saved_profile=whom_seen)
                    profile_view_instance.save()
                    print("Saved User added")
                else:
                    print("saved user data already exists")    
        else:
            print("Saved users not exist")  


# def blocked_users():
#     mydb = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="Root",
#     database="medico_final_db"
#     )
#     mycursor = mydb.cursor()
#     mycursor.execute("SELECT * FROM medico_donot_show_profile WHERE medico_donot_show_profile.member_id IN ( SELECT mm.id FROM medico_members mm WHERE LENGTH(mm.candidates_name) >= 30)")
#     result = mycursor.fetchall()
#     data = []
#     for row in result:
#         row_dict = {}
#         for i, column in enumerate(mycursor.description):
#             row_dict[column[0]] = row[i]
#         data.append(row_dict)
#     mycursor.close()
#     mydb.close()
#     print(len(data))
    # for i in range(len(data)):
    #     temp_data= data[i]
    #     print(i)
    #     member_id = f"MLP00{temp_data['member_id']}"
    #     donot_show_profile_ids = temp_data['donot_show_profile_id']
        
    #     # Convert the donot_show_profile_ids to a list of integers
    #     blocked_user_ids = [int(id_str) for id_str in donot_show_profile_ids.split(',') if id_str.strip().isdigit()]
    #     blocked_by = User.objects.filter(mlp_id__iexact=member_id, is_active=True).first()
    #     for blocked_user_id in blocked_user_ids:
    #         blocked_to = User.objects.filter(mlp_id__iexact=f"MLP00{blocked_user_id}", is_active=True).first()
    #         b_exists = BlockedUsers.objects.filter(user = blocked_by, blocked_user = blocked_to).exists()
    #         if not b_exists:
    #             if blocked_by and blocked_to:
    #                 blocked = BlockedUsers(user=blocked_by, blocked_user=blocked_to)
    #                 blocked.save()
    #                 print("Added blocked data")
    #             else:
    #                 print("One or more users not found.")
    #         else:
    #             print("already exists data") 



# For Interest table data
def interested_data():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * from medico_interested_profile where medico_interested_profile.id IN ( 71966, 143781)")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()

    print(len(data))
    
    for i in range(len(data)):
        temp_data = data[i]
        print(i)
        who_id = f"MLP00{temp_data['id']}"
        whom_id = f"MLP00{temp_data['interested_id']}"

        invitation_by = User.objects.filter(mlp_id__iexact=who_id, is_active=True).first()
        invitation_to = User.objects.filter(mlp_id__iexact=whom_id, is_active=True).first()
        interest_exists = Intrest.objects.filter(invitation_by=invitation_by, invitation_to=invitation_to).exists() 
        if invitation_by and invitation_to:
            if temp_data['accept_status'] == '1':
                status = "Accepted"
            elif temp_data['accept_status'] == '0':
                status = "Pending"
            else:
                status = "Rejected"
            if not interest_exists:
                interest = Intrest(invitation_by=invitation_by, invitation_to=invitation_to, status=status)
                interest.save()
                print("Added interest data")
                if status =="Accepted":
                    connection_list_instance=ConnectionList(user_one=invitation_by, user_two=invitation_to)
                    connection_list_instance.save()
                    print("connection data also saved")
            else:
                print("interest data already present")    
        else:
            print("One or more users not found.")



def blocked_users():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM medico_donot_show_profile WHERE  medico_donot_show_profile.member_id IN ( 71966, 143781)")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()
    print(len(data))
    for i in range(len(data)):
        temp_data= data[i]
        print(i)
        member_id = f"MLP00{temp_data['member_id']}"
        donot_show_profile_ids = temp_data['donot_show_profile_id']
        
        # Convert the donot_show_profile_ids to a list of integers
        blocked_user_ids = [int(id_str) for id_str in donot_show_profile_ids.split(',') if id_str.strip().isdigit()]
        blocked_by = User.objects.filter(mlp_id__iexact=member_id, is_active=True).first()
        for blocked_user_id in blocked_user_ids:
            blocked_to = User.objects.filter(mlp_id__iexact=f"MLP00{blocked_user_id}", is_active=True).first()
            b_exists = BlockedUsers.objects.filter(user = blocked_by, blocked_user = blocked_to).exists()
            if not b_exists:
                if blocked_by and blocked_to:
                    blocked = BlockedUsers(user=blocked_by, blocked_user=blocked_to)
                    blocked.save()
                    print("Added blocked data")
                else:
                    print("One or more users not found.")
            else:
                print("already exists data") 


# def connection_list_data():
#         accepted_invitations = Intrest.objects.filter(status="Accepted")
#         count =0 
#         for invitation in accepted_invitations:
#             print(count)
#             who_seen = User.objects.filter(mlp_id__iexact =  invitation.invitation_by.mlp_id, is_active=True,mandatory_questions_completed=True).first()
#             whom_seen = User.objects.filter(mlp_id__iexact = invitation.invitation_to.mlp_id , is_active=True,mandatory_questions_completed=True).first()
#             connect_exists = ConnectionList.objects.filter(user_one=who_seen, user_two=whom_seen)
#             if who_seen  and whom_seen:
#                     if  who_seen != whom_seen:
#                         connection_list_instance=ConnectionList(user_one=who_seen, user_two=whom_seen)
#                         connection_list_instance.save()
#                         print("user saved")
#                     else:
#                         print("Both are same")     
#             else:
#                 print("mandatory false of users")
#             count+=1               

#         print("data added successfully")     

   
def report_data():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("Select * from medico_report_profile where report_from IN ( SELECT mm.id FROM medico_members mm WHERE LENGTH(mm.candidates_name) >= 30)")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()
    
    for i in range(len(data)):
        temp_data= data[i]
        print(i)
        
        report_from_id = f"MLP00{temp_data['report_from']}"
        report_for_id = f"MLP00{temp_data['report_for']}"
        report_reason = f"MLP00{temp_data['report_reasion']}"

        report_from = User.objects.filter(mlp_id__iexact= report_from_id).first()
        report_for = User.objects.filter(mlp_id__iexact= report_for_id).first()
        
        if report_for and report_from:
            reason_list = [report_reason]

            # Serialize reason list to JSON before storing in the database
            serialized_reason = json.dumps(reason_list)

            report_instance = ReportUsers(user= report_from, report_user= report_for, reason= serialized_reason)
            report_instance.save()
            print("report added")
        else:
            print("Report related Users not found") 



def contact_viewed_data():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM medico_viewed_profile_details WHERE contact_seen = 'Yes' AND (who_seen_status = 'Provisional' OR who_seen_status = 'Active') And who_seen IN (SELECT mm.id FROM medico_members mm WHERE LENGTH(mm.candidates_name) >= 30)")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()
    print(len(data))
    for i in range(6,len(data)):
        temp_data =data[i]
        print(i)
        user_id = f"MLP00{temp_data['who_seen']}"
        seen_user_id = f"MLP00{temp_data['whom_seen']}"

        user_exists = User.objects.filter(mlp_id__iexact=user_id, is_active=True).first()
        seen_user_exists = User.objects.filter(mlp_id__iexact=seen_user_id, is_active=True).first()
        #contact_already_exists = ContactViewed.objects.filter(user__mlp_id__iexact=user_id, seen_contact__mlp_id__iexact=seen_user_id).exists()

        if user_exists and seen_user_exists :
               # if not contact_already_exists:
                # user = User.objects.get(mlp_id__iexact=user_id)
                # seen_user = User.objects.get(mlp_id__iexact=seen_user_id)
            contact_instance = ContactViewed(user=user_exists, seen_contact=seen_user_exists)
            contact_instance.save()
            print("data added")
              
            # else:
            #     print("contact viewed already exists")    
        else:
            print("contact users not found")


def seen_user_data():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM medico_viewed_profile_details WHERE contact_seen = 'Yes' AND  who_seen_status = 'Active' AND who_seen IN (71966, 143781)")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()

    print(len(data))

    for i in range(len(data)):
        temp_data = data[i] 
        print(i)

        seen_user_id = f"MLP00{temp_data['whom_seen']}"
        user_id = f"MLP00{temp_data['who_seen']}"

        user = User.objects.filter(mlp_id__iexact = user_id, is_active=True).first()
        seen_user = User.objects.filter(mlp_id__iexact = seen_user_id, is_active=True).first()


        if user and seen_user:
            seen_instance = ProfileView.objects.filter(viewer=user, viewed_user=seen_user).exists()

            if not seen_instance:
                # If entry does not exist, create a new SeenUser instance
                seen_instance = ProfileView( viewer=user,  viewed_user=seen_user)
                seen_instance.save()
            else:
                print("data already present")    
        else:
            print("user data already exist") 



def subscribed_data():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT medico_members.id as MlP_id , plan_name, subscription_start_date from medico_members join medico_membership_plan ON  medico_members.package_id = medico_membership_plan.id where medico_members.status='Active'")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()
    
    for temp_data in data:
        user_id = f"MLP00{temp_data['MlP_id']}"
        plan_name = temp_data['plan_name'].strip()  # Remove leading/trailing whitespaces
        create_date = temp_data['subscription_start_date']
        
        print("Processing user with ID:", user_id)
       # print("Plan name retrieved:", plan_name)

        # Your existing plan name transformations
        if plan_name == "Gold":
            plan_name = "Gold Old"
        if plan_name == "Premium":
            plan_name = "Premium Old"
        if plan_name == "Silver":
            plan_name = "Silver Old"
        if plan_name == "Platinum":
            plan_name = "Platinum Old"
        if plan_name == "Gold Plus":
            plan_name = "Gold Plus Web"
        if plan_name == "Premium Plus":
            plan_name = "Premium Plus Web"        

       # print("Transformed plan name:", plan_name)

        user = User.objects.filter(mlp_id__iexact=user_id).first()
        subscription = Subscription.objects.filter(name__iexact=plan_name).first()

        if user and subscription:
            # Check if the subscription already exists for the user
            existing_subscription = UserSubscription.objects.filter(user=user, subscription=subscription).first()

            if existing_subscription:
                print("Subscription already exists for this user")
            else:
                # Create a new UserSubscription instance
                sub_instance = UserSubscription(user=user, subscription=subscription, created_date=create_date)
                sub_instance.save()
                print("Subscribed user saved successfully")
        else:
            print("User and/or subscription not found")


def subscription_date_update():
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT medico_members.id as MlP_id , plan_name, subscription_start_date from medico_members join medico_membership_plan ON  medico_members.package_id = medico_membership_plan.id where medico_members.status='Active'")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close()

    print(len(data))
    
    for temp_data in data:
        user_id = f"MLP00{temp_data['MlP_id']}"
        plan_name = temp_data['plan_name'].strip()  # Remove leading/trailing whitespaces
        create_date = temp_data['subscription_start_date']

        if plan_name == "Gold":
            plan_name = "Gold Old"
        if plan_name == "Premium":
            plan_name = "Premium Old"
        if plan_name == "Silver":
            plan_name = "Silver Old"
        if plan_name == "Platinum":
            plan_name = "Platinum Old"
        if plan_name == "Gold Plus":
            plan_name = "Gold Plus Web"
        if plan_name == "Premium Plus":
            plan_name = "Premium Plus Web"        
        
        user = User.objects.filter(mlp_id__iexact=user_id).first()
        subscription = Subscription.objects.filter(name__iexact=plan_name).first()
        
        if user and subscription:
            # Check if the subscription already exists for the user
            existing_subscription = UserSubscription.objects.filter(user=user, subscription=subscription).first()

            if existing_subscription:
                # Update the created_date if create_date is provided
                if create_date:
                    existing_subscription.created_date = create_date
                
                # Save the updated instance
                existing_subscription.save()
                print("Subscribed user date updated successfully")
        else:
            print("User and/or subscription not found")


def remove_duplicates():
    from django.db.models import Count

    duplicates = ContactViewed.objects.values('user', 'seen_contact').annotate(count=Count('id')).filter(count__gt=1)
    print("Number of duplictes",duplicates)
    count =0
    for duplicate in duplicates:
        print(count)
        entries = ContactViewed.objects.filter(user=duplicate['user'], seen_contact=duplicate['seen_contact'])
        entries.exclude(id=entries.first().id).delete()
        count+=1
    print("Done") 



def remove_duplicates_notifications():
        from django.db.models import Count

        # Find duplicates
        duplicates = Notifications.objects.values('user', 'message', 'type') \
                                            .annotate(count=Count('id')) \
                                            .filter(count__gt=1)
        print("duplicates",duplicates)
        count = 0
        for duplicate in duplicates:
            print(count)
            count +=1
            # Get IDs of duplicate records
            ids = Notifications.objects.filter(user=duplicate['user'], 
                                                message=duplicate['message'], 
                                                type=duplicate['type']) \
                                    .values_list('id', flat=True)
            # Keep the first record and delete the rest
            Notifications.objects.filter(id__in=ids[1:]).delete()
        print("Deleted successfully")



def update_remove_profiles():
          # Connect to MySQL
    mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Root",
    database="medico_final_db"
    )
    mycursor = mydb.cursor()
    #mycursor.execute("SELECT *,medico_members.id as Mlp_id,country.country_c as Country_Code, medico_partner_preference.second_marriage AS Marital_Pref, medico_partner_preference.physically_challenged AS Preference,country.country_name AS Country_Name,state.state_name AS State_Name FROM medico_members LEFT JOIN medico_partner_preference ON medico_members.id = medico_partner_preference.user_id LEFT JOIN country ON medico_members.country = country.country_id LEFT JOIN state ON medico_members.state= state.state_id WHERE  email_id = 'sandipbhosale0019@gmail.com'")
    mycursor.execute("select  id , status , candidates_name from medico_members")
    result = mycursor.fetchall()
    data = []
    for row in result:
        row_dict = {}
        for i, column in enumerate(mycursor.description):
            row_dict[column[0]] = row[i]
        data.append(row_dict)
    mycursor.close()
    mydb.close() 

    
    for item in data:
        print(item['candidates_name'])
        mlp_id = f"MLP00{item['id']}"
        existing_user = User.objects.filter(mlp_id=mlp_id).first()

        if existing_user:
            print("user:",existing_user)
            print("status:",item['status'])
           
            if item['status'] == "Remove" or item['status'] == "Wrong" or item['status']=="Pending":
                is_active = False
            else:
                is_active = True
            print("is_active",is_active)
            existing_user.is_active = is_active
            existing_user.save()  

    print("Data updated sucessfully")



# # To add MLP00 in all mlp_ids
# from django.db.models import Value
# from django.db.models.functions import Concat
# from users.models import User

# # Update all mlp_id values by appending "MLP00"
# #User.objects.update(mlp_id=Concat(Value("MLP00"), 'mlp_id'))

# def remove_mlp():
#     users = User.objects.all()

#     # Iterate over each user and update their mlp_id
#     for user in users:
#         user.mlp_id = user.mlp_id.replace("MLP00", "").replace("LP00", "")  # Remove both prefixes
#         user.save()



from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def update_user_upgrade_status():
    # Get the active subscription of the user
    users = User.objects.filter(is_active=True)
    for user in users:
        print("User",user)
        active_subscriptions = UserSubscription.objects.filter(user=user, is_subscription_active=True)
        print("active subscrptions",active_subscriptions)
        
        if active_subscriptions.exists():
            # Assuming we consider only the latest subscription
            active_subscription = active_subscriptions.latest('created_date')
            print("latest subscription",active_subscription)
            
            # If subscription exists, check for upgrade eligibility
            if active_subscription.subscription:
                # subscription_start_date = active_subscription.created_date
                # subscription_end_date = subscription_start_date + relativedelta(months=active_subscription.subscription.timeframe)  # Assuming this is part of Subscription model
                subscription_start_date = active_subscription.created_date
                # Calculate the subscription end date based on the subscription's timeframe in months
                subscription_end_date = subscription_start_date + relativedelta(months=active_subscription.subscription.timeframe)
                
                # Get the current time as timezone-aware
                now = timezone.now()

                print("start date",subscription_start_date)
                print("end date",subscription_end_date)
                # Calculate the one-month window after subscription creation
                upgrade_window_end_date = subscription_start_date + relativedelta(months=1)
                
                # Check if the subscription end date is in the future (i.e., still valid)
                if subscription_end_date >= now:
                    # Check if the current date is within the upgrade window
                    if now <= upgrade_window_end_date:
                        can_upgrade_subscription = 1
                    else:
                        can_upgrade_subscription = 0
                else:
                    can_upgrade_subscription = -1
            else:
                # Handle cases where subscription data is missing or inactive
                can_upgrade_subscription = -1
        else:
            # No active subscription found
            can_upgrade_subscription = -1

        print("can upgrade subscription",can_upgrade_subscription)    

        # Update the user's can_upgrade_subscription field
        user.can_upgrade_subscription = can_upgrade_subscription
        user.save()
    print("Done succesfully") 



def subscription_create_date():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url = "https://www.medicolifepartner.com/index.php/api/migrate_payment"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()
        items = data['changes']['create']['registration'][0]['fields'] 
        for temp_data in items:
            user_id = f"MLP00{temp_data['user_id']}"
            plan_name = temp_data['plan_name']  # Remove leading/trailing whitespaces
            create_date = temp_data['subscription_start_date']  
            
            user = User.objects.filter(mlp_id__iexact=user_id).first()
            subscription = Subscription.objects.filter(name__iexact=plan_name).first()
            
            subscription_start_date = timezone.make_aware(
                datetime.strptime(temp_data['subscription_start_date'], "%Y-%m-%d %H:%M:%S"),
                timezone.get_default_timezone()
            )
            subscription_end_date = timezone.make_aware(
                datetime.strptime(temp_data['subscription_end_date'], "%Y-%m-%d %H:%M:%S"),
                timezone.get_default_timezone()
            )

            
            if user and subscription:
                # Check if the subscription already exists for the user
                existing_subscription = UserSubscription.objects.filter(user=user, subscription=subscription).first()

                if existing_subscription:
                    # Update the created_date if create_date is provided
                    if create_date:
                        existing_subscription.created_date = subscription_start_date
                    
                    # Save the updated instance
                    existing_subscription.save()
                    print("Subscribed user date updated successfully")
                else:
                    print(f"no existing subscription for user {user.mlp_id}")    
            else:
                print("User and/or subscription not found")

    except Exception as e:
        response["error"] = f"Error: {str(e)}"
        return response  
    

def update_user_upgrade_status_code():
    # Get all users who have active subscriptions
    active_subscriptions = UserSubscription.objects.filter(is_subscription_active=True).order_by('user', '-created_date')
    print("active subscription count",active_subscriptions.count())

    processed_users = set()  # To track users we've already processed

    for subscription in active_subscriptions:
        # Only process the latest subscription per user
        if subscription.user.mlp_id in processed_users:
            print("skipped already processed data for the user with mlp_id",subscription.user.mlp_id)
            continue  # Skip if this user's latest subscription was already processed
        
        # Mark this user as processed
        processed_users.add(subscription.user.mlp_id)

        if subscription.subscription is None:
            print(f"User with mlp_id {subscription.user.mlp_id} with ios subscription")
            continue
        
        # Extract relevant information from the latest subscription
        mlp_id = subscription.user.mlp_id
        plan_name = subscription.subscription if subscription.subscription is not None else None
        subscription_start_date = subscription.created_date
        subscription_end_date = subscription_start_date + relativedelta(months=subscription.subscription.timeframe)

        print("User_mlp_id:", mlp_id)
        print("user name",subscription.user.name)
        print("Plan Name:", plan_name)
        print("Subscription Start Date:", subscription_start_date)
        print("Subscription End Date:", subscription_end_date)

        # Check if the user exists in the User model
        active_user = User.objects.filter(mlp_id=mlp_id).first()

        if active_user:
            # Get the current time as timezone-aware
            now = timezone.now()

            # Calculate the upgrade window end date (one month after start)
            upgrade_window_end_date = subscription_start_date + relativedelta(months=1)

            # Determine if the user is eligible for an upgrade based on the dates
            if subscription_end_date >= now:
                if now <= upgrade_window_end_date:
                    can_upgrade_subscription = 1  # Eligible for upgrade
                else:
                    can_upgrade_subscription = 0  # Not eligible
            else:
                can_upgrade_subscription = -1  # Subscription expired
            
            # Update the `can_upgrade_subscription` field in the User model
            active_user.can_upgrade_subscription = can_upgrade_subscription
            active_user.save()

            print(f"User {mlp_id} and  can_upgrade_subscription set to {can_upgrade_subscription}")
        else:
            print(f"User with mlp_id {mlp_id} not found")

    print("Process completed successfully")


def wrong_profile_update():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url = "https://www.medicolifepartner.com/index.php/api/migrate_registration"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()
        items = data['changes']['create']['registration'][0]['fields']

        for item in items:
            mlp_id = f"MLP00{item['id']}"
            status = item['status']

            user = User.objects.filter(mlp_id=mlp_id).first()
            print("user",user)
            if user and status == "Wrong":
                user.is_wrong=True
                user.save()
                print("updated")
            else:
                print("User not exists")    
        print("Done successfully")
    except Exception as e:
        response["error"] = str(e)
        return response      


def update_user_plans_code():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url = "https://www.medicolifepartner.com/index.php/api/migrate_payment"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()

        
        items = data['changes']['create']['registration'][0]['fields'] 
        for fields in items:
            print(fields['user_id'])
            user_id = f"MLP00{fields['user_id']}"
            price = fields["price"]
            plan_name = fields["plan_name"]
            create_date = fields['subscription_start_date']
            mihpayid = fields['mihpayid'] if fields['mihpayid'] and fields['mihpayid'] != "" else user_id
            status = fields['payment_status']

            user = User.objects.filter(mlp_id=user_id).first()
            subscription = Subscription.objects.filter(name__iexact=plan_name).first()
            print("user",user)

            subscription_exists = UserSubscription.objects.filter(user=user)
            print("subscriptions",subscription_exists)
            if subscription_exists.exists():
                subscription_instance = subscription_exists.latest('created_date')  # Get the latest subscription
                print("latest subscriptions",subscription_exists)
                if status == "complete" and user:
                    # Update the existing subscription instead of deleting
                    subscription_instance.subscription = subscription
                    subscription_instance.save()
                    print("Subscribed user updated successfully")
                else:
                    print("status is not complete or user not found")    
                
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

                print(f"User {user_id} and  can_upgrade_subscription set to {can_upgrade_subscription}") 
                user.can_upgrade_subscription = can_upgrade_subscription
                user.save() 
                print("Can upgrade subscription value updated successfully") 

                # transaction_exists = TransactionEntity.objects.filter(mihpayid=mihpayid, user=user).exists()
                # if  transaction_exists:
                #     TransactionEntity.objects.filter(mihpayid=mihpayid, user=user).update(
                #         amount=price,
                #         user=user,
                #         subscription=subscription
                #     )
                #     print("Transaction data updated successfully")
                # else:
                #     print("Transaction already exists") 
                transaction_exists = TransactionEntity.objects.filter(mihpayid=mihpayid, user=user).first()
                if transaction_exists:
                    # Update the existing transaction
                    transaction_exists.amount = price
                    transaction_exists.subscription = subscription
                    transaction_exists.save()
                    print("Transaction data updated successfully")
                else:
                    print("No transaction exists") 
            else:
                print(f"No subscription present for {user_id}")

    except Exception as e:
        response["error"] = str(e)
        return response  

from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def sync_subs():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url =  "https://www.medicolifepartner.com/index.php/api/migrate_registration"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()
       
        print("before fetching data")
      
        payment_data = data['changes']['create']['registration'][0]['fields']  
        
        print("Payment data started")
        for fields in payment_data:
            print("Inside payment")
            user_id = f"MLP00{fields['id']}"
            plan_name = fields["plan_name"]
            status = fields['payment_status']
            coupon_code = None

            print("Processing user with ID:", user_id)
            print("Plan name retrieved:", plan_name) 

            print("Transformed plan name:", plan_name)
            print("status",status)


            if user_id == "MLP00142329" or user_id == "MLP00156371" or user_id == "MLP00159156" or user_id == "MLP00159200" or user_id == "MLP00160728" or user_id=="MLP00161137":
                continue 
            user = User.objects.filter(mlp_id__iexact=user_id, is_active=True).first()
            subscription = Subscription.objects.filter(name__iexact=plan_name).first()

            subscription_start_date = timezone.make_aware(
                datetime.strptime(fields['subscription_start_date'], "%Y-%m-%d %H:%M:%S"),
                timezone.get_default_timezone()
            )
            subscription_end_date = timezone.make_aware(
                datetime.strptime(fields['subscription_end_date'], "%Y-%m-%d %H:%M:%S"),
                timezone.get_default_timezone()
            )

            if user and subscription and status == "complete":
                # Check if UserSubscription already exists
                subscription_exists = UserSubscription.objects.filter(user=user, subscription=subscription, is_subscription_active=True).exists()
                if not subscription_exists:
                    sub_instance = UserSubscription(user=user, subscription=subscription, subscription_ios=None, created_date=subscription_start_date)
                    sub_instance.save()
                    print("Subscribed user saved successfully")
                    
                    print("Can upgrade subscription value")
                    can_upgrade_subscription = -1 
                    if status == "complete":
                        # subscription_start_date = item['subscription_start_date']
                        # subscription_end_date = item['subscription_end_date']
                        # subscription_start_date = datetime.strptime(fields['subscription_start_date'], "%Y-%m-%d %H:%M:%S")
                        # subscription_end_date = datetime.strptime(fields['subscription_end_date'], "%Y-%m-%d %H:%M:%S")
                       

                        # Calculate the one-month window after subscription creation
                        upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                        # Check if subscription is active
                        if subscription_end_date >= timezone.now():
                            # Check if within the upgrade window
                            if timezone.now() <= upgrade_window_end_date:
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
            else:
                print("User and/or subscription not found")

        print("payment data added successfully")


    except Exception as e:
        response["error"] =  f"Error: {str(e)}"
        return response        

def sync_payment_data_proper():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url =  "https://www.medicolifepartner.com/index.php/api/migrate_payment"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()
       
        print("before fetching data")
      
        payment_data = data['changes']['create']['registration'][0]['fields']  
        
        print("Payment data started")
        for fields in payment_data:
            print("Inside payment")
            user_id = f"MLP00{fields['id']}"
            price = fields["price"]
            plan_name = fields["plan_name"]
            create_date = fields['subscription_start_date']
            mihpayid = fields['mihpayid'] if fields['mihpayid'] and fields['mihpayid'] != "" else user_id
            status = fields['payment_status']
            coupon_code = None
            payload = {}

            print("Processing user with ID:", user_id)
            print("Plan name retrieved:", plan_name) 

            print("Transformed plan name:", plan_name)
            print("status",status)



            user = User.objects.filter(mlp_id__iexact=user_id, is_active=True).first()
            subscription = Subscription.objects.filter(name__iexact=plan_name).first()

            subscription_start_date = timezone.make_aware(
                datetime.strptime(fields['subscription_start_date'], "%Y-%m-%d %H:%M:%S"),
                timezone.get_default_timezone()
            )
            subscription_end_date = timezone.make_aware(
                datetime.strptime(fields['subscription_end_date'], "%Y-%m-%d %H:%M:%S"),
                timezone.get_default_timezone()
            )



            if user and subscription and status == "complete":
                # Check if UserSubscription already exists
                subscription_exists = UserSubscription.objects.filter(user=user, subscription=subscription).exists()
                if not subscription_exists:
                    sub_instance = UserSubscription(user=user, subscription=subscription, subscription_ios=None, created_date=subscription_start_date)
                    sub_instance.save()
                    print("Subscribed user saved successfully")
                    
                    print("Can upgrade subscription value")
                    can_upgrade_subscription = -1 
                    if status == "complete":
                        # subscription_start_date = item['subscription_start_date']
                        # subscription_end_date = item['subscription_end_date']
                        # subscription_start_date = datetime.strptime(fields['subscription_start_date'], "%Y-%m-%d %H:%M:%S")
                        # subscription_end_date = datetime.strptime(fields['subscription_end_date'], "%Y-%m-%d %H:%M:%S")
                       

                        # Calculate the one-month window after subscription creation
                        upgrade_window_end_date = subscription_start_date + timedelta(days=30)

                        # Check if subscription is active
                        if subscription_end_date >= timezone.now():
                            # Check if within the upgrade window
                            if timezone.now() <= upgrade_window_end_date:
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
    except Exception as e:
        response["error"] =  f"Error: {str(e)}"
        return response



#delete other accounts of active accounts

def deactivate_other_accounts():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        subscriptions = UserSubscription.objects.filter(is_subscription_active=True)

        for  subscription in subscriptions:
            mobile_number = subscription.user.mobile_number
            mlp_id = subscription.user.mlp_id

            users = User.objects.filter(mobile_number=mobile_number)
            print("same users",users)
            #exclude the user with mlp_id having subscription
            remaining_users = users.exclude(mlp_id=mlp_id)
            print("Remaining users",remaining_users)

            for user in remaining_users:
                user.is_active = False
                user.save()
                print("User not subscribed is_acive = false updated successfully")

            # remaining_users.update(is_active = False)
            print(f"Deactivated users with mobile number {mobile_number} excluding mlp_id {mlp_id}.")

        print("Done successfully!!")    

    except Exception as e:
        response["error"] = str(e)
        return response    


def activate_subscribed_account():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    try:
        subscriptions = UserSubscription.objects.filter(is_subscription_active=True)

        for  subscription in subscriptions:
            # mobile_number = subscription.user.mobile_number
            mlp_id = subscription.user.mlp_id
            print("Mlp id",mlp_id)

            user = User.objects.filter(mlp_id=mlp_id).first()
            print("user",user)
            if user:
                user.is_active = True
                user.save()

                print("User is active activated successfully")
            else:
                print("No user exists with mlp_id",mlp_id)    

    except Exception as e:
        response["error"] = str(e)
        return response


def success_stories_data():
    response = {
        "status_code": 500,
        "message": "Internal server error"
    }
    # API endpoint URL
    api_url =  "https://www.medicolifepartner.com/index.php/api/sucess_story"

    try:
        # Fetch data from the API
        api_response = requests.get(api_url)
        data = api_response.json()
        items = data['changes']['create']['registration'][0]['fields']
       
        print("before fetching data")

        for item in items:
            print(item)
            name = item['name']
            partner_name = item['partner_name']
            story = item['description']
            # image = f"https://www.medicolifepartner.com/assets/img/{item['story_pic']}" if item['story_pic'] else "[]"

            image_url = (
                f"https://www.medicolifepartner.com/assets/img/{item['story_pic']}"
                if item.get('story_pic') 
                else "https://www.medicolifepartner.com/assets/img/success-story1.jpg"
            )

            # Convert image_url to JSON array format
            image = json.dumps([image_url])

            user = User.objects.filter(name=name).first()
            print(user)
            if not user:
                print(f"User '{name}' not found in database.")
                continue

            # Check if a success story already exists for this partner
            success_story= SuccessStory( user= user, partner_name=partner_name,story= story,  image= image, created_date= timezone.now() ) 
            success_story.save()
            print("Success story saved successfully")

    except Exception as e:
        response["error"] = str(e)
        return response

   
    