from django.urls import path

from misc.service import CreateUserView

# from misc.service import CreateUserView
from . import views

urlpatterns = [
    path("sync/",views.sync,name='sync'),
    path("log-data/",views.reterieve_sync_data, name="change log data in app") ,
    path("user_sync/",views.user_data_sync,name='user data syncing from web'), 
    path("user_data_subs/",views.UsersWithSubscriptionAPIView.as_view(),name='user data with subscription'),
    path("user_data_prov/",views.UsersWithProvisionalAPIView.as_view(),name="provisional user data"),
    path('registeration_sync/',CreateUserView.as_view(),name="register user sync")
]
