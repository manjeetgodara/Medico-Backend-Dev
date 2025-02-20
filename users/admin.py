from django.contrib import admin

from misc.models import ChangeLog
from .models import *
from django import forms
from django.db.models import Q
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)



class TimePeriodFilter(admin.SimpleListFilter):
    title = 'User Creation Time Period'
    parameter_name = 'time_period'

    def lookups(self, request, model_admin):
        return (
            ('last_1_day', 'Last 1 Day'),
            ('last_7_days', 'Last 7 Days'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'last_1_day':
            last_1_day = now - timedelta(days=1)
            return queryset.filter(created_date__gte=last_1_day)
        if self.value() == 'last_7_days':
            last_7_days = now - timedelta(days=7)
            return queryset.filter(created_date__gte=last_7_days)
        
        return queryset

# Custom filter for mandatory questions completed
class MandatoryQuestionsFilter(admin.SimpleListFilter):
    title = 'Mandatory Questions Completed'
    parameter_name = 'mandatory_questions_completed'

    def lookups(self, request, model_admin):
        return (
            ('completed', 'Completed'),
            ('not_completed', 'Not Completed'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'completed':
            return queryset.filter(mandatory_questions_completed=True)
        if self.value() == 'not_completed':
            return queryset.filter(mandatory_questions_completed=False)
        return queryset


# Custom Filter for Subscription and Mandatory Questions Status
class SubscriptionStatusFilter(admin.SimpleListFilter):
    title = 'Subscription Status'  # Display title in the admin panel
    parameter_name = 'subscription_status'  # Internal name for the filter

    def lookups(self, request, model_admin):
        # Define the filter categories and their labels
        return (
            ('provisional', 'Provisional'),
            ('active', 'Active'),
            ('remove', 'Remove'),
            ('pending', 'Pending'),
            ('wrong', 'Wrong'),
        )

    def queryset(self, request, queryset):
        # Apply different filters based on the selected option
        if self.value() == 'provisional':
            return queryset.filter(can_upgrade_subscription=-1, mandatory_questions_completed=True, is_active=True,is_wrong=False)
        elif self.value() == 'active':
            return queryset.filter(usersubscription__is_subscription_active=True)
        elif self.value() == 'remove':
            return queryset.filter(is_active=False)
        elif self.value() == 'pending':
            return queryset.filter(mandatory_questions_completed=False,is_active=True, is_wrong=False)
        elif self.value() == 'wrong':  
            return queryset.filter(is_wrong=True)
        return queryset

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Specify fields to show with an asterisk
        fields_with_asterisk = [
            'mlp_id', 'mobile_number', 'email', 'gender', 'dob', 'religion', 
            'profile_pictures', 'partner_age_preference', 'partner_age_from',
            'partner_age_to', 'completed_post_grad', 'marital_status', 'mandatory_questions_completed'
        ]
        
        for field_name in fields_with_asterisk:
            if field_name in self.fields:
                # Add an asterisk to the field label
                self.fields[field_name].label = f"{self.fields[field_name].label} *"



# Register your models here.
class OTPSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_id', 'identifier', 'expires_at', 'otp',)
    

class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'user', 'created_at',)

class MotherTongueAdmin(admin.ModelAdmin):
    list_display=('id','name')

class LanguagesAdmin(admin.ModelAdmin):
    list_display=('id','name')

class UserAdmin(admin.ModelAdmin):
    list_display=('id','mlp_id','name','gender','is_active','contact_viewed_count','created_date')
    search_fields = ('name','mobile_number','gender','mlp_id')
    form = UserAdminForm

    # Filters for admin panel, including the custom ones
    list_filter = (SubscriptionStatusFilter, TimePeriodFilter,("created_date", DateRangeFilterBuilder()), MandatoryQuestionsFilter, 'gender', 'is_active')


    def contact_viewed_count(self, obj):
        # user_subscription = UserSubscription.objects.filter(
        #     user=obj,
        #         is_subscription_active=True
        #     ).values(
        #         'subscription_id', 'subscription_id__name', 'subscription_id__timeframe', 
        #         'subscription_id__amount', 'subscription_id__description', 
        #         'subscription_id__regular_plan', 'subscription_ios_id', 
        #         'subscription_ios__name', 'subscription_ios__timeframe',
        #         'subscription_ios__amount', 'subscription_ios__description', 
        #         'subscription_ios__regular_plan', 'is_subscription_active', 
        #         'created_date', 'updated_date'
        #     ).first()
        # if user_subscription:
        #    created_date = user_subscription['created_date']
        # contact_viewed= ContactViewed.objects.filter(user=obj).exclude(created_date__lte=created_date).count()
        contact_viewed = ContactViewed.objects.filter(user=obj).count()
        profile_viewed=  ProfileView.objects.filter(viewed_user=obj).count()
        return f"{contact_viewed}/{profile_viewed}"
       
    contact_viewed_count.short_description = "Contact Viewed Count / Profile Viewed Count"

    # Customize the queryset to enhance performance or add custom behavior
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


class UserSubscriptionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['user']
    list_display = ('user', 'subscription', 'subscription_ios',  'created_date', 'updated_date')
    search_fields = ('user__name', 'user__mlp_id', 'subscription__name', 'subscription_ios__name')
    list_filter = ('is_subscription_active',)  

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

class SpecializationAdmin(admin.ModelAdmin):
    list_display=('id','name')

class SiblingsAdmin(admin.ModelAdmin):
    list_display=('id', 'user','sibling_name')




class NotificationsAdmin(admin.ModelAdmin):
    list_display=('id','user', 'message', 'created_date')

class StoriesAdmin(admin.ModelAdmin):
    list_display=('id','user','url','type')

class ViewedStoriesAdmin(admin.ModelAdmin):
    list_display=('id','story','viewed_by','is_viewed')

class ContactViewedAdmin(admin.ModelAdmin):
    list_display = ('id','user','seen_contact','created_date')

class ReportUsersAdmin(admin.ModelAdmin):
    list_display=('id','user', 'user_mlp_id','report_user','report_user_mlpid','reason')
    search_fields = ('user__name', 'report_user__name')

    def user_mlp_id(self, obj):
        return obj.user.mlp_id if obj.user else None
    user_mlp_id.short_description = 'User MLP ID'  # Column header in the admin panel

    # Custom method to display `report_user`'s `mlp_id`
    def report_user_mlpid(self, obj):
        return obj.report_user.mlp_id if obj.report_user else None
    report_user_mlpid.short_description = 'Reported User MLP ID'

class InterestAdmin(admin.ModelAdmin):
    list_display=('invitation_by', 'invitation_to', 'status')

class ConnectionListAdmin(admin.ModelAdmin):
    list_display=('user_one', 'user_two')


class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'app_name', 'model_name', 'fields', 'created_at')
    list_filter = ('action', 'app_name', 'model_name')
    search_fields = ('app_name', 'model_name')  # Basic search fields

    def get_search_results(self, request, queryset, search_term):
        # Call the parent method to retain default functionality
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Add custom JSONField search for `mlp_id` and `phone_number`
        if search_term:
            custom_queryset = ChangeLog.objects.filter(
                Q(fields__mlp_id__icontains=search_term) | Q(fields__mobile_number__icontains=search_term) |  Q(fields__name__icontains=search_term)
            )
            queryset |= custom_queryset  # Combine with default queryset

        return queryset, use_distinct

class BachelorOfTheDayAdmin(admin.ModelAdmin):
    list_display = ['user', 'religion', 'date_selected']  

class LinkedAccountAdmin(admin.ModelAdmin):
    list_display = ['primary_user', 'linked_user']  


class RatingReviewAdmin(admin.ModelAdmin):
    list_display = ['user','rating','review_text', 'approve']


class SuccessStoryAdmin(admin.ModelAdmin):
    autocomplete_fields = ['user']  # Enable autocomplete for the user field
    # list_display = ('user', 'partner_mlp_id', 'partner_name', 'created_date')
    search_fields = ('user__mlp_id',)  # Enable searching by mlp_id in the admin

# admin.site.register(SuccessStory, SuccessStoryAdmin)
   
       
admin.site.register(ChangeLog,ChangeLogAdmin)
admin.site.register(Expertise)
admin.site.register(Graduation)
admin.site.register(PostGraduation)
admin.site.register(Religion)
admin.site.register(MaritalStatus)
admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
admin.site.register(UserSubscription,UserSubscriptionAdmin)
admin.site.register(SeenUser)
admin.site.register(SavedUser)
admin.site.register(UserPostGraduation)
admin.site.register(PartnerExpertisePreference)
admin.site.register(PartnerReligionPreference)
admin.site.register(PartnerMaritalStatusPreference)
admin.site.register(PartnerSpecializationPreference)
admin.site.register(Notifications, NotificationsAdmin)
admin.site.register(Stories,StoriesAdmin)
admin.site.register(ViewedStories, ViewedStoriesAdmin)
admin.site.register(PartnerGraduationPreference)
admin.site.register(PartnerPGPreference)
admin.site.register(Caste)
admin.site.register(SubCaste)
admin.site.register(BlockedUsers)
admin.site.register(LinkedAccount,LinkedAccountAdmin)
admin.site.register(Intrest, InterestAdmin)
admin.site.register(ConnectionList, ConnectionListAdmin)
admin.site.register(AuthToken, AuthTokenAdmin)
admin.site.register(OTPSession, OTPSessionAdmin)
admin.site.register(ProfileView)
admin.site.register(MotherTongue,MotherTongueAdmin)
admin.site.register(Languages, LanguagesAdmin)
# admin.site.register(Profession,ProfessionAdmin)
admin.site.register(Specialization, SpecializationAdmin)
admin.site.register(Siblings, SiblingsAdmin)
admin.site.register(ContactViewed, ContactViewedAdmin)
admin.site.register(RatingReview, RatingReviewAdmin)
admin.site.register(BachelorOfTheDay)
admin.site.register(SuccessStory, SuccessStoryAdmin)
admin.site.register(ReportUsers, ReportUsersAdmin)
admin.site.register(DeleteProfile)
admin.site.register(AppleSubscription)


