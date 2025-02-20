import json
from django.core.mail import EmailMessage
from MLP import settings
import os
import ast
from MLP.services.templates import registration_email,Interest_received, Interest_accepted,recently_joined, Interest_rejected,Thank_payment,Plan_expire_reminder
import logging
from datetime import datetime


logger = logging.getLogger("error_logger")

def send_email(subject, message, to_email):
    try:
        email = EmailMessage(subject, message, from_email="shreya@medicolifepartner.com",to=to_email)
        email.content_subtype = 'html'
        email.send()
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

def set_email_content_successfulregistration(user_obj):
    try:
        email_content={}
        email_msg = registration_email.email_conf
        email_msg = email_msg.replace("{name}",user_obj.name)
        email_msg = email_msg.replace("{mobile}",user_obj.mobile_number if user_obj.mobile_number else "NA")
        email_msg = email_msg.replace("{email}",user_obj.email if user_obj.email else "NA")
        email_msg = email_msg.replace("{password}",user_obj.password if user_obj.password else "NA")
        email_content['message'] = email_msg
        return email_content
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

def set_email_interestreceived(name,user_obj, grad, postgrad,img,match_percent):
    try:
        email_content={}
        email_msg = Interest_received.email_conf
        email_msg = email_msg.replace("{name}",name if name else "NA")
        email_msg = email_msg.replace("{candidate_name}",user_obj.name if user_obj.name else "NA")
        email_msg = email_msg.replace("{candidate_mlp}",user_obj.mlp_id if user_obj.mlp_id else "NA")
        email_msg = email_msg.replace("{candidate_dob}",str(user_obj.dob) if user_obj.dob else "NA")
        email_msg = email_msg.replace("{candidate_height}",str(user_obj.height) if user_obj.height else "NA")
        profile_pictures = json.loads(user_obj.profile_pictures)
        first_profile_picture = profile_pictures[0] if profile_pictures else "NA"
        email_msg = email_msg.replace("{candidate_img}", first_profile_picture)
        age = calculate_age(user_obj.dob) if user_obj.dob else "NA"
        email_msg = email_msg.replace("{candidate_age}", str(age))
        email_msg = email_msg.replace("{candidate_grad}",grad if grad else "NA")
        email_msg = email_msg.replace("{candidate_postgrad}",postgrad if postgrad else "NA")
        email_msg = email_msg.replace("{candidate_caste}",user_obj.caste if user_obj.caste else "NA")
        email_msg = email_msg.replace("{candidate_city}",user_obj.city if user_obj.city else "NA")
       # email_msg = email_msg.replace("{image}",img if img else "NA")
        email_msg = email_msg.replace("{matched_percentage}",str(match_percent) if match_percent else "NA")
        email_content['message'] = email_msg
        return email_content
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

def set_email_interestaccepted(user_obj,name, grad, postgrad,img,match_percent):
    try:
        email_content={}
        email_msg = Interest_accepted.email_conf
        email_msg = email_msg.replace("{name}",name if name else "NA")
        email_msg = email_msg.replace("{candidate_name}",user_obj.name if user_obj.name else "NA")
        email_msg = email_msg.replace("{candidate_mlp}",user_obj.mlp_id if user_obj.mlp_id else "NA")
        email_msg = email_msg.replace("{candidate_dob}",str(user_obj.dob) if user_obj.dob else "NA")
        email_msg = email_msg.replace("{candidate_height}",str(user_obj.height) if user_obj.height else "NA")
        profile_pictures = json.loads(user_obj.profile_pictures)
        first_profile_picture = profile_pictures[0] if profile_pictures else "NA"
        email_msg = email_msg.replace("{candidate_img}", first_profile_picture)
        age = calculate_age(user_obj.dob) if user_obj.dob else "NA"
        email_msg = email_msg.replace("{candidate_age}", str(age))
        email_msg = email_msg.replace("{candidate_grad}",grad if grad else "NA")
        email_msg = email_msg.replace("{candidate_postgrad}",postgrad if postgrad else "NA")
        email_msg = email_msg.replace("{candidate_caste}",user_obj.caste if user_obj.caste else "NA")
        email_msg = email_msg.replace("{candidate_city}",user_obj.city if user_obj.city else "NA")
       # email_msg = email_msg.replace("{image}",img if img else "NA")
        email_msg = email_msg.replace("{matched_percentage}",str(match_percent) if match_percent else "NA")
        email_content['message'] = email_msg
        return email_content
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

