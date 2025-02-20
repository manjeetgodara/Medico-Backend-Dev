from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/availability/(?P<MLP_id>\w+)/$", consumers.UserAvailability.as_asgi()),
]