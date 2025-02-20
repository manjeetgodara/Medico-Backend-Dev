import logging
from celery import shared_task
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from users.models import *
from pyfcm import FCMNotification

logger = logging.getLogger("error_logger")
push_service = FCMNotification(api_key=os.getenv("SERVER_KEY"))

# @receiver(post_save, sender=Promotions)
# def send_notifications_promotion(sender, instance, created, **kwargs):
#     if created:
#         if instance.users=="all":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 Notifications.objects.create(
#                     user=user,
#                     message=instance.message_body,
#                     type="promotion"
#                 )
#                 custom_data={
#                     "screen":"promotions",
#                     "userid":user.mlp_id
#                     }
#                 if user.notification_token!=None:
                    
#                     push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                 all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                
#                 notificationtokens=[]
#                 for i in all_linked_users:
#                     if i.linked_user.notification_token:
#                         notificationtokens.append(i.linked_user.notification_token) 
                
#                 if notificationtokens:
                    
#                     push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="silverregular":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Silver" and existing_subscription.subscription.regular_plan==True:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="goldregular":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Gold" and existing_subscription.subscription.regular_plan==True:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="platinumregular":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Platinum" and existing_subscription.subscription.regular_plan==True:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
#                     if user.notification_token!=None:
#                         custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="silver":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Silver" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="gold":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Gold" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="platinum":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Platinum" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="premium":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Premium" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()
#         elif instance.users=="Noplans":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if not existing_subscription:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=instance.message_body,
#                         type="promotion"
#                     )
                    
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=instance.message_title,message_body=instance.message_body,data_message=custom_data)
#             instance.sent=True
#             instance.save()




# @shared_task
# def send_notifications_promotion(promotion_id):
#     response = {
#         'status_code': 500,
#         'message': 'Internal server error'
#     }
#     try:
#         promotion = Promotions.objects.get(id=promotion_id)
#         #if sent == True then function return
#         if promotion.sent:
#             return
        
#         if promotion.users=="all":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 Notifications.objects.create(
#                     user=user,
#                     message=promotion.message_body,
#                     type="promotion"
#                 )
#                 custom_data={
#                     "screen":"promotions",
#                     "userid":user.mlp_id
#                     }
#                 if user.notification_token!=None:
                    
#                     push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                 all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                
#                 notificationtokens=[]
#                 for i in all_linked_users:
#                     if i.linked_user.notification_token:
#                         notificationtokens.append(i.linked_user.notification_token) 
                
#                 if notificationtokens:
                    
#                     push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="silverregular":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Silver" and existing_subscription.subscription.regular_plan==True:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="goldregular":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Gold" and existing_subscription.subscription.regular_plan==True:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="platinumregular":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Platinum" and existing_subscription.subscription.regular_plan==True:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
#                     if user.notification_token!=None:
#                         custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="silver":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Silver" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="gold":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Gold" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="platinum":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Platinum" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="premium":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if existing_subscription and existing_subscription.subscription.name=="Premium" and existing_subscription.subscription.regular_plan==False:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()
#         elif promotion.users=="Noplans":
#             all_users = User.objects.filter(is_active=True)
#             for user in all_users:
#                 existing_subscription=UserSubscription.objects.filter(user=user, is_subscription_active=True).first()
#                 if not existing_subscription:
                    
#                     Notifications.objects.create(
#                         user=user,
#                         message=promotion.message_body,
#                         type="promotion"
#                     )
                    
#                     custom_data={
#                         "screen":"promotions",
#                         "userid":user.mlp_id
#                         }
#                     if user.notification_token!=None:
                        
#                         push_service.notify_single_device(registration_id=user.notification_token,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#                     all_linked_users=LinkedAccount.objects.filter(primary_user=user).all()
                    
#                     notificationtokens=[]
#                     for i in all_linked_users:
#                         if i.linked_user.notification_token:
#                             notificationtokens.append(i.linked_user.notification_token) 
                    
#                     if notificationtokens:
                        
#                         push_service.notify_multiple_devices(registration_ids=notificationtokens,message_title=promotion.message_title,message_body=promotion.message_body,data_message=custom_data)
#             promotion.sent=True
#             promotion.save()

#     except Exception as e:
#         logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
#         # traceback.print_exc()
#         return response




                