import json

from channels.generic.websocket import WebsocketConsumer
from .models import *
from .utils import *
import logging
from .constants import heart_beat_interval

logger = logging.getLogger("error_logger")
buffer_time = 5
redis_client = connect()
expiry_time = heart_beat_interval + buffer_time

class UserAvailability(WebsocketConsumer):
    def connect(self):
        try:
            self.mlp_id = self.scope["url_route"]["kwargs"]["MLP_id"].strip()
            self.accept()
            user = User.objects.get(mlp_id=self.mlp_id)
            user.activity_status = True
            user.last_seen = None  
            user.save()
            self.redis_key = f"online_{self.mlp_id}"
            redis_client.setex(self.redis_key,expiry_time, self.mlp_id)
            print(f"Set Redis key for: {self.mlp_id}")
            print("connection extablished for: ", self.mlp_id)
            response = {
                "heart_beat_in_sec": heart_beat_interval
            }
            self.send(text_data=json.dumps(response))
            res = add_field_firebase(self.mlp_id)
            print(res)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

    def disconnect(self, close_code):
        try:
            print("connection disconnected for: ", self.mlp_id)
            user = User.objects.get(mlp_id=self.mlp_id)
            user.activity_status = False
            user.last_seen = timezone.now()
            user.save()
            
            redis_client.delete(self.redis_key)
            print(f"Deleted Redis key for: {self.mlp_id}")
            res = delete_field_firebase(self.mlp_id)
            print(res)
        except Exception as e:
            logger.error(f'{e.__traceback__.tb_lineno} - {str(e)}')

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print("test message: ", text_data)

        redis_client.setex(self.redis_key,expiry_time,self.redis_key.split("_")[1])

        response = {
            "message": "PONG",
        }
        self.send(text_data=json.dumps(response))

        #self.send(text_data=json.dumps({"message": message}))