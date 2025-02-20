from datetime import timedelta
from django.conf import settings
from django.db import models
import hashlib
import binascii
import os
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.indexes import GinIndex
import requests

GENDER = (
    ("m", "Male"),
    ("f", "Female")
)

EATING_HABITS = (
    ("veg", "VEGETARIAN"),
    ("non_veg", "NON-VEGETARIAN"),
    ("eggitarian", "VEG+EGG"),
    ("jain", "JAIN")
)

SMOKING_HABITS = (
    ("ns", "Non-Smoker"),
    ("os", "Occasional Smoker"),
    ("rs", "Regular Smoker"),
    ("tq", "Trying to Quit")
)

DRINKING_HABITS = (
    ("nd", "Non-Drinker"),
    ("sd", "Social Drinker"),
    ("od", "Occasional Drinker"),
    ("rd", "Regular Drinker"),
)

RELATIONS = (
    ("son", "SON"),
    ("daughter", "DAUGHTER"),
    ("sibling", "SIBLING"),
    ("relative", "RELATIVE"),
    ("friend", "FRIEND"),
)



# Create your models here.
class Expertise(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name


class Graduation(models.Model):
    expertise_obj = models.ForeignKey(Expertise, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name


class PostGraduation(models.Model):
    graduation_obj = models.ForeignKey(Graduation, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name
    
class Religion(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name

# class Profession(models.Model):
#     name = models.CharField(max_length=50, null=False, blank=False)
#     def __str__(self):
#         return self.name
    
class Specialization(models.Model):
    name = models.CharField(max_length=50, null=True, blank=False, db_index=True)
    def __str__(self):
        return self.name
    

class MaritalStatus(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name

class MotherTongue(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name
    
class Languages(models.Model):
    name = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name
    
class Caste(models.Model):
    name = models.CharField(max_length=500, null=False, blank=False, db_index=True)
    def __str__(self):
        return self.name
    
class SubCaste(models.Model):
    caste= models.ForeignKey(Caste,related_name='caste', on_delete=models.CASCADE, default=None, null=True, blank=True)
    name = models.CharField(max_length=500, null=True, blank=False, db_index=True)
    def __str__(self):
        return self.name if self.name else ""
    
class Subscription(models.Model):
    name = models.CharField(max_length=500, db_index=True)
    description = models.TextField()
    regular_plan = models.BooleanField(default=True)
    timeframe = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField()
    
    def __str__(self):
        return self.name

    
class AppleSubscription(models.Model):
    name = models.CharField(max_length=500, db_index=True)
    description = models.TextField()
    regular_plan = models.BooleanField(default=True)
    timeframe = models.PositiveSmallIntegerField()
    amount = models.PositiveIntegerField()
    
    def __str__(self):
        return self.name      

class User(models.Model):
    mlp_id = models.CharField(max_length=20, unique=True, null=False, blank=False,db_index=True)
    mobile_number = models.CharField(max_length=30, null=False, blank=False,db_index=True)
    name = models.CharField(max_length=500,db_index=True)
    email = models.CharField(max_length=500,db_index=True)
    gender = models.CharField(max_length=10,db_index=True, choices=GENDER)
    dob = models.DateField(blank=True, null=True,db_index=True)
    time_birth = models.TimeField(blank=True, null=True,db_index=True)
    birth_location = models.CharField(max_length=500, null=True, blank=True,db_index=True)
    horoscope_matching = models.CharField(max_length=500, null=True, blank=True,db_index=True)
    about = models.TextField(blank=True, null=True)
    future_aspirations = models.TextField(blank=True, null=True)
    mother_tongue = models.ManyToManyField(MotherTongue,related_name="mother_tongue", blank=True)
    languages = models.ManyToManyField(Languages, related_name="language_spoken", blank=True)
    is_primary_account = models.BooleanField(default=True, blank=False, null=False, help_text="if false then this account is linked to someone else",db_index=True)
    religion = models.ForeignKey(Religion, on_delete=models.SET_NULL, null=True)
    profile_pictures = models.TextField(default="[]",db_index=True)
    video = models.TextField(default="[]",db_index=True)
    family_photos = models.TextField(default="[]",db_index=True)
    manglik = models.IntegerField(help_text="If true means you state you are manglik",null=True, blank=True, default=-1,db_index=True)
    height = models.PositiveIntegerField(default=None, null=True,db_index=True,blank=True)
    weight = models.PositiveIntegerField(default=None, null=True,db_index=True,blank=True)
    complexion = models.CharField(max_length=500, null=True, blank=True, help_text="Indicates Complexion",db_index=True)
    body_build = models.CharField(max_length=500, null=True, blank=True,db_index=True, help_text="Indicates lean, wellbuild or heavy")
    physical_status = models.CharField(max_length=500, null=True, blank=True,db_index=True, help_text="Indicates normal or disabled")
    salary = models.CharField(max_length=500, null=True,db_index=True,blank=True)
    password = models.CharField(max_length=500, null=True, blank=True,db_index=True)  
    whatsapp_number = models.CharField(max_length=50, null=True, blank=True,db_index=True) 
    marital_status = models.ForeignKey(MaritalStatus, on_delete=models.SET_NULL, null=True,db_index=True)
    eating_habits = models.CharField(max_length=100, choices=EATING_HABITS, default=None, blank=True, null=True,db_index=True)
    smoking_habits = models.CharField(max_length=100, choices=SMOKING_HABITS, default=None, blank=True, null=True,db_index=True)
    drinking_habits = models.CharField(max_length=100, choices=DRINKING_HABITS, default=None, blank=True, null=True,db_index=True)
    hobbies = models.TextField(default="[]",db_index=True)
    other_hobbies = models.TextField(default="[]",db_index=True)
    activity_status = models.BooleanField(default=False,db_index=True)
    city = models.CharField(max_length=500, blank=True, null=True, help_text="City you live in",db_index=True)
    state = models.CharField(max_length=500, blank=True, null=True, help_text="State you live in",db_index=True)
    country = models.CharField(max_length=500, blank=True, null=True, help_text="Country you live in",db_index=True)
    caste = models.CharField(max_length=500, blank=True, null=True, help_text="Your Caste",db_index=True)
    sub_caste = models.ForeignKey(SubCaste,related_name="user_subcaste", on_delete=models.SET_NULL, null=True, blank=True, help_text="Your_subcaste")
    mandatory_questions_completed = models.BooleanField(default=False, help_text='If True then it means user have completed its mandatory questions',db_index=True)
    profile_createdby = models.CharField(max_length=100, null=True, blank=True,default="Candidate", help_text="Indicates who has created that profile",db_index=True)
    disease_history = models.CharField(max_length=1000, blank=True, null=True, help_text="Disease/Surgery undergone",db_index=True)
    blood_group = models.CharField(max_length=500, blank=True, null=True, help_text="Your Bloodgroup",db_index=True)
    graduation_status=models.CharField(max_length=500, blank=True, null=True, help_text="Your graduation status",db_index=True)
    graduation_institute=models.CharField(max_length=500, blank=True, null=True,db_index=True)
    post_graduation_status=models.CharField(max_length=500, blank=True, null=True, help_text="Your graduation status",db_index=True)
    post_graduation_institute=models.CharField(max_length=500, blank=True, null=True,db_index=True)
    profession = models.TextField(default="[]",db_index=True)
    specialization = models.ForeignKey(Specialization, related_name="specialization",on_delete=models.SET_NULL,null=True, blank=True)
    profession_description = models.CharField(max_length=500, blank=True, null=True,db_index=True)
    schooling_details = models.CharField(max_length=500, blank=True, null=True,db_index=True)
    facebook_profile = models.CharField(max_length=1000, null=True, blank=True,db_index=True)
    instagram_profile = models.CharField(max_length=1000, null=True, blank=True,db_index=True)
    linkedin_profile = models.CharField(max_length=1000, null=True, blank=True , db_index=True)
    mother_name = models.CharField(max_length=500, null=True, blank=True , db_index=True)
    mother_occupation = models.CharField(max_length=500, null=True, blank=True , db_index=True)
    mother_education = models.CharField(max_length=500, null=True, blank=True , db_index=True)
    father_name = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    father_occupation = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    father_education = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    sibling = models.IntegerField(help_text="Indicates whether user has siblings or not", null=True, blank=True, default=-1, db_index=True)
    family_financial_status = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    family_environment = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    family_car = models.CharField(max_length=500, null=True, blank=True, help_text="Family owns a car", db_index=True)
    city_parents = models.CharField(max_length=550, blank=True, null=True, help_text="City where parents reside", db_index=True)
    family_house = models.CharField(max_length=550, blank=True, null=True, help_text="Whether house is owned or rented", db_index=True)
    own_car=models.CharField(max_length=500, null=True, blank=True, help_text="Candidate owns a car", db_index=True)
    residence = models.CharField(max_length=500, null=True, blank=True, help_text="Indicates whether residence is owned or rented", db_index=True)
    religious_practices=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates religious practice of candidates", db_index=True)
    interest_party=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates whether candidate loves dining or partying", db_index=True)
    interest_music=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates whether an art lover/music enthusiast", db_index=True)
    foodie=models.IntegerField(help_text="If true you are a foodie", null=True, blank=True, default=-1, db_index=True)
    nature=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates your nature", db_index=True)
    beauty_consciousness=models.IntegerField(help_text="If true you are a conscious about beauty/body", null=True, blank=True, default=-1, db_index=True)
    work_out=models.IntegerField(help_text="If true you are a interested in yogs/gym/workout", null=True, blank=True, default=-1, db_index=True)
    body_clock=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates whether you are a morning/latenight person", db_index=True)
    kids_choice=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates your preference on kids", db_index=True)
    registration_number=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates your doctor's registartion number", db_index=True)
    eyesight=models.CharField(max_length=500, null=True, blank=True, help_text="Indicates your eyesight", db_index=True)
    preferred_time_connect = models.CharField(max_length=500, blank=True, null=True, db_index=True, help_text="Indicates preferred time for connect")
    phone_is_verified = models.BooleanField(default=False, db_index=True)
    notification_token = models.CharField(max_length=1000, null=True, blank=True, db_index=True)
    can_upgrade_subscription = models.IntegerField(default=-1, help_text="This indicates if user can upgrade their current subscription or not, -1 for no subcription, 1 for can upgrade and 0 for not able to upgrade", db_index=True)
    graduation_obj = models.ForeignKey(Graduation, on_delete=models.SET_NULL,null=True, blank=True)
    completed_post_grad = models.BooleanField(default=True, help_text="if False then no postgraduation done by user", db_index=True)
     
    partner_age_preference = models.BooleanField(default=False, help_text="If False then no partner age preference", db_index=True)
    partner_age_from = models.PositiveIntegerField(default=None, null=True, db_index=True , blank=True)
    partner_age_to = models.PositiveIntegerField(default=None, null=True, db_index=True,blank=True)
    partner_expertise_preference = models.BooleanField(default=False, help_text="If False then no partner expertise preference", db_index=True)
    partner_religion_preference = models.BooleanField(default=False, help_text="If False then no partner religion preference", db_index=True)
    partner_marital_status_preference = models.BooleanField(default=False, help_text="If False then no partner marital status preference", db_index=True)
    partner_specialization_preference = models.BooleanField(default=False, help_text="If False then no specialization preference", db_index=True)
    partner_graduation_preference = models.BooleanField(default=False, help_text="If False then no graduation preference", db_index=True)
    partner_postgraduation_preference = models.BooleanField(default=False, help_text="If False then no postgrad preference", db_index=True)
    partner_height_preference = models.BooleanField(default=False, help_text="If False then no partner height preference", db_index=True)
    partner_height_from = models.PositiveIntegerField(default=None, null=True, db_index=True , blank=True)
    partner_height_to = models.PositiveIntegerField(default=None, null=True, db_index=True,blank=True)
    partner_cities_preference = models.BooleanField(default=False, help_text="If False then no partner cities preference", db_index=True)
    partner_cities_from = models.TextField(default="[]", db_index=True)
    partner_state_preference = models.BooleanField(default=False, help_text="If False then no partner state preference", db_index=True)
    partner_state_from = models.TextField(default="[]", db_index=True)
    partner_country_preference = models.BooleanField(default=False, help_text="If False then no partner country preference", db_index=True)
    partner_country_from = models.TextField(default="[]", db_index=True)
    partner_caste_preference = models.BooleanField(default=False, help_text="If False then no partner caste preference", db_index=True)
    partner_caste_from = models.TextField(default="[]", db_index=True)
    partner_income_preference=models.BooleanField(default=False,help_text="If False then no partner income preference",db_index=True)
    partner_income_from = models.PositiveIntegerField(default=None, null=True, db_index=True , blank=True)
    partner_income_to = models.PositiveIntegerField(default=None, null=True, db_index=True,blank=True)
    partner_mothertongue_preference= models.BooleanField(default=False, help_text="If False then no partner mother tongue preference", db_index=True)
    partner_mothertongue_from = models.ManyToManyField(MotherTongue, related_name="partner_mothertongue", blank=True)
    partner_physicalstatus=models.CharField(max_length=500, null=True, blank=True, db_index=True)
    is_wrong = models.BooleanField(default=False, db_index=True,help_text="wrong profiles can not login again") 
    last_seen = models.DateTimeField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, db_index=True)

    
    # def __str__(self):
    #     return self.name if self.name else self.mlp_id

    def __str__(self):
        return self.mlp_id
    
    def save(self, *args, **kwargs):
        # if not self.mlp_id:
        #     self.mlp_id = "MLP00"+hashlib.shake_128(self.mobile_number.encode('ASCII')).hexdigest(4)
        # super().save(*args, **kwargs)
        if not self.mlp_id:
            response = requests.post("https://www.medicolifepartner.com/index.php/api/get_reg_data", json={"phone": self.mobile_number})
            print("response",response)
            if response.status_code == 200:
                self.mlp_id ="MLP00" + str(response.json().get("mlp_id"))
                print("mlp_id",self.mlp_id)
            else:
                raise ValueError("Failed to generate mlp_id")
        super().save(*args, **kwargs)
    
    def delete(self):
        self.is_active = False
        self.save()
    
    #Cache, invalidate cache if any field changes, 10min
    def calculate_profile_percentage(self):
        fields_to_check=self._meta.get_fields()
        completedcount=0
        field_exclude=['user', 'seen_profile','primary_user','linked_user','blocking_user','blocked_user','saving_user','saved_profile','invitation_from','invitation_to','user_one', 'user_two','user_token','searchresult','usersubscription','userapplesubscription','webapptransaction','user_notifications','searchhistory','user_notifications', 'coupon','transactionentity','user_sender_notifications','ratingreview','userstories','stories_viewedby','contactsviewed','seencontact','bachelor_of_the_day','success_stories', 'partnerpgpreference', 'partnergraduationpreference','notification_settings', 'userblockedendpoints']
        incompletefield=[]
        total_fields=0
        for field in fields_to_check:
            if field.is_relation:
                if field.name in field_exclude:
                    pass
                elif field.many_to_many:
                    total_fields+=1
                    if getattr(self, field.name).all():
                        completedcount+=1
                    else:
                        incompletefield.append(field.name)
                else:
                    total_fields+=1
                    if getattr(self, field.name):
                        completedcount+=1
                    else:
                        incompletefield.append(field.name)
            else:
                total_fields+=1
                if getattr(self, field.name) is not None and getattr(self, field.name) !='' and getattr(self, field.name) !='[]':
                    completedcount+=1
                else:
                    incompletefield.append(field.name)
        # print(incompletefield)
        # print(completedcount, total_fields)
        percent=completedcount/total_fields*100 if completedcount else 0
        return round(percent,0)
    
    


class BlockEndPoints(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userblockedendpoints")
    endpoint = models.CharField(max_length=100)
    session = models.CharField(max_length=4)
    created_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'endpoint')


class SeenUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    seen_profile = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seen_profile')
    times_visited = models.PositiveIntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="usersubscription")
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE,null=True,blank=True)
    subscription_ios = models.ForeignKey(AppleSubscription , on_delete=models.CASCADE,null=True,blank=True)
    is_subscription_active = models.BooleanField(default=True, db_index=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Use provided created_date if set, else default to current date
        if not self.created_date:
            self.created_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        subscription_name = self.subscription.name if self.subscription else None
        subscription_ios_name = self.subscription_ios.name if self.subscription_ios else None
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {subscription_name or subscription_ios_name}"

class ContactViewed(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="contactsviewed")
    seen_contact = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seencontact')
    contactsviewed = models.PositiveIntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)


class Siblings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_siblings')
    sibling_gender = models.CharField(max_length=10, choices=GENDER, null=True, blank=True)
    sibling_name = models.CharField(max_length=100, null=True, blank=True)
    sibling_education = models.CharField(max_length=100, null=True, blank=True)
    sibling_marital_status = models.CharField(max_length=30, null=True, blank=True)
    sibling_profession = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return self.sibling_name if self.sibling_name else self.id

class PartnerExpertisePreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="partnerexpertisepreference")
    expertise = models.ForeignKey(Expertise, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {self.expertise.name}"

class PartnerPGPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="partnerpgpreference")
    post_graduation = models.ForeignKey(PostGraduation, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {self.post_graduation.name}"

class PartnerGraduationPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="partnergraduationpreference")
    graduation = models.ForeignKey(Graduation, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {self.graduation.name}"


    
class PartnerSpecializationPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="partnerspecializationpreference")
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {self.specialization.name}"

class PartnerReligionPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="partnerreligionpreference")
    religion = models.ForeignKey(Religion, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {self.religion.name}"

    
class PartnerMaritalStatusPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="partnermaritalstatuspreference")
    marital_status = models.ForeignKey(MaritalStatus, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {self.marital_status.name}"


class UserPostGraduation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="partnerpostgraduationpreference")
    post_graduation = models.ForeignKey(PostGraduation, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.name if self.user.name else self.user.mlp_id} -> {self.post_graduation.name}"


class LinkedAccount(models.Model):
    primary_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='primary_user', help_text='Main user account')
    linked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='linked_user', help_text='Linked users account')
    relation = models.CharField(max_length=20, choices=RELATIONS, blank=False, null=False, db_index=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

class Notifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_notifications")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_sender_notifications", null=True, blank=True)
    message = models.CharField(max_length=1000, null=True, blank=True, db_index=True)
    type = models.CharField(max_length=30, null=True, blank=True, db_index=True)
    created_date = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural="Notifications"
        unique_together = ('user', 'sender','message', 'type')

class BlockedUsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking_user')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_user')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, db_index=True)
    
    def save(self, *args, **kwargs):
        if self.user != self.blocked_user:
            super().save(*args, **kwargs)


class SavedUser(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saving_user')
    saved_profile = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_profile')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, db_index=True)

    def save(self, *args, **kwargs):
        if self.user != self.saved_profile:
            super().save(*args, **kwargs)


class Intrest(models.Model):
    invitation_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitation_from')
    invitation_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitation_to')
    status = models.CharField(max_length=20, default="Pending", db_index=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, db_index=True)

    def save(self, *args, **kwargs):
        if self.invitation_by != self.invitation_to:
            super().save(*args, **kwargs)


class ConnectionList(models.Model):
    user_one = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_one')
    user_two = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_two')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.user_one != self.user_two:
            super().save(*args, **kwargs)
            
class OTPSession(models.Model):
    otp = models.CharField(max_length=4)
    expires_at = models.DateTimeField()
    session_id = models.UUIDField()
    identifier = models.CharField(max_length=255)

    def __str__(self):
        return self.identifier
    class Meta:
        verbose_name_plural="OTP_Sessions"

class AuthToken(models.Model):
    user = models.ForeignKey(User, related_name="user_token", on_delete=models.CASCADE)
    token = models.CharField(max_length=40, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.token)
        
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_key()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()
    class Meta:
        verbose_name_plural="Auth_Tokens"

class ProfileView(models.Model):
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_views')
    viewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_viewed')
    viewed_at = models.DateTimeField(default=timezone.now, db_index=True)
    visited_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-visited_at']  # Order by the latest views

    def __str__(self):
        return f'{self.viewer} -> {self.viewed_user}'


class RatingReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='ratingreview')
    rating = models.FloatField()
    review_text = models.TextField(blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    approve = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'{self.user} -> {self.rating}'
    
class Stories(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="userstories")
    url = models.CharField(max_length=1000, null=True, blank=True)
    type = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural="Stories"

class ViewedStories(models.Model):
    story = models.ForeignKey(Stories, on_delete=models.CASCADE, related_name="viewed_stories")
    viewed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stories_viewedby")
    is_viewed = models.BooleanField(default=True)
    viewed_datetime = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural="Viewed_Stories"



class BachelorOfTheDay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bachelor_of_the_day')
    religion = models.CharField(max_length=300,null=True,db_index=True)
    date_selected = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def get_latest_bachelor_of_the_day(cls, religion, user_gender):
        # current_date_midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # # Get the datetime for the next day at midnight
        # next_day_midnight = current_date_midnight + timedelta(days=1)
        current_date_midnight = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get the datetime for the previous day at midnight
        previous_day_midnight = current_date_midnight - timedelta(days=1)
        
        # Query the bachelor of the day added between two midnights
        latest_bachelor = cls.objects.filter(
            religion=religion,
            user__gender=user_gender,
            date_selected__gte=previous_day_midnight,
            date_selected__lt=current_date_midnight
        ).first()
        if latest_bachelor:
           return latest_bachelor
        return None
   



class SuccessStory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE , related_name='success_stories')
    partner_mlp_id= models.CharField(max_length=50, unique=True, null=True, blank=False,db_index=True)
    partner_name=models.CharField(max_length=100,null=True,db_index=True)
    partner_mobile_number=models.CharField(max_length=20,null=True,blank=False, db_index=True)
    reason = models.CharField(max_length=180,null=True,db_index=True)
    experience = models.CharField(max_length=180 , null=True,db_index=True)
    story = models.TextField()
    image = models.TextField(default="[]", db_index=True)  
    video = models.TextField(default="[]", db_index=True)
    created_date = models.DateTimeField(default=timezone.now)  
    

    def __str__(self):
        return f"Success story of {self.user.name}"
          

class DeleteProfile(models.Model):
    mlp_id = models.CharField(max_length=50,db_index=True)
    reason = models.CharField(max_length=180,null=True,db_index=True)
    experience = models.CharField(max_length=180 , null=True,db_index=True)
    deleted_at = models.DateTimeField()

    def __str__(self):
        return f"Deleted profile for MLP ID: {self.mlp_id}"

class ReportUsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reporting_user')
    report_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_user')
    report_user_mlp_id = models.CharField(max_length=255, null=True, blank=True, db_index=True) 
    reason = models.TextField(default="[]", null=True, blank=True, db_index=True)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        verbose_name_plural = "Report Users"

    def save(self, *args, **kwargs):
        # Automatically populate `report_user_mlp_id` from the `report_user` before saving
        if self.report_user and not self.report_user_mlp_id:
            self.report_user_mlp_id = self.report_user.mlp_id
        super().save(*args, **kwargs)    
    
    def __str__(self):
        return f"User: {self.user} has reported user {self.report_user}"
    

