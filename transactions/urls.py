from django.urls import path
from . import views

urlpatterns = [
    path("pay-u",views.payU,name='payU'),
    path('ios-purchase/', views.ios_purchase, name='ios_purchase'),
    path("get-subscriptions",views.get_subscriptions,name='get_subscriptions'),
    path("get-ios-subscriptions",views.get_ios_subscriptions,name='get_subscriptions'),
    path("upgrade-subscriptions-list",views.upgrade_subscriptions,name='upgrade_subscriptions'),
    path("apply-coupon",views.apply_coupons,name='apply_coupons'),
    path("get-coupons",views.get_user_coupons,name='get_user_coupons'),
    path("web_app_payment/<str:logged_mlp_id>/",views.web_app_payment_post_view,name="web app payment data"),
    path("get_web_app_payment_data/<str:logged_mlp_id>/",views.get_web_app_payment_data_view,name="get_web_app_payment"),
    path('create_payment_link/', views.CreatePaymentLink.as_view(), name='create_payment_link'),
]
