import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from device_management import consumers
from django.urls import path
from device_management.consumers import VideoStreamConsumer,DomTreeConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform_2025_new.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            [
                # 在这里添加 WebSocket 路由
                path('ws/video_stream/', VideoStreamConsumer.as_asgi()),
                # DOM树的ws路由
                path('ws/dom_tree/', DomTreeConsumer.as_asgi())
            ]
        )
    ),
})