def set_email_interestrejected(user_obj,name, grad, postgrad,img,match_percent):
    try:
        email_content={}
        email_msg = Interest_rejected.email_conf
        email_msg = email_msg.replace("{name}",name if name else "NA")
        email_msg = email_msg.replace("{candidate_name}",user_obj.name if user_obj.name else "NA")
        email_msg = email_msg.replace("{candidate_mlp}",user_obj.mlp_id if user_obj.mlp_id else "NA")
        email_msg = email_msg.replace("{candidate_dob}",str(user_obj.dob) if user_obj.dob else "NA")
        email_msg = email_msg.replace("{candidate_height}",str(user_obj.height) if user_obj.height else "NA")
        profile_pictures = json.loads(user_obj.profile_pictures)
        first_profile_picture = profile_pictures[0] if profile_pictures else "NA"
        email_msg = email_msg.replace("{candidate_img}", first_profile_picture)
        age = calculate_age(user_obj.dob) if user_obj.dob else "NA"
        email_msg = email_msg.replace("{candidate_age}", str(age))
        email_msg = email_msg.replace("{candidate_grad}",grad if grad else "NA")
        email_msg = email_msg.replace("{candidate_postgrad}",postgrad if postgrad else "NA")
        email_msg = email_msg.replace("{candidate_caste}",user_obj.caste if user_obj.caste else "NA")
        email_msg = email_msg.replace("{candidate_city}",user_obj.city if user_obj.city else "NA")
       # email_msg = email_msg.replace("{image}",img if img else "NA")
        email_msg = email_msg.replace("{matched_percentage}",str(match_percent) if match_percent else "NA")
        email_content['message'] = email_msg
        return email_content
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')
        

def set_email_newly_joined(suggested_users_data):
    try:
        email_content = {}
        email_msg_template = recently_joined.email_conf  # Use the template content directly

        formatted_data_list = []

        for data in suggested_users_data:
            formatted_data = {
                "candidate_name": data.get("name", "NA"),
                "candidate_dob": str(data.get("dob", "NA")),
                "candidate_height": str(data.get("height", "NA")),
                "candidate_grad": data.get("graduation_id", "NA"),
                "candidate_postgrad": data.get("user_post_graduation", ["NA"])[0],
                "candidate_caste": data.get("caste", "NA"),
                "candidate_city": data.get("city", "NA"),
                "candidate_religion": data.get("religion", "NA")
            }

            email_msg_middle = f"""
                <div id="profile">
                    <h4>Name: {formatted_data['candidate_name']}</h4>
                    <h4>BirthDate: {formatted_data['candidate_dob']}</h4>
                    <h4>Height: {formatted_data['candidate_height']}</h4>
                    <h4>Graduation: {formatted_data['candidate_grad']}</h4>
                    <h4>Postgraduation: {formatted_data['candidate_postgrad']}</h4>
                    <h4>Caste: {formatted_data['candidate_caste']}</h4>
                    <h4>City: {formatted_data['candidate_city']}</h4>
                    <h4>Religion: {formatted_data['candidate_religion']}</h4>
                </div>"""

            formatted_data_list.append(email_msg_middle)

    
        middle_content = "\n".join(formatted_data_list)

        email_msg = email_msg_template.replace("{middle_content_placeholder}", middle_content)

        email_content['message'] = email_msg
        return email_content
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')


def set_email_thank_you_payment(user_obj):
    try:
        email_content = {}
        email_msg = Thank_payment.email_conf
        email_msg = email_msg.replace("{candidate_name}", user_obj.name if user_obj.name else "NA")
        email_msg = email_msg.replace("{candidate_mlp_id}", user_obj.mlp_id if user_obj.mlp_id else "NA")
        # email_msg = email_msg.replace("{amount}", str(amount) if amount else "NA")  
        # email_msg = email_msg.replace("{subscription_name}", subscription_name if subscription_name else "NA")
        # email_msg = email_msg.replace("{subscription_duration}", str(subscription_duration) if subscription_duration else "NA")  
        email_content['message'] = email_msg
        return email_content
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

def set_email_plan_expire_reminder(user_obj,remaining_days):
    try:
        email_content = {}
        email_msg = Plan_expire_reminder.email_conf
        email_msg = email_msg.replace("{candidate_name}", user_obj.name if user_obj.name else "NA")
        email_msg = email_msg.replace("{remaining_days}", str(remaining_days) if remaining_days else "NA")  
       # email_msg = email_msg.replace("{expiry_end_date}", str(expiry_end_date) if expiry_end_date else "NA")
        email_content['message'] = email_msg
        return email_content
    except Exception as e:
        logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')    


def calculate_age(birth_date):
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age
