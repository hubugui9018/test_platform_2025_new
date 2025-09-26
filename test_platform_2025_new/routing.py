from django.urls import path
from device_management.consumers import VideoStreamConsumer

websocket_urlpatterns = [
    path('ws/video_stream/', VideoStreamConsumer.as_asgi()),
]
