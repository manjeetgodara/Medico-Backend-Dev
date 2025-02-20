from datetime import datetime

from users.models import User
from users.service import newly_joined_users_email


def cronjob():
    try:
        current_time = datetime.now()

        if current_time.weekday() == 6:  
            all_users = User.objects.filter(is_active=True, is_wrong=False,mandatory_questions_completed=True) 
           
            for user in all_users:
                mlp_id = user.mlp_id
                newly_joined_users_email(mlp_id)
    except Exception as e:
        print(f'{e.__traceback__.tb_lineno} - {str(e)}')